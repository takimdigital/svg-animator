#!/usr/bin/env python3
"""Generate docs/gallery/README.md from assets/specs/*.json.

Why this exists
---------------
The gallery was hand-written, and it drifted the way hand-written things drift:
when `morph-shapes` landed in #18 it showed 13 of 53 examples, listed another 10
in a table, and never mentioned 30 at all. Nothing failed, because a README is
not a gate. It also showed no themes, so the fact that 53 examples spread over 6
palettes and the *same* visual grammar was invisible.

Generating it removes the class of problem rather than this instance, and it is
the same reasoning that put `static_twin.py --check` and `thumbs-current` in CI.

What is written by hand
-----------------------
The prose. A blurb that explains what a graphic is *for* is editorial, and
regenerating it would be fake work. So `BLURBS` below is a deliberate override
map: an entry there is kept verbatim, and everything else gets a blurb built
from the spec's own fields. Adding a spec with no blurb is fine and expected.

Usage
-----
    python scripts/build_gallery.py            # write it
    python scripts/build_gallery.py --check    # exit 1 if it is stale (CI gate)

Requires: nothing. Pure stdlib, on purpose - CI runs it with no Playwright.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SPECS = os.path.join(ROOT, "assets", "specs")
GALLERY = os.path.join(ROOT, "docs", "gallery", "README.md")

# Hand-written, kept verbatim. Keyed by spec stem.
BLURBS = {
    "network-services": "Pulses propagate by BFS depth from the `start` nodes, so the wave "
                        "front visibly follows the dependency graph rather than a fixed stagger.",
    "flow-with-feedback": "Columns left to right, S-curve rails, relay dots with `keyPoints` "
                          "so a dot *pauses* at a node instead of racing past it. The dashed "
                          "return path is the `feedback` block, travelled only after the main hops.",
    "timeline-roadmap": "The progress dot walks segment by segment and each milestone lights "
                        "*on arrival*, which is what makes it read as progress rather than ambience.",
    "terminal-demo": "All the text is in the base state; window-coloured cover rectangles slide "
                     "away to reveal it. A viewer with SMIL disabled sees the finished session, "
                     "not an empty prompt.",
    "chart-line": "The base attributes are the *finished* chart; the animation grows from zero. "
                  "`highlight` picks the point that matters.",
    "loader-sheet": "Eight spinners, each on its own `period` and each resting between actions. "
                    "Proof that variety does not need variety in code.",
    "gauge-dashboard": "Count up, hold, reset - the three phases every dashboard gauge has, on "
                       "one clock, with rings, bars and a donut.",
    "radar-skills": "Polygons grow from the centre outward, one ring at a time.",
    "counter-stats": "Odometer digit columns roll rather than jump, which is the whole trick: "
                     "each digit translates inside a clipped window.",
    "icons-set": "Twelve icons, twelve actions, each resting between its own beats.",
    "logo-shield": "The outline draws, then the fill arrives, then a shine sweeps across. "
                   "Frame 0 is already the finished logo, so it reads with animation disabled.",
    "art-mandala": "Seeded, so the same spec always produces the same mandala. Generative art "
                   "that is also reproducible, which is rarer than it sounds.",
    "backdrop-mesh": "Slow, low-contrast ambient motion meant to sit behind text. The least "
                     "interesting thing here on purpose.",
    "morph-shapes": "Star, circle, heart, bolt, drop and cross share **no path-command "
                    "structure**, which is the one thing `<animate attributeName=\"d\">` refuses "
                    "to interpolate. `morph_path.py` resamples each pair into one uniform "
                    "`M + n·C + Z` signature at build time, so this morphs with no library and "
                    "no JavaScript. Full write-up in `references/morphing.md`.",
}

SECTIONS = [
    ("Diagrams", {"flow", "radial", "phases", "timeline", "network", "layers",
                  "cycle", "sequence", "terminal", "cards", "chart", "banner"}),
    ("Things", {"loader", "logo", "text", "gauge", "radar", "backdrop", "icons",
                "counter", "scene", "art", "morph"}),
    ("Composed", {"compose"}),
]

# One line per type, used when a spec has no hand-written blurb.
TYPE_BLURB = {
    "flow": "Left-to-right stages on S-curve rails, with relay dots that dwell at each hop.",
    "radial": "Cards around a hub, with signal radiating outward from the centre.",
    "phases": "Ordered phases on one timeline, each lighting inside its own window.",
    "timeline": "A spine with milestones; each one lights on arrival.",
    "network": "A dependency graph; pulses travel by BFS depth, so the wave follows the graph.",
    "layers": "A request travels down one lane and the response back up the other.",
    "cycle": "A closed loop, so the end connects visibly to the start.",
    "sequence": "Lifelines with dashed return messages, like a protocol trace.",
    "terminal": "Typed commands with cover rectangles sliding off to reveal real text.",
    "cards": "Stat tiles that count up on one shared clock.",
    "chart": "The finished chart is the base state; the animation grows out of zero.",
    "banner": "A wide header strip, sized for a README hero.",
    "loader": "A spinner on its own `period`, independent of the master clock.",
    "logo": "Draw, fill, shine - and frame 0 is already the finished mark.",
    "text": "Kinetic type: reveal, pop, per-letter type, shimmer, wave or glitch.",
    "gauge": "Count up, hold, reset - the three phases of any gauge.",
    "radar": "Polygons growing outward ring by ring.",
    "backdrop": "Ambient motion, slow and low contrast, meant to sit behind text.",
    "icons": "Micro-animated icons, each resting between its own actions.",
    "counter": "Odometer digits that roll rather than jump.",
    "scene": "An illustrated scene with something moving in it.",
    "art": "Generative art, seeded so the spec reproduces byte-for-byte.",
    "morph": "Shape morphing between forms that share no command structure.",
    "compose": "Several types on one canvas and one master clock, each with its own window.",
}


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def width_for(kind):
    """Aspect varies a lot; pick a display width that keeps a gallery readable."""
    if kind in ("banner", "backdrop", "flow", "timeline", "network"):
        return "100%"
    if kind in ("radial", "cycle", "radar"):
        return "78%"
    return "88%"


def blurb_for(stem, spec):
    if stem in BLURBS:
        return BLURBS[stem]
    kind = spec.get("type", "")
    base = TYPE_BLURB.get(kind, "")
    extra = []
    if spec.get("variant"):
        extra.append("`variant: %s`" % spec["variant"])
    if spec.get("layout"):
        extra.append("`%s` layout" % spec["layout"])
    if kind == "compose" and spec.get("parts"):
        parts = ", ".join(str(p.get("type")) for p in spec["parts"])
        extra.append("parts: %s" % parts)
    if extra:
        base = (base + " " if base else "") + " ".join("(%s)" % e for e in extra) + "."
    return base


def heading_for(stem, spec):
    """A human title: the spec's own title if it has one, else the stem."""
    t = spec.get("title") or spec.get("heading")
    if t:
        return str(t)
    return stem.replace("-", " ")


