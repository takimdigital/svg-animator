"""Things, part 5: nine types for the gaps in the catalog: scatter, heatmap, funnel, venn, waveform, clock,
calendar, marquee, sprite.

Repo rules apply: computed timing, base state = finished graphic, refusals that name the fix, and a contract
docstring on every builder (tests/test_contracts.py checks it). Shared helpers: diagram_common.py.
"""
import calendar
import math
import random
import re
import sys
import xml.etree.ElementTree as ET

from diagram_common import FONT, SANS, F, T, esc, lerp_hex, make_slots, part, tdesc


def _nice(lo, hi, n=5):
    """A tidy axis: (low, high, step) that covers [lo, hi] with about n steps."""
    if lo == hi:
        hi = lo + 1
    raw = (hi - lo) / n
    mag = 10 ** math.floor(math.log10(raw))
    step = next(m * mag for m in (1, 2, 2.5, 5, 10) if m * mag >= raw)
    return math.floor(lo / step) * step, math.ceil(hi / step) * step, step


def build_scatter(spec, th, idp=""):
    """scatter: points on two numeric axes; points appear in order, and an optional trend line draws on.

    Fields:
      points (required; list of {x, y, label, color}, x and y numeric); trend (false; true draws a least-squares
      line); x_label; y_label; dur (loop seconds, default 8); title (eyebrow label); title_zone (84 if title else 24).
    Refuses:
      no points: 'scatter: needs at least one point'. A point without numeric x and y:
      'scatter: point N needs numeric x and y'.
    Base state:
      all points and the trend line are fully drawn; points appear by opacity steps and the trend draws on.
    Timing:
      points appear in list order, one slot each (make_slots); the trend line draws after the last point.
    Alternatives:
      axes are rounded to tidy steps (_nice), so the scale never shows an awkward maximum.
    Breaks if changed:
      a point's position must come from the same scale as the axis ticks; the trend uses the same points.
    Example:
      scatter-effort.json   Tests: tests/test_type_coverage.py.
    """
    pts = spec.get("points") or []
    if not pts:
        sys.exit("scatter: needs at least one point")
    for k, p in enumerate(pts):
        if not (isinstance(p.get("x"), (int, float)) and isinstance(p.get("y"), (int, float))):
            sys.exit(f"scatter: point {k + 1} needs numeric x and y")
    dur = float(spec.get("dur", 8))
    tz = spec.get("title_zone", 84 if spec.get("title") else 24)
    xs = [float(p["x"]) for p in pts]
    ys = [float(p["y"]) for p in pts]
    x0, x1, xs_step = _nice(min(xs), max(xs))
    y0, y1, ys_step = _nice(min(ys), max(ys))
    L, R, TOP, BOT = 80, 40, tz + 16, 60
    PW, PH = 860 - L - R, 340
    W, H = L + PW + R, TOP + PH + BOT

    def sx(v):
        return L + (v - x0) / (x1 - x0) * PW

    def sy(v):
        return TOP + PH - (v - y0) / (y1 - y0) * PH

    body = []
    for i in range(int(round((y1 - y0) / ys_step)) + 1):
        v = y0 + i * ys_step
        body.append(f'<path d="M{L},{F(sy(v))} H{L + PW}" stroke="{th["stroke_dim"]}" stroke-width="1" opacity="0.5"/>'
                    f'<text x="{L - 10}" y="{F(sy(v) + 4)}" text-anchor="end" font-family="{FONT}" font-size="11" fill="{th["muted"]}">{v:g}</text>')
    for i in range(int(round((x1 - x0) / xs_step)) + 1):
        v = x0 + i * xs_step
        body.append(f'<text x="{F(sx(v))}" y="{TOP + PH + 20}" text-anchor="middle" font-family="{FONT}" font-size="11" fill="{th["muted"]}">{v:g}</text>')
    body.append(f'<path d="M{L},{TOP} V{TOP + PH} H{L + PW}" stroke="{th["stroke"]}" stroke-width="1.2" fill="none"/>')
    if spec.get("x_label"):
        body.append(f'<text x="{L + PW}" y="{H - 14}" text-anchor="end" font-family="{FONT}" font-size="12" fill="{th["muted"]}">{esc(spec["x_label"])}</text>')
    if spec.get("y_label"):
        body.append(f'<text x="{L}" y="{TOP - 10}" font-family="{FONT}" font-size="12" fill="{th["muted"]}">{esc(spec["y_label"])}</text>')
    if spec.get("trend") and len(pts) >= 2:
        n = len(pts)
        mx, my = sum(xs) / n, sum(ys) / n
        den = sum((x - mx) ** 2 for x in xs)
        slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den if den else 0.0
        icpt = my - slope * mx
        d = f"M{F(sx(x0))},{F(sy(slope * x0 + icpt))} L{F(sx(x1))},{F(sy(slope * x1 + icpt))}"
        body.append(f'<path d="{d}" pathLength="1" fill="none" stroke="{th["accent3"]}" stroke-width="2" stroke-dasharray="1 1">'
                    f'<animate attributeName="stroke-dasharray" calcMode="discrete" values="0 1;1 1;1 1" '
                    f'keyTimes="0;0.9;1" dur="{dur:g}s" repeatCount="indefinite"/></path>')
    win, _ = make_slots(len(pts))
    for k, p in enumerate(pts):
        on, _off = win[k]
        col = p.get("color") or th["accent"]
        body.append(f'<circle cx="{F(sx(xs[k]))}" cy="{F(sy(ys[k]))}" r="6" fill="{col}" stroke="{th["bg"]}" stroke-width="1.5">'
                    f'<animate attributeName="opacity" calcMode="discrete" values="0;1" keyTimes="0;{T(on)}" '
                    f'dur="{dur:g}s" repeatCount="indefinite"/></circle>')
        if p.get("label"):
            body.append(f'<text x="{F(sx(xs[k]) + 10)}" y="{F(sy(ys[k]) - 8)}" font-family="{FONT}" font-size="12" fill="{th["text"]}" opacity="1">{esc(str(p["label"]))}</text>')
    sb = [f"type=scatter  points={len(pts)}  x {x0:g}..{x1:g}  y {y0:g}..{y1:g}"]
    sb += [tdesc(f"point {k + 1}", *win[k]) for k in range(len(pts))]
    return part("".join(body), W, H, sb, False, "Scatter plot of " + str(len(pts)) + " points")


