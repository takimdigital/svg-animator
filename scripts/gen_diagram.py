#!/usr/bin/env python3
"""gen_diagram.py - build README-grade animated SVG diagrams from a JSON spec.

Usage:
  python gen_diagram.py spec.json out.svg [--theme ember|ocean|forest|mono|paper|violet|sunset]

Types ("type" in the spec):
  flow      left-to-right pipeline in columns, fan-out / fan-in, optional feedback loop (relay dots)
  radial    hub with N clusters on a ring, sonar rings + clockwise glow sweep
  phases    stacked phase panels lighting in sequence, chips inside
  timeline  milestones on a spine, alternating cards, a progress dot travelling the spine
  network   arbitrary graph (circle / grid / explicit x,y), pulses spread by BFS from start nodes
  layers    stacked architecture layers, request dot going down, response dot coming back up
  cycle     steps on a ring, a dot orbiting around the loop (CI/CD, feedback, lifecycle)
  sequence  actors + lifelines + messages, a packet travelling each message in order
  terminal  terminal window typing commands and printing output (static-first)
  cards     stat / feature tiles with a glow wave
  chart     bar or line chart that grows in (static-first)
  banner    README header banner: shimmer title, subtitle, tag chips, drifting particles
  --- not diagrams (general SVG animation) ---
  loader    8 spinner/loader variants as a sheet (ring, dots, bars, orbit, pulse, dual, wave, progress)
  logo      logo reveal: mark draw-on, fill, initials, wordmark, tagline, shine
  text      kinetic text: wave, reveal, pop, type, shimmer, glitch
  gauge     gauge / ring / bar / donut with count-up numbers
  radar     radar (spider) chart, one or more series
  backdrop  animated backgrounds: waves, stars, grid, bubbles, rain, mesh
  icons     12 micro-animated icons (check, heart, bell, gear, download, star, play-pause, sun, lock, wifi, bolt, cross)
  scene     illustrated scenes: rocket, coffee, ocean, orbit
  counter   odometer counters that roll to their values
  art       generative art: mandala, lissajous, spiral, orbits, flower
  compose   COMBINE any of the above (stack / row / grid) on one master clock, optional per-part time window

Why a generator: layout, rail endpoints and every keyTime are COMPUTED from the spec, so rails touch their
cards, glows match the dots and keyTimes end at 1. The schedule is printed and embedded as a comment.
No JavaScript, no external assets, no xlink: works in GitHub READMEs (<img>), docs and slides.
Spec reference: references/diagram-types.md  and  assets/specs/*.json
"""
import argparse
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diagram_common import (DARK_THEMES, FONT, THEMES, F, T, aurora, apply_window, card_w, common_defs, eyebrow, esc,  # noqa: E402
                            glow_overlay, gradient_colors, header, make_slots, map_sb, node_card, part, rail,
                            relay_traveller, tdesc)

PICTURE_TMPL = """<picture>
  <source media="(prefers-color-scheme: dark)" srcset="{dark}">
  <img src="{light}" alt="{alt}" width="100%">
</picture>"""

from static_twin import main as static_twin_main  # noqa: E402


