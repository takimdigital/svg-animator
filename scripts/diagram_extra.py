"""Extra diagram types for gen_diagram.py: timeline, network, layers, cycle, sequence, terminal, cards, chart, banner.

Every builder follows the contract in diagram_common.py:  build(spec, th, idp="") -> Part
All of them are STATIC-FIRST: the first frame is already a complete graphic; motion is overlay (or, for
terminal/chart, an animation whose base attribute is the finished state).
"""
import math
import random
import sys

from diagram_common import (FONT, SANS, F, T, card_w, esc, glow_dot, glow_overlay, lerp_hex, make_slots, node_card,
                            part, rail, relay_traveller, tdesc)


def ray_exit(ox, oy, dx, dy, w, h):
    """Distance t at which the ray (ox,oy)+t*(dx,dy) leaves a w*h rect centred on the origin."""
    ts = []
    if dx > 1e-9:
        ts.append((w / 2 - ox) / dx)
    elif dx < -1e-9:
        ts.append((-w / 2 - ox) / dx)
    if dy > 1e-9:
        ts.append((h / 2 - oy) / dy)
    elif dy < -1e-9:
        ts.append((-h / 2 - oy) / dy)
    return min(ts)


def _tz(spec, with_title=84, without=28):
    return spec.get("title_zone", with_title if spec.get("title") else without)


# ------------------------------------------------------------------ TIMELINE
def build_timeline(spec, th, idp=""):
    dur = float(spec.get("dur", 8))
    items = spec["items"]
    n = len(items)
    if n < 2:
        sys.exit("timeline needs at least 2 items")
    cw, ch, stem, r = spec.get("card_w", 168), 68, 34, 7
    sx = spec.get("spacing", cw + 28)
    margin = 48
    tz = _tz(spec)
    W = 2 * margin + (n - 1) * sx + cw
    spine_y = tz + ch + stem + 16
    H = spine_y + stem + ch + 36
    xs = [margin + cw / 2 + i * sx for i in range(n)]
    slots, _ = make_slots(n - 1)
    arr = [[slots[0][0]]] + [[slots[i - 1][1]] for i in range(1, n)]
    sb = [f"type=timeline  items={n}  hops={n - 1}"] + [tdesc(f"segment {i}", a, b) for i, (a, b) in enumerate(slots)]
    body = []
    for i in range(n - 1):
        body.append("  " + rail(f"M{F(xs[i] + r)},{F(spine_y)} L{F(xs[i + 1] - r)},{F(spine_y)}", th, sw=2) + "\n")
    for i, it in enumerate(items):
        up = (i % 2 == 0) if spec.get("alternate", True) else False
        cy_card = spine_y - stem - ch if up else spine_y + stem
        d = (f"M{F(xs[i])},{F(spine_y - r)} L{F(xs[i])},{F(cy_card + ch)}" if up else f"M{F(xs[i])},{F(spine_y + r)} L{F(xs[i])},{F(cy_card)}")
        body.append("  " + rail(d, th, color=th["stroke_dim"], sw=1.5) + "\n")
        body.append(f'  <circle cx="{F(xs[i])}" cy="{F(spine_y)}" r="{r}" fill="{th["surface"]}" stroke="{th["accent"]}" stroke-width="2"/>')
        body.append(glow_dot(xs[i], spine_y, r, th["accent"], arr[i], dur) + "\n")
        body.append("  " + node_card(th, idp + "ms-", f"{i}", xs[i] - cw / 2, cy_card, cw, ch, it["label"], it.get("sub", ""),
                                    it.get("key", False), arr[i], dur, lsz=15, tag=it.get("tag")) + "\n")
    for i, (a, b) in enumerate(slots):
        body.append("  " + relay_traveller(f"M{F(xs[i] + r)},{F(spine_y)} L{F(xs[i + 1] - r)},{F(spine_y)}", a, b, th["accent"], th["dot"], dur) + "\n")
    return part("".join(body), W, H, sb, False, "Timeline: " + " -> ".join(i["label"] for i in items))


