#!/usr/bin/env python3
"""readme_page.py - generate a full "one-page" GitHub README made of seamless animated SVG blocks.

Usage:
  python readme_page.py spec.json OUTDIR [--preview] [--check]

Writes   OUTDIR/README.md
         OUTDIR/docs/readme/NN-<block>-dark.svg   and   -light.svg   (one pair per block)
         OUTDIR/docs/readme/preview-{dark,light}-t*.png              (with --preview: the stitched page as GitHub shows it)

STYLE "spine" (the only style so far; see references/readme-kit.md):
  * one vertical spine runs through EVERY block (same x), with a numbered station node per section
  * a pulse travels down the whole page on one clock; each section's content plays when the pulse reaches it
  * ghost chapter numerals, corner crop marks, a page-aligned ruler on the right edge
  * background glow lives in PAGE coordinates, so it continues across block borders
  * blocks are TRANSPARENT (the GitHub page is the background) and ship in dark + light variants

Why it looks like one page: all blocks share width/spine/ruler/glow coordinates, and the README stacks them in ONE
<div> with <img align="top"> (verified: 0 px gaps; plain images leave 7 px, separate paragraphs 16 px).
"""
import argparse
import json
import math
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diagram_common import (FONT, SANS, F, T, apply_window, common_defs, esc, glow_dot, header, map_sb)  # noqa: E402
from gen_diagram import registry, theme_for  # noqa: E402

W, SPX, CX, CW, RULER = 1000, 56, 120, 820, 972
CONTENT_R = CX + CW
# Parts that hide their own content until a reveal cue (typewriter, odometer, grow-in...). A short window would leave
# them blank for most of the loop, so they keep the whole loop; overlay-type parts play when the spine pulse arrives.
REVEAL_TYPES = {"terminal", "counter", "gauge", "chart", "logo", "text", "radar"}
WIDTH_KEY = {"terminal": "width", "chart": "width", "layers": "width", "banner": "width", "scene": "width",
             "backdrop": "width", "logo": "width", "phases": "width", "art": "size"}


# ------------------------------------------------------------------ helpers
def wrap(s, n):
    """Greedy wrap, then re-wrap to the narrowest width that keeps the same line count (no orphan words)."""
    words = str(s).split()

    def greedy(limit):
        lines, cur = [], ""
        for w in words:
            if len(cur) + len(w) + (1 if cur else 0) <= limit:
                cur = (cur + " " + w).strip()
            else:
                lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return lines

    first = greedy(n)
    for limit in range(max(len(w) for w in words) if words else 1, n + 1):
        cand = greedy(limit)
        if len(cand) == len(first):
            return cand
    return first


def tp_factory(Htot):
    """page y -> time fraction of the master loop (pulse crosses the page in 0.03..0.88)."""
    return lambda y: 0.03 + 0.85 * (y / Htot)


# ------------------------------------------------------------------ part fitting
def build_part(ps, th, idp, dur, target, reg, window=(0.0, 1.0), real_cps=18):
    ps = dict(ps)
    ps.pop("title", None)
    ps["dur"] = dur
    ps.setdefault("title_zone", 6)
    ps["aurora"] = False
    a, b = window
    if ps.get("type") == "terminal":
        ps.setdefault("cps", real_cps * (b - a))
    t = ps["type"]
    if t not in reg:
        sys.exit(f"section part type '{t}' unknown")
    scale = 1.0
    p = reg[t](dict(ps), th, idp)
    if p["W"] > target + 0.5:
        tried = []
        if t == "flow":
            tried = [dict(ps, gap_x=g, margin=16) for g in (72, 60, 50, 42, 36)]
        elif t == "cards":
            cols = ps.get("cols", min(len(ps["items"]), 4))
            tried = [dict(ps, tile_w=int((target - 80 - (cols - 1) * 24) / cols))]
        elif t == "timeline":
            n = len(ps["items"])
            cw_ = min(ps.get("card_w", 168), int((target - 96) / (n * 1.25)))
            tried = [dict(ps, card_w=cw_, spacing=int((target - 96 - cw_) / (n - 1)))]
        elif t in WIDTH_KEY:
            tried = [dict(ps, **{WIDTH_KEY[t]: int(target)})]
        elif t == "radial":
            tried = [dict(ps, radius=r_) for r_ in (200, 170, 150, 130)]
        elif t in ("network", "cycle"):
            tried = [dict(ps, radius=r_) for r_ in (190, 160, 140)]
        elif t == "sequence":
            tried = [dict(ps, spacing=s_) for s_ in (200, 170, 150)]
        elif t == "counter":
            tried = [dict(ps, size=s_) for s_ in (42, 36, 30)]
        elif t == "gauge":
            tried = [dict(ps, cols=max(1, ps.get("cols", 3) - 1))]
        elif t == "radar":
            tried = [dict(ps, radius=r_) for r_ in (120, 100)]
        for ps2 in tried:
            q = reg[t](dict(ps2), th, idp)
            if q["W"] <= target + 0.5:
                p = q
                break
        if p["W"] > target + 0.5:
            scale = target / p["W"]
            print(f"WARNING: part '{t}' is {p['W']:.0f}px wide (> {target}); scaled to {scale:.2f} (geometry lint is skipped for scaled parts)", file=sys.stderr)
    body = apply_window(p["body"], a, b, p.get("preroll"), p.get("dur"))
    return dict(p=p, body=body, scale=scale, W=p["W"] * scale, H=p["H"] * scale, sb=map_sb(p["sb"], a, b))