# ------------------------------------------------------------------ FLOW
def build_flow(spec, th, idp=""):
    dur = float(spec.get("dur", 6.0))
    cols = spec["columns"]
    C = len(cols)
    arrows = spec.get("arrows", True)
    gx, gy, nh = spec.get("gap_x", 84), spec.get("gap_y", 46), spec.get("node_h", 62)
    margin = spec.get("margin", 48)
    tz = spec.get("title_zone", 84 if spec.get("title") else 28)
    g_arrow = 4 if arrows else 0
    warns = []

    nodes = {}
    for ci, col in enumerate(cols):
        for n in col:
            lbl, sub = n["label"], n.get("sub", "")
            lsz = n.get("label_size", 18 if len(lbl) <= 16 else 15)
            nodes[n["id"]] = dict(id=n["id"], col=ci, label=lbl, sub=sub, key=n.get("key", False), color=n.get("color"),
                                  w=card_w(lbl, sub, lsz), h=nh, lsz=lsz)
    colw = [max(nodes[n["id"]]["w"] for n in col) for col in cols]
    colx, cur = [], margin
    for w in colw:
        colx.append(cur)
        cur += w + gx
    W = cur - gx + margin
    colh = [len(col) * nh + (len(col) - 1) * gy for col in cols]
    Hmax = max(colh)
    cy0 = tz + Hmax / 2
    for ci, col in enumerate(cols):
        y = cy0 - colh[ci] / 2
        for n in col:
            nd = nodes[n["id"]]
            nd.update(x=colx[ci] + (colw[ci] - nd["w"]) / 2, y=y)
            nd["cx"], nd["cy"] = nd["x"] + nd["w"] / 2, y + nh / 2
            y += nh + gy

    fb = spec.get("feedback")
    H = tz + Hmax + 44
    if fb:
        a, b = nodes[fb["from"]], nodes[fb["to"]]
        lbl, sub = fb["label"], fb.get("sub", "")
        w = card_w(lbl, sub, 18, minw=150)
        fy = tz + Hmax + 56
        nodes[fb["id"]] = dict(id=fb["id"], col=-1, label=lbl, sub=sub, key=False, color=th["loop"], w=w, h=nh, lsz=18,
                               x=(a["cx"] + b["cx"]) / 2 - w / 2, y=fy, cx=(a["cx"] + b["cx"]) / 2, cy=fy + nh / 2, fb=True)
        H = fy + nh + 44
    H = max(H, spec.get("min_height", 160))

    edges = spec.get("edges", "auto")
    pairs = []
    if edges == "auto":
        for ci in range(C - 1):
            for a in cols[ci]:
                for b in cols[ci + 1]:
                    pairs.append((a["id"], b["id"]))
    else:
        pairs = [tuple(e) for e in edges]
    rails = []
    for a_id, b_id in pairs:
        A, B = nodes[a_id], nodes[b_id]
        if B["col"] <= A["col"]:
            sys.exit(f"edge {a_id}->{b_id}: only left-to-right edges are supported (use 'feedback' for loops, or type 'network')")
        if B["col"] > A["col"] + 1:
            warns.append(f"edge {a_id}->{b_id} skips a column; it may cross a node")
        x1, y1, x2, y2 = A["x"] + A["w"], A["cy"], B["x"] - g_arrow, B["cy"]
        if abs(y1 - y2) < 0.5:
            d = f"M{F(x1)},{F(y1)} L{F(x2)},{F(y2)}"
        else:
            mx = (x1 + x2) / 2
            d = f"M{F(x1)},{F(y1)} C{F(mx)},{F(y1)} {F(mx)},{F(y2)} {F(x2)},{F(y2)}"
        rails.append(dict(d=d, slot=A["col"], src=a_id, dst=b_id, loop=False))

    slots = C - 1
    if fb:
        fa, tb = nodes[fb["from"]], nodes[fb["to"]]
        s1 = fa["col"] if fa["col"] <= C - 2 else C - 1
        s2 = max(C - 1, s1 + 1)
        slots = max(slots, s2 + 1)
        m = nodes[fb["id"]]
        ex = m["x"] + m["w"] + g_arrow
        fx, fyb, my = fa["cx"], fa["y"] + fa["h"], m["cy"]
        d1 = f"M{F(fx)},{F(fyb)} C{F(fx)},{F(fyb + 0.65 * (my - fyb))} {F(ex + 0.5 * (fx - ex))},{F(my)} {F(ex)},{F(my)}"
        sx = m["x"]
        tx, tyb = tb["cx"], tb["y"] + tb["h"] + g_arrow
        d2 = f"M{F(sx)},{F(my)} C{F(sx - 0.5 * (sx - tx))},{F(my)} {F(tx)},{F(tyb + 0.65 * (my - tyb))} {F(tx)},{F(tyb)}"
        if fx - ex < 30 or sx - tx < 30:
            warns.append("feedback node is too close to its source/target; widen gap_x or pick non-adjacent columns")
        rails.append(dict(d=d1, slot=s1, src=fb["from"], dst=fb["id"], loop=True))
        rails.append(dict(d=d2, slot=s2, src=fb["id"], dst=fb["to"], loop=True))

    win, h = make_slots(slots)
    arrivals = {nid: [] for nid in nodes}
    for c0 in cols[0]:
        arrivals[c0["id"]].append(win[0][0])
    for r in rails:
        arrivals[r["dst"]].append(win[r["slot"]][1])

    sb = [f"type=flow  loop={dur:g}s  columns={C}  hops={slots}  hop_len={h:.3f}",
          "travellers = relay dots (one per rail), parked invisible outside their slot; they only ever travel on rails"]
    sb += [tdesc(f"slot {i}", a, b) for i, (a, b) in enumerate(win)]
    for nid, arr in arrivals.items():
        sb.append(f"glow {nid}: arrivals {', '.join(f'{x:.3f}' for x in sorted(arr))}")
    for w_ in warns:
        sb.append("WARNING: " + w_)
        print("WARNING:", w_, file=sys.stderr)

    body = []
    for r in rails:
        body.append("  " + rail(r["d"], th, loop=r["loop"], arrows=arrows) + "\n")
    for nid, nd in nodes.items():
        acc = nd["color"] or th["accent"]
        body.append("  " + node_card(th, idp + "node-", nid, nd["x"], nd["y"], nd["w"], nd["h"], nd["label"], nd["sub"],
                                    nd["key"] or nd.get("fb", False), arrivals[nid], dur, lsz=nd["lsz"], accent=acc) + "\n")
    for r in rails:
        ts, te = win[r["slot"]]
        body.append("  " + relay_traveller(r["d"], ts, te, th["loop"] if r["loop"] else th["accent"], th["dot"], dur) + "\n")
    return part("".join(body), W, H, sb, arrows, "Flow diagram: " + " -> ".join(n["label"] for col in cols for n in col[:1]))


