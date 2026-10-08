#!/usr/bin/env python3
"""Prove an animated SVG does the one thing XML reading cannot decide.

Why this exists
---------------
`lint_svg_anim.py` reads the file. This runs it in a real browser with a real
clock. There is one defect that reads as perfectly valid markup and is still
visibly wrong:

  **Parked element.** Something gated behind a *positive* `begin` has no effect
  until that time. Per the static-first rule it must be invisible until then, so
  it carries base `opacity="0"`. When it does not, it sits at its base value -
  a traveller parked at the canvas origin, in full view. This is the trap that
  bit the terminal example (#8) and the logo pre-roll (#9), and it is exactly
  the class `measure_frame0.py` could not decide statically after four measured
  attempts, because deciding it needs a running browser and a clock.

What is deliberately NOT here
-----------------------------
Two sibling checks were built and then **cut**, and the reason is worth keeping:

  * **"never changes"** (is the browser applying this animation at all?) and
  * **"visible loop seam"** (does the loop jump once per cycle?)

Both were implemented, then measured against all 52 shipped examples. Sampling
each animation across its *own* window rather than the file's longest loop -
which is required, because backdrop-rain has 70 animations of 0.92s inside a
30s loop and evenly spaced global samples never land inside one - still left
175 and 250 warnings respectively on a corpus that is known good. An instrument
that fires on 425 known-good files is worse than no instrument, so they were
removed rather than shipped with a caveat.

Do not reintroduce either without first getting **zero** warnings on all 52
examples. That is the bar `scripts/check_workflow.py` set, and it is the same
bar `measure_frame0.py` failed to clear four times.

Usage
-----
    python scripts/verify.py file.svg
    python scripts/verify.py assets/examples/*.svg      # exit 1 if any fail
    python scripts/verify.py file.svg --json

Exit codes: 0 all pass, 1 something failed, 2 Playwright unavailable.

Requires: pip install playwright && playwright install chromium
"""
import argparse
import glob
import json
import os
import re
import sys

# How many samples across one loop. More samples catch shorter or offset
# animations; 9 keeps the runtime low enough to run over 52 files.
DEFAULT_SAMPLES = 9


def longest_dur(text):
    """Longest duration in the file, so samples span a whole loop."""
    durs = []
    for m in re.finditer(r'dur="([\d.]+)(ms|s)"', text):
        v = float(m.group(1))
        durs.append(v / 1000 if m.group(2) == "ms" else v)
    for m in re.finditer(r"animation:[^;}]*?([\d.]+)(ms|s)", text):
        v = float(m.group(1))
        durs.append(v / 1000 if m.group(2) == "ms" else v)
    return max(durs) if durs else 4.0


# Runs in the page. For every animation element, resolve the element it targets
# and read the attribute it animates, at whatever the current time is.
PROBE = r"""
() => {
  const s = document.querySelector('svg');
  const out = { anims: [], viewBox: null };
  const secs = (v, dflt) => {
    if (!v) return dflt;
    const m = String(v).trim().match(/^(-?[\d.]+)(ms|s)$/);
    if (!m) return dflt;
    return parseFloat(m[1]) / (m[2] === 'ms' ? 1000 : 1);
  };

  for (const a of s.querySelectorAll('animate, animateTransform, animateMotion, set')) {
    const owner = a.parentElement;
    if (!owner) continue;
    const tag = a.tagName;
    const attr = tag === 'animateMotion' ? 'transform'
               : a.getAttribute('attributeName');
    if (tag !== 'animateMotion' && !attr) continue;
    const cs = getComputedStyle(owner);
    out.anims.push({
      i: out.anims.length,
      tag: tag, attr: attr, owner: owner.tagName,
      begin: a.getAttribute('begin') || '0s',
      // negative begins are legal and common; keep them, the caller clamps
      beginSec: secs(a.getAttribute('begin'), 0),
      durSec: secs(a.getAttribute('dur'), null),
      repeat: a.getAttribute('repeatCount'),
      values: a.getAttribute('values'),
      calcMode: a.getAttribute('calcMode'),
      ctm: cs.transform,
      opacity: parseFloat(cs.opacity),
      baseOpacity: owner.getAttribute('opacity'),
      val: attr && attr !== 'transform' ? owner.getAttribute(attr) : null,
      id: owner.id || null
    });
  }

  for (const e of s.querySelectorAll('*')) {
    if (!e.getAnimations) continue;
    for (const a of e.getAnimations()) {
      if (a.animationName === undefined) continue;   // SMIL appears here too
      const cs = getComputedStyle(e);
      const t = a.effect && a.effect.getTiming();
      out.anims.push({
        i: out.anims.length, tag: 'CSS', attr: a.animationName, owner: e.tagName,
        begin: '0s', beginSec: 0, durSec: t ? t.duration / 1000 : null,
        repeat: t ? String(t.iterations) : null,
        values: null, calcMode: null,
        ctm: cs.transform, opacity: parseFloat(cs.opacity),
        baseOpacity: e.getAttribute('opacity'),
        val: cs.fill, id: e.id || null
      });
    }
  }

  const va = s.querySelector(':scope > animate[attributeName="viewBox"]');
  out.viewBox = va ? s.getAttribute('viewBox') : null;
  return out;
}
"""


