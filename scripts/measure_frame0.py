#!/usr/bin/env python3
"""measure_frame0.py - measure how static-first an SVG is. ADVISORY, not a gate.

    python scripts/measure_frame0.py assets/examples/*.svg
    python scripts/measure_frame0.py --csv assets/examples > report.csv

Why this is not a lint check
----------------------------
Because we could not make one that works. An SVG referenced by an <img> runs in
the W3C's secure animated mode and can silently drop to secure *static* mode in a
PDF export, a markdown rasteriser or a phone preview. When it does, the viewer
gets frame 0 and nothing else. So frame 0 has to be the finished graphic.

We shipped that bug three times - terminal standalone (#8), logo standalone
(#6), and logo inside a compose (#9) - and none were visible to a syntax check.
The obvious fix is a linter rule. Four were built and measured against the real
pre-fix files. All four failed, for reasons worth recording so nobody re-treads
them:

  1. "no <text> invisible at frame 0" (opacity down the ancestor chain)
     FAILS: false-positive city. gauge-dashboard legitimately hides 45 count-up
     labels at frame 0 and renders a complete, readable graphic.

  2. "visible character count at frame 0 vs mid-loop"
     FAILS: reads 1.00 even on the broken files. Opacity cannot see OCCLUSION -
     the pre-fix terminal hid its text under a cover RECT of the window colour,
     so every text node's computed opacity was still 1.

  3. "absolute painted pixels at frame 0"
     FAILS: every example paints a full-canvas background rect, so ink saturates
     at ~100% for every file, broken or not.

  4. "fraction of pixels differing between frame 0 and mid-loop"
     MECHANICALLY WORKS, and still useless as a gate. Measured:
         broken terminal (pre-#8)   2.1% differing
         fixed  terminal (now)      1.9% differing
     The broken file scores HIGHER than the fixed one. Ambient motion - aurora
     blobs, drifting backgrounds, shimmer - dominates the pixel budget and
     swamps the one part that regressed.

The honest conclusion is the one #6 already reached and that we should have
heeded then: separating "hidden until its cue" from "genuinely blank" needs
per-type knowledge of intent, which static analysis does not have. So this stays
a measurement, and CI gates the things it *can* decide: the linter, and
byte-reproducibility.

What it reports, per file
-------------------------
  text@0     fraction of <text> nodes with non-zero effective opacity at frame 0
             (ancestor-aware - a compose wraps each part in a group that is
             itself at opacity 0 outside the part's window, so reading only a
             node's own opacity reports a blank composed part as complete)
  differ%    worst fraction of pixels that change between frame 0 and 0.25/0.5/0.75
             of the loop, sampled from real screenshots

Read it as a trend across a diff, not as a pass/fail. A file whose numbers jump
when you did not touch it is the interesting signal; that is how #9 was found.

Requires Playwright + Chromium.
"""
import base64
import pathlib
import re
import sys

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("measure_frame0.py needs Playwright:  pip install playwright && playwright install chromium",
          file=sys.stderr)
    sys.exit(2)

HTML = """<!doctype html><meta charset="utf-8">
<style>html,body{{margin:0;background:#0b0f15}}</style><div id="w" style="width:1100px">{svg}</div>"""

# Effective opacity of a text node = product of its own and every ancestor's.
TEXT_RATIO = """() => {
  const s = document.querySelector('svg');
  const eff = el => { let o = 1;
    for (let p = el; p && p.nodeType === 1; p = p.parentNode) {
      const cs = getComputedStyle(p);
      if (cs.visibility === 'hidden' || cs.display === 'none') return 0;
      const v = parseFloat(cs.opacity); if (!isNaN(v)) o *= v;
      const f = parseFloat(cs.fillOpacity); if (!isNaN(f) && p.tagName === 'text') o *= f;
    } return o; };
  const t = [...s.querySelectorAll('text')].filter(n => (n.textContent || '').trim());
  if (!t.length) return -1;
  return +(t.filter(n => eff(n) > 0.9).length / t.length).toFixed(2);
}"""

SET_T = """(t) => { const s = document.querySelector('svg'); s.pauseAnimations(); s.setCurrentTime(t); }"""

# Decode two PNG screenshots in-page and count pixels that differ enough to see.
DIFF = """async ([a, b]) => {
  const load = async s => { const i = new Image(); i.src = 'data:image/png;base64,' + s; await i.decode(); return i; };
  const [ia, ib] = await Promise.all([load(a), load(b)]);
  const W = Math.min(ia.width, ib.width), H = Math.min(ia.height, ib.height);
  const c = document.createElement('canvas'); c.width = W; c.height = H;
  const x = c.getContext('2d', { willReadFrequently: true });
  x.drawImage(ia, 0, 0); const da = x.getImageData(0, 0, W, H).data;
  x.clearRect(0, 0, W, H); x.drawImage(ib, 0, 0); const db = x.getImageData(0, 0, W, H).data;
  let d = 0;
  for (let i = 0; i < da.length; i += 4)
    if (Math.abs(da[i]-db[i]) + Math.abs(da[i+1]-db[i+1]) + Math.abs(da[i+2]-db[i+2]) > 60) d++;
  return d / (W * H);
}"""


def measure(page, blank, path):
    svg = path.read_text(encoding="utf-8")
    durs = [float(x) for x in re.findall(r'dur="([\d.]+)s"', svg)]
    dur = max(durs) if durs else 6.0
    page.set_content(HTML.format(svg=svg))
    page.wait_for_timeout(220)
    worst = 0.0
    for frac in (0.25, 0.5, 0.75):
        page.evaluate(SET_T, 0.0)
        page.wait_for_timeout(60)
        a = base64.b64encode(page.locator("#w").screenshot()).decode()
        page.evaluate(SET_T, dur * frac)
        page.wait_for_timeout(60)
        b = base64.b64encode(page.locator("#w").screenshot()).decode()
        worst = max(worst, blank.evaluate(DIFF, [a, b]))
    page.evaluate(SET_T, 0.0)
    page.wait_for_timeout(60)
    return page.evaluate(TEXT_RATIO), worst


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("-")]
    csv = "--csv" in argv
    if not args:
        print(__doc__)
        return 2
    paths = []
    for a in args:
        p = pathlib.Path(a)
        paths.extend(sorted(p.glob("*.svg")) if p.is_dir() else [p])
    paths = [p for p in paths if p.exists()]
    if not paths:
        print("no .svg files matched", file=sys.stderr)
        return 2

    rows = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1200, "height": 1000})
        blank = browser.new_page()
        for p in paths:
            try:
                ratio, diff = measure(page, blank, p)
            except Exception as exc:                          # noqa: BLE001
                print(f"{p.name}: could not render ({exc})", file=sys.stderr)
                ratio, diff = -1.0, -1.0
            rows.append((p.name, ratio, diff))
        browser.close()

    if csv:
        print("file,text_visible_at_frame0,pixels_differing_worst")
        for n, r, d in rows:
            print(f"{n},{r},{d:.4f}")
    else:
        print(f"{'file':<38} {'text@0':>8} {'differ%':>9}")
        for n, r, d in sorted(rows, key=lambda t: (t[1] if t[1] >= 0 else 9, -t[2])):
            print(f"{n:<38} {r:>8.2f} {d*100:>8.1f}%")
        print(f"\n{len(rows)} file(s) measured. Advisory only - see the docstring for why this is not a gate.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))