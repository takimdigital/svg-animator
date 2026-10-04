"""Non-diagram types (part 1): loader, logo, text, gauge, radar.

Same contract as diagram_extra.py (build(spec, th, idp="") -> Part) so every type also works inside compose.
All are static-first: the base attributes show the finished graphic; animations start from "empty" or "rest".
"""
import math
import sys

from diagram_common import FONT, SANS, F, T, esc, gradient_colors, part, tdesc


def _tz(spec, a=84, b=24):
    return spec.get("title_zone", a if spec.get("title") else b)


# ------------------------------------------------------------------ LOADER
def _l_ring(cx, cy, r, th, p, k):
    arc = f"M{F(cx)},{F(cy - r)} A{F(r)},{F(r)} 0 0 1 {F(cx + r)},{F(cy)}"
    return (f'<circle cx="{F(cx)}" cy="{F(cy)}" r="{F(r)}" fill="none" stroke="{th["rail"]}" stroke-width="5"/>'
            f'<path d="{arc}" fill="none" stroke="{th["accent"]}" stroke-width="5" stroke-linecap="round">'
            f'<animateTransform attributeName="transform" type="rotate" values="0 {F(cx)} {F(cy)};360 {F(cx)} {F(cy)}" dur="{p}s" repeatCount="indefinite"/></path>')


def _l_dots(cx, cy, r, th, p, k):
    s = []
    for i in range(3):
        x = cx + (i - 1) * 24
        s.append(f'<circle cx="{F(x)}" cy="{F(cy)}" r="7" fill="{th["accent"]}">'
                 f'<animate attributeName="cy" values="{F(cy)};{F(cy - 14)};{F(cy)}" dur="{p}s" begin="{-i * p / 6:.2f}s" repeatCount="indefinite" calcMode="spline" keyTimes="0;0.5;1" keySplines="0.45 0 0.55 1;0.45 0 0.55 1"/>'
                 f'<animate attributeName="opacity" values="0.45;1;0.45" dur="{p}s" begin="{-i * p / 6:.2f}s" repeatCount="indefinite"/></circle>')
    return "".join(s)


def _l_bars(cx, cy, r, th, p, k):
    s = []
    for i in range(5):
        x = cx + (i - 2) * 14 - 4
        lo, hi = 12, 30 + (i % 3) * 8
        s.append(f'<rect x="{F(x)}" y="{F(cy - lo / 2)}" width="8" height="{lo}" rx="4" fill="{th["accent"]}">'
                 f'<animate attributeName="height" values="{lo};{hi};{lo}" dur="{p}s" begin="{-i * p / 7:.2f}s" repeatCount="indefinite"/>'
                 f'<animate attributeName="y" values="{F(cy - lo / 2)};{F(cy - hi / 2)};{F(cy - lo / 2)}" dur="{p}s" begin="{-i * p / 7:.2f}s" repeatCount="indefinite"/></rect>')
    return "".join(s)


def _l_orbit(cx, cy, r, th, p, k):
    return (f'<circle cx="{F(cx)}" cy="{F(cy)}" r="{F(r)}" fill="none" stroke="{th["rail"]}" stroke-width="1.2"/>'
            f'<circle cx="{F(cx)}" cy="{F(cy)}" r="{F(r * 0.55)}" fill="none" stroke="{th["rail"]}" stroke-width="1.2"/>'
            f'<circle cx="{F(cx)}" cy="{F(cy)}" r="6" fill="{th["accent"]}"/>'
            f'<g><animateTransform attributeName="transform" type="rotate" values="0 {F(cx)} {F(cy)};360 {F(cx)} {F(cy)}" dur="{p * 1.6:.2f}s" repeatCount="indefinite"/><circle cx="{F(cx + r)}" cy="{F(cy)}" r="5" fill="{th["accent3"]}"/></g>'
            f'<g><animateTransform attributeName="transform" type="rotate" values="0 {F(cx)} {F(cy)};-360 {F(cx)} {F(cy)}" dur="{p:.2f}s" repeatCount="indefinite"/><circle cx="{F(cx + r * 0.55)}" cy="{F(cy)}" r="4" fill="{th["accent2"]}"/></g>')


def _l_pulse(cx, cy, r, th, p, k):
    s = [f'<circle cx="{F(cx)}" cy="{F(cy)}" r="6" fill="{th["accent"]}"/>']
    for i in range(2):
        b = f"{-i * p / 2:.2f}s"
        s.append(f'<circle cx="{F(cx)}" cy="{F(cy)}" r="6" fill="none" stroke="{th["accent"]}" stroke-width="2.4" opacity="0.7">'
                 f'<animate attributeName="r" values="6;{F(r)}" dur="{p}s" begin="{b}" repeatCount="indefinite"/>'
                 f'<animate attributeName="opacity" values="0.7;0" dur="{p}s" begin="{b}" repeatCount="indefinite"/></circle>')
    return "".join(s)


