"""Shared helpers for gen_diagram.py / diagram_extra.py (themes, timing, glow, relay dots, defs).

Contract used by every builder:  build(spec, th, idp="") -> Part dict
    Part = dict(body=str, W=float, H=float, sb=[str], arrows=bool, desc=str)
  * body    SVG fragment (no <svg>, no defs, no background, no title eyebrow)
  * sb      storyboard lines; lines of the form  "at 0.123..0.456 label"  are used to pick frame times
  * idp     id prefix (needed so several parts can live in one SVG when composing)
All schedule animations carry keyTimes in 0..1 of the part's own loop; compose can remap them
into a time window of the master loop (apply_window).
"""
import math
import re
from xml.sax.saxutils import escape

THEMES = {
    "ember": dict(bg="#1F1B16", surface="#241d17", surface_key="#2a2018", stroke="#6f5a48", stroke_dim="#5c4a3b",
                  rail="#4a3a2e", arrow="#8a6f58", accent="#D97757", accent2="#B85C3C", accent3="#F5B095",
                  loop="#C98A8A", text="#EAD9CC", text_key="#FFF3EC", muted="#9c8675", eyebrow="#7d6857", dot="#FFF3EC"),
    "ocean": dict(bg="#0E1620", surface="#122030", surface_key="#162a40", stroke="#34506b", stroke_dim="#2b4358",
                  rail="#2a3f54", arrow="#5f86a8", accent="#4FB3FF", accent2="#2B7FD1", accent3="#9AD7FF",
                  loop="#7FA8E0", text="#D6E6F5", text_key="#F2F9FF", muted="#7D97AE", eyebrow="#5F7A91", dot="#F2F9FF"),
    "forest": dict(bg="#101712", surface="#16211A", surface_key="#1B2A20", stroke="#3F5C48", stroke_dim="#344C3B",
                   rail="#2E4535", arrow="#6E9A7B", accent="#5FD38D", accent2="#2FA564", accent3="#A9F0C3",
                   loop="#C9B26A", text="#DCEBDF", text_key="#F3FBF5", muted="#85A08C", eyebrow="#648069", dot="#F3FBF5"),
    "mono": dict(bg="#111214", surface="#17181B", surface_key="#1D1F23", stroke="#3A3D44", stroke_dim="#30333A",
                 rail="#2C2F36", arrow="#7B8190", accent="#E6E8EE", accent2="#A9AEBB", accent3="#FFFFFF",
                 loop="#9AA0AE", text="#D9DCE3", text_key="#FFFFFF", muted="#8B91A0", eyebrow="#666C7A", dot="#FFFFFF"),
    "paper": dict(bg="#FBF8F3", surface="#FFFFFF", surface_key="#FFF4EA", stroke="#CFC4B5", stroke_dim="#DDD3C5",
                  rail="#CBBFAE", arrow="#9C8A74", accent="#C4562F", accent2="#9A3F20", accent3="#E8855F",
                  loop="#B07A7A", text="#2B2621", text_key="#1B1713", muted="#7B6F63", eyebrow="#9C8F80", dot="#7A2E14"),
    "violet": dict(bg="#15121F", surface="#1C1830", surface_key="#241E3D", stroke="#4A4170", stroke_dim="#3C345C",
                   rail="#352E55", arrow="#8B7FC7", accent="#A78BFA", accent2="#7C5CE0", accent3="#D4C5FF",
                   loop="#F0A6CA", text="#E4DEFA", text_key="#F8F5FF", muted="#9A91C4", eyebrow="#6F66A0", dot="#F8F5FF"),
    "sunset": dict(bg="#1A1216", surface="#231A1F", surface_key="#2D1F26", stroke="#6B4655", stroke_dim="#573A47",
                   rail="#4A2F3B", arrow="#C98A9A", accent="#FF7A59", accent2="#E0457B", accent3="#FFC2A8",
                   loop="#FFD166", text="#F3DDE0", text_key="#FFF4F2", muted="#B58C98", eyebrow="#8A6270", dot="#FFF4F2"),
}
FONT = "'JetBrains Mono','Cascadia Mono','Menlo','Consolas',monospace"
SANS = "ui-sans-serif,system-ui,-apple-system,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif"