# ------------------------------------------------------------------ shared decoration
def aurora_slice(ctx, y0, h, idp):
    th, Htot = ctx["th"], ctx["Htot"]
    cols = [th["accent"], th["accent2"], th["accent3"], th["accent"], th["accent2"], th["accent3"]]
    alpha = ctx["glow_alpha"]
    defs, els = [], []
    n = max(4, int(Htot / 700) + 3)
    for k in range(n):
        cy = Htot * (k + 0.5) / n
        cx = 230 if k % 2 == 0 else 780
        rx, ry = 430, 380
        if cy + ry < y0 or cy - ry > y0 + h:
            continue
        gid = f"{idp}bl{k}"
        defs.append(f'<radialGradient id="{gid}" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="{cols[k % 6]}" stop-opacity="{alpha}"/><stop offset="1" stop-color="{cols[k % 6]}" stop-opacity="0"/></radialGradient>')
        d_ = round(ctx["dur"] * (1 + 0.125 * k), 1)  # ambient drift, proportional to the master clock (24/27/30/33... s at dur=24)
        els.append(f'<ellipse cx="{cx}" cy="{F(cy - y0)}" rx="{rx}" ry="{ry}" fill="url(#{gid})">'
                   f'<animateTransform attributeName="transform" type="translate" values="0 0;{(-1) ** k * 40} {(-1) ** k * 24};0 0" dur="{d_}s" repeatCount="indefinite"/></ellipse>')
    return "<defs>" + "".join(defs) + "</defs>" + "".join(els)


def ruler(ctx, y0, h):
    th = ctx["th"]
    d = []
    yy = math.ceil(y0 / 24) * 24
    while yy < y0 + h:
        ln = 14 if yy % 120 == 0 else 6
        d.append(f"M{RULER - ln},{yy - y0} h{ln}")
        yy += 24
    s = [f'<path d="{" ".join(d)}" fill="none" stroke="{th["stroke_dim"]}" stroke-width="1" opacity="0.7"/>']
    for lbl, yp in ctx["ruler_labels"]:
        if y0 <= yp < y0 + h:
            s.append(f'<text x="{RULER - 20}" y="{F(yp - y0 + 4)}" text-anchor="end" font-family="{FONT}" font-size="10" fill="{th["accent"]}" letter-spacing="1">{esc(lbl)}</text>')
    return "".join(s)


def spine_and_pulse(ctx, y0, h, nodes, top_y=0.0, bottom_y=None, first=False, last=False):
    """Spine segments (gaps around station nodes) + the travelling pulse (page-wide clock)."""
    th, dur, tp = ctx["th"], ctx["dur"], ctx["tp"]
    bottom_y = h if bottom_y is None else bottom_y
    segs, cur = [], top_y
    for ny, r in sorted(nodes):
        if ny - r - 6 > cur:
            segs.append(f"M{SPX},{F(cur)} V{F(ny - r - 6)}")
        cur = max(cur, ny + r + 6)
    if bottom_y > cur:
        segs.append(f"M{SPX},{F(cur)} V{F(bottom_y)}")
    s = [f'<path d="{" ".join(segs)}" fill="none" stroke="{th["stroke"]}" stroke-width="2" stroke-linecap="butt" opacity="0.85"/>']
    ts, te = tp(y0 + top_y), tp(y0 + bottom_y)
    f_in = min(0.012 if first else 0.0004, (te - ts) / 3)
    f_out = min(0.02 if last else 0.0004, (te - ts) / 3)
    mkt = f"0;{T(ts)};{T(te)};1"
    okt = f"0;{T(ts)};{T(ts + f_in)};{T(te - f_out)};{T(te)};1"
    cys = f"{F(top_y)};{F(top_y)};{F(bottom_y)};{F(bottom_y)}"
    for r, op, fill, flt in ((11, 0.55, th["accent"], ' filter="url(#glow)"'), (4.6, 1, th["dot"], "")):
        s.append(f'<circle cx="{SPX}" cy="{F(top_y)}" r="{r}" fill="{fill}"{flt} opacity="0">'
                 f'<animate attributeName="cy" dur="{dur:g}s" repeatCount="indefinite" calcMode="linear" keyTimes="{mkt}" values="{cys}"/>'
                 f'<animate attributeName="opacity" dur="{dur:g}s" repeatCount="indefinite" keyTimes="{okt}" values="0;0;{op};{op};0;0"/></circle>')
    return "".join(s), (ts, te)


