"""readme_blueprint.py - the "blueprint" style for readme_page.py.

A drafting-sheet README: a millimetre-style grid behind every block (page-aligned, so it continues across
block borders), a dimension line down the left margin with a tick at every section, numbered section
circles, dimension lines under each embedded part (labelled with its real width), and a title block in the
bottom-right corner of the footer. The same spec format, fitting logic, pulse clock and checks as "spine".

Entry point: build_blueprint_page(spec, mode, reg, helpers) -> (svgs, Htot)
"""
import math

from diagram_common import FONT, SANS, F, T, common_defs, esc, header

W = 1000
GRID = 24          # minor grid, px
MAJOR = 120        # major grid, px
LEFT = 96          # dimension line x
CX, CW = 140, 760  # content column
CONTENT_R = CX + CW


def _grid(th, y0, h, idp):
    """Minor + major grid for one block, using page-absolute y so blocks join up exactly."""
    minor, major = [], []
    xs = list(range(0, W + 1, GRID))
    y = math.ceil(y0 / GRID) * GRID
    while y < y0 + h:
        (major if y % MAJOR == 0 else minor).append(f"M0,{F(y - y0)} H{W}")
        y += GRID
    for x in xs:
        (major if x % MAJOR == 0 else minor).append(f"M{x},0 V{F(h)}")
    return (f'<path d="{" ".join(minor)}" stroke="{th["stroke_dim"]}" stroke-width="0.6" opacity="0.28" fill="none"/>'
            f'<path d="{" ".join(major)}" stroke="{th["stroke_dim"]}" stroke-width="1" opacity="0.5" fill="none"/>')


def _dim_h(th, x0, x1, y, label):
    """Horizontal dimension line with slash ticks and a centred label."""
    mx = (x0 + x1) / 2
    return (f'<path d="M{F(x0)},{F(y)} H{F(x1)} M{F(x0 - 5)},{F(y + 5)} L{F(x0 + 5)},{F(y - 5)} M{F(x1 - 5)},{F(y + 5)} L{F(x1 + 5)},{F(y - 5)}" '
            f'stroke="{th["accent"]}" stroke-width="1" fill="none" opacity="0.8"/>'
            f'<text x="{F(mx)}" y="{F(y - 6)}" text-anchor="middle" font-family="{FONT}" font-size="10" fill="{th["accent"]}" letter-spacing="1">{esc(label)}</text>')


def _pulse(ctx, y0, h, first=False, last=False):
    """A square marker travelling down the left dimension line on the page clock (same timing as spine)."""
    th, dur, tp = ctx["th"], ctx["dur"], ctx["tp"]
    ts, te = tp(y0), tp(y0 + h)
    mkt = f"0;{T(ts)};{T(te)};1"
    okt = f"0;{T(ts)};{T(ts + (0.012 if first else 0.0004))};{T(te - (0.02 if last else 0.0004))};{T(te)};1"
    return (f'<rect x="{LEFT - 4}" y="0" width="8" height="8" fill="{th["accent"]}" opacity="0">'
            f'<animateTransform attributeName="transform" type="translate" dur="{dur:g}s" repeatCount="indefinite" calcMode="linear" '
            f'keyTimes="{mkt}" values="0 0;0 0;0 {F(h - 8)};0 {F(h - 8)}"/>'
            f'<animate attributeName="opacity" dur="{dur:g}s" repeatCount="indefinite" keyTimes="{okt}" values="0;0;1;1;0;0"/></rect>')


def _axis(ctx, y0, h, ticks, first=False, last=False):
    th = ctx["th"]
    s = [f'<path d="M{LEFT},0 V{F(h)}" stroke="{th["accent"]}" stroke-width="1" opacity="0.7"/>']
    for ty, lbl in ticks:
        s.append(f'<path d="M{LEFT - 8},{F(ty)} H{LEFT + 8}" stroke="{th["accent"]}" stroke-width="1.2"/>'
                 f'<text x="{LEFT - 14}" y="{F(ty + 4)}" text-anchor="end" font-family="{FONT}" font-size="10" fill="{th["muted"]}">{esc(lbl)}</text>')
    s.append(_pulse(ctx, y0, h, first, last))
    return "".join(s)


def _badge_row(th, x, y, items, max_x):
    out, cx_, cy_ = [], x, y
    for b in items:
        w = round(len(b) * 7.6 + 24)
        if cx_ + w > max_x:
            cx_, cy_ = x, cy_ + 38
        out.append(f'<g><rect x="{cx_}" y="{cy_}" width="{w}" height="28" fill="none" stroke="{th["stroke"]}" stroke-width="1.1"/>'
                   f'<text x="{F(cx_ + w / 2)}" y="{cy_ + 19}" text-anchor="middle" font-family="{FONT}" font-size="11" fill="{th["text"]}">{esc(b)}</text></g>')
        cx_ += w + 10
    return "".join(out), cy_ + 28