# ------------------------------------------------------------- small helpers
def F(v):
    s = f"{v:.1f}"
    return s[:-2] if s.endswith(".0") else s


def T(v):
    return f"{max(0.0, min(1.0, v)):.3f}"


def esc(s):
    return escape(str(s), {'"': "&quot;"})


def lerp_hex(a, b, t):
    a, b = a.lstrip("#"), b.lstrip("#")
    ca = [int(a[i:i + 2], 16) for i in (0, 2, 4)]
    cb = [int(b[i:i + 2], 16) for i in (0, 2, 4)]
    return "#%02X%02X%02X" % tuple(round(ca[i] + (cb[i] - ca[i]) * t) for i in range(3))


def gradient_colors(th, n):
    out = []
    for i in range(n):
        t = i / max(1, n - 1)
        out.append(lerp_hex(th["accent3"], th["accent"], t * 2) if t < 0.5 else lerp_hex(th["accent"], th["accent2"], (t - 0.5) * 2))
    return out


def tdesc(label, a, b):
    return f"at {a:.3f}..{b:.3f} {label}"


def card_w(label, sub="", lsz=18, pad=34, minw=120):
    return max(minw, math.ceil((max(len(label) * lsz * 0.6, len(sub) * 6.6) + pad) / 2) * 2)


def rect_exit(w, h, dx, dy):
    """Parameter t (distance from the rect centre) at which a ray with unit direction (dx,dy) leaves a w*h rect."""
    ts = []
    if abs(dx) > 1e-9:
        ts.append((w / 2) / abs(dx))
    if abs(dy) > 1e-9:
        ts.append((h / 2) / abs(dy))
    return min(ts)


def make_slots(n, start=0.02, dwell=0.03, tail=0.10, end=0.97):
    h = (end - start - tail - (n - 1) * dwell) / n
    if h < 0.04:
        raise SystemExit("too many hops for one loop; increase dur or reduce steps")
    if h < 0.07:
        import sys
        print(f"WARNING: each hop takes only {h:.3f} of the loop (very fast dots); raise dur, reduce columns/steps, or split with compose", file=sys.stderr)
    return [(start + i * (h + dwell), start + i * (h + dwell) + h) for i in range(n)], h


# ------------------------------------------------------------- animation builders
def pulse_frames(arrivals, rise=0.05, decay=0.11, peak=0.95):
    """Opacity keyframes: rises into every arrival, decays after it, ends at 0 with keyTimes ending at 1."""
    pts = [(0.0, 0.0)]
    arr = sorted(arrivals)
    prev_off = 0.0
    for i, a in enumerate(arr):
        rs = max(prev_off, a - rise)
        off = a + decay
        if i + 1 < len(arr):
            off = min(off, arr[i + 1] - rise - 0.005)
        off = min(off, 0.985)
        if off <= a:
            off = min(0.99, a + 0.01)
        pts += [(rs, 0.0), (a, peak), (off, 0.0)]
        prev_off = off
    pts.append((1.0, 0.0))
    out, last = [], 0.0
    for t, v in pts:
        t = max(t, last)
        out.append((t, v))
        last = t
    return ";".join(f"{v:g}" for _, v in out), ";".join(T(t) for t, _ in out)


def glow_overlay(x, y, w, h, rx, color, arrivals, dur, sw=2.6, rise=0.05, decay=0.11, peak=0.95):
    vals, kts = pulse_frames(arrivals, rise, decay, peak)
    return (f'<rect x="{F(x)}" y="{F(y)}" width="{F(w)}" height="{F(h)}" rx="{rx}" fill="none" stroke="{color}" '
            f'stroke-width="{sw}" filter="url(#glow)" opacity="0">'
            f'<animate attributeName="opacity" dur="{dur:g}s" repeatCount="indefinite" keyTimes="{kts}" values="{vals}"/></rect>')