def station(ctx, y0, ny, idx):
    th, dur, tp = ctx["th"], ctx["dur"], ctx["tp"]
    arr = tp(y0 + ny)
    return (f'<circle cx="{SPX}" cy="{F(ny)}" r="9" fill="none" stroke="{th["accent"]}" stroke-width="2.2"/>'
            f'<circle cx="{SPX}" cy="{F(ny)}" r="3" fill="{th["accent"]}"/>' + glow_dot(SPX, ny, 9, th["accent"], [arr], dur, rise=0.02, decay=0.07)
            + f'<path d="M{SPX + 14},{F(ny)} H{CX - 16}" stroke="{th["stroke_dim"]}" stroke-width="1" fill="none"/>'), arr


def crop_marks(ctx, x, y, w, h, ln=14):
    th = ctx["th"]
    c = []
    for (px, py, sx, sy) in ((x, y, 1, 1), (x + w, y, -1, 1), (x, y + h, 1, -1), (x + w, y + h, -1, -1)):
        c.append(f"M{px + sx * ln},{py} H{px} V{py + sy * ln}")
    return f'<path d="{" ".join(c)}" fill="none" stroke="{th["stroke"]}" stroke-width="1.2" opacity="0.8"/>'


def ghost_numeral(ctx, num, y):
    th = ctx["th"]
    return (f'<text x="{CONTENT_R}" y="{F(y)}" text-anchor="end" font-family="{SANS}" font-size="150" font-weight="800" fill="none" '
            f'stroke="{th["accent"]}" stroke-width="1.4" stroke-opacity="0.16">{num}</text>')