def _hero(ctx, spec, helpers):
    th, dur = ctx["th"], ctx["dur"]
    hs = spec.get("hero", {})
    name = ctx["name"]
    size = max(34, min(72, int(420 / (max(len(name), 1) * 0.6))))
    wrap, build_part, reg = helpers["wrap"], helpers["build_part"], helpers["reg"]
    tag = wrap(ctx["tagline"], 36)
    desc = wrap(ctx["description"], 58)
    y = 120
    ty = y
    y += 56
    tag_y = y
    y += 30 * len(tag) + 14
    desc_y = y
    y += 22 * len(desc) + 22
    badges_svg, y = _badge_row(th, CX, y, ctx["badges"], 560)
    y += 14
    cta_y = y
    ctas = hs.get("cta", [{"label": "Get started"}, {"label": "Read the docs"}])
    y += 56
    vis = hs.get("visual", {"type": "art", "variant": "orbits"})
    if vis["type"] in ("art", "scene"):
        vis = dict(vis, size=340, width=340, height=340)
    vp = build_part(vis, th, "bpv0-", dur, 340, reg, (0.0, 1.0))
    h = int(max(y + 40, 140 + vp["H"] + 60, 480))
    s = [f'<text x="{CX}" y="60" font-family="{FONT}" font-size="11" fill="{th["accent"]}" letter-spacing="3">{esc(hs.get("eyebrow", "SHEET 00 · OVERVIEW").upper())}</text>']
    s.append(f'<text x="{CX}" y="{ty}" font-family="{SANS}" font-size="{size}" font-weight="800" letter-spacing="-1.5" fill="{th["text_key"]}">{esc(name)}</text>')
    for i, ln in enumerate(tag):
        s.append(f'<text x="{CX}" y="{tag_y + 30 * i}" font-family="{SANS}" font-size="22" font-weight="600" fill="{th["text_key"]}">{esc(ln)}</text>')
    for i, ln in enumerate(desc):
        s.append(f'<text x="{CX}" y="{desc_y + 22 * i}" font-family="{SANS}" font-size="15" fill="{th["muted"]}">{esc(ln)}</text>')
    s.append(badges_svg)
    bx = CX
    for i, c in enumerate(ctas):
        w = round(len(c["label"]) * 9 + 40)
        fill = th["accent"] if i == 0 else "none"
        fg = th["bg"] if i == 0 else th["text"]
        stroke = "none" if i == 0 else th["stroke"]
        s.append(f'<g><rect x="{bx}" y="{cta_y}" width="{w}" height="44" fill="{fill}" stroke="{stroke}" stroke-width="1.2"/>'
                 f'<text x="{F(bx + w / 2)}" y="{cta_y + 28}" text-anchor="middle" font-family="{SANS}" font-size="14" font-weight="700" fill="{fg}">{esc(c["label"])}</text></g>')
        bx += w + 12
    vx = 600 + (CONTENT_R - 600 - vp["W"]) / 2
    sc = f" scale({vp['scale']:.3f})" if vp["scale"] != 1 else ""
    s.append(f'<rect x="{600}" y="110" width="{CONTENT_R - 600}" height="{F(vp["H"] + 60)}" fill="none" stroke="{th["stroke_dim"]}" stroke-width="1" stroke-dasharray="4 5"/>')
    s.append(f'<g transform="translate({F(vx)} 140){sc}">{vp["body"]}</g>')
    return dict(name="hero", h=h, inner="".join(s), axis_ticks=[], first=True, last=False, arrows=vp["p"]["arrows"],
                sb=["hero: sheet header, title, spec tags, visual in a dashed callout"] + vp["sb"], aria=f"{name}: {ctx['tagline']}")


def _nav(ctx, labels):
    th = ctx["th"]
    h = 84
    n = len(labels)
    xs = [CX + 16 + i * (CW - 32) / max(1, n - 1) for i in range(n)]
    y = 40
    s = [f'<path d="M{CX},{y} H{CONTENT_R}" stroke="{th["stroke"]}" stroke-width="1" fill="none"/>']
    for i, (x, lab) in enumerate(zip(xs, labels)):
        s.append(f'<circle cx="{F(x)}" cy="{y}" r="11" fill="{th["bg"]}" stroke="{th["accent"]}" stroke-width="1.4"/>'
                 f'<text x="{F(x)}" y="{y + 4}" text-anchor="middle" font-family="{FONT}" font-size="10" fill="{th["accent"]}">{i + 1}</text>'
                 f'<text x="{F(x)}" y="{y + 32}" text-anchor="middle" font-family="{FONT}" font-size="11" fill="{th["text"]}">{esc(lab)}</text>')
    return dict(name="nav", h=h, inner="".join(s), axis_ticks=[], first=False, last=False, arrows=False,
                sb=["nav: sheet index"], aria="Sheet index: " + ", ".join(labels))