# ------------------------------------------------------------------ NETWORK
def build_network(spec, th, idp=""):
    dur = float(spec.get("dur", 8))
    nodes_in, edges = spec["nodes"], [tuple(e) for e in spec["edges"]]
    arrows = spec.get("arrows", True)
    g = 4 if arrows else 0
    N = len(nodes_in)
    nodes = {}
    for nd in nodes_in:
        sub = nd.get("sub", "")
        nodes[nd["id"]] = dict(id=nd["id"], label=nd["label"], sub=sub, key=nd.get("key", False),
                               w=card_w(nd["label"], sub, 16, minw=96), h=62 if sub else 46, lsz=16, x=nd.get("x"), y=nd.get("y"))
    maxw, maxh = max(n["w"] for n in nodes.values()), max(n["h"] for n in nodes.values())
    layout = spec.get("layout", "circle")
    ids = [nd["id"] for nd in nodes_in]
    if all(nodes[i]["x"] is not None and nodes[i]["y"] is not None for i in ids):
        for i in ids:
            nodes[i]["cx"], nodes[i]["cy"] = nodes[i]["x"], nodes[i]["y"]
    elif layout == "grid":
        cols = spec.get("cols", math.ceil(math.sqrt(N)))
        for k, i in enumerate(ids):
            nodes[i]["cx"], nodes[i]["cy"] = (k % cols) * (maxw + 90), (k // cols) * (maxh + 80)
    else:
        R = spec.get("radius", max(170, (maxw + 50) / (2 * math.sin(math.pi / max(N, 3))), 26 * N))
        for k, i in enumerate(ids):
            a = math.radians(-90 + 360 * k / N)
            nodes[i]["cx"], nodes[i]["cy"] = R * math.cos(a), R * math.sin(a)
    minx = min(n["cx"] - n["w"] / 2 for n in nodes.values())
    miny = min(n["cy"] - n["h"] / 2 for n in nodes.values())
    maxx = max(n["cx"] + n["w"] / 2 for n in nodes.values())
    maxy = max(n["cy"] + n["h"] / 2 for n in nodes.values())
    tz, margin = _tz(spec), 56
    ox, oy = margin - minx, tz - miny
    W, H = (maxx - minx) + 2 * margin, (maxy - miny) + tz + margin
    for n in nodes.values():
        n["cx"] += ox
        n["cy"] += oy
        n["x"], n["y"] = n["cx"] - n["w"] / 2, n["cy"] - n["h"] / 2

    # BFS depth from start nodes
    start = spec.get("start", [ids[0]])
    depth = {s: 0 for s in start}
    queue = list(start)
    while queue:
        u = queue.pop(0)
        for a, b in edges:
            if a == u and b not in depth:
                depth[b] = depth[u] + 1
                queue.append(b)
    unreachable = [i for i in ids if i not in depth]
    if unreachable:
        print("WARNING: nodes not reachable from start:", unreachable, file=sys.stderr)
        for i in unreachable:
            depth[i] = max(depth.values()) + 1
    pairs = set(edges)
    geo, warns = [], []
    for a_id, b_id in edges:
        A, B = nodes[a_id], nodes[b_id]
        dx, dy = B["cx"] - A["cx"], B["cy"] - A["cy"]
        L = math.hypot(dx, dy)
        dx, dy = dx / L, dy / L
        off = 0.0
        if (b_id, a_id) in pairs:
            off = 7 if ids.index(a_id) < ids.index(b_id) else -7
        ox_, oy_ = -dy * off, dx * off
        ta = ray_exit(ox_, oy_, dx, dy, A["w"], A["h"])
        tb = ray_exit(ox_, oy_, -dx, -dy, B["w"], B["h"])
        p1 = (A["cx"] + ox_ + dx * ta, A["cy"] + oy_ + dy * ta)
        p2 = (B["cx"] + ox_ - dx * tb - dx * g, B["cy"] + oy_ - dy * tb - dy * g)
        d = f"M{F(p1[0])},{F(p1[1])} L{F(p2[0])},{F(p2[1])}"
        for nid, nn in nodes.items():
            if nid in (a_id, b_id):
                continue
            for k in range(1, 40):
                t = k / 40
                px, py = p1[0] + (p2[0] - p1[0]) * t, p1[1] + (p2[1] - p1[1]) * t
                if abs(px - nn["cx"]) < nn["w"] / 2 - 2 and abs(py - nn["cy"]) < nn["h"] / 2 - 2:
                    warns.append(f"edge {a_id}->{b_id} crosses node {nid}: reorder nodes or give explicit x,y")
                    break
        geo.append(dict(d=d, slot=depth[a_id], src=a_id, dst=b_id))
    nslots = max(g_["slot"] for g_ in geo) + 1
    slots, _ = make_slots(nslots)
    arrivals = {i: [] for i in ids}
    for s in start:
        arrivals[s].append(slots[0][0])
    for e in geo:
        arrivals[e["dst"]].append(slots[e["slot"]][1])
    sb = [f"type=network  nodes={N}  edges={len(edges)}  waves={nslots}  start={start}"]
    sb += [tdesc(f"wave {i}", a, b) for i, (a, b) in enumerate(slots)]
    for w_ in sorted(set(warns)):
        sb.append("WARNING: " + w_)
        print("WARNING:", w_, file=sys.stderr)
    body = ["  " + rail(e["d"], th, arrows=arrows) + "\n" for e in geo]
    for i in ids:
        n = nodes[i]
        body.append("  " + node_card(th, idp + "n-", i, n["x"], n["y"], n["w"], n["h"], n["label"], n["sub"],
                                    n["key"] or i in start, arrivals[i], dur, lsz=16) + "\n")
    for e in geo:
        a, b = slots[e["slot"]]
        body.append("  " + relay_traveller(e["d"], a, b, th["accent"], th["dot"], dur) + "\n")
    return part("".join(body), W, H, sb, arrows, f"Network of {N} nodes: " + ", ".join(nodes[i]["label"] for i in ids))


# ------------------------------------------------------------------ LAYERS
def build_layers(spec, th, idp=""):
    dur = float(spec.get("dur", 10))
    layers = spec["layers"]
    L = len(layers)
    if L < 2:
        sys.exit("layers needs at least 2 layers")
    arrows = spec.get("arrows", True)
    g = 4 if arrows else 0
    lh, gapv, px = 88, spec.get("gap_y", 44), 60
    chip_off = 300
    tz = _tz(spec)
    cws = [[round(len(c) * 7.6 + 26) for c in l.get("chips", [])] for l in layers]
    need = max((px + chip_off + sum(w) + 14 * max(0, len(w) - 1) + 230 for w in cws), default=0)
    W = max(spec.get("width", 960), need)
    pw = W - 2 * px
    lane_d, lane_u = px + pw - 130, px + pw - 70
    ys = [tz + i * (lh + gapv) for i in range(L)]
    H = ys[-1] + lh + 40
    slots, _ = make_slots(2 * (L - 1))
    arr = [[] for _ in range(L)]
    arr[0].append(slots[0][0])
    for k in range(L - 1):
        arr[k + 1].append(slots[k][1])
    for u in range(L - 1):
        arr[L - 2 - u].append(slots[L - 1 + u][1])
    sb = [f"type=layers  layers={L}  hops={2 * (L - 1)} (down then up)"]
    sb += [tdesc(("request " if i < L - 1 else "response ") + str(i), a, b) for i, (a, b) in enumerate(slots)]
    body = []
    rails = []
    for k in range(L - 1):
        rails.append((f"M{F(lane_d)},{F(ys[k] + lh)} L{F(lane_d)},{F(ys[k + 1] - g)}", k, False))
    for u in range(L - 1):
        k = L - 2 - u
        rails.append((f"M{F(lane_u)},{F(ys[k + 1])} L{F(lane_u)},{F(ys[k] + lh + g)}", L - 1 + u, True))
    for d, _, loop in rails:
        body.append("  " + rail(d, th, loop=loop, arrows=arrows) + "\n")
    for i, l in enumerate(layers):
        y = ys[i]
        body.append(f'  <g id="{idp}layer-{i}"><rect x="{px}" y="{F(y)}" width="{F(pw)}" height="{lh}" rx="12" fill="{th["surface_key"] if l.get("key") else th["surface"]}" stroke="{th["accent"] if l.get("key") else th["stroke_dim"]}" stroke-width="{1.7 if l.get("key") else 1.1}"/>')
        body.append(glow_overlay(px, y, pw, lh, 12, th["accent"], arr[i], dur, rise=0.04, decay=0.09))
        body.append(f'<text x="{px + 24}" y="{F(y + 38)}" font-family="{FONT}" font-size="15" font-weight="700" fill="{th["accent"]}" letter-spacing="1">{esc(l["name"])}</text>')
        if l.get("sub"):
            body.append(f'<text x="{px + 24}" y="{F(y + 60)}" font-family="{FONT}" font-size="12" fill="{th["muted"]}">{esc(l["sub"])}</text>')
        cx_ = px + chip_off
        for j, c in enumerate(l.get("chips", [])):
            w = cws[i][j]
            body.append(f'<g><rect x="{cx_}" y="{F(y + 27)}" width="{w}" height="34" rx="8" fill="{th["bg"]}" stroke="{th["stroke_dim"]}" stroke-width="1.1"/>'
                        + glow_overlay(cx_, y + 27, w, 34, 8, th["accent"], [a + 0.02 * j for a in arr[i]], dur, sw=2, rise=0.03, decay=0.07)
                        + f'<text x="{F(cx_ + w / 2)}" y="{F(y + 49)}" text-anchor="middle" font-family="{FONT}" font-size="13" fill="{th["text"]}">{esc(c)}</text></g>')
            cx_ += w + 14
        body.append("</g>\n")
    body.append(f'  <text x="{W - px}" y="{max(18, tz - 14)}" text-anchor="end" font-family="{FONT}" font-size="11" fill="{th["muted"]}">request \u2193   response \u2191</text>\n')
    for (d, s, loop) in rails:
        a, b = slots[s]
        body.append("  " + relay_traveller(d, a, b, th["loop"] if loop else th["accent"], th["dot"], dur) + "\n")
    return part("".join(body), W, H, sb, arrows, "Layered architecture: " + " / ".join(l["name"] for l in layers))


# ------------------------------------------------------------------ CYCLE
def build_cycle(spec, th, idp=""):
    dur = float(spec.get("dur", 8))
    steps = spec["steps"]
    N = len(steps)
    if N < 3:
        sys.exit("cycle needs at least 3 steps")
    arrows = spec.get("arrows", True)
    g = 4 if arrows else 0
    cards = []
    for s in steps:
        sub = s.get("sub", "")
        cards.append(dict(s=s, w=card_w(s["label"], sub, 16, minw=110), h=62 if sub else 46, sub=sub))
    maxw = max(c["w"] for c in cards)
    R = spec.get("radius", max(170, (maxw + 44) / (2 * math.sin(math.pi / N)), 36 * N * 0.7))
    angs = [math.radians(-90 + 360 * i / N) for i in range(N)]
    for c, a in zip(cards, angs):
        c["cx"], c["cy"] = R * math.cos(a), R * math.sin(a)

    def inside(p, c, m=0.0):
        return abs(p[0] - c["cx"]) < c["w"] / 2 + m and abs(p[1] - c["cy"]) < c["h"] / 2 + m

    arcs = []
    for i in range(N):
        j = (i + 1) % N
        a_i, a_j = angs[i], angs[j] + (2 * math.pi if j == 0 else 0)
        th_s = a_i
        while inside((R * math.cos(th_s), R * math.sin(th_s)), cards[i]):
            th_s += 0.002
        th_e = a_j
        while inside((R * math.cos(th_e), R * math.sin(th_e)), cards[j]):
            th_e -= 0.002
        th_e -= g / R
        if th_e - th_s < 0.05:
            sys.exit("cycle: cards too close; increase radius or shorten labels")
        arcs.append((th_s, th_e))
    minx = min(c["cx"] - c["w"] / 2 for c in cards)
    maxx = max(c["cx"] + c["w"] / 2 for c in cards)
    miny = min(c["cy"] - c["h"] / 2 for c in cards)
    maxy = max(c["cy"] + c["h"] / 2 for c in cards)
    tz, margin = _tz(spec), 56
    ox, oy = margin - minx, tz - miny
    W, H = (maxx - minx) + 2 * margin, (maxy - miny) + tz + margin
    slots, _ = make_slots(N)
    arr = [[] for _ in range(N)]
    arr[0].append(slots[0][0])
    for i in range(N):
        arr[(i + 1) % N].append(slots[i][1])
    sb = [f"type=cycle  steps={N}  radius={R:.0f}"] + [tdesc(f"hop {i}->{(i + 1) % N}", a, b) for i, (a, b) in enumerate(slots)]
    body, paths = [], []
    for (ts_, te_) in arcs:
        p1 = (ox + R * math.cos(ts_), oy + R * math.sin(ts_))
        p2 = (ox + R * math.cos(te_), oy + R * math.sin(te_))
        d = f"M{F(p1[0])},{F(p1[1])} A{F(R)},{F(R)} 0 0 1 {F(p2[0])},{F(p2[1])}"
        paths.append(d)
        body.append("  " + rail(d, th, arrows=arrows, sw=1.8) + "\n")
    if spec.get("deco", True):
        body.append(f'  <circle cx="{F(ox)}" cy="{F(oy)}" r="{F(R * 0.5)}" fill="none" stroke="{th["rail"]}" stroke-width="1.2" stroke-dasharray="3 9">'
                    f'<animateTransform attributeName="transform" type="rotate" values="0 {F(ox)} {F(oy)};360 {F(ox)} {F(oy)}" dur="60s" repeatCount="indefinite"/></circle>\n')
    c0 = spec.get("center", {})
    if c0.get("label"):
        body.append(f'  <text x="{F(ox)}" y="{F(oy - 2)}" text-anchor="middle" font-family="{FONT}" font-size="22" font-weight="700" fill="{th["text_key"]}">{esc(c0["label"])}</text>\n')
        if c0.get("sub"):
            body.append(f'  <text x="{F(ox)}" y="{F(oy + 20)}" text-anchor="middle" font-family="{FONT}" font-size="12" fill="{th["muted"]}">{esc(c0["sub"])}</text>\n')
    for i, c in enumerate(cards):
        body.append("  " + node_card(th, idp + "s-", str(i), ox + c["cx"] - c["w"] / 2, oy + c["cy"] - c["h"] / 2, c["w"], c["h"],
                                    c["s"]["label"], c["sub"], c["s"].get("key", False), arr[i], dur, lsz=16) + "\n")
    for d, (a, b) in zip(paths, slots):
        body.append("  " + relay_traveller(d, a, b, th["accent"], th["dot"], dur) + "\n")
    return part("".join(body), W, H, sb, arrows, "Cycle: " + " -> ".join(s["label"] for s in steps) + " -> back")


# ------------------------------------------------------------------ SEQUENCE
def build_sequence(spec, th, idp=""):
    dur = float(spec.get("dur", 10))
    actors, msgs = spec["actors"], spec["messages"]
    n, m = len(actors), len(msgs)
    aw = max(card_w(a["label"], a.get("sub", ""), 16, minw=120) for a in actors)
    ah = 56
    spacing = spec.get("spacing", max(aw + 70, 200))
    margin, tz = 56, _tz(spec)
    idx = {a["id"]: i for i, a in enumerate(actors)}
    xs = [margin + aw / 2 + i * spacing for i in range(n)]
    W = 2 * margin + (n - 1) * spacing + aw
    y0 = tz + ah + 46
    pitch = spec.get("pitch", 54)
    ys = [y0 + k * pitch for k in range(m)]
    H = ys[-1] + 64
    slots, _ = make_slots(m, dwell=0.02, tail=0.08)
    arr = {a["id"]: [] for a in actors}
    sb = [f"type=sequence  actors={n}  messages={m}"]
    body = []
    for a in actors:
        x = xs[idx[a["id"]]]
        body.append(f'  <path class="life" d="M{F(x)},{F(tz + ah)} L{F(x)},{F(H - 30)}" fill="none" stroke="{th["rail"]}" stroke-width="1.3" stroke-dasharray="4 6"/>\n')
    paths = []
    for k, mg in enumerate(msgs):
        if mg["from"] == mg["to"]:
            sys.exit("sequence: self-messages are not supported (from == to)")
        fi, ti = idx[mg["from"]], idx[mg["to"]]
        sgn = 1 if xs[ti] > xs[fi] else -1
        x1, x2 = xs[fi], xs[ti] - sgn * 4
        ret = mg.get("kind", "call") == "return"
        d = f"M{F(x1)},{F(ys[k])} L{F(x2)},{F(ys[k])}"
        paths.append((d, ret))
        if k == 0:
            arr[mg["from"]].append(slots[0][0])
        arr[mg["to"]].append(slots[k][1])
        dash = ' stroke-dasharray="5 6"' if ret else ""
        body.append(f'  <path class="msg" d="{d}" fill="none" stroke="{th["loop"] if ret else th["rail"]}" stroke-width="1.6"{dash} marker-end="url(#arrow)"/>\n')
        body.append(f'  <text x="{F((xs[fi] + xs[ti]) / 2)}" y="{F(ys[k] - 9)}" text-anchor="middle" font-family="{FONT}" font-size="12" fill="{th["muted"] if ret else th["text"]}">{esc(mg["label"])}</text>\n')
        sb.append(tdesc(f"msg {k} {mg['from']}->{mg['to']}", *slots[k]))
        body.append(f'  <circle cx="{F(xs[ti])}" cy="{F(ys[k])}" r="3.5" fill="{th["stroke"]}"/>')
        body.append(glow_dot(xs[ti], ys[k], 3.5, th["accent"], [slots[k][1]], dur) + "\n")
    for a in actors:
        i = idx[a["id"]]
        body.append("  " + node_card(th, idp + "a-", a["id"], xs[i] - aw / 2, tz, aw, ah, a["label"], a.get("sub", ""),
                                    a.get("key", False), arr[a["id"]], dur, lsz=16) + "\n")
    for (d, ret), (a, b) in zip(paths, slots):
        body.append("  " + relay_traveller(d, a, b, th["loop"] if ret else th["accent"], th["dot"], dur) + "\n")
    return part("".join(body), W, H, sb, True, "Sequence diagram: " + ", ".join(a["label"] for a in actors))


# ------------------------------------------------------------------ TERMINAL
def build_terminal(spec, th, idp=""):
    dur = float(spec.get("dur", 10))
    lines = spec["lines"]
    fs, pitch, bar, padx = 14, 26, 38, 22
    cw = fs * 0.6
    maxc = max(len(l["text"]) + (2 if l.get("kind", "out") == "cmd" else 0) for l in lines)
    W = spec.get("width", max(640, math.ceil(maxc * cw + 2 * padx + 70)))
    tz = _tz(spec, 72, 20)
    wx, wy, ww = 20, tz, W - 40
    wh = bar + len(lines) * pitch + 30
    H = wy + wh + 20
    # schedule (fractions): natural typing speed, pauses stretched so the session fills ~0.80 of the loop
    cps = spec.get("cps", 22)
    tc = 1 / (cps * dur)
    n_lines = len(lines)

    def layout(pad, f=1.0):
        t, plan = 0.04, []
        for l in lines:
            if l.get("kind", "out") == "cmd":
                n = len(l["text"])
                plan.append((t, t + n * tc * f))
                t += n * tc * f + (0.03 + pad) * f
            else:
                plan.append((t, t + 0.02 * f))
                t += (0.045 + pad) * f
        return t, plan

    t, plan = layout(0.0)
    if t < 0.80:
        pad = (0.80 - t) / n_lines
        t, plan = layout(pad)
    elif t > 0.86:
        f = (0.86 - 0.04) / (t - 0.04)
        t, plan = layout(0.0, f)
    colors = {"cmd": th["text_key"], "out": th["muted"], "ok": th["accent3"], "err": "#FF7B72", "dim": th["eyebrow"]}
    sb = [f"type=terminal  lines={len(lines)}  fit_end={t:.3f}  cps={cps}", "static-first: all text is drawn; cover rects (window colour) hide the not-yet-typed part while the animation runs"]
    body = [f'  <rect x="{wx}" y="{wy}" width="{ww}" height="{wh}" rx="12" fill="{th["surface"]}" stroke="{th["stroke_dim"]}" stroke-width="1.1"/>\n',
            f'  <path d="M{wx},{wy + 12} a12,12 0 0 1 12,-12 H{wx + ww - 12} a12,12 0 0 1 12,12 V{wy + bar} H{wx} Z" fill="{th["surface_key"]}"/>\n']
    for k, col in enumerate(("#FF5F56", "#FFBD2E", "#27C93F")):
        body.append(f'  <circle cx="{wx + 22 + k * 20}" cy="{wy + bar / 2}" r="5" fill="{col}"/>\n')
    if spec.get("window_title"):
        body.append(f'  <text x="{wx + ww / 2}" y="{wy + bar / 2 + 4}" text-anchor="middle" font-family="{FONT}" font-size="12" fill="{th["muted"]}">{esc(spec["window_title"])}</text>\n')
    body.append(f'  <g id="{idp}term"><animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.90;0.96;1" dur="{dur:g}s" repeatCount="indefinite"/>\n')
    for k, l in enumerate(lines):
        kind = l.get("kind", "out")
        y = wy + bar + 24 + k * pitch
        x_t = wx + padx
        col = colors.get(kind, th["text"])
        if kind == "cmd":
            n = len(l["text"])
            tx0 = x_t + 2 * cw
            body.append(f'    <text x="{F(x_t)}" y="{F(y)}" font-family="{FONT}" font-size="{fs}" fill="{th["accent"]}" xml:space="preserve">$ </text>'
                        f'<text x="{F(tx0)}" y="{F(y)}" font-family="{FONT}" font-size="{fs}" fill="{col}" xml:space="preserve">{esc(l["text"])}</text>\n')
            ts, te = plan[k]
            kts = [0.0] + [ts + j * (te - ts) / n for j in range(1, n + 1)]
            kt = ";".join(T(v) for v in kts)
            xs_ = ";".join(F(tx0 + j * cw) for j in range(n + 1))
            ws_ = ";".join(F(max(0.0, (n - j) * cw + (4 if j < n else 0))) for j in range(n + 1))
            region = n * cw + 4
            body.append(f'    <rect x="{F(tx0 + n * cw)}" y="{F(y - fs)}" width="0" height="{fs + 6}" fill="{th["surface"]}">'
                        f'<animate attributeName="x" calcMode="discrete" keyTimes="{kt}" values="{xs_}" dur="{dur:g}s" repeatCount="indefinite"/>'
                        f'<animate attributeName="width" calcMode="discrete" keyTimes="{kt}" values="{ws_}" dur="{dur:g}s" repeatCount="indefinite"/></rect>\n')
            ckt = f"0;{T(ts - 0.005)};{T(ts)};{T(te + 0.02)};{T(te + 0.03)};1"
            body.append(f'    <rect x="{F(tx0)}" y="{F(y - fs + 1)}" width="8" height="{fs + 2}" fill="{th["accent"]}" opacity="0">'
                        f'<animate attributeName="x" calcMode="discrete" keyTimes="{kt}" values="{xs_}" dur="{dur:g}s" repeatCount="indefinite"/>'
                        f'<animate attributeName="opacity" keyTimes="{ckt}" values="0;0;1;1;0;0" dur="{dur:g}s" repeatCount="indefinite"/></rect>\n')
            sb.append(tdesc(f"type line {k}", ts, te))
        else:
            ts, te = plan[k]
            okt = f"0;{T(ts)};{T(te)};1"
            body.append(f'    <text x="{F(x_t)}" y="{F(y)}" font-family="{FONT}" font-size="{fs}" fill="{col}" xml:space="preserve">{esc(l["text"])}'
                        f'<animate attributeName="opacity" keyTimes="{okt}" values="0;0;1;1" dur="{dur:g}s" repeatCount="indefinite"/></text>\n')
            sb.append(tdesc(f"print line {k}", ts, te))
    body.append("  </g>\n")
    return part("".join(body), W, H, sb, False, "Terminal session: " + "; ".join(l["text"] for l in lines if l.get("kind") == "cmd"))


# ------------------------------------------------------------------ CARDS
def build_cards(spec, th, idp=""):
    dur = float(spec.get("dur", 6))
    items = spec["items"]
    n = len(items)
    cols = spec.get("cols", min(n, 4))
    tw, tih, gap, margin = spec.get("tile_w", 220), spec.get("tile_h", 118), 24, 40
    rows = math.ceil(n / cols)
    tz = _tz(spec)
    W = 2 * margin + cols * tw + (cols - 1) * gap
    H = tz + rows * tih + (rows - 1) * gap + margin
    step = min(0.1, 0.8 / n)
    sb = [f"type=cards  tiles={n}  cols={cols}  wave step={step:.3f}"]
    body = []
    for i, it in enumerate(items):
        x, y = margin + (i % cols) * (tw + gap), tz + (i // cols) * (tih + gap)
        a = 0.04 + i * step
        key = it.get("key", False)
        val = str(it["value"])
        vs = 34 if len(val) <= 8 else max(18, 34 * 8 / len(val))
        body.append(f'  <g id="{idp}tile-{i}"><rect x="{F(x)}" y="{F(y)}" width="{tw}" height="{tih}" rx="12" fill="{th["surface_key"] if key else th["surface"]}" stroke="{th["accent"] if key else th["stroke_dim"]}" stroke-width="{1.7 if key else 1.1}"/>')
        body.append(f'<rect x="{F(x + 20)}" y="{F(y + 18)}" width="28" height="3" rx="1.5" fill="{th["accent"]}"/>')
        body.append(glow_overlay(x, y, tw, tih, 12, th["accent"], [a + 0.03], dur, rise=0.03, decay=0.12))
        body.append(f'<text x="{F(x + 20)}" y="{F(y + 66)}" font-family="{FONT}" font-size="{vs:.0f}" font-weight="700" fill="{th["text_key"] if key else th["accent3"]}">{esc(val)}</text>')
        body.append(f'<text x="{F(x + 20)}" y="{F(y + 88)}" font-family="{FONT}" font-size="13" fill="{th["text"]}">{esc(it["label"])}</text>')
        if it.get("sub"):
            body.append(f'<text x="{F(x + 20)}" y="{F(y + 106)}" font-family="{FONT}" font-size="11" fill="{th["muted"]}">{esc(it["sub"])}</text>')
        body.append("</g>\n")
        sb.append(tdesc(f"tile {i}", a, a + 0.15))
    return part("".join(body), W, H, sb, False, "Stat tiles: " + ", ".join(f'{i["value"]} {i["label"]}' for i in items))


# ------------------------------------------------------------------ CHART
def _nice_max(v):
    if v <= 0:
        return 1
    e = 10 ** math.floor(math.log10(v))
    for m in (1, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10):
        if v <= m * e:
            return m * e
    return 10 * e


def build_chart(spec, th, idp=""):
    dur = float(spec.get("dur", 8))
    data = spec["data"]
    n = len(data)
    kind = spec.get("kind", "bar")
    W, Hc = spec.get("width", 860), spec.get("height", 340)
    tz = _tz(spec)
    left, right, bottom = 70, 40, 64
    top = tz + 16
    H = tz + Hc
    plot_w, plot_h = W - left - right, H - top - bottom
    vmax = max(d["value"] for d in data)
    ymax = _nice_max(vmax * 1.1)
    base = top + plot_h
    unit = spec.get("unit", "")
    hi = spec.get("highlight", "max")
    hi_i = max(range(n), key=lambda i: data[i]["value"]) if hi == "max" else (hi if isinstance(hi, int) else None)
    sb = [f"type=chart kind={kind}  points={n}  ymax={ymax:g}"]
    body = []
    for k in range(5):
        v = ymax * k / 4
        y = base - plot_h * k / 4
        body.append(f'  <line x1="{left}" y1="{F(y)}" x2="{W - right}" y2="{F(y)}" stroke="{th["rail"]}" stroke-width="1" opacity="{0.9 if k == 0 else 0.45}"/>'
                    f'<text x="{left - 10}" y="{F(y + 4)}" text-anchor="end" font-family="{FONT}" font-size="11" fill="{th["muted"]}">{v:g}{unit if k == 4 else ""}</text>\n')
    slot = plot_w / n
    pts = []
    for i, d in enumerate(data):
        cx = left + slot * (i + 0.5)
        h = d["value"] / ymax * plot_h
        pts.append((cx, base - h, h, d))
        body.append(f'  <text x="{F(cx)}" y="{F(base + 22)}" text-anchor="middle" font-family="{FONT}" font-size="12" fill="{th["muted"]}">{esc(d["label"])}</text>\n')
    if kind == "line":
        d_path = "M" + " L".join(f"{F(x)},{F(y)}" for x, y, _, _ in pts)
        area = d_path + f" L{F(pts[-1][0])},{F(base)} L{F(pts[0][0])},{F(base)} Z"
        cid = f"{idp}clip"
        body.append(f'  <clipPath id="{cid}"><rect x="{left}" y="{F(top)}" width="{F(plot_w)}" height="{F(plot_h + 2)}"><animate attributeName="width" values="0;0;{F(plot_w)};{F(plot_w)};0" keyTimes="0;0.02;0.38;0.9;1" dur="{dur:g}s" repeatCount="indefinite"/></rect></clipPath>\n')
        body.append(f'  <path d="{area}" fill="{th["accent"]}" opacity="0.13" clip-path="url(#{cid})"/>\n')
        body.append(f'  <path d="{d_path}" pathLength="1" fill="none" stroke="{th["accent"]}" stroke-width="3" stroke-linejoin="round" stroke-linecap="butt">'
                    f'<animate attributeName="stroke-dasharray" values="0 1;0 1;1 1;1 1;0 1" keyTimes="0;0.02;0.38;0.9;1" dur="{dur:g}s" repeatCount="indefinite"/></path>\n')
        for i, (x, y, h, d) in enumerate(pts):
            a = 0.02 + 0.36 * i / max(1, n - 1)
            body.append(f'  <circle cx="{F(x)}" cy="{F(y)}" r="5" fill="{th["bg"]}" stroke="{th["accent"]}" stroke-width="2.2"><animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;{T(a)};{T(a + 0.02)};0.9;1" dur="{dur:g}s" repeatCount="indefinite"/></circle>\n')
            body.append(f'  <text x="{F(x)}" y="{F(y - 12)}" text-anchor="middle" font-family="{FONT}" font-size="12" font-weight="700" fill="{th["text_key"]}">{d["value"]:g}<animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;{T(a)};{T(a + 0.02)};0.9;1" dur="{dur:g}s" repeatCount="indefinite"/></text>\n')
            sb.append(tdesc(f"point {i}", a, a + 0.02))
    else:
        bw = slot * 0.54
        for i, (cx, y, h, d) in enumerate(pts):
            g0 = 0.05 + i * min(0.05, 0.3 / n)
            g1 = g0 + 0.16
            col = th["accent"] if i == hi_i else th["accent2"]
            op = 1 if i == hi_i else 0.85
            ks = "0 0 1 1;0.16 1 0.3 1;0 0 1 1;0.4 0 1 1"
            kt = f"0;{T(g0)};{T(g1)};0.9;1"
            body.append(f'  <rect x="{F(cx - bw / 2)}" y="{F(y)}" width="{F(bw)}" height="{F(h)}" rx="4" fill="{col}" opacity="{op}">'
                        f'<animate attributeName="height" calcMode="spline" keyTimes="{kt}" keySplines="{ks}" values="0;0;{F(h)};{F(h)};0" dur="{dur:g}s" repeatCount="indefinite"/>'
                        f'<animate attributeName="y" calcMode="spline" keyTimes="{kt}" keySplines="{ks}" values="{F(base)};{F(base)};{F(y)};{F(y)};{F(base)}" dur="{dur:g}s" repeatCount="indefinite"/></rect>\n')
            body.append(f'  <text x="{F(cx)}" y="{F(y - 9)}" text-anchor="middle" font-family="{FONT}" font-size="12" font-weight="700" fill="{th["text_key"] if i == hi_i else th["text"]}">{d["value"]:g}'
                        f'<animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;{T(g1 - 0.02)};{T(g1)};0.9;1" dur="{dur:g}s" repeatCount="indefinite"/></text>\n')
            sb.append(tdesc(f"bar {i}", g0, g1))
    return part("".join(body), W, H, sb, False, f"{kind.title()} chart: " + ", ".join(f'{d["label"]} {d["value"]:g}' for d in data))


# ------------------------------------------------------------------ BANNER
def build_banner(spec, th, idp=""):
    dur = float(spec.get("dur", 12))
    W, H = spec.get("width", 1200), spec.get("height", 360)
    heading = spec["heading"]
    sub = spec.get("subtitle", "")
    tags = spec.get("tags", [])
    font = SANS if spec.get("font", "sans") == "sans" else FONT
    x0 = spec.get("x", 80)
    tsize = spec.get("title_size", 64 if len(heading) <= 18 else 48)
    ty = H * 0.42 + tsize * 0.3
    gw = max(240, len(heading) * tsize * 0.6)
    gid = f"{idp}tg"
    rng = random.Random(spec.get("seed", 7))
    sb = [f"type=banner  loop={dur:g}s  (ambient motion: shimmer, rings, drifting particles)", "static-first: title, subtitle and chips are fully visible without animation"]
    body = [f'  <linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="{x0}" y1="0" x2="{x0 + gw:.0f}" y2="0" spreadMethod="repeat">'
            f'<stop offset="0" stop-color="{th["accent2"]}"/><stop offset="0.35" stop-color="{th["accent"]}"/><stop offset="0.5" stop-color="{th["accent3"]}"/>'
            f'<stop offset="0.65" stop-color="{th["accent"]}"/><stop offset="1" stop-color="{th["accent2"]}"/>'
            f'<animateTransform attributeName="gradientTransform" type="translate" values="0 0;{gw:.0f} 0" dur="{dur:g}s" repeatCount="indefinite"/></linearGradient>\n']
    cx, cy = W - 230, H / 2
    for k, (rr, d, dash) in enumerate(((120, 60, "2 10"), (84, 90, "6 8"), (52, 45, "1 7"))):
        sgn = 1 if k % 2 == 0 else -1
        body.append(f'  <circle cx="{F(cx)}" cy="{F(cy)}" r="{rr}" fill="none" stroke="{th["accent"]}" stroke-opacity="{0.32 - k * 0.05:.2f}" stroke-width="1.6" stroke-dasharray="{dash}">'
                    f'<animateTransform attributeName="transform" type="rotate" values="0 {F(cx)} {F(cy)};{360 * sgn} {F(cx)} {F(cy)}" dur="{d}s" repeatCount="indefinite"/></circle>\n')
    body.append(f'  <circle cx="{F(cx)}" cy="{F(cy)}" r="6" fill="{th["accent"]}" filter="url(#glow)"><animate attributeName="opacity" values="0.45;1;0.45" dur="{dur / 4:g}s" repeatCount="indefinite"/></circle>\n')
    for i in range(spec.get("particles", 24)):
        px, py = rng.uniform(0, W), rng.uniform(0, H)
        r = rng.uniform(0.8, 2.2)
        d = rng.uniform(9, 18)
        rise = rng.uniform(40, 90)
        b = -rng.uniform(0, d)
        body.append(f'  <circle cx="{px:.0f}" cy="{py:.0f}" r="{r:.1f}" fill="{th["accent3"]}" opacity="0.3">'
                    f'<animateTransform attributeName="transform" type="translate" values="0 0;0 {-rise:.0f}" dur="{d:.1f}s" begin="{b:.1f}s" repeatCount="indefinite"/>'
                    f'<animate attributeName="opacity" values="0.08;0.5;0.08" dur="{d:.1f}s" begin="{b:.1f}s" repeatCount="indefinite"/></circle>\n')
    body.append(f'  <text x="{x0}" y="{F(ty)}" font-family="{font}" font-size="{tsize}" font-weight="800" letter-spacing="-1" fill="url(#{gid})">{esc(heading)}</text>\n')
    y = ty
    if sub:
        y = ty + 46
        body.append(f'  <text x="{x0}" y="{F(y)}" font-family="{font}" font-size="{spec.get("subtitle_size", 20)}" fill="{th["muted"]}">{esc(sub)}</text>\n')
    if tags:
        cxp, ty2 = x0, y + 30
        for t in tags:
            w = round(len(t) * 8.2 + 30)
            body.append(f'  <g><rect x="{cxp}" y="{F(ty2)}" width="{w}" height="32" rx="8" fill="{th["surface_key"]}" stroke="{th["stroke_dim"]}" stroke-width="1.1"/>'
                        f'<text x="{F(cxp + w / 2)}" y="{F(ty2 + 21)}" text-anchor="middle" font-family="{FONT}" font-size="13" fill="{th["text"]}">{esc(t)}</text></g>\n')
            cxp += w + 12
    return part("".join(body), W, H, sb, False, f"Banner: {heading}. {sub}")


EXTRA_BUILDERS = {
    "timeline": build_timeline, "network": build_network, "layers": build_layers, "cycle": build_cycle,
    "sequence": build_sequence, "terminal": build_terminal, "cards": build_cards, "chart": build_chart, "banner": build_banner,
}