# ------------------------------------------------------------------ blocks
def block_hero(ctx, spec, reg):
    th, dur = ctx["th"], ctx["dur"]
    name = ctx["name"]
    hs = spec.get("hero", {})
    node_y = 66
    size = max(34, min(78, int(430 / (max(len(name), 1) * 0.6))))
    ty = 190
    tag_lines = wrap(ctx["tagline"], 34)
    desc_lines = wrap(ctx["description"], 54)
    y = ty + 52
    tag_y = y
    y += 30 * len(tag_lines) + 8
    desc_y = y
    y += 22 * len(desc_lines) + 18
    badges_y = y
    bx, by = CX, badges_y
    chips = []
    for b in ctx["badges"]:
        w = round(len(b) * 7.8 + 26)
        if bx + w > 560:
            bx, by = CX, by + 40
        chips.append((bx, by, w, b))
        bx += w + 10
    y = by + 40 + 22
    cta_y = y
    ctas = hs.get("cta", [{"label": "Get started"}, {"label": "Read the docs"}])
    y += 52
    vis = hs.get("visual", {"type": "art", "variant": "orbits"})
    vis_p = build_part(dict(vis, size=380, width=380, height=380) if vis["type"] in ("art", "scene") else vis, th, "bh0p-", dur, 400, reg, (0.0, 0.3))
    vis_y = 54
    h = int(max(y + 50, vis_y + vis_p["H"] + 40, 520))
    idp = "b0-"
    gid = f"{idp}hg"
    gw = max(240, len(name) * size * 0.6)
    sh = (f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="{CX}" y1="0" x2="{F(CX + gw)}" y2="0" spreadMethod="repeat">'
          f'<stop offset="0" stop-color="{th["accent2"]}"/><stop offset="0.35" stop-color="{th["accent"]}"/><stop offset="0.5" stop-color="{th["accent3"]}"/><stop offset="0.65" stop-color="{th["accent"]}"/><stop offset="1" stop-color="{th["accent2"]}"/>'
          f'<animateTransform attributeName="gradientTransform" type="translate" values="0 0;{F(gw)} 0" dur="{dur / 2:g}s" repeatCount="indefinite"/></linearGradient>')
    inner = [sh]
    # origin node + sonar
    for k in range(3):
        bgn = f"{-k * dur / 12:g}s"
        inner.append(f'<circle cx="{SPX}" cy="{node_y}" r="14" fill="none" stroke="{th["accent"]}" stroke-width="2" opacity="0.5">'
                     f'<animate attributeName="r" values="14;52" dur="{dur / 4:g}s" begin="{bgn}" repeatCount="indefinite"/>'
                     f'<animate attributeName="opacity" values="0.5;0" dur="{dur / 4:g}s" begin="{bgn}" repeatCount="indefinite"/></circle>')
    inner.append(f'<circle cx="{SPX}" cy="{node_y}" r="14" fill="none" stroke="{th["accent"]}" stroke-width="2.6"/><circle cx="{SPX}" cy="{node_y}" r="5" fill="{th["accent"]}"/>')
    inner.append(f'<path d="M{SPX + 20},{node_y} H{CX - 16}" stroke="{th["stroke_dim"]}" stroke-width="1" fill="none"/>')
    inner.append(f'<text x="{CX}" y="{node_y + 5}" font-family="{FONT}" font-size="12" fill="{th["accent"]}" letter-spacing="3">{esc(hs.get("eyebrow", "OPEN SOURCE").upper())}</text>')
    inner.append(f'<text x="{CX}" y="{ty}" font-family="{SANS}" font-size="{size}" font-weight="800" letter-spacing="-2" fill="url(#{gid})">{esc(name)}</text>')
    for i, ln in enumerate(tag_lines):
        inner.append(f'<text x="{CX}" y="{tag_y + 30 * i}" font-family="{SANS}" font-size="24" font-weight="600" fill="{th["text_key"]}">{esc(ln)}</text>')
    for i, ln in enumerate(desc_lines):
        inner.append(f'<text x="{CX}" y="{desc_y + 22 * i}" font-family="{SANS}" font-size="15" fill="{th["muted"]}">{esc(ln)}</text>')
    for (x, yy, w, b) in chips:
        inner.append(f'<g><rect x="{x}" y="{yy}" width="{w}" height="30" rx="8" fill="{th["surface"]}" stroke="{th["stroke_dim"]}" stroke-width="1.1"/>'
                     f'<text x="{F(x + w / 2)}" y="{yy + 20}" text-anchor="middle" font-family="{FONT}" font-size="12" fill="{th["text"]}">{esc(b)}</text></g>')
    bx = CX
    for i, c in enumerate(ctas):
        w = round(len(c["label"]) * 9 + 44)
        if i == 0:
            inner.append(f'<g><rect x="{bx}" y="{cta_y}" width="{w}" height="44" rx="10" fill="{th["accent"]}"/><text x="{F(bx + w / 2)}" y="{cta_y + 28}" text-anchor="middle" font-family="{SANS}" font-size="15" font-weight="700" fill="{th["bg"]}">{esc(c["label"])}</text></g>')
        else:
            inner.append(f'<g><rect x="{bx}" y="{cta_y}" width="{w}" height="44" rx="10" fill="none" stroke="{th["stroke"]}" stroke-width="1.4"/><text x="{F(bx + w / 2)}" y="{cta_y + 28}" text-anchor="middle" font-family="{SANS}" font-size="15" font-weight="600" fill="{th["text"]}">{esc(c["label"])}</text></g>')
        bx += w + 14
    vx = 540 + (CONTENT_R - 540 - vis_p["W"]) / 2
    sc = f" scale({vis_p['scale']:.3f})" if vis_p["scale"] != 1 else ""
    inner.append(f'<g id="{idp}visual" transform="translate({F(vx)} {F(vis_y)}){sc}">{vis_p["body"]}</g>')
    return dict(name="hero", h=h, inner="".join(inner), nodes=[(node_y, 14)], top_y=node_y, bottom_y=None, first=True, last=False,
                arrows=vis_p["p"]["arrows"], sb=["hero: sonar rings at the spine origin, shimmer title, visual part"] + vis_p["sb"], aria=f"{name}: {ctx['tagline']}", station_ys=[node_y])