# ------------------------------------------------------------------ RADIAL
def build_radial(spec, th, idp=""):
    dur = float(spec.get("dur", 6.0))
    items, core = spec["items"], spec["center"]
    n = len(items)
    core_r = spec.get("core_r", 60)
    R = spec.get("radius", 256 if n >= 7 else (230 if n >= 5 else 210))
    cards = []
    for i, it in enumerate(items):
        lines = it.get("lines", [])
        cnt = str(it.get("count", ""))
        w = math.ceil(max(max((len(x) for x in lines), default=6) * 7.3 + 26, len(it["title"]) * 8.4 + len(cnt) * 7 + 34))
        h = 34 + 17 * len(lines)
        a = math.radians(-90 + 360 * i / n)
        px, py = R * math.cos(a), R * math.sin(a)
        cards.append(dict(it=it, w=w, h=h, a=a, x=px - w / 2, y=py - h / 2, cnt=cnt, lines=lines))
    minx = min(min(c["x"] for c in cards), -core_r)
    maxx = max(max(c["x"] + c["w"] for c in cards), core_r)
    miny = min(min(c["y"] for c in cards), -core_r)
    maxy = max(max(c["y"] + c["h"] for c in cards), core_r)
    margin = 56
    top = spec.get("title_zone", 88 if spec.get("title") else 40)
    ox, oy = margin - minx, top - miny
    W, H = (maxx - minx) + 2 * margin, (maxy - miny) + top + margin
    cx, cy = ox, oy
    step = 0.9 / n
    decay = min(0.12, step * 1.1)
    sb = [f"type=radial  loop={dur:g}s  clusters={n}  ring_radius={R}", "sonar rings: 3 rings phased by negative begin (pre-rolled), drawn UNDER the cards"]
    sb += [tdesc(f"cluster {i}", i * step + 0.03, i * step + 0.03 + decay) for i in range(n)]
    body = []
    for c in cards:
        dx, dy = math.cos(c["a"]), math.sin(c["a"])
        ts = []
        for lo, hi, d_ in ((c["x"], c["x"] + c["w"], dx), (c["y"], c["y"] + c["h"], dy)):
            if abs(d_) > 1e-9:
                t1, t2 = lo / d_, hi / d_
                ts.append((min(t1, t2), max(t1, t2)))
        t_in = max(t[0] for t in ts)
        body.append("  " + rail(f"M{F(cx + core_r * dx)},{F(cy + core_r * dy)} L{F(cx + t_in * dx)},{F(cy + t_in * dy)}", th, sw=1.3) + "\n")
    rmax = R + 12
    for k in range(3):
        b = f"{-k * dur / 3:g}s"
        body.append(f'  <circle cx="{F(cx)}" cy="{F(cy)}" r="{core_r}" fill="none" stroke="{th["accent"]}" stroke-width="2" opacity="0.55">'
                    f'<animate attributeName="r" values="{core_r};{rmax}" dur="{dur:g}s" begin="{b}" repeatCount="indefinite"/>'
                    f'<animate attributeName="opacity" values="0.55;0" dur="{dur:g}s" begin="{b}" repeatCount="indefinite"/>'
                    f'<animate attributeName="stroke-width" values="2.4;0.4" dur="{dur:g}s" begin="{b}" repeatCount="indefinite"/></circle>\n')
    for i, c in enumerate(cards):
        x, y, w, h = c["x"] + ox, c["y"] + oy, c["w"], c["h"]
        body.append(f'  <g id="{idp}cluster-{i}"><rect x="{F(x)}" y="{F(y)}" width="{F(w)}" height="{F(h)}" rx="9" fill="{th["surface"]}" stroke="{th["stroke_dim"]}" stroke-width="1.1"/>')
        body.append(glow_overlay(x, y, w, h, 9, th["accent"], [i * step + 0.03], dur, sw=2.3, rise=0.03, decay=decay, peak=0.85))
        body.append(f'<text x="{F(x + 13)}" y="{F(y + 19)}" font-family="{FONT}" font-size="12" font-weight="600" fill="{th["accent"]}" letter-spacing="0.6">{esc(c["it"]["title"])}</text>')
        if c["cnt"]:
            body.append(f'<text x="{F(x + w - 13)}" y="{F(y + 19)}" text-anchor="end" font-family="{FONT}" font-size="11" fill="{th["eyebrow"]}">{esc(c["cnt"])}</text>')
        for j, ln in enumerate(c["lines"]):
            body.append(f'<text x="{F(x + 13)}" y="{F(y + 38 + 17 * j)}" font-family="{FONT}" font-size="12" fill="{th["text"]}">{esc(ln)}</text>')
        body.append("</g>\n")
    body.append(f'  <circle cx="{F(cx)}" cy="{F(cy)}" r="{core_r}" fill="{th["surface_key"]}" stroke="{th["accent"]}" stroke-width="1.7"/>\n')
    body.append(f'  <circle cx="{F(cx)}" cy="{F(cy)}" r="{core_r}" fill="none" stroke="{th["accent"]}" stroke-width="2.6" filter="url(#glow)" opacity="0.4">'
                f'<animate attributeName="opacity" values="0.3;0.7;0.3" dur="{dur / 2:g}s" repeatCount="indefinite"/></circle>\n')
    body.append(f'  <text x="{F(cx)}" y="{F(cy - 5)}" text-anchor="middle" font-family="{FONT}" font-size="13" font-weight="600" fill="{th["text_key"]}">{esc(core["label"])}</text>\n')
    if core.get("sub"):
        body.append(f'  <text x="{F(cx)}" y="{F(cy + 12)}" text-anchor="middle" font-family="{FONT}" font-size="11" fill="{th["muted"]}">{esc(core["sub"])}</text>\n')
    return part("".join(body), W, H, sb, False, "Radial diagram: a hub broadcasting to " + ", ".join(c["it"]["title"] for c in cards))