def build_heatmap(spec, th, idp=""):
    """heatmap: a grid of values as colours; cells appear in a diagonal wave and show their value.

    Fields:
      rows (required; list of row labels); cols (required; list of column labels); values (required; one list
      per row, each as long as cols); cell (cell size in px, default 52); dur (loop seconds, default 8);
      title (eyebrow label); title_zone (84 if title else 24).
    Refuses:
      no rows or no cols: 'heatmap: needs rows and cols'. values with a different row count:
      'heatmap: values has N rows, expected M'. A row with the wrong length:
      'heatmap: row N has X values, expected Y'.
    Base state:
      the full grid in its final colours is the base state; cells fade in by opacity steps.
    Timing:
      a diagonal wave: cells appear in order of their row plus column index, over the first 60 % of the loop.
    Alternatives:
      colour runs from accent3 (lowest) to accent2 (highest) linearly, so the scale comes from the theme.
    Breaks if changed:
      each cell's colour must come from the same min and max as the legend; values are shown on the cells, so
      long numbers need a larger cell.
    Example:
      heatmap-week.json   Tests: tests/test_type_coverage.py.
    """
    rows = spec.get("rows") or []
    cols = spec.get("cols") or []
    vals = spec.get("values") or []
    if not rows or not cols:
        sys.exit("heatmap: needs rows and cols")
    if len(vals) != len(rows):
        sys.exit(f"heatmap: values has {len(vals)} rows, expected {len(rows)}")
    for k, r in enumerate(vals):
        if len(r) != len(cols):
            sys.exit(f"heatmap: row {k + 1} has {len(r)} values, expected {len(cols)}")
    flat = [float(v) for r in vals for v in r]
    lo, hi = min(flat), max(flat)
    cell = int(spec.get("cell", 52))
    dur = float(spec.get("dur", 8))
    tz = spec.get("title_zone", 84 if spec.get("title") else 24)
    LW, TOP = 130, 40
    W = LW + len(cols) * cell + 40
    H = tz + TOP + len(rows) * cell + 30
    body = []
    for j, c in enumerate(cols):
        body.append(f'<text x="{F(LW + j * cell + cell / 2)}" y="{tz + 24}" text-anchor="middle" font-family="{FONT}" font-size="12" fill="{th["muted"]}">{esc(str(c))}</text>')
    R, C = len(rows), len(cols)
    for i, r in enumerate(rows):
        body.append(f'<text x="{LW - 12}" y="{F(tz + TOP + i * cell + cell / 2 + 4)}" text-anchor="end" font-family="{FONT}" font-size="12" fill="{th["muted"]}">{esc(str(r))}</text>')
        for j in range(C):
            v = float(vals[i][j])
            t = 0.0 if hi == lo else (v - lo) / (hi - lo)
            on = (i + j) / (R + C) * 0.6
            x, y = LW + j * cell, tz + TOP + i * cell
            body.append(f'<rect x="{F(x + 2)}" y="{F(y + 2)}" width="{cell - 4}" height="{cell - 4}" rx="6" fill="{lerp_hex(th["accent3"], th["accent2"], t)}" opacity="1">'
                        f'<animate attributeName="opacity" calcMode="discrete" values="0;1" keyTimes="0;{T(on)}" dur="{dur:g}s" repeatCount="indefinite"/></rect>'
                        f'<text x="{F(x + cell / 2)}" y="{F(y + cell / 2 + 4)}" text-anchor="middle" font-family="{FONT}" font-size="12" fill="{th["text_key"]}">{v:g}</text>')
    sb = [f"type=heatmap  {R} x {C}  range {lo:g}..{hi:g}"]
    return part("".join(body), W, H, sb, False, f"Heatmap {R} by {C}")