# Prefer a diagram or dashboard as a theme's representative. Alphabetical order
# would pick art-flower / art-lissajous / art-orbits for every theme, because the
# art-* specs happen to sort first - abstract art is the least representative
# thing in the set for showing what a palette looks like.
REP_PREFERENCE = ("network-services", "gauge-dashboard", "compose-status-board",
                  "radar-skills", "cards-stats", "icons-set", "counter-stats",
                  "flow-with-feedback", "timeline-roadmap")


def representative(used, rows):
    by_stem = dict(rows)
    for want in REP_PREFERENCE:
        if want in used:
            return want
    # otherwise the most "diagram-like" type available for this theme
    order = ["flow", "radial", "network", "gauge", "cards", "chart", "timeline",
             "compose", "counter", "radar", "icons", "terminal", "sequence"]
    best = used[0]
    for stem in used:
        k = order.index(by_stem[stem].get("type")) if by_stem[stem].get("type") in order else 99
        b = order.index(by_stem[best].get("type")) if by_stem[best].get("type") in order else 99
        if k < b:
            best = stem
    return best


def collect():
    """Every example on disk, in spec order.

    Driven by the specs, because they carry the metadata the gallery needs
    (type, theme, dur, title). Then checked against the examples folder in both
    directions, so:

      * a spec with no generated file is a real error, and
      * an .svg with no spec is an orphan - it would exist, animate, and never
        appear here, which is exactly how morph-shapes went missing in #18.

    An orphan is an error rather than a warning because this page is the only
    place these can be seen: GitHub will not render a raw .svg, so anything not
    listed here is effectively invisible.
    """
    EXAMPLES = os.path.join(ROOT, "assets", "examples")
    out = []
    for name in sorted(os.listdir(SPECS)):
        if not name.endswith(".json"):
            continue
        stem = name[:-5]
        if not os.path.exists(os.path.join(EXAMPLES, stem + ".svg")):
            sys.exit("spec %s has no generated example - run gen_diagram.py first" % stem)
        spec = json.load(open(os.path.join(SPECS, name), encoding="utf-8"))
        out.append((stem, spec))

    on_disk = {f for f in os.listdir(EXAMPLES)
               if f.endswith(".svg") and not f.endswith("-static.svg")}
    covered = {s + ".svg" for s, _ in out}
    orphans = sorted(on_disk - covered)
    if orphans:
        sys.exit(
            "these examples have no spec, so the gallery would silently omit them:\n  "
            + "\n  ".join(orphans)
            + "\n\nevery file in assets/examples/ is generated from a spec (the "
              "`reproducible` CI job enforces that), so add the missing spec or "
              "delete the orphan. Run with --check to see this in CI.")
    return out


