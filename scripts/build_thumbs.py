#!/usr/bin/env python3
"""Build uniform gallery tiles from the generated examples.

Why this exists
---------------
GitHub markdown gives us no CSS and no real layout control: a row of
`<img width="24%">` tags aligns only if every image has the same aspect ratio.
The examples range from 0.97 (network) to 3.08 (timeline), so a shared row is
impossible -- wide graphics shrink to a sliver while square ones tower, and the
leftover space reads as an unfinished page.

The fix is to stop asking the browser to lay out mismatched artwork and do the
layout ourselves. Every tile is a FIXED-SIZE standalone SVG:

  * the artwork is *contained* (never cropped -- a 3:1 timeline cover-fit into
    a 1.33 tile loses 57% of itself),
  * the leftover bars are filled with a blurred, cover-scaled copy of the same
    artwork, so the tile is always completely full and page-white never shows,
  * so every tile is exactly TILE_W x TILE_H and a markdown table lays them out
    on a rigid grid with zero gaps.

Two details that are easy to get wrong and are handled here:

  * IDs are namespaced TWICE, because the blurred backdrop is a second copy of
    the same fragment. One prefix would produce duplicate IDs, which the linter
    correctly rejects.
  * The loop is pre-rolled by a negative `begin`, because a looping intro
    animation is hidden at frame 0 by definition (the logo shield outline has
    stroke-dasharray "0 1" and the wordmark sits at opacity 0 until its cue).
    That is correct for the deliverable -- the loop restarts clean -- but it
    means a frame-0 thumbnail would be blank. A negative `begin` lands frame 0
    mid-show instead. The source examples are never modified.

Usage
-----
    python scripts/build_thumbs.py                     # all curated tiles
    python scripts/build_thumbs.py --only logo-shield  # one, for iteration
    python scripts/build_thumbs.py --preroll 0         # keep frame 0 as-is
    python scripts/build_thumbs.py --size 560x420      # bigger tiles

Output is standalone and self-contained: the example's body is inlined (no
<image href>, which browsers refuse to load inside an <img>), nothing is
fetched at render time, and every tile passes the linter like the rest of the
repo.
"""
import argparse
import os
import re
import sys

TILE_W, TILE_H = 480, 360          # every tile, no exceptions
CAPTION_H = 74                     # reserved for the label strip
PAD = 10                           # inner padding around the artwork
RADIUS = 18
ART_BLUR = 22

CHROME_BG = "#12101C"
CHROME_BG2 = "#1B1730"
LABEL = "#F2EEFF"
SUB = "#9C93C4"

# Curated set: 12 tiles covering both families and a wide spread of aspect
# ratios, so the grid has to work without special-casing anything.
TILES = [
    ("network-services",   "network",  "pulses spread by graph depth"),
    ("flow-with-feedback", "flow",    "relay dots pause at each node"),
    ("timeline-roadmap",   "timeline", "each milestone lights on arrival"),
    ("terminal-demo",      "terminal", "text is in the DOM, covers slide off"),
    ("loader-sheet",       "loader",   "eight spinners, eight rhythms"),
    ("gauge-dashboard",    "gauge",    "counts up, holds, resets"),
    ("radar-skills",       "radar",    "polygons grow from the centre"),
    ("counter-stats",      "counter",  "odometer digit columns roll"),
    ("icons-set",          "icons",    "each icon rests between actions"),
    ("logo-shield",        "logo",     "outline draws, then fills"),
    ("art-mandala",        "art",      "seeded, so output reproduces"),
    ("backdrop-mesh",      "backdrop", "ambient bed, slow and low contrast"),
]


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def viewbox_of(svg_text):
    m = re.search(r'viewBox="([-\d.]+)[ ,]+([-\d.]+)[ ,]+([\d.]+)[ ,]+([\d.]+)"', svg_text)
    if not m:
        sys.exit("no viewBox found")
    return tuple(float(m.group(i)) for i in range(1, 5))