def build_funnel(spec, th, idp=""):
    """funnel: stages that shrink from the top; each stage slides in, and the drop between stages is shown.

    Fields:
      stages (required; list of {label, value}, each value positive and not larger than the stage before);
      dur (loop seconds, default 8); title (eyebrow label); title_zone (84 if title else 24).
    Refuses:
      no stages: 'funnel: needs at least one stage'. A value that is not positive:
      'funnel: stage <label> must have a positive value'. A stage larger than the one before it:
      'funnel: stage <label> is larger than the stage before it; funnels only shrink'.
    Base state:
      every stage is drawn at full width; the slide-in starts from zero width.
    Timing:
      stages scale in top to bottom, one slot each (make_slots).
    Alternatives:
      widths are proportional to value, so the drop is visible without reading the labels.
    Breaks if changed:
      stage values must not increase (refused); the drop percentages are computed from the same values.
    Example:
      funnel-sales.json   Tests: tests/test_type_coverage.py.
    """
    stages = spec.get("stages") or []
    if not stages:
        sys.exit("funnel: needs at least one stage")
    prev = None
    for s in stages:
        v = float(s.get("value", 0))
        name = s.get("label", "?")
        if v <= 0:
            sys.exit(f"funnel: stage {name} must have a positive value")
        if prev is not None and v > prev:
            sys.exit(f"funnel: stage {name} is larger than the stage before it; funnels only shrink")
        prev = v
    dur = float(spec.get("dur", 8))
    tz = spec.get("title_zone", 84 if spec.get("title") else 24)
    MAXW, BAR, GAP = 620, 54, 22
    W = 860
    H = int(tz + 20 + len(stages) * (BAR + GAP) + 20)
    cx = W / 2
    first = float(stages[0]["value"])
    win, _ = make_slots(len(stages))
    body = []
    for k, s in enumerate(stages):
        v = float(s["value"])
        w = v / first * MAXW
        y = tz + 20 + k * (BAR + GAP)
        on, off = win[k]
        col = lerp_hex(th["accent3"], th["accent2"], k / max(1, len(stages) - 1))
        mid_y = y + BAR / 2 + 6
        body.append(f'<rect x="{F(cx - w / 2)}" y="{F(y)}" width="{F(w)}" height="{BAR}" rx="8" fill="{col}">'
                    f'<animateTransform attributeName="transform" type="scale" calcMode="spline" additive="sum" '
                    f'keyTimes="0;{T(on)};{T(off)};1" keySplines="0.16 1 0.3 1;0 0 1 1;0 0 1 1" values="0 1;0 1;1 1;1 1" dur="{dur:g}s" repeatCount="indefinite"/>'
                    f'</rect>')
        body.append(f'<text x="{F(cx - MAXW / 2 - 14)}" y="{F(mid_y)}" text-anchor="end" font-family="{SANS}" font-size="15" font-weight="700" fill="{th["text_key"]}">{esc(str(s.get("label", "")))}</text>'
                    f'<text x="{F(cx + w / 2 + 10)}" y="{F(mid_y)}" font-family="{FONT}" font-size="14" fill="{th["text"]}">{v:g}</text>')
        if k > 0:
            drop = round((1 - v / float(stages[k - 1]["value"])) * 100)
            body.append(f'<text x="{F(cx + MAXW / 2 + 16)}" y="{F(y - GAP / 2 + 4)}" font-family="{FONT}" font-size="12" fill="{th["muted"]}">-{drop}%</text>')
    sb = [f"type=funnel  stages={len(stages)}  scale-in top to bottom"]
    sb += [tdesc(f"stage {k + 1}", *win[k]) for k in range(len(stages))]
    return part("".join(body), W, H, sb, False, "Funnel: " + " > ".join(str(s.get("label", "")) for s in stages))