def block_nav(ctx, spec, labels):
    th, dur = ctx["th"], ctx["dur"]
    h = 96
    y = 46
    n = len(labels)
    xs = [CX + 24 + i * (CW - 48) / max(1, n - 1) for i in range(n)]
    inner = [f'<path d="M{CX},{y} H{CONTENT_R}" stroke="{th["stroke"]}" stroke-width="1.4" fill="none"/>']
    arr0 = ctx["nav_t0"]
    for i, (x, lab) in enumerate(zip(xs, labels)):
        a = arr0 + i * 0.012
        inner.append(f'<circle cx="{F(x)}" cy="{y}" r="5" fill="none" stroke="{th["accent"]}" stroke-width="1.8"/>' + glow_dot(x, y, 5, th["accent"], [a], dur, rise=0.01, decay=0.05)
                     + f'<text x="{F(x)}" y="{y - 14}" text-anchor="middle" font-family="{FONT}" font-size="10" fill="{th["accent"]}" letter-spacing="1.5">{i + 1:02d}</text>'
                     + f'<text x="{F(x)}" y="{y + 26}" text-anchor="middle" font-family="{FONT}" font-size="12" fill="{th["text"]}">{esc(lab)}</text>')
    return dict(name="nav", h=h, inner="".join(inner), nodes=[], top_y=0, bottom_y=None, first=False, last=False, arrows=False,
                sb=["nav: station index; nodes pulse in order at the start of the loop"], aria="Page index: " + ", ".join(labels), station_ys=[])


def block_section(ctx, sec, idx, reg):
    """Section header metadata; the embedded part and its window are built in finish_section (needs page y)."""
    lede = wrap(sec.get("lede", ""), 84) if sec.get("lede") else []
    header_h = 118 + 24 * len(lede) + (14 if lede else 0)
    return dict(sec=sec, idx=idx, lede=lede, header_h=header_h)


def finish_section(ctx, meta, y0, reg):
    th, dur, tp = ctx["th"], ctx["dur"], ctx["tp"]
    sec, idx, lede, header_h = meta["sec"], meta["idx"], meta["lede"], meta["header_h"]
    node_y = 30
    a = tp(y0 + node_y)
    win = (0.0, 1.0) if sec["part"].get("type") in REVEAL_TYPES else (min(a, 0.9), min(0.98, a + 0.17))
    part = build_part(sec["part"], th, f"b{idx + 2}p-", dur, CW, reg, win)
    h = int(header_h + part["H"] + 70)
    idp = f"b{idx + 2}-"
    inner = []
    st, _ = station(ctx, y0, node_y, idx)
    inner.append(st)
    inner.append(ghost_numeral(ctx, f"{idx + 1:02d}", 128))
    inner.append(f'<text x="{CX}" y="{node_y + 4}" font-family="{FONT}" font-size="12" fill="{th["accent"]}" letter-spacing="3">STATION {idx + 1:02d}</text>')
    inner.append(f'<text x="{CX}" y="{node_y + 50}" font-family="{SANS}" font-size="38" font-weight="800" letter-spacing="-0.5" fill="{th["text_key"]}">{esc(sec["title"])}</text>')
    for i, ln in enumerate(lede):
        inner.append(f'<text x="{CX}" y="{node_y + 84 + 24 * i}" font-family="{SANS}" font-size="17" fill="{th["muted"]}">{esc(ln)}</text>')
    py = header_h
    px = CX + (CW - part["W"]) / 2
    sc = f" scale({part['scale']:.3f})" if part["scale"] != 1 else ""
    inner.append(crop_marks(ctx, CX - 14, py - 10, CW + 28, part["H"] + 20))
    inner.append(f'<g id="{idp}part" transform="translate({F(px)} {F(py)}){sc}">{part["body"]}</g>')
    sb = [f"section {idx + 1} '{sec['title']}': pulse reaches the node at {a:.3f}; part window {win[0]:.3f}..{win[1]:.3f}"] + part["sb"]
    return dict(name=f"{idx + 1:02d}-{sec.get('id', 'section')}", h=h, inner="".join(inner), nodes=[(node_y, 9)], top_y=0, bottom_y=None,
                first=False, last=False, arrows=part["p"]["arrows"], sb=sb, aria=f"{sec['title']}. {sec.get('lede', '')}".strip(), station_ys=[node_y],
                ruler=(f"§{idx + 1:02d}", y0 + node_y))