# ------------------------------------------------------------------ PHASES
def build_phases(spec, th, idp=""):
    dur = float(spec.get("dur", 8.0))
    phases = spec["phases"]
    n = len(phases)
    auto = gradient_colors(th, n)
    colors = [p.get("color") or auto[i] for i, p in enumerate(phases)]
    chip_x = spec.get("chip_x", 416)
    ph, pitch = 112, 130
    py0 = spec.get("title_zone", 84 if spec.get("title") else 24)
    chip_ws = [[round(len(c) * 7.6 + 26) for c in p.get("chips", [])] for p in phases]
    need = max((chip_x + sum(ws) + 16 * max(0, len(ws) - 1) + 40 for ws in chip_ws), default=0)
    W = max(spec.get("width", 1020), need + 50)
    H = py0 + n * pitch - (pitch - ph) + 36
    px, pw = 116, W - 116 - 50
    pitch_t = (1 - 0.03 - 0.20 - 0.12) / max(1, n - 1)
    wlen = min(0.17, pitch_t * 0.78)
    sb = [f"type=phases  loop={dur:g}s  phases={n}  window={wlen:.3f}  pitch={pitch_t:.3f}",
          "static base + animated overlays only: the first frame is already a complete diagram"]
    body = []
    cy0, cy1 = py0 + ph / 2, py0 + (n - 1) * pitch + ph / 2
    body.append(f'  <line x1="84" y1="{F(cy0)}" x2="84" y2="{F(cy1)}" stroke="{th["rail"]}" stroke-width="2"/>\n')
    for i, p in enumerate(phases):
        col, y = colors[i], py0 + i * pitch
        cy = y + ph / 2
        s = 0.03 + i * pitch_t
        kts = f"0;{T(s)};{T(s + 0.03)};{T(s + wlen - 0.04)};{T(s + wlen)};1"
        sb.append(tdesc(f"phase {i} ({p['name']})", s, s + wlen))
        body.append(f'  <circle cx="84" cy="{F(cy)}" r="5.5" fill="{th["surface"]}" stroke="{col}" stroke-width="2"/>'
                    f'<circle cx="84" cy="{F(cy)}" r="5.5" fill="{col}" filter="url(#glow)" opacity="0"><animate attributeName="opacity" dur="{dur:g}s" repeatCount="indefinite" keyTimes="{kts}" values="0;0;1;1;0;0"/></circle>'
                    f'<line x1="90" y1="{F(cy)}" x2="116" y2="{F(cy)}" stroke="{col}" stroke-width="1.4" opacity="0.45"/>\n')
        body.append(f'  <g id="{idp}phase-{i}"><rect x="{px}" y="{y}" width="{F(pw)}" height="{ph}" rx="12" fill="{th["surface"]}" stroke="{th["stroke_dim"]}" stroke-width="1.1"/>')
        body.append(f'<rect x="{px}" y="{y}" width="{F(pw)}" height="{ph}" rx="12" fill="{col}" opacity="0"><animate attributeName="opacity" dur="{dur:g}s" repeatCount="indefinite" keyTimes="{kts}" values="0;0;0.11;0.11;0;0"/></rect>')
        body.append(f'<rect x="{px}" y="{y}" width="{F(pw)}" height="{ph}" rx="12" fill="none" stroke="{col}" stroke-width="2.2" filter="url(#glow)" opacity="0"><animate attributeName="opacity" dur="{dur:g}s" repeatCount="indefinite" keyTimes="{kts}" values="0;0;0.9;0.9;0;0"/></rect>')
        body.append(f'<text x="142" y="{y + 38}" font-family="{FONT}" font-size="12" fill="{th["eyebrow"]}">{i + 1:02d}</text>'
                    f'<text x="142" y="{y + 66}" font-family="{FONT}" font-size="24" font-weight="700" fill="{col}" letter-spacing="1">{esc(p["name"])}</text>')
        if p.get("sub"):
            body.append(f'<text x="142" y="{y + 90}" font-family="{FONT}" font-size="12" fill="{th["muted"]}">{esc(p["sub"])}</text>')
        cx_ = chip_x
        for j, chip in enumerate(p.get("chips", [])):
            w = chip_ws[i][j]
            c0 = s + 0.018 + j * 0.018
            ckt = f"0;{T(c0)};{T(c0 + 0.03)};{T(c0 + 0.10)};{T(c0 + 0.14)};1"
            body.append(f'<g><rect x="{cx_}" y="{y + 39}" width="{w}" height="34" rx="8" fill="{th["surface_key"]}" stroke="{th["stroke_dim"]}" stroke-width="1.1"/>'
                        f'<rect x="{cx_}" y="{y + 39}" width="{w}" height="34" rx="8" fill="none" stroke="{col}" stroke-width="2" filter="url(#glow)" opacity="0"><animate attributeName="opacity" dur="{dur:g}s" repeatCount="indefinite" keyTimes="{ckt}" values="0;0;0.95;0.95;0;0"/></rect>'
                        f'<text x="{F(cx_ + w / 2)}" y="{y + 60}" text-anchor="middle" font-family="{FONT}" font-size="13" fill="{th["text"]}">{esc(chip)}</text></g>')
            cx_ += w + 16
        body.append("</g>\n")
    return part("".join(body), W, H, sb, False, "Phases: " + " -> ".join(p["name"] for p in phases))