def inner_body(svg_text):
    """Return (body, head_style) with the <svg> wrapper stripped.

    <defs> stays inside the body on purpose: the artwork references its
    gradients, filters and clipPaths by id.
    """
    s = re.sub(r"<\?xml[^>]*\?>", "", svg_text).strip()
    open_m = re.search(r"<svg\b[^>]*>", s)
    if not open_m or "</svg>" not in s:
        sys.exit("malformed <svg>")
    head = open_m.group(0)
    body = s[open_m.end(): s.rindex("</svg>")]
    style = ""
    ms = re.search(r"<style[^>]*>.*?</style>", head, re.S)
    if ms:
        style = ms.group(0)
    return body, style


def loop_dur(svg_text):
    """Longest animation duration in the file, in seconds -- the master clock."""
    durs = []
    for pat in (r'dur="([\d.]+)(ms|s)"', r'animation:[^;}]*?([\d.]+)(ms|s)'):
        for m in re.finditer(pat, svg_text):
            v = float(m.group(1))
            durs.append(v / 1000 if m.group(2) == "ms" else v)
    return max(durs) if durs else 4.0


def preroll(body, seconds):
    """Give every animation lacking a `begin` a negative one, pre-rolling the loop."""
    if seconds <= 0:
        return body
    off = "-%.3fs" % seconds

    def fix(m):
        tag = m.group(0)
        if "begin=" in tag:
            return tag
        return re.sub(r"^(<animate\w+)",
                      lambda mm: mm.group(1) + ' begin="' + off + '"',
                      tag, count=1)

    return re.sub(r"<animate\w[^>]*>", fix, body)


def namespace(body, pfx):
    """Prefix every id in a fragment and rewrite every reference to it.

    Needed per-copy, not per-file: the blurred backdrop is a second copy of the
    same fragment, so a single prefix would leave every id defined twice.
    """
    body = re.sub(r'\bid="([^"]+)"', lambda m: 'id="%s%s"' % (pfx, m.group(1)), body)
    body = re.sub(r'url\(#([^)]+)\)', lambda m: "url(#%s%s)" % (pfx, m.group(1)), body)
    body = re.sub(r'href="#([^"]+)"', lambda m: 'href="#%s%s"' % (pfx, m.group(1)), body)
    return body


def build_tile(name, kind, blurb, svg_text, idx, preroll_s=0.0,
               tile_w=TILE_W, tile_h=TILE_H):
    pfx = "t%d-" % idx
    _, _, W0, H0 = viewbox_of(svg_text)
    body, style = inner_body(svg_text)
    body = preroll(body, preroll_s)

    art_w = tile_w - PAD * 2
    art_h = tile_h - CAPTION_H - PAD

    # sharp copy: contained, so nothing important is ever cropped
    scale = min(art_w / W0, art_h / H0)
    tx = PAD + (art_w - W0 * scale) / 2
    ty = PAD + (art_h - H0 * scale) / 2

    # blurred copy: cover-scaled, fills whatever the sharp copy doesn't reach
    b_scale = max(art_w / W0, art_h / H0)
    b_tx = PAD + (art_w - W0 * b_scale) / 2
    b_ty = PAD + (art_h - H0 * b_scale) / 2

    sharp = namespace(body, pfx)
    blur = namespace(body, pfx + "b-")

    clip = pfx + "clip"
    blurb = blurb if len(blurb) <= 42 else blurb[:41] + "…"
    pre_note = ('Loop pre-rolled %.2fs so frame 0 lands mid-show, not blank.' % preroll_s
                if preroll_s > 0 else '')

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {tile_w} {tile_h}" width="{tile_w}" height="{tile_h}"
     role="img" aria-labelledby="{pfx}ttl {pfx}dsc">
  <title id="{pfx}ttl">{esc(name)} — {esc(kind)}</title>
  <desc id="{pfx}dsc">Gallery tile for the {esc(kind)} generator output "{esc(name)}": {esc(blurb)}.</desc>
  <!--
    Uniform gallery tile, built by scripts/build_thumbs.py.
    Source: assets/examples/{name}.svg ({W0:.0f}x{H0:.0f}, aspect {W0 / H0:.2f}).
    Sharp artwork contained at scale {scale:.4f} (never cropped); leftover bars
    filled by a cover-scaled blurred copy at {b_scale:.4f}. Tile is exactly
    {tile_w}x{tile_h}, so a markdown table aligns the grid with no gaps.
    {pre_note}
  -->
  <defs>
    <linearGradient id="{pfx}bg" x1="0" y1="0" x2="{tile_w}" y2="{tile_h}" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="{CHROME_BG2}"/>
      <stop offset="1" stop-color="{CHROME_BG}"/>
    </linearGradient>
    <clipPath id="{clip}">
      <rect x="{PAD}" y="{PAD}" width="{art_w}" height="{art_h}" rx="{RADIUS - 6}"/>
    </clipPath>
    <filter id="{pfx}blur" x="-25%" y="-25%" width="150%" height="150%">
      <feGaussianBlur stdDeviation="{ART_BLUR}"/>
    </filter>
  </defs>
{style}
  <rect x="0" y="0" width="{tile_w}" height="{tile_h}" rx="{RADIUS}" fill="url(#{pfx}bg)"/>
  <g clip-path="url(#{clip})">
    <g opacity="0.55">
      <g transform="translate({b_tx:.2f} {b_ty:.2f}) scale({b_scale:.4f})">
        <g filter="url(#{pfx}blur)">{blur}</g>
      </g>
    </g>
    <g transform="translate({tx:.2f} {ty:.2f}) scale({scale:.4f})">
{sharp}
    </g>
  </g>
  <rect x="{PAD}" y="{PAD}" width="{art_w}" height="{art_h}" rx="{RADIUS - 6}" fill="none" stroke="#3A3160" stroke-width="1.5"/>
  <g font-family="'JetBrains Mono','Cascadia Mono',Menlo,Consolas,monospace">
    <text x="{PAD + 6}" y="{tile_h - CAPTION_H + 36}" font-size="22" font-weight="700" fill="{LABEL}">{esc(kind)}</text>
    <text x="{PAD + 6}" y="{tile_h - CAPTION_H + 60}" font-size="15" fill="{SUB}">{esc(blurb)}</text>
  </g>