def block_footer(ctx, spec):
    th = ctx["th"]
    fs = spec.get("footer", {})
    h = 300
    node_y = 56
    inner = [f'<path d="M{SPX - 10},{node_y} L{SPX},{node_y - 12} L{SPX + 10},{node_y} L{SPX},{node_y + 12} Z" fill="none" stroke="{th["accent"]}" stroke-width="2.2"/>',
             f'<path d="M{SPX + 16},{node_y} H{CX - 16}" stroke="{th["stroke_dim"]}" stroke-width="1" fill="none"/>',
             f'<text x="{CX}" y="{node_y + 4}" font-family="{FONT}" font-size="12" fill="{th["accent"]}" letter-spacing="3">END OF LINE</text>']
    for i, ln in enumerate(wrap(fs.get("closing", "Build something worth reading."), 40)):
        inner.append(f'<text x="{CX}" y="{node_y + 70 + 48 * i}" font-family="{SANS}" font-size="40" font-weight="800" letter-spacing="-1" fill="{th["text_key"]}">{esc(ln)}</text>')
    ly = node_y + 70 + 48 * len(wrap(fs.get("closing", "Build something worth reading."), 40)) + 18
    x = CX
    for lk in fs.get("links", []):
        w = round(len(lk["label"]) * 8.4 + 30)
        inner.append(f'<g><rect x="{x}" y="{ly}" width="{w}" height="34" rx="8" fill="none" stroke="{th["stroke"]}" stroke-width="1.2"/><text x="{F(x + w / 2)}" y="{ly + 22}" text-anchor="middle" font-family="{FONT}" font-size="12" fill="{th["text"]}">{esc(lk["label"])}</text></g>')
        x += w + 12
    inner.append(f'<text x="{CX}" y="{h - 40}" font-family="{FONT}" font-size="12" fill="{th["muted"]}">{esc(fs.get("text", ""))}</text>')
    return dict(name="footer", h=h, inner="".join(inner), nodes=[], top_y=0, bottom_y=node_y - 12, first=False, last=True, arrows=False,
                sb=["footer: the spine ends in a diamond; the pulse fades out here"], aria="End of page. " + fs.get("text", ""), station_ys=[])


# ------------------------------------------------------------------ page assembly
def build_page(spec, mode, reg):
    style = spec.get("style", "spine")
    if style == "blueprint":
        from readme_blueprint import build_blueprint_page
        helpers = {"wrap": wrap, "build_part": build_part}
        return build_blueprint_page(spec, mode, reg, helpers, theme_for, tp_factory)
    if style != "spine":
        sys.exit(f"unknown style '{style}': choose spine or blueprint")
    th = theme_for({"theme": spec.get("themes", {"dark": "ember", "light": "paper"})[mode], "colors": spec.get("brand", {})})
    dur = float(spec.get("dur", 24))
    ctx = dict(th=th, dur=dur, name=spec["name"], tagline=spec.get("tagline", ""), description=spec.get("description", ""),
               badges=spec.get("badges", []), glow_alpha=0.20 if mode == "dark" else 0.13)
    sections = spec["sections"]
    # pass 1: heights (Htot must be known before times)
    ctx["Htot"], ctx["tp"] = 4000.0, tp_factory(4000.0)
    ctx["ruler_labels"], ctx["nav_t0"] = [], 0.04
    labels = [s.get("nav", s["title"].split()[0]) for s in sections]
    hero = block_hero(ctx, spec, reg)
    nav = block_nav(ctx, spec, labels) if spec.get("nav", True) else None
    metas = [block_section(ctx, s, i, reg) for i, s in enumerate(sections)]
    y = hero["h"] + (nav["h"] if nav else 0)
    tmp = []
    for m in metas:
        sec_blk = finish_section(ctx, m, y, reg)
        tmp.append(sec_blk["h"])
        y += sec_blk["h"]
    Htot = y + 300
    ctx["Htot"], ctx["tp"] = float(Htot), tp_factory(float(Htot))
    # pass 2: real build
    hero = block_hero(ctx, spec, reg)
    blocks, y = [hero], hero["h"]
    if nav:
        blocks.append(nav)
        y += nav["h"]
    labs = []
    for m in metas:
        blk = finish_section(ctx, m, y, reg)
        labs.append(blk["ruler"])
        blocks.append(blk)
        y += blk["h"]
    ctx["ruler_labels"] = labs
    blocks.append(block_footer(ctx, spec))
    assert abs(sum(b["h"] for b in blocks) - Htot) < 1, (sum(b["h"] for b in blocks), Htot)
    svgs, y0 = [], 0
    for bi, b in enumerate(blocks):
        idp = f"b{bi}-"
        sp, _ = spine_and_pulse(ctx, y0, b["h"], b["nodes"], b["top_y"], b["bottom_y"], first=b["first"], last=b["last"])
        inner = aurora_slice(ctx, y0, b["h"], idp) + ruler(ctx, y0, b["h"]) + sp + b["inner"]
        sb = [f"block {bi} '{b['name']}'  y={y0}..{y0 + b['h']} of {Htot}  mode={mode}"] + b["sb"]
        hdr = header(W, b["h"], {"aria": b["aria"], "title_text": f"{spec['name']} - {b['name']}"}, sb, b["aria"])
        svg = hdr + "  " + common_defs(th, b["arrows"]) + "\n  " + inner + "\n</svg>\n"
        svgs.append((b["name"], svg, b["h"]))
        y0 += b["h"]
    return svgs, Htot