def _l_dual(cx, cy, r, th, p, k):
    def arc(rr, col, sgn, per):
        d = f"M{F(cx)},{F(cy - rr)} A{F(rr)},{F(rr)} 0 0 1 {F(cx + rr)},{F(cy)}"
        return (f'<path d="{d}" fill="none" stroke="{col}" stroke-width="5" stroke-linecap="round">'
                f'<animateTransform attributeName="transform" type="rotate" values="0 {F(cx)} {F(cy)};{360 * sgn} {F(cx)} {F(cy)}" dur="{per:.2f}s" repeatCount="indefinite"/></path>')
    return (f'<circle cx="{F(cx)}" cy="{F(cy)}" r="{F(r)}" fill="none" stroke="{th["rail"]}" stroke-width="2"/>'
            f'<circle cx="{F(cx)}" cy="{F(cy)}" r="{F(r * 0.62)}" fill="none" stroke="{th["rail"]}" stroke-width="2"/>'
            + arc(r, th["accent"], 1, p) + arc(r * 0.62, th["accent3"], -1, p * 0.8))


def _l_wave(cx, cy, r, th, p, k):
    s = []
    for i in range(5):
        x = cx + (i - 2) * 20
        s.append(f'<circle cx="{F(x)}" cy="{F(cy)}" r="6" fill="{th["accent"]}">'
                 f'<animate attributeName="cy" values="{F(cy + 11)};{F(cy - 11)};{F(cy + 11)}" dur="{p}s" begin="{-i * p / 10:.2f}s" repeatCount="indefinite" calcMode="spline" keyTimes="0;0.5;1" keySplines="0.45 0 0.55 1;0.45 0 0.55 1"/></circle>')
    return "".join(s)


def _l_progress(cx, cy, r, th, p, k):
    w, h = r * 2.2, 10
    cid = f"lc{k}"
    return (f'<clipPath id="{{idp}}{cid}"><rect x="{F(cx - w / 2)}" y="{F(cy - h / 2)}" width="{F(w)}" height="{h}" rx="5"/></clipPath>'
            f'<rect x="{F(cx - w / 2)}" y="{F(cy - h / 2)}" width="{F(w)}" height="{h}" rx="5" fill="{th["rail"]}"/>'
            f'<g clip-path="url(#{{idp}}{cid})"><rect x="{F(cx - w / 2)}" y="{F(cy - h / 2)}" width="{F(w * 0.4)}" height="{h}" rx="5" fill="{th["accent"]}">'
            f'<animateTransform attributeName="transform" type="translate" values="{F(-w * 0.4)} 0;{F(w)} 0" dur="{p * 1.3:.2f}s" repeatCount="indefinite"/></rect></g>')


LOADERS = {"ring": _l_ring, "dots": _l_dots, "bars": _l_bars, "orbit": _l_orbit, "pulse": _l_pulse,
           "dual": _l_dual, "wave": _l_wave, "progress": _l_progress}