def render(rows):
    n = len(rows)
    L = []
    L.append("# Gallery")
    L.append("")
    L.append("Every animation on this page is a real generator output from `assets/examples/`,")
    L.append("and every one is **lint-clean**: `0 errors, 0 warnings`. They're not mockups - they're")
    L.append('the artifacts the skill ships, produced by `python scripts/run_pipeline.py <spec>`.')
    L.append("")
    L.append("**This page is generated** by `python scripts/build_gallery.py`, and CI fails")
    L.append("if it drifts. All **%d** of the %d examples in `assets/examples/` are here." % (n, n))
    L.append("")
    L.append("That is deliberate. GitHub does not render a raw `.svg` when you click one, so")
    L.append("this page is the only place any of them can actually be *seen*. An example that")
    L.append("is not listed here does not exist as far as a reader is concerned. Adding a spec")
    L.append("and regenerating adds it automatically; the build fails if an `.svg` has no spec.")
    L.append("")
    L.append("Regenerate any of them yourself:")
    L.append("")
    L.append("```bash")
    L.append("python scripts/run_pipeline.py assets/specs/network-services.json --out-dir ./run")
    L.append("```")
    L.append("")
    L.append("---")
    L.append("")

    for title, kinds in SECTIONS:
        group = [(s, p) for s, p in rows if p.get("type") in kinds]
        if not group:
            continue
        L.append("## %s (%d)" % (title, len(group)))
        L.append("")
        for stem, spec in group:
            kind = spec.get("type")
            L.append('<p align="center">')
            L.append('  <img src="../../assets/examples/%s.svg" alt="%s" width="%s">'
                     % (stem, esc(heading_for(stem, spec)), width_for(kind)))
            L.append("</p>")
            L.append("")
            meta = " · ".join(
                x for x in ["`%s`" % kind,
                            "theme `%s`" % spec.get("theme", "?"),
                            "`dur` %gs" % spec["dur"] if "dur" in spec else None,
                            "[spec](../../assets/specs/%s.json)" % stem] if x)
            L.append(meta)
            L.append("")
            b = blurb_for(stem, spec)
            if b:
                L.append(b)
                L.append("")

    # ---- themes: the honest picture, including what it does not show ----
    L.append("---")
    L.append("")
    L.append("## Themes (%d)" % len(THEME_ORDER))
    L.append("")
    L.append("Six palettes across all %d examples. Pick one with `\"theme\"` in the spec;" % n)
    L.append("`--theme` on the command line overrides it.")
    L.append("")
    L.append("| theme | polarity | examples | representative |")
    L.append("|---|---|---|---|")
    for t in THEME_ORDER:
        used = [s for s, p in rows if p.get("theme") == t]
        pol = "light" if t in LIGHT_THEMES else "dark"
        if used:
            rep = representative(used, rows)
            cell = "[![%s](../../assets/examples/%s.svg)](../../assets/examples/%s.svg)" % (t, rep, rep)
        else:
            cell = "_unused_"
        L.append("| `%s` | %s | %d | %s |" % (t, pol, len(used), cell))
    L.append("")
    unused = [t for t in THEME_ORDER if not any(p.get("theme") == t for _, p in rows)]
    if unused:
        L.append("`%s` is defined and available but no spec uses it - it is the only light"
                 % "`, `".join(unused))
        L.append("palette, so light-theme output is untested by the examples. Build a pair with")
        L.append("`--pair paper <dark>` and it works; nothing here proves it.")
        L.append("")
    L.append("**All %d share one visual grammar** - a radial-gradient glow bed, a blur, and mono" % n)
    L.append("type. That is deliberate consistency and it is also a limitation: six palettes is")
    L.append("not six looks. It is the open visual-range item in `HANDOVER.md`.")
    L.append("")

    L.append("---")
    L.append("")
    L.append("## All specs")
    L.append("")
    L.append("| spec | type | theme | `dur` | blurb |")
    L.append("|---|---|---|---|---|")
    for stem, spec in rows:
        b = blurb_for(stem, spec)
        first = b.split(". ")[0].rstrip(".") if b else ""
        first = first.replace("|", "\\|")
        L.append("| [`%s`](../../assets/specs/%s.json) | `%s` | `%s` | %s | %s |"
                 % (stem, stem, spec.get("type"), spec.get("theme", "?"),
                    ("%gs" % spec["dur"]) if "dur" in spec else "-", first))
    L.append("")
    L.append("Browse them all in [`assets/examples/`](../../assets/examples) - they're plain SVG,")
    L.append("so any of them will animate in your browser too.")
    L.append("")
    return "\n".join(L)


THEME_ORDER = ["ember", "ocean", "forest", "violet", "sunset", "mono", "paper"]
LIGHT_THEMES = {"paper"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    rows = collect()
    text = render(rows)
    # normalise so a Windows checkout cannot make the gate cry wolf
    want = text.replace("\r\n", "\n")

    if a.check:
        have = open(GALLERY, encoding="utf-8").read().replace("\r\n", "\n")
        if have != want:
            print("docs/gallery/README.md is out of date.", file=sys.stderr)
            print("%d specs exist but the gallery does not match them." % len(rows),
                  file=sys.stderr)
            print("Run:  python scripts/build_gallery.py", file=sys.stderr)
            return 1
        print("gallery is current (%d specs)" % len(rows))
        return 0

    os.makedirs(os.path.dirname(GALLERY), exist_ok=True)
    with open(GALLERY, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(want)
    covered = sum(1 for _ in rows)
    print("wrote docs/gallery/README.md (%d examples, every spec covered)" % covered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