def write_all(spec, outdir, reg, do_preview=False, do_check=False):
    adir = os.path.join(outdir, "docs", "readme")
    os.makedirs(adir, exist_ok=True)
    modes = ["dark", "light"]
    files = {}
    Htot = 0
    for mode in modes:
        svgs, Htot = build_page(spec, mode, reg)
        for i, (name, svg, h) in enumerate(svgs):
            fn = f"{i:02d}-{name}-{mode}.svg" if not name[:2].isdigit() else f"{i:02d}-{name.split('-', 1)[1]}-{mode}.svg"
            with open(os.path.join(adir, fn), "w", encoding="utf-8") as fh:
                fh.write(svg)
            files.setdefault(i, {"name": name, "h": h})[mode] = fn
    # README.md
    name = spec["name"]
    out = [f'<!-- Generated by svg-animator readme_page.py (style: {spec.get("style", "spine")}). Blocks are stacked in ONE <div> with align="top" so there are no gaps. -->', "<div>"]
    hero_href = spec.get("hero", {}).get("href")
    for i in sorted(files):
        f = files[i]
        alt = esc(f["name"].split("-", 1)[-1].replace("-", " "))
        pic = (f'<picture><source media="(prefers-color-scheme: dark)" srcset="docs/readme/{f["dark"]}">'
               f'<img alt="{name} - {alt}" src="docs/readme/{f["light"]}" width="100%" align="top"></picture>')
        if i == 0 and hero_href:
            pic = f'<a href="{hero_href}">{pic}</a>'
        out.append(pic)
    out.append("</div>\n")
    for md in spec.get("prose", []):
        # Markdown text after the page: the page's words are inside images, so this is what search and screen readers see.
        out.append("")
        out.append(md.rstrip("\n"))
    copies = [(s["title"], s["copy"]) for s in spec["sections"] if s.get("copy")]
    if copies:
        out.append("<details><summary>Copy the commands</summary>\n")
        for t, cmds in copies:
            out.append(f"**{t}**\n\n```bash\n" + "\n".join(cmds) + "\n```\n")
        out.append("</details>\n")
    links = spec.get("footer", {}).get("links", [])
    if links:
        out.append('<p align="center">' + " · ".join(f'<a href="{l["href"]}">{l["label"]}</a>' for l in links if l.get("href")) + "</p>\n")
    with open(os.path.join(outdir, "README.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(out))
    if do_check:
        bad = 0
        for fn in sorted(os.listdir(adir)):
            if fn.endswith(".svg"):
                r = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lint_svg_anim.py"), os.path.join(adir, fn), "--quiet"], capture_output=True, text=True)
                last = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else "?"
                flag = "" if "0 error(s), 0 warning(s)" in last else "   <-- CHECK"
                bad += 1 if flag else 0
                print(f"  {fn:38s} {last.split('svg: ')[-1]}{flag}")
        print("lint: all blocks clean" if not bad else f"lint: {bad} block(s) need attention")
    if do_preview:
        preview(spec, outdir, adir, files)
    return files


def preview(spec, outdir, adir, files):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright unavailable: preview skipped")
        return
    dur = float(spec.get("dur", 24))
    times = [0.0, 0.2 * dur, 0.5 * dur, 0.8 * dur]
    with sync_playwright() as p:
        b = p.chromium.launch()
        for mode, bg in (("dark", "#0d1117"), ("light", "#ffffff")):
            blocks = "".join(open(os.path.join(adir, files[i][mode]), encoding="utf-8").read() for i in sorted(files))
            html = (f"<!doctype html><html><head><style>body{{margin:0;background:{bg};width:888px}}svg{{display:block;width:100%;height:auto}}</style></head><body>{blocks}</body></html>")
            pg = b.new_page(viewport={"width": 888, "height": 900})
            pg.set_content(html)
            for t in times:
                pg.evaluate("(t)=>document.querySelectorAll('svg').forEach(s=>{s.pauseAnimations();s.setCurrentTime(t)})", t)
                pg.wait_for_timeout(80)
                fn = os.path.join(adir, f"preview-{mode}-t{t:05.1f}.png")
                pg.screenshot(path=fn, full_page=True)
                print("preview:", os.path.relpath(fn, outdir))
        b.close()


def seam_check(adir, files, widths=(888, 760, 640, 480, 390), align="top", max_gap=0.5, max_dip=40):
    """Render the README markup as real <img> elements (what GitHub does) at several widths and measure every block seam:
    the layout gap between images, and how much the spine dims where two blocks meet (sum of RGB; 0 = invisible).
    Needs Playwright + Pillow (optional extras). Returns (ok, lines)."""
    try:
        from playwright.sync_api import sync_playwright
        from PIL import Image
    except ImportError:
        return None, ["seam check skipped: Playwright and Pillow are optional extras and are not installed"]
    out, ok, tmp = [], True, os.path.join(adir, ".seam-tmp")
    os.makedirs(tmp, exist_ok=True)
    order = sorted(files)
    with sync_playwright() as p:
        b = p.chromium.launch()
        for mode, bg in (("dark", "#0d1117"), ("light", "#ffffff")):
            names = [files[i][mode] for i in order]
            for w in widths:
                imgs = "\n".join('<picture><img src="file://%s/%s" width="100%%"%s></picture>' % (adir, f, f' align="{align}"' if align else "") for f in names)
                hp = os.path.join(tmp, f"{mode}-{w}.html")
                with open(hp, "w", encoding="utf-8") as fh:
                    fh.write(f'<!doctype html><html><body style="margin:0;background:{bg}"><div style="width:{w}px;font:16px/1.5 sans-serif">{imgs}</div></body></html>')
                pg = b.new_page(viewport={"width": w + 24, "height": 800})
                pg.goto("file://" + hp)
                pg.evaluate("Promise.all([...document.images].map(i=>i.decode().catch(()=>0)))")
                pg.wait_for_timeout(300)
                rects = pg.evaluate("[...document.images].map(i=>{const r=i.getBoundingClientRect();return [r.top,r.bottom]})")
                shot = os.path.join(tmp, f"{mode}-{w}.png")
                pg.screenshot(path=shot, full_page=True)
                pg.close()
                im = Image.open(shot).convert("RGB")
                px = im.load()
                sx = round(SPX / W * w)
                gap = max(abs(rects[i + 1][0] - rects[i][1]) for i in range(len(rects) - 1))
                dip = 0
                for i in range(len(rects) - 1):
                    sy = int(rects[i][1])
                    ref = sorted(sum(px[sx, y]) for y in range(sy - 14, sy - 6))[2]
                    dip = max(dip, ref - min(sum(px[sx, y]) for y in range(sy - 4, sy + 5)))
                good = gap <= max_gap and dip <= max_dip
                ok = ok and good
                out.append(f"  {mode:5s} width {w:>3}px  layout gap {gap:5.2f}px  worst spine dip {max(dip, 0):>4}  {'ok' if good else 'SEAM VISIBLE'}")
        b.close()
    shutil.rmtree(tmp, ignore_errors=True)
    return ok, out


def seam_selftest(adir, files):
    """A gate that cannot fail is not a gate: the correct markup must pass AND plain <img> (no align) must fail."""
    good, lines_g = seam_check(adir, files, widths=(888, 480), align="top")
    bad, lines_b = seam_check(adir, files, widths=(888, 480), align=None)
    if good is None:
        return None, lines_g
    res = ["correct markup  (align=\"top\"):"] + lines_g + ["known-bad markup (no align, baseline gap):"] + lines_b
    return (good is True and bad is False), res + [f"self-test: {'PASS (correct passes, bad fails)' if good and not bad else 'FAIL'}"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("outdir")
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--check", action="store_true", help="lint every block with lint_svg_anim.py")
    ap.add_argument("--seams", action="store_true", help="render the README markup as real <img> at 5 widths and measure every seam")
    ap.add_argument("--seams-selftest", action="store_true", help="prove the seam gate can fail: correct markup passes, plain <img> fails")
    a = ap.parse_args()
    spec = json.load(open(a.spec, encoding="utf-8"))
    files = write_all(spec, a.outdir, registry(), a.preview, a.check)
    print(f"wrote {len(files)} blocks x 2 modes + README.md to {os.path.abspath(a.outdir)}")
    adir = os.path.join(os.path.abspath(a.outdir), "docs", "readme")
    code = 0
    if a.seams or a.seams_selftest:
        ok, lines = (seam_selftest if a.seams_selftest else seam_check)(adir, files)
        print("\n".join(lines))
        code = 0 if ok in (True, None) else 1
    sys.exit(code)


if __name__ == "__main__":
    main()