def _section(ctx, sec, idx, helpers):
    wrap, build_part, reg = helpers["wrap"], helpers["build_part"], helpers["reg"]
    lede = wrap(sec.get("lede", ""), 84) if sec.get("lede") else []
    header_h = 96 + 24 * len(lede) + (14 if lede else 0)
    return dict(sec=sec, idx=idx, lede=lede, header_h=header_h, build_part=build_part, reg=reg)


def _finish_section(ctx, meta, y0, helpers):
    th, dur = ctx["th"], ctx["dur"]
    sec, idx, lede, hh = meta["sec"], meta["idx"], meta["lede"], meta["header_h"]
    build_part, reg = meta["build_part"], meta["reg"]
    win = (0.0, 1.0)  # blueprint parts keep the whole loop: the sheet is read as a whole
    part = build_part(sec["part"], th, f"bs{idx + 2}p-", dur, CW - 40, reg, win)
    pad = 26
    h = int(hh + part["H"] + pad * 2 + 30)
    s = []
    cy = 46
    s.append(f'<circle cx="{CX - 40}" cy="{cy}" r="18" fill="{th["bg"]}" stroke="{th["accent"]}" stroke-width="1.8"/>'
             f'<text x="{CX - 40}" y="{cy + 5}" text-anchor="middle" font-family="{FONT}" font-size="14" font-weight="700" fill="{th["accent"]}">{idx + 1:02d}</text>')
    s.append(f'<text x="{CX}" y="{cy + 6}" font-family="{FONT}" font-size="10" fill="{th["accent"]}" letter-spacing="3">SECTION {idx + 1:02d} · {esc(sec.get("nav", sec["title"]).upper())}</text>')
    s.append(f'<text x="{CX}" y="{cy + 42}" font-family="{SANS}" font-size="34" font-weight="800" letter-spacing="-0.5" fill="{th["text_key"]}">{esc(sec["title"])}</text>')
    for i, ln in enumerate(lede):
        s.append(f'<text x="{CX}" y="{cy + 74 + 24 * i}" font-family="{SANS}" font-size="16" fill="{th["muted"]}">{esc(ln)}</text>')
    py = hh + pad
    px = CX + (CW - 40 - part["W"]) / 2
    sc = f" scale({part['scale']:.3f})" if part["scale"] != 1 else ""
    s.append(f'<rect x="{F(CX - 14)}" y="{F(py - 14)}" width="{F(CW - 12)}" height="{F(part["H"] + 28)}" fill="none" stroke="{th["stroke_dim"]}" stroke-width="1" stroke-dasharray="6 6"/>')
    s.append(f'<g id="bs{idx + 2}-part" transform="translate({F(px)} {F(py)}){sc}">{part["body"]}</g>')
    dim_y = h - 14
    s.append(_dim_h(th, px, px + part["W"], dim_y, f"{part['W']:.0f} PX"))
    sb = [f"section {idx + 1} '{sec['title']}': whole-loop part, dimension {part['W']:.0f}px"] + part["sb"]
    return dict(name=f"{idx + 1:02d}-{sec.get('id', 'section')}", h=h, inner="".join(s), axis_ticks=[(cy, "")],
                first=False, last=False, arrows=part["p"]["arrows"], sb=sb, aria=f"{sec['title']}. {sec.get('lede', '')}".strip(),
                ruler=None)


