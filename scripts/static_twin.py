#!/usr/bin/env python3
"""static_twin.py - write the no-animation twin of an animated SVG.

Usage:
    python scripts/static_twin.py hero.svg hero-static.svg
    python scripts/static_twin.py --check assets/examples        # verify twins are current

Why this exists
---------------
`prefers-reduced-motion` cannot be honoured from inside the file. SMIL is a
separate animation system from CSS, so neither `animation: none` nor
`display: none` on an <animate*> element stops its clock - measured, not
assumed:

    reduce + svg * { animation: none !important }   bean x: 718 -> 792 -> 870   MOVING
    reduce + display:none on animate*               bean x: 721 -> 800 -> 878   MOVING
    no-preference (baseline)                        bean x: 718 -> 792 -> 870   MOVING

So the honest way to respect it is a second file, chosen by the host page:

    <picture>
      <source media="(prefers-reduced-motion: reduce)" srcset="hero-static.svg">
      <img src="hero.svg" alt="...">
    </picture>

Why it costs almost nothing
---------------------------
A well-built example here is static-first: delete every animation element and
the file is still the finished graphic (see references/static-first.md). That
makes the twin mechanical - strip animation elements, keep every last one of the
static drawing - so the two files cannot drift and there is no second design to
maintain. A file that is NOT static-first produces a twin that is missing its
content; --check reports that rather than shipping a broken fallback.
"""
import argparse
import pathlib
import re
import sys
import xml.etree.ElementTree as ET

SVG_NS = "{http://www.w3.org/2000/svg}"
ANIM = {SVG_NS + "animate", SVG_NS + "animateTransform", SVG_NS + "animateMotion"}

# A file whose only visible content is created by animation has no useful twin.
INERT_TEXT = {SVG_NS + "text", SVG_NS + "tspan"}


def strip_animations(svg_text):
    """Remove every SMIL animation element, returning (text, count)."""
    out = re.sub(r"<animate(?:Transform|Motion)?\b[^>]*?/>", "", svg_text)
    out = re.sub(r"<animate(?:Transform|Motion)?\b.*?</animate(?:Transform|Motion)?>", "", out, flags=re.S)
    return out, len(ANIM_ISH.findall(svg_text))


ANIM_ISH = re.compile(r"<animate(?:Transform|Motion)?\b")


def visible_text_ratio(root):
    """Is the twin a usable graphic?

    The question is NOT "what fraction of <text> nodes are visible". Stacked
    techniques - a count-up drawing nine numbers where one is shown at a time, a
    typewriter line, a scroll reveal - legitimately hide most of their text in the
    base state, because only one instance is ever visible at once. gauge-dashboard
    hides 40 of 57 text nodes with good reason: the twin shows one finished number
    per gauge instead of all nine stacked on top of each other, and it looks
    correct.

    So the denominator is a per-position check, not a per-node count: group the
    text nodes by their (x, y) anchor and ask whether every occupied anchor has at
    least one visible node. That is the shape of the defect we actually care about
    - content that exists nowhere in the fallback - without punishing techniques
    that hide alternates of the same position.

    A file whose whole canvas is blank has no visible anchors at all, so the
    ratio is 0.0 and it fails.
    """
    parent = {c: p for p in root.iter() for c in p}

    def chain(el):
        while el is not None:
            yield el
            el = parent.get(el)

    def eff(el):
        o = 1.0
        for p in chain(el):
            v = p.get("opacity")
            if v is not None:
                try:
                    o *= float(v)
                except ValueError:
                    pass
            if p.get("display") == "none" or p.get("visibility") == "hidden":
                return 0.0
        return o

    anchors = {}
    for t in root.iter():
        if t.tag not in INERT_TEXT:
            continue
        if not "".join(t.itertext()).strip():
            continue
        try:
            key = (round(float(t.get("x", 0)), 1), round(float(t.get("y", 0)), 1))
        except ValueError:
            key = ("?", "?")
        anchors.setdefault(key, []).append(eff(t) > 0.5)

    if not anchors:
        return 1.0, 0
    filled = sum(1 for states in anchors.values() if any(states))
    return filled / len(anchors), len(anchors)


def twin(svg_text):
    stripped, n = strip_animations(svg_text)
    root = ET.fromstring(stripped)
    ratio, total = visible_text_ratio(root)
    return stripped, n, ratio, total


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("output", nargs="?")
    ap.add_argument("--check", action="store_true",
                    help="verify <stem>-static.svg is current for every .svg in this directory")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv[1:])

    if a.check:
        return check_dir(pathlib.Path(a.input))

    if not a.output:
        ap.error("output is required unless --check is used")

    src = pathlib.Path(a.input)
    svg_text = src.read_text(encoding="utf-8")
    try:
        stripped, n, ratio, total = twin(svg_text)
    except ET.ParseError as exc:
        print(f"FAIL: {src.name} is not well-formed XML: {exc}", file=sys.stderr)
        return 1

    if n == 0:
        print(f"FAIL: {src.name} has no animation elements, so it needs no static twin", file=sys.stderr)
        return 1

    kb = len(stripped.encode("utf-8")) // 1024
    if ratio < 0.5:
        # Refuse BEFORE writing: a twin that is missing content is worse than no
        # twin, because the host page will happily serve it to exactly the users
        # who asked for less motion.
        print(f"FAIL: {src.name} is not static-first - only {ratio:.0%} of its {total} text position(s) "
              f"survive without animation, so the twin would be missing content. "
              f"Give the base state the finished drawing, then rerun. "
              f"See references/static-first.md.", file=sys.stderr)
        return 1

    pathlib.Path(a.output).write_text(stripped, encoding="utf-8")
    if not a.quiet:
        print(f"wrote {a.output} ({kb} KB) - {n} animation element(s) removed, "
              f"{ratio:.0%} of {total} text position(s) still carry visible text")
    return 0


def check_dir(d):
    """Every animated .svg must have a current -static.svg twin beside it."""
    problems, twins = [], 0
    for src in sorted(d.glob("*.svg")):
        if src.name.endswith("-static.svg"):
            continue
        svg_text = src.read_text(encoding="utf-8")
        if not ANIM_ISH.search(svg_text):
            continue
        twins += 1
        want = src.with_name(src.stem + "-static.svg")
        if not want.exists():
            problems.append(f"{src.name}: no static twin")
            continue
        try:
            stripped, _, ratio, total = twin(svg_text)
        except ET.ParseError as exc:
            problems.append(f"{src.name}: {exc}")
            continue
        if ratio < 0.5:
            problems.append(f"{src.name}: only {ratio:.0%} of {total} text position(s) have any visible "
                            f"text - the fallback is missing content")
        if want.read_text(encoding="utf-8") != stripped:
            problems.append(f"{src.name}: {want.name} is stale - rerun static_twin.py")
    for p in problems:
        print(f"FAIL: {p}", file=sys.stderr)
    print(f"{twins} animated file(s) checked, {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))