def set_time(page, t):
    page.evaluate(
        """(t) => {
            const s = document.querySelector('svg');
            s.pauseAnimations(); s.setCurrentTime(t);
            document.getAnimations().forEach(a => {
                try { a.pause(); a.currentTime = t * 1000; } catch (e) {}
            });
        }""",
        t,
    )


def _secs(v, dflt=None):
    m = re.match(r"^\s*(-?[\d.]+)(ms|s)\s*$", str(v or ""))
    if not m:
        return dflt
    return float(m.group(1)) / (1000 if m.group(2) == "ms" else 1)


def run_file(path, samples=DEFAULT_SAMPLES, times=None):
    """Return (errors, warnings, notes) for one file."""
    text = open(path, encoding="utf-8").read()

    from playwright.sync_api import sync_playwright

    html = re.sub(r"<\?xml[^>]*\?>", "", text)
    page_html = (
        "<!doctype html><html><body style='margin:0;background:#000'>"
        "<div id='wrap' style='width:1200px'>%s</div></body></html>" % html
    )

    errors, warnings, notes = [], [], []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1200, "height": 700})
        page.set_content(page_html)
        page.wait_for_timeout(150)
        page.evaluate(
            """() => { const s = document.querySelector('svg');
                       s.setAttribute('width','100%'); s.setAttribute('height','100%'); }"""
        )

        # t=0 only. The parked-element question is entirely about frame 0, and
        # every extra sample is runtime this check does not need.
        set_time(page, 0.0)
        page.wait_for_timeout(50)
        meta = page.evaluate(PROBE)["anims"]
        browser.close()

    if not meta:
        return [], [], ["no animation elements found - this file is a still"]

    # ---- parked element, decided at t=0 with a real clock ----
    # A positive `begin` means no effect until then, so per the static-first
    # rule it must be invisible until then. One report per element: several
    # <animate> children usually share one begin.
    seen = set()
    for a in meta:
        b = _secs(a["begin"], 0.0) or 0.0
        if b <= 0:
            continue
        key = (a["owner"], a["id"], a["begin"])
        if key in seen:
            continue
        op = a["opacity"] if a["opacity"] is not None else 1.0
        if op > 0.02:
            seen.add(key)
            errors.append(
                "parked at t=0: <%s> on <%s%s> has begin=%s so it has no effect "
                "yet, but its opacity is %.2f - give it opacity=\"0\" as a base "
                "value, or pre-roll it with a negative begin"
                % (a["tag"], a["owner"], (" id=%s" % a["id"]) if a["id"] else "",
                   a["begin"], op))

    notes.append("%d animation element(s) checked at frame 0" % len(meta))
    return errors, warnings, notes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("svg", nargs="+")
    ap.add_argument("--times", default=None,
                    help="comma-separated seconds; default spans one loop")
    ap.add_argument("--samples", type=int, default=DEFAULT_SAMPLES)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    files = []
    for pat in args.svg:
        files.extend(sorted(glob.glob(pat)) if any(c in pat for c in "*?[")
                     else [pat])

    try:
        import playwright  # noqa: F401
    except ImportError:
        print("Playwright is not installed; cannot verify by running the file.")
        print("  pip install playwright && playwright install chromium")
        return 2

    times = [float(x) for x in args.times.split(",")] if args.times else None
    total_err = total_warn = 0
    results = {}

    for f in files:
        if f.endswith("-static.svg"):
            continue
        try:
            errs, warns, notes = run_file(f, args.samples, times)
        except Exception as exc:  # noqa: BLE001 - report, do not crash the batch
            errs, warns, notes = ["could not verify: %s" % exc], [], []
        total_err += len(errs)
        total_warn += len(warns)
        results[f] = {"errors": errs, "warnings": warns, "notes": notes}

        if args.json:
            continue
        base = os.path.basename(f)
        if errs or warns:
            print(base)
            for e in errs:
                print("  ERROR: %s" % e)
            for w in warns:
                print("  WARN:  %s" % w)
        else:
            print("  ok  %-42s %s" % (base, notes[0] if notes else ""))

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print("\n%d file(s): %d error(s), %d warning(s)"
              % (len(results), total_err, total_warn))
        if total_err:
            print("An ERROR means the file does not do what its markup claims. "
                  "The fix is at the root cause, not in the linter.")
    return 1 if total_err else 0


if __name__ == "__main__":
    sys.exit(main())