def _footer(ctx, spec):
    th = ctx["th"]
    fs = spec.get("footer", {})
    h = 260
    s = [f'<text x="{CX}" y="60" font-family="{FONT}" font-size="11" fill="{th["accent"]}" letter-spacing="3">END OF SHEET</text>']
    closing = fs.get("closing", "Build something worth reading.")
    s.append(f'<text x="{CX}" y="110" font-family="{SANS}" font-size="36" font-weight="800" letter-spacing="-1" fill="{th["text_key"]}">{esc(closing)}</text>')
    x = CX
    for lk in fs.get("links", []):
        w = round(len(lk["label"]) * 8.4 + 30)
        s.append(f'<g><rect x="{x}" y="140" width="{w}" height="32" fill="none" stroke="{th["stroke"]}" stroke-width="1.1"/>'
                 f'<text x="{F(x + w / 2)}" y="161" text-anchor="middle" font-family="{FONT}" font-size="12" fill="{th["text"]}">{esc(lk["label"])}</text></g>')
        x += w + 10
    # title block, bottom right
    bx, by, bw, bh = CONTENT_R - 300, 186, 300, 64
    s.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" fill="{th["bg"]}" stroke="{th["accent"]}" stroke-width="1.2"/>'
             f'<path d="M{bx},{by + 26} H{bx + bw} M{bx + 150},{by + 26} V{by + bh}" stroke="{th["accent"]}" stroke-width="0.8" fill="none"/>'
             f'<text x="{bx + 10}" y="{by + 16}" font-family="{FONT}" font-size="9" fill="{th["muted"]}" letter-spacing="1">PROJECT</text>'
             f'<text x="{bx + 10}" y="{by + 20 + 22}" font-family="{FONT}" font-size="12" fill="{th["text"]}">{esc(ctx["name"])}</text>'
             f'<text x="{bx + 160}" y="{by + 16}" font-family="{FONT}" font-size="9" fill="{th["muted"]}" letter-spacing="1">REV / SHEET</text>'
             f'<text x="{bx + 160}" y="{by + 46}" font-family="{FONT}" font-size="12" fill="{th["text"]}">{esc(fs.get("rev", "1.0 · 01/" + str(len(spec["sections"]) + 2).zfill(2)))}</text>')
    s.append(f'<text x="{CX}" y="{h - 26}" font-family="{FONT}" font-size="11" fill="{th["muted"]}">{esc(fs.get("text", ""))}</text>')
    return dict(name="footer", h=h, inner="".join(s), axis_ticks=[], first=False, last=True, arrows=False,
                sb=["footer: sheet closing, links, title block"], aria="End of sheet. " + fs.get("text", ""))


def build_blueprint_page(spec, mode, reg, helpers, theme_for, tp_factory):
    """Returns (svgs, Htot). Same two-pass height logic as spine so the pulse clock matches the page."""
    th = theme_for({"theme": spec.get("themes", {"dark": "ocean", "light": "paper"})[mode], "colors": spec.get("brand", {})})
    dur = float(spec.get("dur", 24))
    ctx = dict(th=th, dur=dur, name=spec["name"], tagline=spec.get("tagline", ""), description=spec.get("description", ""),
               badges=spec.get("badges", []))
    sections = spec["sections"]
    helpers = dict(helpers, reg=reg)
    labels = [s.get("nav", s["title"].split()[0]) for s in sections]

    def assemble(Htot):
        ctx["Htot"], ctx["tp"] = float(Htot), tp_factory(float(Htot))
        blocks = [_hero(ctx, spec, helpers)]
        if spec.get("nav", True):
            blocks.append(_nav(ctx, labels))
        y = sum(b["h"] for b in blocks)
        for i, s in enumerate(sections):
            blk = _finish_section(ctx, _section(ctx, s, i, helpers), y, helpers)
            blocks.append(blk)
            y += blk["h"]
        blocks.append(_footer(ctx, spec))
        return blocks

    Htot = sum(b["h"] for b in assemble(4000.0)) + 40
    blocks = assemble(Htot)
    total = sum(b["h"] for b in blocks)
    if total != Htot:
        Htot = total
        blocks = assemble(Htot)
    svgs, y0 = [], 0
    for bi, b in enumerate(blocks):
        idp = f"bp{bi}-"
        inner = _grid(th, y0, b["h"], idp)
        inner += "".join(_axis_for(ctx, y0, b, bi, len(blocks)))
        inner += b["inner"]
        sb = [f"block {bi} '{b['name']}'  y={y0}..{y0 + b['h']} of {Htot}  mode={mode}"] + b["sb"]
        hdr = header(W, b["h"], {"aria": b["aria"], "title_text": f"{spec['name']} - {b['name']}"}, sb, b["aria"])
        svg = hdr + "  " + common_defs(th, b["arrows"]) + "\n  " + inner + "\n</svg>\n"
        svgs.append((b["name"], svg, b["h"]))
        y0 += b["h"]
    return svgs, Htot


def _axis_for(ctx, y0, b, bi, nblocks):
    """Dimension line + ticks for one block, in block-local coordinates."""
    if not b["axis_ticks"] and b["name"] in ("hero", "nav", "footer"):
        return [f'<path d="M{LEFT},0 V{F(b["h"])}" stroke="{ctx["th"]["accent"]}" stroke-width="1" opacity="0.7"/>', _pulse(ctx, y0, b["h"], b["first"], b["last"])]
    return [_axis(ctx, y0, b["h"], b["axis_ticks"], b["first"], b["last"])]