</svg>
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--examples", default="assets/examples")
    ap.add_argument("--out-dir", default="docs/thumbs")
    ap.add_argument("--only", default=None)
    ap.add_argument("--cols", type=int, default=3,
                    help="only used to print the suggested markdown table")
    ap.add_argument("--size", default=None, help="WxH, e.g. 560x420 (default 480x360)")
    ap.add_argument("--preroll", type=float, default=0.30,
                    help="pre-roll the loop by this fraction of dur so frame 0 is "
                         "mid-show rather than blank (0 disables)")
    args = ap.parse_args()

    tw, th = TILE_W, TILE_H
    if args.size:
        try:
            tw, th = (int(v) for v in args.size.lower().split("x"))
        except ValueError:
            sys.exit("--size must look like 560x420")

    os.makedirs(args.out_dir, exist_ok=True)
    rows = [t for t in TILES if not args.only or t[0] == args.only]
    written = 0

    for i, (name, kind, blurb) in enumerate(TILES):
        if args.only and name != args.only:
            continue
        src = os.path.join(args.examples, name + ".svg")
        if not os.path.exists(src):
            print("  skip %s: %s missing" % (name, src), file=sys.stderr)
            continue
        svg_text = open(src, encoding="utf-8").read()
        out = os.path.join(args.out_dir, name + ".svg")
        pre = loop_dur(svg_text) * args.preroll
        open(out, "w", encoding="utf-8").write(
            build_tile(name, kind, blurb, svg_text, i, pre, tw, th))
        print("  %s  (%d KB, %dx%d, preroll %.2fs)"
              % (out, os.path.getsize(out) // 1024, tw, th, pre))
        written += 1

    print("\n%d tile(s) written, all exactly %dx%d." % (written, tw, th))
    print('Suggested markdown table (%d columns):' % args.cols)
    print()
    print("| | | |")
    print("|---|---|---|")
    for r in range(0, len(rows), args.cols):
        cells = []
        for name, kind, blurb in rows[r:r + args.cols]:
            cells.append(
                # The tile is the linked image and the click-through goes to the
                # full-size example. docs/gallery/*.svg was deleted in #13, so the
                # target is assets/examples/ -- do not point back at docs/gallery/.
                '<a href="../assets/examples/%s.svg"><img src="thumbs/%s.svg" alt="%s — %s" width="100%%"></a>'
                % (name, name, esc(kind), esc(blurb)))
        print("| " + " | ".join(cells) + " |")
    return 0


if __name__ == "__main__":
    sys.exit(main())