def build_loader(spec, th, idp=""):
    names = spec.get("variants") or ([spec["variant"]] if spec.get("variant") else list(LOADERS))
    for n in names:
        if n not in LOADERS:
            sys.exit(f"loader variant '{n}' unknown; choose from {sorted(LOADERS)}")
    p = float(spec.get("period", 1.2))
    cols = spec.get("cols", min(len(names), 4))
    cell, r, margin = spec.get("cell", 170), 34, 24
    tz = _tz(spec)
    rows = math.ceil(len(names) / cols)
    W = 2 * margin + cols * cell
    H = tz + rows * (cell - 10) + margin
    sb = [f"type=loader  variants={names}  period={p}s (loops are independent of the master clock)"]
    body = []
    for i, n in enumerate(names):
        cx = margin + (i % cols) * cell + cell / 2
        cy = tz + (i // cols) * (cell - 10) + 56
        g = LOADERS[n](cx, cy, r, th, p, i).replace("{idp}", idp)
        body.append(f'  <g id="{idp}loader-{n}">{g}<text x="{F(cx)}" y="{F(cy + r + 34)}" text-anchor="middle" font-family="{FONT}" font-size="11" fill="{th["muted"]}" letter-spacing="1">{esc(n)}</text></g>\n')
    if spec.get("label"):
        sb.append("label shown under the sheet")
    return part("".join(body), W, H, sb, False, "Loaders: " + ", ".join(names))


# ------------------------------------------------------------------ LOGO
def _mark_path(mark, cx, cy, R):
    def poly(n, rot, k=1.0):
        pts = [(cx + R * k * math.cos(math.radians(rot + 360 * i / n)), cy + R * k * math.sin(math.radians(rot + 360 * i / n))) for i in range(n)]
        return "M" + " L".join(f"{F(x)},{F(y)}" for x, y in pts) + " Z"
    if mark == "hexagon":
        return poly(6, -90)
    if mark == "diamond":
        return poly(4, -90, 1.12)
    if mark == "triangle":
        return poly(3, -90, 1.2)
    if mark == "pentagon":
        return poly(5, -90)
    if mark == "circle":
        return f"M{F(cx - R)},{F(cy)} A{F(R)},{F(R)} 0 1 1 {F(cx + R)},{F(cy)} A{F(R)},{F(R)} 0 1 1 {F(cx - R)},{F(cy)} Z"
    if mark == "shield":
        return (f"M{F(cx)},{F(cy - R)} L{F(cx + R * .85)},{F(cy - R * .55)} V{F(cy + R * .1)} C{F(cx + R * .85)},{F(cy + R * .65)} {F(cx + R * .3)},{F(cy + R * .9)} {F(cx)},{F(cy + R)} "
                f"C{F(cx - R * .3)},{F(cy + R * .9)} {F(cx - R * .85)},{F(cy + R * .65)} {F(cx - R * .85)},{F(cy + R * .1)} V{F(cy - R * .55)} Z")
    rr = 16  # rounded square
    x, y, w = cx - R * .9, cy - R * .9, R * 1.8
    return (f"M{F(x + rr)},{F(y)} H{F(x + w - rr)} A{rr},{rr} 0 0 1 {F(x + w)},{F(y + rr)} V{F(y + w - rr)} A{rr},{rr} 0 0 1 {F(x + w - rr)},{F(y + w)} "
            f"H{F(x + rr)} A{rr},{rr} 0 0 1 {F(x)},{F(y + w - rr)} V{F(y + rr)} A{rr},{rr} 0 0 1 {F(x + rr)},{F(y)} Z")


def build_logo(spec, th, idp=""):
    dur = float(spec.get("dur", 8))
    W, H = spec.get("width", 860), spec.get("height", 280)
    mark = spec.get("mark", "hexagon")
    ini = str(spec.get("initials", ""))[:3]
    word, tag = spec.get("wordmark", ""), spec.get("tagline", "")
    R, wsz = 56, spec.get("wordmark_size", 46)
    ww = len(word) * wsz * 0.58
    total = 2 * R + (40 + ww if word else 0)
    x0 = (W - total) / 2
    mx, my = x0 + R, H / 2
    d = _mark_path(mark, mx, my, R)
    cid, gid = f"{idp}lmc", f"{idp}lmg"
    # Static-first for an intro animation (issue #5).
    #
    # A logo reveal is a timed intro: the outline has no dash and the wordmark is
    # at opacity 0 until its cue, so at t=0 the canvas is empty. That is correct
    # for a clean loop and wrong for principle 1 -- a viewer whose client does
    # not run SMIL sees a blank rectangle.
    #
    # A negative `begin` pre-rolls the loop, so frame 0 lands wherever we choose.
    # PRE sits inside the hold window (after the shine at 0.78, before the
    # fade-out at 0.93), which means frame 0 shows the COMPLETED logo and the
    # reveal still plays on from there. The loop stays seamless: pre-rolling a
    # periodic animation does not change its period.
    PRE = 0.85
    begin = f' begin="{-PRE * dur:.3f}s"'

    sb = [f"type=logo  loop={dur:g}s  mark={mark}", tdesc("draw outline", 0.04, 0.30), tdesc("fill + initials", 0.30, 0.42),
          tdesc("wordmark", 0.38, 0.52), tdesc("tagline", 0.50, 0.62), tdesc("shine", 0.62, 0.78),
          "whole lockup fades out at 0.93-0.98 so the loop restarts clean; base state = finished logo",
          f"loop pre-rolled by {PRE * dur:.2f}s so frame 0 lands in the hold window, fully drawn (static-first)"]

    # Static-first for an intro animation (issue #5).
    #
    # A logo reveal is a timed intro: the outline has no dash and the wordmark is
    # at opacity 0 until its cue, so at t=0 the canvas is empty. That is correct
    # for a clean loop and wrong for principle 1 -- a viewer whose client does
    # not run SMIL sees a blank rectangle.
    #
    # A negative `begin` pre-rolls the loop, so frame 0 lands wherever we choose.
    # PRE is placed inside the hold window (after the shine at 0.78, before the
    # fade-out at 0.93) which means frame 0 shows the COMPLETED logo, and the
    # reveal still plays on from there. The loop stays seamless: pre-rolling a
    # periodic animation does not change its period.
    ani = lambda a, v, kt, extra="": f'<animate attributeName="{a}" values="{v}" keyTimes="{kt}" dur="{dur:g}s"{begin} repeatCount="indefinite"{extra}/>'
    body = [f'  <clipPath id="{cid}"><path d="{d}"/></clipPath>'
            f'<linearGradient id="{gid}" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="0.5" stop-color="#fff" stop-opacity="0.55"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>\n',
            f'  <g id="{idp}logo">{ani("opacity", "1;1;0;0", "0;0.93;0.98;1")}',
            f'<path d="{d}" fill="{th["accent"]}" fill-opacity="0.16">{ani("fill-opacity", "0;0;0.16;0.16", "0;0.28;0.42;1")}</path>',
            f'<path d="{d}" pathLength="1" fill="none" stroke="{th["accent"]}" stroke-width="3.2" stroke-linejoin="round" stroke-linecap="butt">'
            f'{ani("stroke-dasharray", "0 1;0 1;1 1;1 1", "0;0.04;0.30;1")}</path>']
    if ini:
        body.append(f'<text x="{F(mx)}" y="{F(my + 14)}" text-anchor="middle" font-family="{SANS}" font-size="40" font-weight="800" fill="{th["text_key"]}">{esc(ini)}'
                    f'{ani("opacity", "0;0;1;1", "0;0.30;0.40;1")}</text>')
    body.append(f'<g clip-path="url(#{cid})"><g><animateTransform attributeName="transform" type="translate" values="0 0;0 0;{F(2 * R + 150)} 0;{F(2 * R + 150)} 0" keyTimes="0;0.62;0.78;1" dur="{dur:g}s"{begin} repeatCount="indefinite"/>'
                f'<rect x="{F(mx - R - 90)}" y="{F(my - R * 1.4)}" width="46" height="{F(R * 2.8)}" fill="url(#{gid})" transform="rotate(18 {F(mx)} {F(my)})"/></g></g>')
    if word:
        wx = mx + R + 40
        wy = my + (8 if tag else wsz * 0.34)
        body.append(f'<text x="{F(wx)}" y="{F(wy)}" font-family="{SANS}" font-size="{wsz}" font-weight="800" letter-spacing="-0.5" fill="{th["text_key"]}">{esc(word)}'
                    f'{ani("opacity", "0;0;1;1", "0;0.38;0.52;1")}'
                    f'<animateTransform attributeName="transform" type="translate" values="-26 0;-26 0;0 0;0 0" keyTimes="0;0.38;0.52;1" dur="{dur:g}s" repeatCount="indefinite"/></text>')
        if tag:
            body.append(f'<text x="{F(wx)}" y="{F(wy + 30)}" font-family="{FONT}" font-size="14" letter-spacing="3" fill="{th["muted"]}">{esc(tag.upper())}'
                        f'{ani("opacity", "0;0;1;1", "0;0.50;0.62;1")}</text>')
    body.append("</g>\n")
    return part("".join(body), W, H, sb, False, f"Logo reveal: {word or ini}")


# ------------------------------------------------------------------ TEXT (kinetic)
def _burst(b):
    return [(b, 0.0), (b + 0.004, 0.85), (b + 0.010, 0.0), (b + 0.016, 0.85), (b + 0.024, 0.0)]


def build_text(spec, th, idp=""):
    dur = float(spec.get("dur", 6))
    txt = str(spec["text"])
    var = spec.get("variant", "wave")
    size = spec.get("size", 72)
    n = len(txt)
    letter_mode = var in ("wave", "reveal", "pop", "type")
    font = FONT if (letter_mode or spec.get("font") == "mono") else SANS
    cw = size * 0.6
    W = spec.get("width", max(760, int(n * cw + 160)))
    H = spec.get("height", int(size * 2.3))
    x0 = (W - n * cw) / 2
    ybase = H / 2 + size * 0.28
    cols = gradient_colors(th, n)
    sb = [f"type=text  variant={var}  loop={dur:g}s  chars={n}"]
    body = []
    if var == "wave":
        p = dur / 2
        for i, ch in enumerate(txt):
            if ch == " ":
                continue
            body.append(f'  <text x="{F(x0 + i * cw)}" y="{F(ybase)}" font-family="{font}" font-size="{size}" font-weight="700" fill="{cols[i]}">{esc(ch)}'
                        f'<animateTransform attributeName="transform" type="translate" values="0 0;0 {F(-size * 0.22)};0 0" dur="{p:g}s" begin="{-i * p / (n * 1.4):.3f}s" repeatCount="indefinite" calcMode="spline" keyTimes="0;0.5;1" keySplines="0.45 0 0.55 1;0.45 0 0.55 1"/></text>\n')
        sb.append("wave: per-letter bob, phase offset by negative begin (pre-rolled); ambient")
    elif var == "reveal":
        for i, ch in enumerate(txt):
            if ch == " ":
                continue
            s = 0.05 + i * 0.30 / max(1, n)
            body.append(f'  <text x="{F(x0 + i * cw)}" y="{F(ybase)}" font-family="{font}" font-size="{size}" font-weight="700" fill="{cols[i]}">{esc(ch)}'
                        f'<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;{T(s)};{T(s + 0.06)};0.88;0.95;1" dur="{dur:g}s" repeatCount="indefinite"/>'
                        f'<animateTransform attributeName="transform" type="translate" values="0 {F(size * 0.45)};0 {F(size * 0.45)};0 0;0 0" keyTimes="0;{T(s)};{T(s + 0.06)};1" dur="{dur:g}s" repeatCount="indefinite" calcMode="spline" keySplines="0 0 1 1;0.16 1 0.3 1;0 0 1 1"/></text>\n')
        sb.append(tdesc("letters rise in", 0.05, 0.05 + 0.30 + 0.06))
    elif var == "pop":
        for i, ch in enumerate(txt):
            if ch == " ":
                continue
            s = 0.05 + i * 0.70 / max(1, n)
            cx, cy = x0 + i * cw + cw / 2, ybase - size * 0.28
            body.append(f'  <g transform="translate({F(cx)} {F(cy)})"><g><animateTransform attributeName="transform" type="scale" values="1;1;1.5;1;1" keyTimes="0;{T(s)};{T(s + 0.04)};{T(s + 0.09)};1" dur="{dur:g}s" repeatCount="indefinite"/>'
                        f'<text x="0" y="{F(size * 0.28)}" text-anchor="middle" font-family="{font}" font-size="{size}" font-weight="700" fill="{cols[i]}">{esc(ch)}</text></g></g>\n')
        sb.append(tdesc("pop sweep", 0.05, 0.80))
    elif var == "type":
        ts, te = 0.08, 0.55
        kts = [0.0] + [ts + j * (te - ts) / n for j in range(1, n + 1)]
        kt = ";".join(T(v) for v in kts)
        xs = ";".join(F(x0 + j * cw) for j in range(n + 1))
        body.append(f'  <g><animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.90;0.96;1" dur="{dur:g}s" repeatCount="indefinite"/>')
        for i, ch in enumerate(txt):
            if ch == " ":
                continue
            body.append(f'<text x="{F(x0 + i * cw)}" y="{F(ybase)}" font-family="{font}" font-size="{size}" font-weight="700" fill="{th["text_key"]}">{esc(ch)}'
                        f'<animate attributeName="opacity" calcMode="discrete" values="0;1" keyTimes="0;{T(kts[i + 1])}" dur="{dur:g}s" repeatCount="indefinite"/></text>')
        body.append(f'<rect x="{F(x0)}" y="{F(ybase - size * 0.8)}" width="{F(size * 0.1)}" height="{F(size * 0.95)}" fill="{th["accent"]}" opacity="0">'
                    f'<animate attributeName="x" calcMode="discrete" keyTimes="{kt}" values="{xs}" dur="{dur:g}s" repeatCount="indefinite"/>'
                    f'<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;{T(ts - 0.01)};{T(ts)};{T(te + 0.05)};{T(te + 0.06)};1" dur="{dur:g}s" repeatCount="indefinite"/></rect></g>\n')
        sb.append("type: each letter appears with a discrete opacity step (no cover rectangle, so it works on any background)")
        sb.append(tdesc("typing", ts, te))
    elif var == "shimmer":
        gw = max(240, n * size * 0.6)
        gid = f"{idp}sh"
        body.append(f'  <linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="{F(W / 2 - gw / 2)}" y1="0" x2="{F(W / 2 + gw / 2)}" y2="0" spreadMethod="repeat">'
                    f'<stop offset="0" stop-color="{th["accent2"]}"/><stop offset="0.35" stop-color="{th["accent"]}"/><stop offset="0.5" stop-color="{th["accent3"]}"/><stop offset="0.65" stop-color="{th["accent"]}"/><stop offset="1" stop-color="{th["accent2"]}"/>'
                    f'<animateTransform attributeName="gradientTransform" type="translate" values="0 0;{F(gw)} 0" dur="{dur:g}s" repeatCount="indefinite"/></linearGradient>\n')
        body.append(f'  <text x="{F(W / 2)}" y="{F(ybase)}" text-anchor="middle" font-family="{font}" font-size="{size}" font-weight="800" letter-spacing="-1" fill="url(#{gid})">{esc(txt)}</text>\n')
        sb.append("shimmer: seamless repeating gradient pass; ambient")
    elif var == "glitch":
        bursts = [0.28, 0.62, 0.81]
        pts = [(0.0, 0.0)]
        for b in bursts:
            pts += _burst(b)
        pts.append((1.0, 0.0))
        kt = ";".join(T(t) for t, _ in pts)
        ov = ";".join(f"{v:g}" for _, v in pts)
        offs = [0] + [0, -6, 5, -4, 0] * len(bursts) + [0]
        for col, sgn in (("#00E5FF", 1), ("#FF2E93", -1)):
            xs_ = ";".join(f"{o * sgn} 0" for o in offs)
            body.append(f'  <text x="{F(W / 2)}" y="{F(ybase)}" text-anchor="middle" font-family="{font}" font-size="{size}" font-weight="800" fill="{col}" opacity="0">'
                        f'{esc(txt)}<animate attributeName="opacity" values="{ov}" keyTimes="{kt}" dur="{dur:g}s" repeatCount="indefinite"/>'
                        f'<animateTransform attributeName="transform" type="translate" values="{xs_}" keyTimes="{kt}" dur="{dur:g}s" repeatCount="indefinite"/></text>\n')
        body.append(f'  <text x="{F(W / 2)}" y="{F(ybase)}" text-anchor="middle" font-family="{font}" font-size="{size}" font-weight="800" fill="{th["text_key"]}">{esc(txt)}</text>\n')
        sb += [tdesc(f"glitch burst {i}", b, b + 0.024) for i, b in enumerate(bursts)]
    else:
        sys.exit("text variant must be one of wave|reveal|pop|type|shimmer|glitch")
    if spec.get("subtitle"):
        body.append(f'  <text x="{F(W / 2)}" y="{F(ybase + size * 0.75)}" text-anchor="middle" font-family="{SANS}" font-size="{spec.get("subtitle_size", 20)}" fill="{th["muted"]}">{esc(spec["subtitle"])}</text>\n')
        H += int(size * 0.5)
    return part("".join(body), W, H, sb, False, f"Animated text ({var}): {txt}")


# ------------------------------------------------------------------ GAUGE (gauge / ring / bar / donut)
def _count(x, y, value, unit, size, col, anchor, dur, t0, t1, th, steps=8):
    """Count-up using stacked texts with discrete visibility; the base state shows the final value."""
    fin = f"{value:g}"
    out = []
    for j in range(steps):
        v = value * j / steps
        txt = f"{v:.0f}" if abs(value) >= 10 else f"{v:.1f}"
        a = t0 + (t1 - t0) * j / steps
        b = t0 + (t1 - t0) * (j + 1) / steps
        out.append(f'<text x="{F(x)}" y="{F(y)}" text-anchor="{anchor}" font-family="{FONT}" font-size="{size}" font-weight="700" fill="{col}" opacity="0">{txt}{esc(unit)}'
                   f'<animate attributeName="opacity" calcMode="discrete" values="0;1;0" keyTimes="0;{T(a)};{T(b)}" dur="{dur:g}s" repeatCount="indefinite"/></text>')
    out.append(f'<text x="{F(x)}" y="{F(y)}" text-anchor="{anchor}" font-family="{FONT}" font-size="{size}" font-weight="700" fill="{col}">{fin}{esc(unit)}'
               f'<animate attributeName="opacity" calcMode="discrete" values="0;1;0" keyTimes="0;{T(t1)};0.92" dur="{dur:g}s" repeatCount="indefinite"/></text>')
    return "".join(out)


def build_gauge(spec, th, idp=""):
    dur = float(spec.get("dur", 8))
    items = spec["items"]
    cols = spec.get("cols", min(len(items), 3))
    cw, chh, margin = 250, 220, 24
    tz = _tz(spec)
    rows = math.ceil(len(items) / cols)
    W = 2 * margin + cols * cw
    H = tz + rows * chh + margin
    kt5 = "0;0.05;0.45;0.9;1"
    ks = "0 0 1 1;0.16 1 0.3 1;0 0 1 1;0.4 0 1 1"
    sb = [f"type=gauge  items={len(items)}  grow 0.05-0.45, hold, reset at 0.9-1.0 (base state = finished)"]
    body = []
    palette = gradient_colors(th, max(2, len(items)))
    for i, it in enumerate(items):
        kind = it.get("kind", "gauge")
        cx = margin + (i % cols) * cw + cw / 2
        top = tz + (i // cols) * chh
        mx = it.get("max", 100)
        v = max(0.0, min(1.0, it.get("value", 0) / mx)) if kind != "donut" else 1.0
        unit = it.get("unit", "%" if mx == 100 else "")
        col = it.get("color") or th["accent"]
        lbl = esc(it.get("label", ""))
        g = [f'  <g id="{idp}gauge-{i}">']
        if kind == "gauge":
            R, cy = 82, top + 118
            d = f"M{F(cx - R)},{F(cy)} A{R},{R} 0 0 1 {F(cx + R)},{F(cy)}"
            g.append(f'<path d="{d}" fill="none" stroke="{th["rail"]}" stroke-width="13" stroke-linecap="round"/>')
            g.append(f'<path d="{d}" pathLength="1" fill="none" stroke="{col}" stroke-width="13" stroke-linecap="round" stroke-dasharray="{v:.3f} 1">'
                     f'<animate attributeName="stroke-dasharray" calcMode="spline" keyTimes="{kt5}" keySplines="{ks}" values="0 1;0 1;{v:.3f} 1;{v:.3f} 1;0 1" dur="{dur:g}s" repeatCount="indefinite"/></path>')
            ang = -180 + 180 * v
            g.append(f'<g transform="rotate({ang:.1f} {F(cx)} {F(cy)})"><animateTransform attributeName="transform" type="rotate" calcMode="spline" keyTimes="{kt5}" keySplines="{ks}" values="-180 {F(cx)} {F(cy)};-180 {F(cx)} {F(cy)};{ang:.1f} {F(cx)} {F(cy)};{ang:.1f} {F(cx)} {F(cy)};-180 {F(cx)} {F(cy)}" dur="{dur:g}s" repeatCount="indefinite"/>'
                     f'<path d="M{F(cx - 8)},{F(cy)} L{F(cx + R - 22)},{F(cy)}" stroke="{th["text_key"]}" stroke-width="3" stroke-linecap="round"/></g>')
            g.append(f'<circle cx="{F(cx)}" cy="{F(cy)}" r="7" fill="{th["surface_key"]}" stroke="{col}" stroke-width="3"/>')
            g.append(_count(cx, cy + 44, it.get("value", 0), unit, 30, th["text_key"], "middle", dur, 0.05, 0.45, th))
            g.append(f'<text x="{F(cx)}" y="{F(cy + 68)}" text-anchor="middle" font-family="{FONT}" font-size="13" fill="{th["muted"]}">{lbl}</text>')
            g.append(f'<text x="{F(cx - R)}" y="{F(cy + 22)}" text-anchor="middle" font-family="{FONT}" font-size="10" fill="{th["eyebrow"]}">0</text><text x="{F(cx + R)}" y="{F(cy + 22)}" text-anchor="middle" font-family="{FONT}" font-size="10" fill="{th["eyebrow"]}">{mx:g}</text>')
        elif kind == "ring":
            R, cy = 66, top + 100
            g.append(f'<circle cx="{F(cx)}" cy="{F(cy)}" r="{R}" fill="none" stroke="{th["rail"]}" stroke-width="12"/>')
            g.append(f'<circle cx="{F(cx)}" cy="{F(cy)}" r="{R}" pathLength="1" fill="none" stroke="{col}" stroke-width="12" stroke-linecap="round" stroke-dasharray="{v:.3f} 1" transform="rotate(-90 {F(cx)} {F(cy)})">'
                     f'<animate attributeName="stroke-dasharray" calcMode="spline" keyTimes="{kt5}" keySplines="{ks}" values="0 1;0 1;{v:.3f} 1;{v:.3f} 1;0 1" dur="{dur:g}s" repeatCount="indefinite"/></circle>')
            g.append(_count(cx, cy + 10, it.get("value", 0), unit, 30, th["text_key"], "middle", dur, 0.05, 0.45, th))
            g.append(f'<text x="{F(cx)}" y="{F(cy + R + 32)}" text-anchor="middle" font-family="{FONT}" font-size="13" fill="{th["muted"]}">{lbl}</text>')
        elif kind == "bar":
            w, y = 200, top + 96
            x = cx - w / 2
            g.append(f'<text x="{F(x)}" y="{F(y - 14)}" font-family="{FONT}" font-size="13" fill="{th["muted"]}">{lbl}</text>')
            g.append(_count(x + w, y - 14, it.get("value", 0), unit, 14, th["text_key"], "end", dur, 0.05, 0.45, th))
            g.append(f'<rect x="{F(x)}" y="{F(y)}" width="{w}" height="14" rx="7" fill="{th["rail"]}"/>')
            g.append(f'<rect x="{F(x)}" y="{F(y)}" width="{F(w * v)}" height="14" rx="7" fill="{col}">'
                     f'<animate attributeName="width" calcMode="spline" keyTimes="{kt5}" keySplines="{ks}" values="0;0;{F(w * v)};{F(w * v)};0" dur="{dur:g}s" repeatCount="indefinite"/></rect>')
        elif kind == "donut":
            R, cy = 66, top + 100
            segs = it["segments"]
            tot = sum(s_["value"] for s_ in segs)
            cs = gradient_colors(th, len(segs))
            g.append(f'<circle cx="{F(cx)}" cy="{F(cy)}" r="{R}" fill="none" stroke="{th["rail"]}" stroke-width="16"/>')
            acc = 0.0
            for j, s_ in enumerate(segs):
                f_ = s_["value"] / tot
                a0 = 0.05 + j * 0.10
                kts = f"0;{T(a0)};{T(a0 + 0.18)};0.9;1"
                g.append(f'<circle cx="{F(cx)}" cy="{F(cy)}" r="{R}" pathLength="1" fill="none" stroke="{s_.get("color") or cs[j]}" stroke-width="16" stroke-dasharray="{max(0.0, f_ - 0.006):.3f} 1" transform="rotate({-90 + 360 * acc:.1f} {F(cx)} {F(cy)})">'
                         f'<animate attributeName="stroke-dasharray" calcMode="spline" keyTimes="{kts}" keySplines="{ks}" values="0 1;0 1;{max(0.0, f_ - 0.006):.3f} 1;{max(0.0, f_ - 0.006):.3f} 1;0 1" dur="{dur:g}s" repeatCount="indefinite"/></circle>')
                acc += f_
            ctext = str(it.get("center", f"{tot:g}"))
            csz = max(12, min(26, 96 / (len(ctext) * 0.6)))
            g.append(f'<text x="{F(cx)}" y="{F(cy + csz * 0.25)}" text-anchor="middle" font-family="{FONT}" font-size="{csz:.0f}" font-weight="700" fill="{th["text_key"]}">{esc(ctext)}</text>')
            g.append(f'<text x="{F(cx)}" y="{F(cy + R + 32)}" text-anchor="middle" font-family="{FONT}" font-size="13" fill="{th["muted"]}">{lbl}</text>')
        else:
            sys.exit("gauge kind must be gauge|ring|bar|donut")
        g.append("</g>\n")
        body.append("".join(g))
    return part("".join(body), W, H, sb, False, "Gauges: " + ", ".join(i.get("label", "") for i in items))


# ------------------------------------------------------------------ RADAR
def build_radar(spec, th, idp=""):
    dur = float(spec.get("dur", 8))
    axes = spec["axes"]
    series = spec["series"]
    N = len(axes)
    if N < 3:
        sys.exit("radar needs at least 3 axes")
    R = spec.get("radius", 150)
    tz = _tz(spec)
    W = 2 * (R + 130)
    cx, cy = W / 2, tz + R + 46
    H = cy + R + 70 + (24 if len(series) > 1 else 0)
    ang = [math.radians(-90 + 360 * i / N) for i in range(N)]

    def pt(i, rr):
        return cx + rr * math.cos(ang[i]), cy + rr * math.sin(ang[i])

    def poly(rr_list):
        return " ".join(f"{F(pt(i, r_)[0])},{F(pt(i, r_)[1])}" for i, r_ in enumerate(rr_list))
    palette = [th["accent"], th["accent3"], th["loop"], th["accent2"]]
    sb = [f"type=radar axes={N} series={len(series)}  polygons grow from the centre (base = final)"]
    body = []
    for k in range(1, 5):
        body.append(f'  <polygon points="{poly([R * k / 4] * N)}" fill="none" stroke="{th["rail"]}" stroke-width="1" opacity="{0.9 if k == 4 else 0.5}"/>\n')
    for i in range(N):
        x, y = pt(i, R)
        body.append(f'  <line x1="{F(cx)}" y1="{F(cy)}" x2="{F(x)}" y2="{F(y)}" stroke="{th["rail"]}" stroke-width="1" opacity="0.6"/>\n')
        lx, ly = pt(i, R + 24)
        anchor = "middle" if abs(math.cos(ang[i])) < 0.2 else ("start" if math.cos(ang[i]) > 0 else "end")
        body.append(f'  <text x="{F(lx)}" y="{F(ly + 4)}" text-anchor="{anchor}" font-family="{FONT}" font-size="12" fill="{th["text"]}">{esc(axes[i])}</text>\n')
    ks = "0 0 1 1;0.16 1 0.3 1;0 0 1 1;0.4 0 1 1"
    for si, s in enumerate(series):
        col = s.get("color") or palette[si % len(palette)]
        vals = s["values"]
        mx = s.get("max", 100)
        fin = poly([R * max(0, min(1, v / mx)) for v in vals])
        zero = poly([0.01] * N)
        a0 = 0.05 + si * 0.06
        kt = f"0;{T(a0)};{T(a0 + 0.35)};0.9;1"
        body.append(f'  <polygon points="{fin}" fill="{col}" fill-opacity="0.2" stroke="{col}" stroke-width="2.4" stroke-linejoin="round">'
                    f'<animate attributeName="points" calcMode="spline" keyTimes="{kt}" keySplines="{ks}" values="{zero};{zero};{fin};{fin};{zero}" dur="{dur:g}s" repeatCount="indefinite"/></polygon>\n')
        for i, v in enumerate(vals):
            x, y = pt(i, R * max(0, min(1, v / mx)))
            body.append(f'  <circle cx="{F(x)}" cy="{F(y)}" r="4" fill="{th["bg"]}" stroke="{col}" stroke-width="2">'
                        f'<animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;{T(a0 + 0.30)};{T(a0 + 0.36)};0.9;1" dur="{dur:g}s" repeatCount="indefinite"/></circle>')
        body.append("\n")
        sb.append(tdesc(f"series {si}", a0, a0 + 0.35))
    if len(series) > 1:
        x = cx - sum(len(s.get("name", "")) * 8 + 40 for s in series) / 2
        for si, s in enumerate(series):
            col = s.get("color") or palette[si % len(palette)]
            body.append(f'  <circle cx="{F(x + 6)}" cy="{F(H - 26)}" r="5" fill="{col}"/><text x="{F(x + 18)}" y="{F(H - 22)}" font-family="{FONT}" font-size="12" fill="{th["text"]}">{esc(s.get("name", ""))}</text>\n')
            x += len(s.get("name", "")) * 8 + 40
    return part("".join(body), W, H, sb, False, "Radar chart: " + ", ".join(axes))


THINGS_A = {"loader": build_loader, "logo": build_logo, "text": build_text, "gauge": build_gauge, "radar": build_radar}