# ------------------------------------------------------------------ registry + compose
def registry():
    from diagram_extra import EXTRA_BUILDERS
    from things_a import THINGS_A
    from things_b import THINGS_B
    b = {"flow": build_flow, "radial": build_radial, "phases": build_phases}
    b.update(EXTRA_BUILDERS)
    b.update(THINGS_A)
    b.update(THINGS_B)
    return b


def theme_for(spec, default_name="ember", cli_theme=None):
    name = cli_theme or spec.get("theme", default_name)
    th = dict(THEMES.get(name, THEMES["ember"]))
    th.update(spec.get("colors", {}))
    return th


def build_compose(spec, th, cli_theme=None):
    """Combine several parts (any type except compose) on one canvas and one master clock."""
    builders = registry()
    dur = float(spec.get("dur", 10))
    layout = spec.get("layout", "stack")
    gap = spec.get("gap", 28)
    margin = spec.get("margin", 24)
    top = spec.get("title_zone", 84 if spec.get("title") else margin)
    built = []
    for i, ps in enumerate(spec["parts"]):
        ps = dict(ps)
        if ps.get("type") not in builders:
            sys.exit(f"parts[{i}].type must be one of {sorted(builders)} (compose cannot be nested)")
        ps["dur"] = dur
        pth = theme_for(ps, default_name=spec.get("theme", "ember"), cli_theme=cli_theme) if ps.get("theme") else th
        p = builders[ps["type"]](ps, pth, f"p{i}-")
        a, b = ps.get("window", [0, 1])
        body = apply_window(p["body"], a, b, p.get("preroll"), p.get("dur"))
        built.append(dict(spec=ps, part=p, body=body, win=(a, b), th=pth))
    if layout == "row":
        W = 2 * margin + sum(b["part"]["W"] for b in built) + gap * (len(built) - 1)
        H = top + max(b["part"]["H"] for b in built) + margin
        x = margin
        for b in built:
            b["x"], b["y"] = x, top + (H - top - margin - b["part"]["H"]) / 2
            x += b["part"]["W"] + gap
    elif layout == "grid":
        cols = spec.get("cols", 2)
        rows = [built[i:i + cols] for i in range(0, len(built), cols)]
        colw = [max((r[c]["part"]["W"] for r in rows if c < len(r)), default=0) for c in range(cols)]
        W = 2 * margin + sum(colw) + gap * (cols - 1)
        y = top
        for r in rows:
            rh = max(b["part"]["H"] for b in r)
            x = margin
            for c, b in enumerate(r):
                b["x"], b["y"] = x + (colw[c] - b["part"]["W"]) / 2, y + (rh - b["part"]["H"]) / 2
                x += colw[c] + gap
            y += rh + gap
        H = y - gap + margin
    else:  # stack
        W = 2 * margin + max(b["part"]["W"] for b in built)
        y = top
        for b in built:
            b["x"], b["y"] = (W - b["part"]["W"]) / 2, y
            y += b["part"]["H"] + gap
        H = y - gap + margin
    sb = [f"type=compose layout={layout} loop={dur:g}s parts={len(built)}"]
    out = []
    for i, b in enumerate(built):
        a, c = b["win"]
        sb.append(f"part {i}: {b['spec']['type']} window {a:.2f}..{c:.2f} at ({b['x']:.0f},{b['y']:.0f})")
        sb += ["  " + ln for ln in map_sb(b["part"]["sb"], a, c)]
        eb = eyebrow(b["spec"], b["th"])
        out.append(f'  <g id="p{i}-group" transform="translate({F(b["x"])} {F(b["y"])})">{eb}\n{b["body"]}  </g>\n')
    desc = "Composite diagram: " + ", ".join(b["spec"]["type"] for b in built)
    return part("".join(out), W, H, sb, any(b["part"]["arrows"] for b in built), desc)