def glow_dot(cx, cy, r, color, arrivals, dur, rise=0.04, decay=0.10, peak=0.9):
    vals, kts = pulse_frames(arrivals, rise, decay, peak)
    return (f'<circle cx="{F(cx)}" cy="{F(cy)}" r="{F(r + 1.5)}" fill="{color}" filter="url(#glow)" opacity="0">'
            f'<animate attributeName="opacity" dur="{dur:g}s" repeatCount="indefinite" keyTimes="{kts}" values="{vals}"/></circle>')


def relay_traveller(path, ts, te, color, dot, dur):
    """Halo + core dot parked invisible at the rail start until ts, travelling during [ts,te], parked at the end."""
    fade = min(0.02, (te - ts) / 4)
    mkt = f"0;{T(ts)};{T(te)};1"
    okt = f"0;{T(ts - 0.01)};{T(ts + fade)};{T(te - fade)};{T(te)};1"
    out = []
    for r, op, fill, flt, stroke in ((11, 0.5, color, ' filter="url(#glow)"', ""),
                                     (4.6, 1, dot, "", ' stroke="#ffffff" stroke-opacity="0.7" stroke-width="0.8"')):
        out.append(
            f'<circle r="{r}" fill="{fill}"{flt}{stroke} opacity="0">'
            f'<animateMotion dur="{dur:g}s" repeatCount="indefinite" calcMode="linear" keyTimes="{mkt}" keyPoints="0;0;1;1" path="{path}"/>'
            f'<animate attributeName="opacity" dur="{dur:g}s" repeatCount="indefinite" keyTimes="{okt}" values="0;0;{op};{op};0;0"/>'
            f'<animate attributeName="r" values="{r};{r * 1.18:.1f};{r}" dur="{dur / 4:g}s" repeatCount="indefinite"/></circle>')
    return "".join(out)


def rail(d, th, loop=False, arrows=False, dash=False, color=None, sw=1.5):
    col = color or (th["loop"] if loop else th["rail"])
    dsh = ' stroke-dasharray="5 6"' if (loop or dash) else ""
    mk = ' marker-end="url(#arrow)"' if arrows else ""
    return f'<path class="rail" d="{d}" fill="none" stroke="{col}" stroke-width="{sw}"{dsh}{mk}/>'


def node_card(th, idp, nid, x, y, w, h, label, sub, key, arrivals, dur, rx=12, lsz=18, accent=None, tag=None, color_text=None):
    """Static card + glow overlay + text. Returns SVG string."""
    accent = accent or th["accent"]
    fill = th["surface_key"] if key else th["surface"]
    stroke = accent if key else th["stroke"]
    sw = 1.7 if key else 1.1
    tcol = color_text or (th["text_key"] if key else th["text"])
    cx = x + w / 2
    if tag:
        ty, ly, sy = y + 17, y + 38, y + 56
    elif sub:
        ty, ly, sy = None, y + 28, y + 48
    else:
        ty, ly, sy = None, y + h / 2 + lsz * 0.33, None
    s = [f'<g id="{idp}{esc(nid)}"><rect x="{F(x)}" y="{F(y)}" width="{F(w)}" height="{F(h)}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>']
    s.append(glow_overlay(x, y, w, h, rx, accent, arrivals, dur))
    if tag:
        s.append(f'<text x="{F(cx)}" y="{F(ty)}" text-anchor="middle" font-family="{FONT}" font-size="10" fill="{accent}" letter-spacing="1.2">{esc(tag)}</text>')
    s.append(f'<text x="{F(cx)}" y="{F(ly)}" text-anchor="middle" font-family="{FONT}" font-size="{lsz}" font-weight="600" fill="{tcol}">{esc(label)}</text>')
    if sub and sy:
        s.append(f'<text x="{F(cx)}" y="{F(sy)}" text-anchor="middle" font-family="{FONT}" font-size="11" fill="{th["muted"]}" letter-spacing="0.4">{esc(sub)}</text>')
    s.append("</g>")
    return "".join(s)