def build_venn(spec, th, idp=""):
    """venn: two overlapping circles, sized by their values; the shared part is labelled.

    Fields:
      sets (required; exactly two of {label, size}, size positive); overlap (0.3; the shared share of the smaller
      circle's diameter, from 0 to 1); both (label drawn in the shared part); dur (loop seconds, default 8);
      title (eyebrow label); title_zone (84 if title else 24).
    Refuses:
      a number of sets other than two: 'venn: supports exactly 2 sets; three sets need an exact-area solver'.
      a size that is not positive: 'venn: set <label> needs a positive size'. An overlap outside 0-1:
      'venn: overlap must be between 0 and 1'.
    Base state:
      both circles and the shared label are fully drawn; the animation fades them in one after another.
    Timing:
      circle one, circle two, then the shared label, one slot each (make_slots).
    Alternatives:
      the overlap is an input, not solved from areas: exact area solving needs an iterative solver, and most
      uses only need the ordering and rough shares, so the honest input is the overlap fraction.
    Breaks if changed:
      circle radii follow the square root of size (area is proportional to size); the centre distance is derived
      from the overlap, so changing one without the other breaks the picture.
    Example:
      venn-skills.json   Tests: tests/test_type_coverage.py.
    """
    sets = spec.get("sets") or []
    if len(sets) != 2:
        sys.exit("venn: supports exactly 2 sets; three sets need an exact-area solver")
    for s in sets:
        if not (isinstance(s.get("size"), (int, float)) and s["size"] > 0):
            sys.exit(f"venn: set {s.get('label', '?')} needs a positive size")
    overlap = float(spec.get("overlap", 0.3))
    if not (0 <= overlap <= 1):
        sys.exit("venn: overlap must be between 0 and 1")
    dur = float(spec.get("dur", 8))
    tz = spec.get("title_zone", 84 if spec.get("title") else 24)
    rmax = 150.0
    s_max = max(float(s["size"]) for s in sets)
    r1, r2 = (rmax * math.sqrt(float(s["size"]) / s_max) for s in sets)
    d = r1 + r2 - overlap * 2 * min(r1, r2)
    W, H = 860, int(tz + 2 * rmax + 40)
    cy = tz + rmax + 20
    cx = W / 2
    x1, x2 = cx - d / 2, cx + d / 2
    cols = [th["accent"], th["accent3"]]
    win, _ = make_slots(3, dwell=0.03, tail=0.1)
    body = []
    for k, (r, xc, s) in enumerate(((r1, x1, sets[0]), (r2, x2, sets[1]))):
        on, _off = win[k]
        body.append(f'<circle cx="{F(xc)}" cy="{F(cy)}" r="{F(r)}" fill="{cols[k]}" fill-opacity="0.28" stroke="{cols[k]}" stroke-width="2" opacity="1">'
                    f'<animate attributeName="opacity" calcMode="discrete" values="0;1" keyTimes="0;{T(on)}" dur="{dur:g}s" repeatCount="indefinite"/></circle>'
                    f'<text x="{F(xc + (-r * 0.55 if k == 0 else r * 0.55))}" y="{F(cy - r - 10)}" text-anchor="middle" font-family="{SANS}" font-size="16" font-weight="700" fill="{th["text_key"]}">{esc(str(s.get("label", "")))}</text>')
    on, _off = win[2]
    shared = spec.get("both")
    if shared:
        body.append(f'<text x="{F(cx)}" y="{F(cy + 6)}" text-anchor="middle" font-family="{SANS}" font-size="14" font-weight="600" fill="{th["text_key"]}" opacity="1">'
                    f'{esc(str(shared))}<animate attributeName="opacity" calcMode="discrete" values="0;1" keyTimes="0;{T(on)}" dur="{dur:g}s" repeatCount="indefinite"/></text>')
    sb = [f"type=venn  sets=2  overlap={overlap:g}"]
    sb += [tdesc(f"circle {k + 1}", *win[k]) for k in range(2)] + [tdesc("shared label", *win[2])]
    return part("".join(body), W, H, sb, False, "Venn diagram: " + " and ".join(str(s.get("label", "")) for s in sets))