def build(spec, th, cli_theme=None):
    kind = spec.get("type")
    if kind == "compose":
        return build_compose(spec, th, cli_theme)
    b = registry()
    if kind not in b:
        sys.exit(f"spec.type must be one of {sorted(list(b) + ['compose'])}")
    return b[kind](spec, th)


def assemble(spec, th, p):
    W, H = p["W"], p["H"]
    out = [header(W, H, spec, p["sb"], p["desc"]),
           "  " + common_defs(th, p["arrows"], spec.get("aurora_blur", 0)) + "\n",
           f'  <rect width="{F(W)}" height="{F(H)}" rx="16" fill="{th["bg"]}"/>\n']
    if spec.get("aurora", True):
        out.append("  " + aurora(W, H, th, spec.get("aurora_blur", 0)) + "\n")
    out.append("  " + eyebrow(spec, th) + "\n")
    body = p["body"]
    if p.get("preroll") is not None and p.get("dur"):
        # Standalone part: the window is the whole loop, so the pre-roll offset is
        # just -preroll*dur. build_compose does the windowed equivalent per part.
        body = apply_window(body, 0.0, 1.0, p["preroll"], p["dur"])
    out.append(body)
    out.append("</svg>\n")
    return "".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("out")
    ap.add_argument("--theme", default=None)
    ap.add_argument("--pair", nargs=2, metavar=("LIGHT", "DARK"), default=None,
                    help="also write <stem>-light.svg and <stem>-dark.svg, and print the <picture> snippet")
    ap.add_argument("--static-twin", action="store_true",
                    help="also write <stem>-static.svg, the animation-free twin for prefers-reduced-motion")
    a = ap.parse_args()
    spec = json.load(open(a.spec, encoding="utf-8"))

    if a.pair:
        light_name, dark_name = a.pair
        for nm in a.pair:
            if nm not in THEMES:
                sys.exit(f"unknown theme '{nm}'; choose from {sorted(THEMES)}")
        if light_name in DARK_THEMES:
            sys.exit(f"'{light_name}' is a dark theme, so it cannot be the light half of a pair "
                     f"(an <img> SVG cannot see the page theme, so the two files must differ in polarity)")
        if dark_name not in DARK_THEMES:
            sys.exit(f"'{dark_name}' is a light theme, so it cannot be the dark half of a pair")
        stem = a.out[:-4] if a.out.endswith(".svg") else a.out
        base = os.path.basename(stem)
        parent = os.path.dirname(stem)
        written = []
        for name, suffix in ((light_name, "-light"), (dark_name, "-dark")):
            th = theme_for(spec, cli_theme=name)
            p = build(spec, th, name)
            svg = assemble(spec, th, p)
            dest = os.path.join(parent, base + suffix + ".svg")
            open(dest, "w", encoding="utf-8").write(svg)
            written.append(dest)
            print(f"wrote {dest} ({max(1, len(svg) // 1024)} KB)  theme={name}")
        alt = spec.get("title") or spec.get("aria") or base
        print("\nEmbed with (GitHub supports <picture> in Markdown since Aug 2022):\n")
        print(PICTURE_TMPL.format(dark=os.path.basename(written[1]), light=os.path.basename(written[0]),
                                  alt=str(alt).replace('"', "'")[:80]))
        print("\nNote: an <img> SVG runs in secure animated mode and cannot read the page's colour")
        print("scheme, which is why this is two files. Both loops are identical in length so the")
        print("transition on theme switch is not a jump.")
        return

    th = theme_for(spec, cli_theme=a.theme)
    p = build(spec, th, a.theme)
    svg = assemble(spec, th, p)
    open(a.out, "w", encoding="utf-8").write(svg)
    print("\n".join(p["sb"]))
    print(f"\nwrote {a.out} ({max(1, len(svg) // 1024)} KB). Next: python run_pipeline.py {a.out}")

    if a.static_twin:
        stem, ext = os.path.splitext(a.out)
        twin_path = stem + "-static" + (ext or ".svg")
        rc = static_twin_main(["static_twin.py", a.out, twin_path, "--quiet"])
        if rc:
            print("\nNo static twin written. CSS cannot switch SMIL off, so a reduced-motion")
            print("fallback needs a separate file; see references/static-first.md.", file=sys.stderr)
            sys.exit(rc)


if __name__ == "__main__":
    main()