def aurora(W, H, th, blur=0):
    """Three large soft gradient blobs drifting on 24/27/30 s loops (ambient, never in sync with the loop)."""
    flt = ' filter="url(#aurora)"' if blur else ""
    blobs = [(0.18, 0.36, 0.29, 0.64, "auWarm", 24, 0.04, 0.06),
             (0.81, 0.79, 0.30, 0.67, "auEmber", 30, -0.035, -0.05),
             (0.49, 0.19, 0.23, 0.48, "auAmber", 27, 0.025, 0.08)]
    s = [f"<g{flt}>"]
    for cx, cy, rx, ry, gid, d, dx, dy in blobs:
        s.append(f'<ellipse cx="{F(cx * W)}" cy="{F(cy * H)}" rx="{F(rx * W)}" ry="{F(ry * H)}" fill="url(#{gid})">'
                 f'<animateTransform attributeName="transform" type="translate" values="0 0;{F(dx * W)} {F(dy * H)};0 0" dur="{d}s" repeatCount="indefinite"/></ellipse>')
    s.append("</g>")
    return "".join(s)


def common_defs(th, arrows, blur=0):
    s = ["<defs>", '<filter id="glow" x="-70%" y="-70%" width="240%" height="240%"><feGaussianBlur stdDeviation="3.6"/></filter>']
    if blur:
        s.append(f'<filter id="aurora" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="{blur}"/></filter>')
    for gid, col, op in (("auWarm", th["accent"], 0.34), ("auEmber", th["accent2"], 0.28), ("auAmber", th["accent3"], 0.20)):
        s.append(f'<radialGradient id="{gid}" cx="50%" cy="50%" r="50%"><stop offset="0%" stop-color="{col}" stop-opacity="{op}"/>'
                 f'<stop offset="100%" stop-color="{col}" stop-opacity="0"/></radialGradient>')
    if arrows:
        s.append(f'<marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto" markerUnits="userSpaceOnUse">'
                 f'<path d="M0,0 L10,5 L0,10 Z" fill="{th["arrow"]}"/></marker>')
    s.append("</defs>")
    return "".join(s)


def header(W, H, spec, storyboard, default_desc):
    aria = esc(spec.get("aria") or spec.get("heading") or spec.get("title") or "animated diagram")
    title = esc(spec.get("title_text") or spec.get("heading") or spec.get("title") or "Diagram")
    desc = esc(spec.get("desc") or default_desc)
    sb = "\n".join("    " + ln for ln in storyboard)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {F(W)} {F(H)}" width="100%" preserveAspectRatio="xMidYMid meet" role="img" aria-label="{aria}">\n'
            f'  <title>{title}</title>\n  <desc>{desc}</desc>\n  <!--\n    GENERATED by gen_diagram.py - edit the spec, not this file.\n{sb}\n  -->\n')


def eyebrow(spec, th, x=40, y=50):
    t = spec.get("title")
    if not t:
        return ""
    return f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="13" fill="{th["eyebrow"]}" letter-spacing="1.6">{esc(t.upper())}</text>'


def part(body, W, H, sb, arrows=False, desc=""):
    return dict(body=body, W=W, H=H, sb=sb, arrows=arrows, desc=desc)


# ------------------------------------------------------------- composition support
_KT = re.compile(r'keyTimes="([^"]*)"')
_AT = re.compile(r"at ([\d.]+)\.\.([\d.]+)")


def apply_window(body, a, b):
    """Remap every schedule keyTimes list of a part into the window [a,b] of the master loop (first stays 0, last 1)."""
    if abs(a) < 1e-9 and abs(b - 1) < 1e-9:
        return body

    def rep(m):
        vals = [float(x) for x in m.group(1).split(";") if x.strip() != ""]
        out = []
        for i, t in enumerate(vals):
            if i == 0:
                out.append(0.0)
            elif i == len(vals) - 1 and abs(t - 1.0) < 1e-9:
                out.append(1.0)
            else:
                out.append(a + t * (b - a))
        last = 0.0
        for i, t in enumerate(out):
            out[i] = max(t, last)
            last = out[i]
        return 'keyTimes="' + ";".join(f"{x:.3f}" for x in out) + '"'
    return _KT.sub(rep, body)


def map_sb(lines, a, b):
    def rep(m):
        return f"at {a + float(m.group(1)) * (b - a):.3f}..{a + float(m.group(2)) * (b - a):.3f}"
    return [_AT.sub(rep, ln) for ln in lines]