def build_waveform(spec, th, idp=""):
    """waveform: a row of bars showing a signal; bars grow from the centre outward.

    Fields:
      samples (list of numbers; any scale, shown relative to the largest absolute value), or generate
      ({kind: 'sine' or 'noise', n: 64, seed: 7}); dur (loop seconds, default 8); title (eyebrow label);
      title_zone (84 if title else 24).
    Refuses:
      neither samples nor generate: 'waveform: needs samples or generate'. A sample that is not a number:
      'waveform: sample N is not a number'. generate.kind other than sine or noise:
      'waveform: generate.kind must be sine or noise'.
    Base state:
      all bars at their final height; the grow-in starts from zero.
    Timing:
      bars grow from the centre outward, one slot each (make_slots), so the middle reacts first.
    Alternatives:
      noise is seeded, so the same spec always draws the same bars (reproducible examples).
    Breaks if changed:
      bar heights are relative to the largest sample; changing the seed changes every bar.
    Example:
      waveform-signal.json   Tests: tests/test_type_coverage.py.
    """
    samples = spec.get("samples")
    gen = spec.get("generate")
    if samples is None and gen is None:
        sys.exit("waveform: needs samples or generate")
    if samples is None:
        kind = gen.get("kind", "sine")
        n = int(gen.get("n", 64))
        if kind == "sine":
            samples = [math.sin(2 * math.pi * 3 * i / n) * (0.6 + 0.4 * math.sin(2 * math.pi * i / n)) for i in range(n)]
        elif kind == "noise":
            rng = random.Random(int(gen.get("seed", 7)))
            samples = [rng.uniform(-1, 1) for _ in range(n)]
        else:
            sys.exit("waveform: generate.kind must be sine or noise")
    for k, v in enumerate(samples):
        if not isinstance(v, (int, float)):
            sys.exit(f"waveform: sample {k + 1} is not a number")
    dur = float(spec.get("dur", 8))
    tz = spec.get("title_zone", 84 if spec.get("title") else 24)
    n = len(samples)
    peak = max(abs(float(v)) for v in samples) or 1.0
    W, H = 860, int(tz + 300)
    mid = tz + 150
    slot_w = (W - 80) / n
    bw = slot_w * 0.7
    order = sorted(range(n), key=lambda i: abs(i - (n - 1) / 2))
    rank = {i: r for r, i in enumerate(order)}
    waves = 8
    win, _ = make_slots(waves, dwell=0.01, tail=0.1)
    body = [f'<path d="M40,{F(mid)} H{W - 40}" stroke="{th["stroke_dim"]}" stroke-width="1" opacity="0.6"/>']
    for i, v in enumerate(samples):
        h = abs(float(v)) / peak * 130
        x = 40 + i * slot_w + (slot_w - bw) / 2
        on, _off = win[min(waves - 1, rank[i] * waves // n)]
        col = th["accent"] if float(v) >= 0 else th["accent2"]
        body.append(f'<rect x="{F(x)}" y="{F(mid - h)}" width="{F(bw)}" height="{F(2 * h)}" rx="2" fill="{col}">'
                    f'<animate attributeName="height" calcMode="spline" keyTimes="0;{T(on)};1" keySplines="0.16 1 0.3 1;0 0 1 1" '
                    f'values="0;0;{F(2 * h)}" dur="{dur:g}s" repeatCount="indefinite"/>'
                    f'<animate attributeName="y" calcMode="spline" keyTimes="0;{T(on)};1" keySplines="0.16 1 0.3 1;0 0 1 1" '
                    f'values="{F(mid)};{F(mid)};{F(mid - h)}" dur="{dur:g}s" repeatCount="indefinite"/></rect>')
    sb = [f"type=waveform  samples={n}  peak={peak:g}  bars grow from the centre in {waves} waves"]
    return part("".join(body), W, H, sb, False, f"Waveform of {n} samples")


def build_clock(spec, th, idp=""):
    """clock: an analogue clock face at a given time; the second hand sweeps one revolution per loop.

    Fields:
      time (required; 'HH:MM', 24-hour); labels (true; numbers at 12, 3, 6 and 9); dur (loop seconds for one
      revolution of the second hand, default 12); title (eyebrow label); title_zone (84 if title else 24).
    Refuses:
      a time that does not look like HH:MM, or out of range: 'clock: time must look like HH:MM (24-hour)'.
    Base state:
      hour and minute hands at the given time; the second hand at 12.
    Timing:
      the second hand rotates linearly, one revolution per dur; nothing else moves.
    Alternatives:
      the hour hand is placed between numbers (it moves with the minutes), which is how a real face looks.
    Breaks if changed:
      the rotation centre must be the face centre; the hand angles are derived from the time, so a wrong formula
      shows the wrong time in the still frame.
    Example:
      clock-meeting.json   Tests: tests/test_type_coverage.py.
    """
    tstr = str(spec.get("time", "10:10"))
    m = re.fullmatch(r"(\d{1,2}):(\d{2})", tstr)
    if not m or int(m.group(1)) > 23 or int(m.group(2)) > 59:
        sys.exit("clock: time must look like HH:MM (24-hour)")
    h, mi = int(m.group(1)), int(m.group(2))
    dur = float(spec.get("dur", 12))
    tz = spec.get("title_zone", 84 if spec.get("title") else 24)
    R = 150
    cx, cy = 260, tz + R + 16
    W, H = 520, int(cy + R + 30)
    hour_a = ((h % 12) + mi / 60) * 30
    min_a = mi * 6
    body = [f'<circle cx="{cx}" cy="{F(cy)}" r="{R}" fill="{th["surface"]}" stroke="{th["stroke"]}" stroke-width="2"/>']
    for k in range(12):
        a = math.radians(k * 30)
        r1, r2 = R - 16, R - 4
        body.append(f'<path d="M{F(cx + r1 * math.sin(a))},{F(cy - r1 * math.cos(a))} L{F(cx + r2 * math.sin(a))},{F(cy - r2 * math.cos(a))}" stroke="{th["muted"]}" stroke-width="2"/>')
    if spec.get("labels", True):
        for k, lab in ((0, "12"), (3, "3"), (6, "6"), (9, "9")):
            a = math.radians(k * 30)
            body.append(f'<text x="{F(cx + (R - 34) * math.sin(a))}" y="{F(cy - (R - 34) * math.cos(a) + 6)}" text-anchor="middle" font-family="{FONT}" font-size="18" font-weight="700" fill="{th["text_key"]}">{lab}</text>')

    def hand(angle, length, width, col, extra=""):
        a = math.radians(angle)
        x2, y2 = cx + length * math.sin(a), cy - length * math.cos(a)
        return f'<path d="M{cx},{cy} L{F(x2)},{F(y2)}" stroke="{col}" stroke-width="{width}" stroke-linecap="round" fill="none"{extra}/>'

    body.append(hand(hour_a, R * 0.5, 7, th["text_key"]))
    body.append(hand(min_a, R * 0.8, 4, th["text"]))
    body.append(f'<g><animateTransform attributeName="transform" type="rotate" values="0 {cx} {F(cy)};360 {cx} {F(cy)}" dur="{dur:g}s" repeatCount="indefinite"/>'
                + hand(0, R * 0.9, 2, th["accent"]) + '</g>')
    body.append(f'<circle cx="{cx}" cy="{F(cy)}" r="6" fill="{th["accent"]}"/>')
    sb = [f"type=clock  time={h:02d}:{mi:02d}  second hand: one revolution per {dur:g} s"]
    return part("".join(body), W, H, sb, False, f"Analogue clock at {h:02d}:{mi:02d}")


def build_calendar(spec, th, idp=""):
    """calendar: one month as a grid; days appear in reading order, highlighted days pulse, events show a dot.

    Fields:
      year (2026); month (1-12, default 10); highlight (list of day numbers); events (list of {day, label});
      week_start ('mon' default, or 'sun'); dur (loop seconds, default 8); title (eyebrow label);
      title_zone (84 if title else 24).
    Refuses:
      a month outside 1-12: 'calendar: month must be 1 to 12'. A highlighted day not in the month:
      'calendar: day N is not in this month'.
    Base state:
      the full month is drawn; days appear by opacity steps, highlighted days are drawn in the highlight colour.
    Timing:
      days appear in reading order over the first 70 % of the loop; highlighted days pulse at the end.
    Alternatives:
      the calendar module supplies the weeks, so leap years and month lengths are never hand-coded.
    Breaks if changed:
      the first weekday must match week_start; a highlighted day must exist in the month (refused).
    Example:
      calendar-launch.json   Tests: tests/test_type_coverage.py.
    """
    year = int(spec.get("year", 2026))
    month = int(spec.get("month", 10))
    if not (1 <= month <= 12):
        sys.exit("calendar: month must be 1 to 12")
    weeks = calendar.Calendar(firstweekday=6 if spec.get("week_start", "mon") == "sun" else 0).monthdayscalendar(year, month)
    in_month = {d for w in weeks for d in w if d}
    hl = {int(d) for d in spec.get("highlight", [])}
    for d in sorted(hl):
        if d not in in_month:
            sys.exit(f"calendar: day {d} is not in this month")
    events = {int(e["day"]): e.get("label", "") for e in spec.get("events", [])}
    dur = float(spec.get("dur", 8))
    tz = spec.get("title_zone", 84 if spec.get("title") else 24)
    CELL = 96
    W = 7 * CELL + 40
    H = int(tz + 50 + len(weeks) * CELL + 20)
    names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"] if spec.get("week_start", "mon") != "sun" else ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    body = []
    for j, nm in enumerate(names):
        body.append(f'<text x="{F(20 + j * CELL + CELL / 2)}" y="{tz + 24}" text-anchor="middle" font-family="{FONT}" font-size="12" fill="{th["muted"]}">{nm}</text>')
    days_order = [d for w in weeks for d in w if d]
    win, _ = make_slots(len(weeks), dwell=0.01, tail=0.1)
    for i, w in enumerate(weeks):
        for j, d in enumerate(w):
            if not d:
                continue
            x, y = 20 + j * CELL, tz + 40 + i * CELL
            on, _off = win[i]
            is_hl = d in hl
            fill = th["accent2"] if is_hl else th["surface"]
            body.append(f'<rect x="{x + 4}" y="{F(y + 4)}" width="{CELL - 8}" height="{CELL - 8}" rx="10" fill="{fill}" stroke="{th["stroke_dim"]}" stroke-width="1" opacity="1">'
                        f'<animate attributeName="opacity" calcMode="discrete" values="0;1" keyTimes="0;{T(on)}" dur="{dur:g}s" repeatCount="indefinite"/></rect>'
                        f'<text x="{x + 14}" y="{F(y + 28)}" font-family="{FONT}" font-size="14" font-weight="{"700" if is_hl else "400"}" fill="{th["text_key"] if is_hl else th["text"]}" opacity="1">{d}</text>')
            if d in events:
                body.append(f'<circle cx="{x + CELL - 18}" cy="{F(y + 18)}" r="4" fill="{th["accent3"]}"/>'
                            f'<text x="{x + 14}" y="{F(y + CELL - 16)}" font-family="{FONT}" font-size="10" fill="{th["muted"]}">{esc(str(events[d])[:12])}</text>')
    sb = [f"type=calendar  {year}-{month:02d}  days={len(days_order)}  highlighted={sorted(hl)}"]
    sb += [tdesc(f"week {i + 1}", *win[i]) for i in range(len(weeks))]
    return part("".join(body), W, H, sb, False, f"Calendar {year}-{month:02d}")


def build_marquee(spec, th, idp=""):
    """marquee: a line of text that scrolls across a window and repeats without a seam.

    Fields:
      items (required; list of strings, at least one, none empty); separator ('   •   '); size (36); width (1000);
      dur (loop seconds for one full scroll, default 14); title (eyebrow label); title_zone (84 if title else 24).
    Refuses:
      no items: 'marquee: needs at least one item'. An empty item: 'marquee: items must not be empty'.
    Base state:
      the first screen of text is the base state (the scroll starts at offset zero).
    Timing:
      a linear translation over one loop, equal to the width of one repeat of the text, so the seam is invisible.
    Alternatives:
      the text is repeated twice and clipped to the window, so the loop restarts without a gap.
    Breaks if changed:
      the translation must equal the width of one repeat; a different width shows a jump at the seam. The width is
      estimated at 0.6 em per character, so a wide fallback font can show a small gap.
    Example:
      marquee-ticker.json   Tests: tests/test_type_coverage.py.
    """
    items = spec.get("items") or []
    if not items:
        sys.exit("marquee: needs at least one item")
    for it in items:
        if not str(it).strip():
            sys.exit("marquee: items must not be empty")
    sep = spec.get("separator", "   •   ")
    size = float(spec.get("size", 36))
    W = int(spec.get("width", 1000))
    dur = float(spec.get("dur", 14))
    tz = spec.get("title_zone", 84 if spec.get("title") else 24)
    unit = sep.join(str(i) for i in items) + sep
    loop_w = len(unit) * size * 0.6
    text = unit * 2
    H = int(tz + size * 2.6)
    y = tz + size * 1.6
    cid = f"{idp}mq"
    body = [f'<clipPath id="{cid}"><rect x="0" y="0" width="{W}" height="{H}"/></clipPath>',
            f'<g clip-path="url(#{cid})"><text x="0" y="{F(y)}" font-family="{FONT}" font-size="{F(size)}" font-weight="600" fill="{th["text_key"]}" xml:space="preserve">'
            f'{esc(text)}<animateTransform attributeName="transform" type="translate" values="0 0;{F(-loop_w)} 0" dur="{dur:g}s" repeatCount="indefinite"/></text></g>']
    sb = [f"type=marquee  items={len(items)}  scroll one repeat per {dur:g} s"]
    return part("".join(body), W, H, sb, False, "Marquee: " + " / ".join(str(i) for i in items))


def build_sprite(spec, th, idp=""):
    """sprite: a frame-by-frame animation; each frame is a piece of SVG markup shown in turn.

    Fields:
      frames (required; list of SVG markup strings, each a complete drawing); fps (6; frames per second);
      dur (loop seconds, default: frames divided by fps); width (320); height (240).
    Refuses:
      no frames: 'sprite: needs at least one frame'. A frame that is not well-formed SVG markup:
      'sprite: frame N is not valid SVG markup: <parser message>'.
    Base state:
      frame 1 is the base state and frames 2 onward are hidden, so the static fallback shows a complete drawing.
    Timing:
      each frame is shown for 1/fps seconds in order and the loop repeats; frame 1 is shown at the start and end.
    Alternatives:
      frames are whole markup strings rather than a shape language, so any drawing from the skill can be a frame.
    Breaks if changed:
      all frames must share one coordinate system and size; a frame with its own viewBox is not scaled to match.
    Example:
      sprite-blink.json   Tests: tests/test_type_coverage.py.
    """
    frames = spec.get("frames") or []
    if not frames:
        sys.exit("sprite: needs at least one frame")
    for k, f in enumerate(frames):
        try:
            ET.fromstring(f"<g xmlns='http://www.w3.org/2000/svg'>{f}</g>")
        except ET.ParseError as e:
            sys.exit(f"sprite: frame {k + 1} is not valid SVG markup: {e}")
    fps = float(spec.get("fps", 6))
    dur = float(spec.get("dur", len(frames) / fps))
    W = int(spec.get("width", 320))
    H = int(spec.get("height", 240))
    N = len(frames)
    body = []
    for k, f in enumerate(frames):
        if k == 0:
            vals, keys, base = "1;0;1", f"0;{T(1 / N)};1", 1
        else:
            vals, keys, base = "0;1;0;0", f"0;{T(k / N)};{T((k + 1) / N)};1", 0
        body.append(f'<g opacity="{base}">{f}<animate attributeName="opacity" calcMode="discrete" values="{vals}" '
                    f'keyTimes="{keys}" dur="{dur:g}s" repeatCount="indefinite"/></g>')
    sb = [f"type=sprite  frames={N}  fps={fps:g}  loop={dur:g}s"]
    return part("".join(body), W, H, sb, False, f"Sprite animation of {N} frames")


THINGS_E = {"scatter": build_scatter, "heatmap": build_heatmap, "funnel": build_funnel, "venn": build_venn,
            "waveform": build_waveform, "clock": build_clock, "calendar": build_calendar,
            "marquee": build_marquee, "sprite": build_sprite}
