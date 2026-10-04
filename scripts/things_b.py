"""Non-diagram types (part 2): backdrop, icons, scene, counter, art.

Same contract as the other builders (build(spec, th, idp="") -> Part); all work inside compose.
Static-first: base attributes = a finished, good-looking still; animation only adds motion.
"""
import math
import random
import sys

from diagram_common import FONT, SANS, F, T, esc, gradient_colors, lerp_hex, part, tdesc


def _tz(spec, a=84, b=24):
    return spec.get("title_zone", a if spec.get("title") else b)


# ------------------------------------------------------------------ BACKDROP
def _wave_path(W, H, y0, amp, L):
    n = math.ceil((W + 2 * L) / (L / 2)) + 1
    d = [f"M{F(-L)},{F(y0)} Q{F(-L + L / 4)},{F(y0 - amp)} {F(-L + L / 2)},{F(y0)}"]
    for k in range(2, n + 1):
        d.append(f"T{F(-L + k * L / 2)},{F(y0)}")
    d.append(f"L{F(-L + n * L / 2)},{F(H)} L{F(-L)},{F(H)} Z")
    return " ".join(d)


def build_backdrop(spec, th, idp=""):
    dur = float(spec.get("dur", 12))
    var = spec.get("variant", "waves")
    W, H = spec.get("width", 1200), spec.get("height", 400)
    rng = random.Random(spec.get("seed", 7))
    sb = [f"type=backdrop  variant={var}  loop={dur:g}s  (ambient motion; static frame is already complete)"]
    body = []
    if var == "waves":
        layers = spec.get("layers", 4)
        for k in range(layers):
            y0 = H * (0.52 + 0.1 * k)
            amp = 16 + 7 * k
            L = W / (1.2 + 0.35 * k)
            col = lerp_hex(th["accent"], th["accent2"], k / max(1, layers - 1))
            d_ = dur * (1.1 + 0.45 * k)
            sgn = -1 if k % 2 == 0 else 1
            body.append(f'  <path d="{_wave_path(W, H, y0, amp, L)}" fill="{col}" fill-opacity="{0.22 + 0.1 * k:.2f}">'
                        f'<animateTransform attributeName="transform" type="translate" values="0 0;{F(sgn * L)} 0" dur="{d_:.1f}s" repeatCount="indefinite"/></path>\n')
    elif var == "stars":
        for i in range(spec.get("count", 90)):
            x, y, r = rng.uniform(0, W), rng.uniform(0, H), rng.choice([0.8, 1.0, 1.3, 1.8, 2.4])
            d_ = rng.uniform(2.5, 6)
            body.append(f'  <circle cx="{x:.0f}" cy="{y:.0f}" r="{r}" fill="{th["accent3"] if i % 7 == 0 else th["text_key"]}" opacity="0.55">'
                        f'<animate attributeName="opacity" values="0.15;0.95;0.15" dur="{d_:.1f}s" begin="{-rng.uniform(0, d_):.1f}s" repeatCount="indefinite"/></circle>\n')
        for k in range(2):
            y = rng.uniform(H * 0.1, H * 0.45)
            x = rng.uniform(W * 0.1, W * 0.5)
            b = -k * dur / 2
            body.append(f'  <g opacity="0"><animateTransform attributeName="transform" type="translate" values="0 0;{F(W * 0.35)} {F(H * 0.3)}" dur="{dur:g}s" begin="{b:g}s" repeatCount="indefinite" keyTimes="0;1"/>'
                        f'<animate attributeName="opacity" values="0;0;1;0;0" keyTimes="0;0.55;0.6;0.68;1" dur="{dur:g}s" begin="{b:g}s" repeatCount="indefinite"/>'
                        f'<line x1="{F(x)}" y1="{F(y)}" x2="{F(x - 70)}" y2="{F(y - 24)}" stroke="{th["text_key"]}" stroke-width="2" stroke-linecap="round" opacity="0.9"/>'
                        f'<circle cx="{F(x)}" cy="{F(y)}" r="2.6" fill="{th["text_key"]}"/></g>\n')
        sb.append("2 shooting stars, half a loop apart")
    elif var == "grid":
        sp = max(40, math.ceil(math.sqrt(W * H / 60) / 2) * 2)
        cols, rows = int(W // sp), int(H // sp)
        ox, oy = (W - (cols - 1) * sp) / 2, (H - (rows - 1) * sp) / 2
        cx, cy = W / 2, H / 2
        maxd = math.hypot(cx, cy)
        for r_ in range(rows):
            for c in range(cols):
                x, y = ox + c * sp, oy + r_ * sp
                delay = math.hypot(x - cx, y - cy) / maxd * 0.6 * dur
                body.append(f'  <circle cx="{F(x)}" cy="{F(y)}" r="2.2" fill="{th["accent"]}" opacity="0.4">'
                            f'<animate attributeName="opacity" values="0.32;0.32;0.95;0.32;0.32" keyTimes="0;0.15;0.3;0.5;1" dur="{dur:g}s" begin="{delay - dur:.2f}s" repeatCount="indefinite"/>'
                            f'<animate attributeName="r" values="2;2;4;2;2" keyTimes="0;0.15;0.3;0.5;1" dur="{dur:g}s" begin="{delay - dur:.2f}s" repeatCount="indefinite"/></circle>\n')
        sb.append(f"grid {cols}x{rows}: ripple travels outward from the centre (negative begin = distance delay)")
    elif var == "bubbles":
        for i in range(spec.get("count", 26)):
            r = rng.uniform(5, 26)
            x, y0 = rng.uniform(0, W), rng.uniform(0, H)
            d_ = rng.uniform(10, 22)
            dy0, dy1 = H + r + 10 - y0, -(y0 + r + 10)
            col = th["accent"] if i % 3 else th["accent3"]
            body.append(f'  <circle cx="{x:.0f}" cy="{y0:.0f}" r="{r:.0f}" fill="{col}" fill-opacity="0.07" stroke="{col}" stroke-opacity="0.45" stroke-width="1.4">'
                        f'<animateTransform attributeName="transform" type="translate" values="0 {dy0:.0f};0 {dy1:.0f}" dur="{d_:.1f}s" begin="{-rng.uniform(0, d_):.1f}s" repeatCount="indefinite"/>'
                        f'<animateTransform attributeName="transform" type="translate" additive="sum" values="0 0;{rng.uniform(8, 22):.0f} 0;0 0" dur="{d_ / 2.3:.1f}s" repeatCount="indefinite"/></circle>\n')
    elif var == "rain":
        for i in range(spec.get("count", 70)):
            x, y0 = rng.uniform(0, W), rng.uniform(0, H)
            d_ = rng.uniform(0.9, 1.9)
            ln = rng.uniform(12, 24)
            body.append(f'  <line x1="{x:.0f}" y1="{y0:.0f}" x2="{x - 5:.0f}" y2="{y0 + ln:.0f}" stroke="{th["accent3"]}" stroke-opacity="{rng.uniform(0.25, 0.7):.2f}" stroke-width="1.4" stroke-linecap="round">'
                        f'<animateTransform attributeName="transform" type="translate" values="0 {-y0 - 30:.0f};{-0.25 * (H + 60):.0f} {H - y0 + 30:.0f}" dur="{d_:.2f}s" begin="{-rng.uniform(0, d_):.2f}s" repeatCount="indefinite"/></line>\n')
    elif var == "mesh":
        cols = [th["accent"], th["accent2"], th["accent3"], th["loop"], th["accent"]]
        body.append("  <defs>" + "".join(f'<radialGradient id="{idp}mg{i}" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="{c}" stop-opacity="0.55"/><stop offset="1" stop-color="{c}" stop-opacity="0"/></radialGradient>' for i, c in enumerate(cols)) + "</defs>\n")
        for i in range(5):
            x, y = rng.uniform(0.1, 0.9) * W, rng.uniform(0.1, 0.9) * H
            rx, ry = W * rng.uniform(0.16, 0.28), H * rng.uniform(0.35, 0.6)
            d_ = rng.uniform(18, 34)
            body.append(f'  <ellipse cx="{x:.0f}" cy="{y:.0f}" rx="{rx:.0f}" ry="{ry:.0f}" fill="url(#{idp}mg{i})">'
                        f'<animateTransform attributeName="transform" type="translate" values="0 0;{rng.uniform(-90, 90):.0f} {rng.uniform(-60, 60):.0f};0 0" dur="{d_:.1f}s" repeatCount="indefinite"/></ellipse>\n')
    else:
        sys.exit("backdrop variant must be one of waves|stars|grid|bubbles|rain|mesh")
    if spec.get("heading"):
        body.append(f'  <text x="{F(W / 2)}" y="{F(H / 2)}" text-anchor="middle" font-family="{SANS}" font-size="{spec.get("heading_size", 56)}" font-weight="800" letter-spacing="-1" fill="{th["text_key"]}">{esc(spec["heading"])}</text>\n')
        if spec.get("subtitle"):
            body.append(f'  <text x="{F(W / 2)}" y="{F(H / 2 + 40)}" text-anchor="middle" font-family="{SANS}" font-size="20" fill="{th["muted"]}">{esc(spec["subtitle"])}</text>\n')
    return part("".join(body), W, H, sb, False, f"Animated backdrop ({var})")


# ------------------------------------------------------------------ ICONS
_LIN = ' calcMode="linear"'
_PPS = ' calcMode="spline" keySplines="0.45 0 0.55 1;0 0 1 1;0.45 0 0.55 1;0 0 1 1"'


def _anim(a, v, kt, p, extra=""):
    return f'<animate attributeName="{a}" values="{v}" keyTimes="{kt}" dur="{p}s" repeatCount="indefinite"{extra}/>'


def _atf(t, v, kt, p, extra=""):
    return f'<animateTransform attributeName="transform" type="{t}" values="{v}" keyTimes="{kt}" dur="{p}s" repeatCount="indefinite"{extra}/>'


def _i_check(th, p):
    return (f'<circle r="10" pathLength="1" fill="none" stroke="{th["accent"]}" stroke-width="1.8" transform="rotate(-90)">{_anim("stroke-dasharray", "0 1;1 1;1 1", "0;0.35;1", p)}</circle>'
            f'<path d="M-5,0.5 L-1.5,4 L5.5,-3.5" pathLength="1" fill="none" stroke="{th["accent3"]}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">{_anim("stroke-dasharray", "0 1;0 1;1 1;1 1", "0;0.3;0.6;1", p)}</path>')


def _i_cross(th, p):
    s = ""
    for k, d in enumerate(("M-5,-5 L5,5", "M5,-5 L-5,5")):
        a = 0.2 + 0.25 * k
        s += f'<path d="{d}" pathLength="1" fill="none" stroke="{th["accent"]}" stroke-width="2.2" stroke-linecap="round">{_anim("stroke-dasharray", "0 1;0 1;1 1;1 1", f"0;{a:.2f};{a + 0.25:.2f};1", p)}</path>'
    return f'<circle r="10" fill="none" stroke="{th["rail"]}" stroke-width="1.8"/>' + s


def _i_heart(th, p):
    return (f'<g>{_atf("scale", "1;1.18;1;1.1;1", "0;0.15;0.3;0.45;1", p)}'
            f'<path d="M0,7 C-11,-1 -7,-9 0,-3.5 C7,-9 11,-1 0,7 Z" fill="{th["accent"]}" fill-opacity="0.85" stroke="{th["accent3"]}" stroke-width="1.4" stroke-linejoin="round"/></g>')


def _i_bell(th, p):
    return (f'<g>{_atf("rotate", "0 0 -9;14 0 -9;-11 0 -9;7 0 -9;-4 0 -9;0 0 -9;0 0 -9", "0;0.1;0.2;0.3;0.4;0.5;1", p)}'
            f'<path d="M-7,6 C-7,-1 -5,-8 0,-8 C5,-8 7,-1 7,6 L9,8 H-9 Z" fill="{th["accent"]}" fill-opacity="0.18" stroke="{th["accent"]}" stroke-width="1.8" stroke-linejoin="round"/>'
            f'<circle cx="0" cy="11" r="2" fill="{th["accent3"]}"/></g>')


def _i_gear(th, p):
    teeth = "".join(f'<rect x="-1.8" y="-12" width="3.6" height="5" rx="1" transform="rotate({k * 45})" fill="{th["accent"]}"/>' for k in range(8))
    return (f'<g>{_atf("rotate", "0;360", "0;1", p * 3, _LIN)}{teeth}'
            f'<circle r="7.5" fill="none" stroke="{th["accent"]}" stroke-width="2"/><circle r="2.8" fill="{th["accent3"]}"/></g>')


def _i_download(th, p):
    return (f'<path d="M-8,9 H8" stroke="{th["rail"]}" stroke-width="2" stroke-linecap="round"/>'
            f'<g>{_atf("translate", "0 0;0 3;0 0;0 0", "0;0.3;0.55;1", p)}<path d="M0,-9 V3 M-5,-2 L0,3 L5,-2" fill="none" stroke="{th["accent"]}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></g>')


def _i_star(th, p):
    pts = " ".join(f"{11 * math.cos(math.radians(-90 + 36 * i)) * (1 if i % 2 == 0 else 0.45):.1f},{11 * math.sin(math.radians(-90 + 36 * i)) * (1 if i % 2 == 0 else 0.45):.1f}" for i in range(10))
    return (f'<g>{_atf("scale", "1;1.2;1;1", "0;0.25;0.5;1", p)}<polygon points="{pts}" fill="{th["accent"]}" fill-opacity="0.85" stroke="{th["accent3"]}" stroke-width="1.2" stroke-linejoin="round"/></g>'
            f'<circle cx="9" cy="-9" r="1.4" fill="{th["text_key"]}">{_anim("opacity", "0;1;0;0", "0;0.3;0.6;1", p)}</circle>'
            f'<circle cx="-10" cy="7" r="1.1" fill="{th["text_key"]}">{_anim("opacity", "0;0;1;0", "0;0.4;0.7;1", p)}</circle>')


def _i_playpause(th, p):
    play = "M-5,-7 L1,-3.5 L1,3.5 L-5,7 Z M1,-3.5 L7,0 L7,0 L1,3.5 Z"
    pause = "M-6,-7 L-2,-7 L-2,7 L-6,7 Z M2,-7 L6,-7 L6,7 L2,7 Z"
    return (f'<path d="{play}" fill="{th["accent"]}" stroke="{th["accent"]}" stroke-width="1.4" stroke-linejoin="round">'
            f'{_anim("d", f"{play};{pause};{pause};{play};{play}", "0;0.2;0.5;0.7;1", p, _PPS)}</path>')


def _i_sun(th, p):
    rays = "".join(f'<path d="M0,-12 V-8.5" transform="rotate({k * 45})" stroke="{th["accent3"]}" stroke-width="2" stroke-linecap="round"/>' for k in range(8))
    return (f'<g>{_atf("rotate", "0;360", "0;1", p * 4, _LIN)}{rays}</g>'
            f'<circle r="5.5" fill="{th["accent"]}">{_anim("r", "5.5;6.6;5.5", "0;0.5;1", p)}</circle>')


def _i_lock(th, p):
    return (f'<g>{_atf("translate", "0 0;0 -3;0 -3;0 0;0 0", "0;0.25;0.55;0.8;1", p)}<path d="M-4,-1 V-5 A4,4 0 0 1 4,-5 V-1" fill="none" stroke="{th["accent3"]}" stroke-width="2" stroke-linecap="round"/></g>'
            f'<rect x="-6.5" y="-1" width="13" height="10" rx="2.2" fill="{th["accent"]}" fill-opacity="0.2" stroke="{th["accent"]}" stroke-width="1.8"/><circle cy="4" r="1.3" fill="{th["accent"]}"/>')


def _i_wifi(th, p):
    s = f'<circle cx="0" cy="7" r="1.6" fill="{th["accent"]}"/>'
    for k, r in enumerate((5, 8.5, 12)):
        x = r * math.cos(math.radians(45))
        y = 7 - r * math.sin(math.radians(45))
        s += (f'<path d="M{-x:.1f},{y:.1f} A{r},{r} 0 0 1 {x:.1f},{y:.1f}" fill="none" stroke="{th["accent"]}" stroke-width="2" stroke-linecap="round" opacity="0.3">'
              f'{_anim("opacity", "0.25;0.25;1;0.25;0.25", f"0;{0.1 + 0.15 * k:.2f};{0.25 + 0.15 * k:.2f};{0.4 + 0.15 * k:.2f};1", p)}</path>')
    return s


def _i_bolt(th, p):
    return (f'<path d="M2,-11 L-5,2 H0 L-2,11 L6,-3 H1 Z" fill="{th["accent"]}" fill-opacity="0.9" stroke="{th["accent3"]}" stroke-width="1.2" stroke-linejoin="round">'
            f'{_anim("opacity", "1;1;0.35;1;0.6;1;1", "0;0.5;0.55;0.6;0.65;0.7;1", p)}</path>')


ICONS = {"check": _i_check, "cross": _i_cross, "heart": _i_heart, "bell": _i_bell, "gear": _i_gear, "download": _i_download,
         "star": _i_star, "playpause": _i_playpause, "sun": _i_sun, "lock": _i_lock, "wifi": _i_wifi, "bolt": _i_bolt}


def build_icons(spec, th, idp=""):
    items = spec.get("items") or [{"name": n, "label": n} for n in ICONS]
    for it in items:
        if it["name"] not in ICONS:
            sys.exit(f"icon '{it['name']}' unknown; choose from {sorted(ICONS)}")
    p = float(spec.get("period", 2.4))
    size = spec.get("size", 56)
    k = size / 24
    cols = spec.get("cols", min(len(items), 6))
    cell, margin = spec.get("cell", 120), 24
    tz = _tz(spec)
    rows = math.ceil(len(items) / cols)
    W, H = 2 * margin + cols * cell, tz + rows * (cell - 8) + margin
    sb = [f"type=icons  count={len(items)}  period={p}s  (independent loops; each icon rests between actions)"]
    body = []
    for i, it in enumerate(items):
        cx, cy = margin + (i % cols) * cell + cell / 2, tz + (i // cols) * (cell - 8) + 52
        body.append(f'  <g id="{idp}icon-{i}" transform="translate({F(cx)} {F(cy)}) scale({k:.3f})">{ICONS[it["name"]](th, p)}</g>')
        body.append(f'<text x="{F(cx)}" y="{F(cy + size / 2 + 26)}" text-anchor="middle" font-family="{FONT}" font-size="11" fill="{th["muted"]}">{esc(it.get("label", it["name"]))}</text>\n')
    return part("".join(body), W, H, sb, False, "Animated icons: " + ", ".join(i["name"] for i in items))


# ------------------------------------------------------------------ COUNTER (odometer)
def build_counter(spec, th, idp=""):
    dur = float(spec.get("dur", 8))
    items = spec["items"]
    size = spec.get("size", 48)
    dw, lh = size * 0.74, size * 1.25
    gap, margin = 70, 40
    tz = _tz(spec)
    ks = "0 0 1 1;0.16 1 0.3 1;0 0 1 1;0.4 0 1 1"
    sb = [f"type=counter  items={len(items)}  odometer roll 0.05-0.5, hold, reset 0.9-1.0 (base = final digits)"]
    layouts, total = [], 0.0
    for it in items:
        s = f"{int(it['value']):,}"
        wpx = len(it.get("prefix", "")) * dw + len(s) * dw + len(it.get("suffix", "")) * dw
        layouts.append((s, wpx))
        total += wpx
    W = 2 * margin + total + gap * (len(items) - 1)
    H = tz + lh + 80
    x = margin
    body = []
    for i, (it, (s, wpx)) in enumerate(zip(items, layouts)):
        y0 = tz
        cx = x
        pre, suf = it.get("prefix", ""), it.get("suffix", "")
        if pre:
            body.append(f'  <text x="{F(cx + dw / 2 * len(pre))}" y="{F(y0 + lh * 0.78)}" text-anchor="middle" font-family="{FONT}" font-size="{size}" font-weight="700" fill="{th["accent"]}">{esc(pre)}</text>\n')
            cx += len(pre) * dw
        j = 0
        for ch in s:
            if ch.isdigit():
                d = int(ch)
                cid = f"{idp}ck{i}-{j}"
                a0 = 0.05 + j * 0.03
                kt = f"0;{T(a0)};{T(a0 + 0.42)};0.9;1"
                fin = F(-(10 + d) * lh)
                stack = "".join(f'<text x="{F(cx + dw / 2)}" y="{F(y0 + (k_ + 0.78) * lh)}" text-anchor="middle" font-family="{FONT}" font-size="{size}" font-weight="700" fill="{th["text_key"]}">{k_ % 10}</text>' for k_ in range(20))
                body.append(f'  <rect x="{F(cx + 1)}" y="{F(y0)}" width="{F(dw - 2)}" height="{F(lh)}" rx="6" fill="{th["surface"]}" stroke="{th["stroke_dim"]}" stroke-width="1"/>'
                            f'<clipPath id="{cid}"><rect x="{F(cx)}" y="{F(y0)}" width="{F(dw)}" height="{F(lh)}"/></clipPath>'
                            f'<g clip-path="url(#{cid})"><g transform="translate(0 {fin})">'
                            f'<animateTransform attributeName="transform" type="translate" calcMode="spline" keyTimes="{kt}" keySplines="{ks}" values="0 0;0 0;0 {fin};0 {fin};0 0" dur="{dur:g}s" repeatCount="indefinite"/>{stack}</g></g>\n')
                j += 1
            else:
                body.append(f'  <text x="{F(cx + dw / 2)}" y="{F(y0 + lh * 0.78)}" text-anchor="middle" font-family="{FONT}" font-size="{size}" font-weight="700" fill="{th["muted"]}">{esc(ch)}</text>\n')
            cx += dw
        if suf:
            body.append(f'  <text x="{F(cx + dw / 2 * len(suf))}" y="{F(y0 + lh * 0.78)}" text-anchor="middle" font-family="{FONT}" font-size="{size}" font-weight="700" fill="{th["accent"]}">{esc(suf)}</text>\n')
        body.append(f'  <text x="{F(x + wpx / 2)}" y="{F(y0 + lh + 34)}" text-anchor="middle" font-family="{FONT}" font-size="14" letter-spacing="1" fill="{th["muted"]}">{esc(it.get("label", "").upper())}</text>\n')
        sb.append(tdesc(f"roll {it.get('label', i)}", 0.05, 0.5))
        x += wpx + gap
    return part("".join(body), W, H, sb, False, "Odometer counters: " + ", ".join(f'{i["value"]} {i.get("label", "")}' for i in items))


# ------------------------------------------------------------------ SCENE
def _stars(rng, W, H, th, n=50, hmax=0.7):
    s = []
    for i in range(n):
        d_ = rng.uniform(2.5, 6)
        s.append(f'<circle cx="{rng.uniform(0, W):.0f}" cy="{rng.uniform(0, H * hmax):.0f}" r="{rng.choice([0.8, 1.1, 1.5, 2]):.1f}" fill="{th["text_key"]}" opacity="0.5">'
                 f'<animate attributeName="opacity" values="0.15;0.95;0.15" dur="{d_:.1f}s" begin="{-rng.uniform(0, d_):.1f}s" repeatCount="indefinite"/></circle>')
    return "".join(s)


def _scene_rocket(W, H, th, dur, idp, rng):
    gid = f"{idp}sky"
    cx, gy = W / 2, H - 70
    py = gy - 62
    body = [f'  <linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{th["bg"]}"/><stop offset="1" stop-color="{th["surface_key"]}"/></linearGradient>'
            f'<rect width="{W}" height="{H}" fill="url(#{gid})"/>\n', "  " + _stars(rng, W, H, th), "\n",
            f'  <ellipse cx="{F(cx)}" cy="{F(H + 40)}" rx="{F(W * 0.7)}" ry="130" fill="{th["surface"]}"/><rect x="{F(cx - 60)}" y="{F(gy)}" width="120" height="8" rx="3" fill="{th["stroke_dim"]}"/>\n']
    smoke = ""
    for k in range(7):
        s0 = 0.20 + k * 0.025
        x = cx + rng.uniform(-30, 30)
        smoke += (f'<circle cx="{F(x)}" cy="{F(gy - 4)}" r="8" fill="{th["text"]}" opacity="0">'
                  f'<animate attributeName="r" values="8;8;{26 + k * 4};{40 + k * 4};40" keyTimes="0;{T(s0)};{T(s0 + 0.12)};{T(s0 + 0.35)};1" dur="{dur:g}s" repeatCount="indefinite"/>'
                  f'<animate attributeName="opacity" values="0;0;0.35;0;0" keyTimes="0;{T(s0)};{T(s0 + 0.06)};{T(s0 + 0.35)};1" dur="{dur:g}s" repeatCount="indefinite"/></circle>')
    body.append("  " + smoke + "\n")
    shake = "0 0;0 0;1.8 0;-1.8 0;1.8 0;-1.8 0;0 0;0 0"
    skt = "0;0.08;0.10;0.12;0.14;0.16;0.2;1"
    body.append(f'  <g id="{idp}rocket" transform="translate({F(cx)} {F(py)})">'
                f'<animateTransform attributeName="transform" type="translate" calcMode="spline" keyTimes="0;0.20;0.6;1" keySplines="0 0 1 1;0.55 0 1 0.45;0 0 1 1" values="{F(cx)} {F(py)};{F(cx)} {F(py)};{F(cx)} {F(py - H - 160)};{F(cx)} {F(py - H - 160)}" dur="{dur:g}s" repeatCount="indefinite"/>'
                f'<animate attributeName="opacity" values="1;1;1;0;0;1" keyTimes="0;0.2;0.58;0.62;0.9;1" dur="{dur:g}s" repeatCount="indefinite"/>'
                f'<g><animateTransform attributeName="transform" type="translate" values="{shake}" keyTimes="{skt}" dur="{dur:g}s" repeatCount="indefinite"/>'
                f'<g transform="translate(0 62)"><g><animateTransform attributeName="transform" type="scale" values="1 1;1 1.45;1 0.85;1 1.3;1 1" dur="0.5s" repeatCount="indefinite"/>'
                f'<path d="M-8,0 C-10,14 -3,30 0,44 C3,30 10,14 8,0 Z" fill="{th["accent3"]}"/><path d="M-4.5,0 C-5,9 -1,18 0,26 C1,18 5,9 4.5,0 Z" fill="{th["text_key"]}"/></g></g>'
                f'<path d="M-24,40 L-34,66 L-12,52 Z M24,40 L34,66 L12,52 Z" transform="translate(0 -14)" fill="{th["accent2"]}"/>'
                f'<path d="M0,-62 C22,-36 22,8 15,52 H-15 C-22,8 -22,-36 0,-62 Z" transform="translate(0 0)" fill="{th["text"]}" stroke="{th["stroke"]}" stroke-width="1.2"/>'
                f'<circle cx="0" cy="-20" r="9" fill="{th["accent"]}" stroke="{th["text_key"]}" stroke-width="2.4"/><rect x="-9" y="50" width="18" height="6" rx="2" fill="{th["stroke"]}"/>'
                f'</g></g>\n')
    return "".join(body), [tdesc("shake", 0.08, 0.20), tdesc("lift-off", 0.20, 0.60), tdesc("exhaust smoke", 0.20, 0.55)]


def _scene_coffee(W, H, th, dur, idp, rng):
    cx, ty = W / 2, H * 0.72
    gid = f"{idp}cupglow"
    body = [f'  <radialGradient id="{gid}" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="{th["accent"]}" stop-opacity="0.35"/><stop offset="1" stop-color="{th["accent"]}" stop-opacity="0"/></radialGradient>'
            f'<circle cx="{F(cx)}" cy="{F(ty - 40)}" r="{F(H * 0.42)}" fill="url(#{gid})"><animate attributeName="opacity" values="0.7;1;0.7" dur="{dur / 2:g}s" repeatCount="indefinite"/></circle>\n',
            f'  <rect x="0" y="{F(ty + 40)}" width="{W}" height="{F(H - ty - 40)}" fill="{th["surface"]}"/><rect x="0" y="{F(ty + 40)}" width="{W}" height="2" fill="{th["stroke_dim"]}"/>\n',
            f'  <g transform="translate({F(cx)} {F(ty)})">'
            f'<ellipse cx="0" cy="40" rx="104" ry="14" fill="#000" opacity="0.35"/><ellipse cx="0" cy="30" rx="96" ry="12" fill="{th["stroke"]}"/>'
            f'<path d="M-62,-30 H62 V10 C62,44 36,58 0,58 C-36,58 -62,44 -62,10 Z" fill="{th["accent3"]}"/>'
            f'<ellipse cx="0" cy="-30" rx="62" ry="11" fill="{th["accent2"]}"/><ellipse cx="0" cy="-30" rx="54" ry="8" fill="{th["bg"]}" opacity="0.65"/>'
            f'<path d="M62,-14 C100,-14 100,30 58,30" fill="none" stroke="{th["accent3"]}" stroke-width="12" stroke-linecap="round"/>']
    for k, x in enumerate((-26, 0, 26)):
        b = f"{-k * dur / 3:g}s"
        body.append(f'<path d="M{x},-42 Q{x - 10},-62 {x},-80 T{x},-118" fill="none" stroke="{th["text_key"]}" stroke-width="6" stroke-linecap="round" opacity="0">'
                    f'<animateTransform attributeName="transform" type="translate" values="0 0;{4 * (1 if k % 2 else -1)} -34" dur="{dur:g}s" begin="{b}" repeatCount="indefinite"/>'
                    f'<animate attributeName="opacity" values="0;0.65;0" keyTimes="0;0.3;1" dur="{dur:g}s" begin="{b}" repeatCount="indefinite"/></path>')
    body.append("</g>\n")
    return "".join(body), ["steam: 3 strands phased by negative begin (pre-rolled), warm glow breathes at dur/2"]


def _scene_ocean(W, H, th, dur, idp, rng):
    gid, sid = f"{idp}osky", f"{idp}osun"
    body = [f'  <linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{th["bg"]}"/><stop offset="1" stop-color="{th["accent2"]}" stop-opacity="0.45"/></linearGradient>'
            f'<radialGradient id="{sid}" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="{th["accent3"]}" stop-opacity="0.8"/><stop offset="1" stop-color="{th["accent3"]}" stop-opacity="0"/></radialGradient>'
            f'<rect width="{W}" height="{H}" fill="url(#{gid})"/>\n']
    hy = H * 0.55
    body.append(f'  <circle cx="{F(W * 0.72)}" cy="{F(hy - 40)}" r="120" fill="url(#{sid})"><animate attributeName="r" values="118;132;118" dur="{dur / 2:g}s" repeatCount="indefinite"/></circle><circle cx="{F(W * 0.72)}" cy="{F(hy - 40)}" r="34" fill="{th["accent3"]}"/>\n')
    for k in range(4):
        L = W / (1.4 + 0.4 * k)
        col = lerp_hex(th["accent"], th["bg"], 0.15 + 0.17 * k)
        sgn = 1 if k % 2 else -1
        body.append(f'  <path d="{_wave_path(W, H, hy + 22 * k, 12 + 5 * k, L)}" fill="{col}" fill-opacity="0.85"><animateTransform attributeName="transform" type="translate" values="0 0;{F(sgn * L)} 0" dur="{dur * (0.9 + 0.35 * k):.1f}s" repeatCount="indefinite"/></path>\n')
        if k == 1:
            bx, by = W * 0.32, hy + 22 * k + 6
            body.append(f'  <g transform="translate({F(bx)} {F(by)})"><g>'
                        f'<animateTransform attributeName="transform" type="translate" values="0 2;0 -5;0 2" dur="{dur / 3:g}s" repeatCount="indefinite" calcMode="spline" keyTimes="0;0.5;1" keySplines="0.45 0 0.55 1;0.45 0 0.55 1"/>'
                        f'<g><animateTransform attributeName="transform" type="rotate" values="-3 0 0;3 0 0;-3 0 0" dur="{dur / 3:g}s" repeatCount="indefinite" calcMode="spline" keyTimes="0;0.5;1" keySplines="0.45 0 0.55 1;0.45 0 0.55 1"/>'
                        f'<path d="M-46,0 H46 L32,18 H-32 Z" fill="{th["text"]}"/><path d="M0,-4 V-78" stroke="{th["stroke"]}" stroke-width="3"/>'
                        f'<path d="M4,-74 L40,-12 H4 Z" fill="{th["accent3"]}"/><path d="M-4,-62 L-30,-12 H-4 Z" fill="{th["accent"]}"/></g></g></g>\n')
    return "".join(body), ["layered waves (seamless translate by one wavelength), boat bobs and rocks at dur/3, sun glow breathes"]


def _scene_orbit(W, H, th, dur, idp, rng):
    cx, cy = W / 2, H / 2
    body = ["  " + _stars(rng, W, H, th, 60, 1.0) + "\n"]
    for r in (90, 150, 215):
        body.append(f'  <ellipse cx="{F(cx)}" cy="{F(cy)}" rx="{r}" ry="{r * 0.46:.0f}" fill="none" stroke="{th["rail"]}" stroke-width="1.2" stroke-dasharray="3 7"/>\n')
    body.append(f'  <circle cx="{F(cx)}" cy="{F(cy)}" r="64" fill="{th["accent"]}" opacity="0.2" filter="url(#glow)"><animate attributeName="opacity" values="0.15;0.3;0.15" dur="{dur / 2:g}s" repeatCount="indefinite"/></circle>'
                f'<circle cx="{F(cx)}" cy="{F(cy)}" r="34" fill="{th["accent"]}"/><circle cx="{F(cx - 8)}" cy="{F(cy - 8)}" r="12" fill="{th["accent3"]}" opacity="0.6"/>\n')
    for rx, rr, col, per, moon in ((90, 9, th["accent3"], 8, False), (150, 14, th["accent2"], 14, True), (215, 8, th["loop"], 22, False)):
        ry = rx * 0.46
        d = f"M{F(cx - rx)},{F(cy)} A{rx},{F(ry)} 0 1 1 {F(cx + rx)},{F(cy)} A{rx},{F(ry)} 0 1 1 {F(cx - rx)},{F(cy)}"
        g = (f'<circle r="{rr}" fill="{col}"><animateMotion dur="{per}s" repeatCount="indefinite" path="{d}" begin="{-rng.uniform(0, per):.1f}s"/></circle>')
        if moon:
            g = (f'<g><animateMotion dur="{per}s" repeatCount="indefinite" path="{d}" begin="-3s"/><circle r="{rr}" fill="{col}"/>'
                 f'<g><animateTransform attributeName="transform" type="rotate" values="0;360" dur="3s" repeatCount="indefinite"/><circle cx="{rr + 14}" r="4" fill="{th["text_key"]}"/></g></g>')
        body.append("  " + g + "\n")
    return "".join(body), ["planets on elliptical orbits (animateMotion), one moon on a nested rotation; ambient"]


SCENES = {"rocket": _scene_rocket, "coffee": _scene_coffee, "ocean": _scene_ocean, "orbit": _scene_orbit}


def build_scene(spec, th, idp=""):
    dur = float(spec.get("dur", 8))
    name = spec.get("scene", "rocket")
    if name not in SCENES:
        sys.exit(f"scene must be one of {sorted(SCENES)}")
    W, H = spec.get("width", 900), spec.get("height", 480)
    rng = random.Random(spec.get("seed", 7))
    b, sb = SCENES[name](W, H, th, dur, idp, rng)
    body = b
    if spec.get("caption"):
        body += f'  <text x="{F(W / 2)}" y="{F(H - 22)}" text-anchor="middle" font-family="{SANS}" font-size="18" fill="{th["muted"]}">{esc(spec["caption"])}</text>\n'
    return part(body, W, H, [f"type=scene  scene={name}  loop={dur:g}s"] + sb, False, f"Illustrated scene: {name}")


# ------------------------------------------------------------------ ART (generative)
def build_art(spec, th, idp=""):
    dur = float(spec.get("dur", 14))
    var = spec.get("variant", "mandala")
    S = spec.get("size", 520)
    W = H = S
    cx = cy = S / 2
    sb = [f"type=art  variant={var}  loop={dur:g}s  (generative, seeded; ambient)"]
    cols = gradient_colors(th, 5)
    body = []
    if var == "mandala":
        n = spec.get("petals", 12)
        for ring, (rr, color, sgn, per) in enumerate(((0.92, cols[0], 1, dur * 4), (0.66, cols[2], -1, dur * 3), (0.42, cols[4], 1, dur * 2))):
            R = S / 2 * rr
            pet = "".join(f'<ellipse cx="0" cy="{-R * 0.62:.1f}" rx="{R * 0.17:.1f}" ry="{R * 0.36:.1f}" transform="rotate({k * 360 / n:.2f})" fill="{color}" fill-opacity="0.09" stroke="{color}" stroke-width="1.6" stroke-opacity="0.8"/>' for k in range(n))
            body.append(f'  <g transform="translate({F(cx)} {F(cy)})"><g>'
                        f'<animateTransform attributeName="transform" type="rotate" values="0;{360 * sgn}" dur="{per:.0f}s" repeatCount="indefinite"/>'
                        f'<g><animateTransform attributeName="transform" type="scale" values="1;1.05;1" dur="{dur / 2:g}s" begin="{-ring * 2}s" repeatCount="indefinite" calcMode="spline" keyTimes="0;0.5;1" keySplines="0.45 0 0.55 1;0.45 0 0.55 1"/>{pet}</g></g></g>\n')
        body.append(f'  <circle cx="{F(cx)}" cy="{F(cy)}" r="{F(S * 0.05)}" fill="{th["accent"]}"><animate attributeName="r" values="{F(S * 0.045)};{F(S * 0.06)};{F(S * 0.045)}" dur="{dur / 4:g}s" repeatCount="indefinite"/></circle>\n')
    elif var == "lissajous":
        a_, b_ = spec.get("a", 3), spec.get("b", 2)
        A = S * 0.42
        pts = [(cx + A * math.sin(a_ * t + math.pi / 2), cy + A * math.sin(b_ * t)) for t in (i * 2 * math.pi / 360 for i in range(361))]
        d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        body.append(f'  <path d="{d}" pathLength="1" fill="none" stroke="{th["accent"]}" stroke-width="2.4" stroke-linejoin="round" stroke-opacity="0.9">'
                    f'<animate attributeName="stroke-dasharray" values="0 1;1 1;1 1;0 1" keyTimes="0;0.5;0.9;1" dur="{dur:g}s" repeatCount="indefinite"/></path>\n')
        for k in range(3):
            body.append(f'  <circle r="{6 - k * 1.6}" fill="{th["text_key"] if k == 0 else th["accent3"]}" opacity="{1 - k * 0.3}"><animateMotion dur="{dur / 2:g}s" begin="{-k * 0.12:.2f}s" repeatCount="indefinite" path="{d}"/></circle>\n')
    elif var == "spiral":
        pts = []
        turns = spec.get("turns", 5)
        for i in range(401):
            t = i / 400
            ang = t * turns * 2 * math.pi
            r = S * 0.46 * t
            pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
        d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        body.append(f'  <g><animateTransform attributeName="transform" type="rotate" values="0 {F(cx)} {F(cy)};360 {F(cx)} {F(cy)}" dur="{dur * 3:g}s" repeatCount="indefinite"/>'
                    f'<path d="{d}" pathLength="1" fill="none" stroke="{th["accent"]}" stroke-width="2.2" stroke-linecap="round"><animate attributeName="stroke-dasharray" values="0 1;1 1;1 1;0 1" keyTimes="0;0.55;0.9;1" dur="{dur:g}s" repeatCount="indefinite"/></path>')
        for i in range(24):
            x, y = pts[int(i / 24 * 400)]
            body.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{2 + i * 0.15:.1f}" fill="{cols[i % 5]}"><animate attributeName="opacity" values="0.2;1;0.2" dur="{dur / 2:g}s" begin="{-i * dur / 48:.2f}s" repeatCount="indefinite"/></circle>')
        body.append("</g>\n")
    elif var == "orbits":
        for k in range(3):
            rot = k * 60
            rx, ry = S * 0.44, S * 0.16
            d = f"M{F(cx - rx)},{F(cy)} A{F(rx)},{F(ry)} 0 1 1 {F(cx + rx)},{F(cy)} A{F(rx)},{F(ry)} 0 1 1 {F(cx - rx)},{F(cy)}"
            body.append(f'  <g transform="rotate({rot} {F(cx)} {F(cy)})"><path d="{d}" fill="none" stroke="{cols[k * 2 % 5]}" stroke-width="1.6" stroke-opacity="0.7"/>'
                        f'<circle r="7" fill="{cols[k * 2 % 5]}"><animateMotion dur="{dur / 2 + k:g}s" repeatCount="indefinite" path="{d}" begin="{-k * 1.7:.1f}s"/></circle></g>\n')
        body.append(f'  <circle cx="{F(cx)}" cy="{F(cy)}" r="{F(S * 0.05)}" fill="{th["accent"]}"/><circle cx="{F(cx)}" cy="{F(cy)}" r="{F(S * 0.05)}" fill="{th["accent"]}" filter="url(#glow)"><animate attributeName="opacity" values="0.3;0.9;0.3" dur="{dur / 4:g}s" repeatCount="indefinite"/></circle>\n')
    elif var == "flower":
        k_ = spec.get("k", 5)
        pts = []
        for i in range(721):
            th_ = i / 720 * math.pi * 2
            r = S * 0.44 * math.cos(k_ * th_)
            pts.append((cx + r * math.cos(th_), cy + r * math.sin(th_)))
        d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + " Z"
        body.append(f'  <g><animateTransform attributeName="transform" type="rotate" values="0 {F(cx)} {F(cy)};360 {F(cx)} {F(cy)}" dur="{dur * 4:g}s" repeatCount="indefinite"/>'
                    f'<path d="{d}" fill="{th["accent"]}" fill-opacity="0.12" stroke="{th["accent"]}" stroke-width="2" stroke-linejoin="round" pathLength="1"><animate attributeName="stroke-dasharray" values="0 1;1 1;1 1;0 1" keyTimes="0;0.5;0.9;1" dur="{dur:g}s" repeatCount="indefinite"/></path>'
                    f'<path d="{d}" fill="none" stroke="{th["accent3"]}" stroke-width="1" stroke-opacity="0.5" transform="translate({F(cx)} {F(cy)}) rotate(36) scale(0.7) translate({F(-cx)} {F(-cy)})"/></g>\n')
    else:
        sys.exit("art variant must be one of mandala|lissajous|spiral|orbits|flower")
    return part("".join(body), W, H, sb, False, f"Generative art ({var})")


THINGS_B = {"backdrop": build_backdrop, "icons": build_icons, "counter": build_counter, "scene": build_scene, "art": build_art}
