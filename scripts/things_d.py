"""Things, part 4: five types the catalog did not cover: tree, table, pie, gantt, code.

All five follow the repo rules: computed timing, base state = finished graphic, refusals that name the fix.
Shared helpers come from diagram_common.py; read its docstrings for make_slots, part and glow_overlay.
"""
import math
import sys

from diagram_common import (FONT, SANS, F, T, card_w, esc, make_slots, node_card,
                            part, rail, relay_traveller, tdesc)


def build_tree(spec, th, idp=""):
    """tree: a hierarchy drawn top-down: parents centred over their children, elbow connectors, one dot per edge.

    Fields:
      root (required; a node object {label, sub, key, children:[...]}, nested to any depth);
      dur (loop seconds, default 8); title (eyebrow label); title_zone (84 if title else 24).
    Refuses:
      root that is not an object: 'tree: root must be an object'. A node without a label:
      'tree: every node needs a label'. A child that is not an object: 'tree: children must be objects'.
    Base state:
      every node and elbow connector is fully drawn; node glows and relay dots are overlays (glows at base opacity 0).
    Timing:
      one hop per depth level (make_slots); a node lights when the dot that reaches it arrives.
    Alternatives:
      elbow connectors (right angles), not curves: a tree reads as structure, and curves would suggest flow.
    Breaks if changed:
      each dot's path must equal its connector's path (lint checks this); all cards share one width so they cannot
      overlap; a connector starts on its parent's bottom edge and ends on its child's top edge.
    Example:
      tree-team.json   Tests: tests/test_type_coverage.py.
    """
    root = spec.get("root")
    if not isinstance(root, dict):
        sys.exit("tree: root must be an object")
    dur = float(spec.get("dur", 8))
    nodes = []

    def walk(node, depth, parent):
        if not node.get("label"):
            sys.exit("tree: every node needs a label")
        i = len(nodes)
        nodes.append(dict(label=node["label"], sub=node.get("sub", ""), key=node.get("key", False),
                          depth=depth, kids=[]))
        for child in node.get("children", []):
            if not isinstance(child, dict):
                sys.exit("tree: children must be objects")
            nodes[i]["kids"].append(walk(child, depth + 1, i))
        return i

    walk(root, 0, None)
    cw = max(card_w(n["label"], n["sub"], 16, minw=120) for n in nodes)
    CH, GAP, VGAP, MARGIN = 62, 28, 60, 48
    tz = spec.get("title_zone", 84 if spec.get("title") else 24)
    leaves = [i for i, n in enumerate(nodes) if not n["kids"]]
    xs = {}
    for k, i in enumerate(leaves):
        xs[i] = MARGIN + cw / 2 + k * (cw + GAP)

    def place(i):
        if nodes[i]["kids"]:
            xs[i] = sum(place(c) for c in nodes[i]["kids"]) / len(nodes[i]["kids"])
        return xs[i]

    place(0)
    D = max(n["depth"] for n in nodes)
    W = 2 * MARGIN + len(leaves) * cw + (len(leaves) - 1) * GAP
    H = tz + (D + 1) * CH + D * VGAP + MARGIN

    def y_of(i):
        return tz + nodes[i]["depth"] * (CH + VGAP)

    win, _ = make_slots(max(D, 1))
    arrivals = {i: [] for i in range(len(nodes))}
    arrivals[0].append(win[0][0])
    edges = []
    for p, n in enumerate(nodes):
        for c in n["kids"]:
            d = nodes[c]["depth"]
            x1, y1 = xs[p], y_of(p) + CH
            x2, y2 = xs[c], y_of(c)
            ym = y1 + VGAP / 2
            edges.append((f"M{F(x1)},{F(y1)} V{F(ym)} H{F(x2)} V{F(y2)}", win[d - 1]))
            arrivals[c].append(win[d - 1][1])
    body = []
    for path, _ in edges:
        body.append(rail(path, th, sw=1.4))
    for i, n in enumerate(nodes):
        body.append(node_card(th, idp + "tr-", str(i), xs[i] - cw / 2, y_of(i), cw, CH, n["label"], n["sub"],
                              n["key"], arrivals[i], dur, lsz=16))
    for path, (ts, te) in edges:
        body.append(relay_traveller(path, ts, te, th["accent"], th["dot"], dur))
    sb = [f"type=tree  nodes={len(nodes)}  levels={D + 1}  one hop per level"]
    sb += [tdesc(f"level {d + 1}", *win[d]) for d in range(len(win))]
    return part("".join(body), W, H, sb, False, "Tree: " + root["label"])


def build_table(spec, th, idp=""):
    """table: a data table with a header row; body rows highlight one after another in a sweep.

    Fields:
      columns (required; list of header strings); rows (list of lists of cell strings, each as long as columns);
      align (one of 'l', 'c', 'r' per column; default all 'l'); highlight ('sweep' default, or 'none');
      col_w (fixed column width in px; default: the longest text in the column, at least 120); dur (loop seconds,
      default 8); title (eyebrow label); title_zone (84 if title else 24).
    Refuses:
      no columns: 'table: needs at least one column'. A row with the wrong cell count:
      'table: row N has X cells, expected Y'. align with the wrong length: 'table: align must have one entry per column'.
      an align entry other than l, c or r: 'table: align entries must be l, c or r'.
    Base state:
      the full table is the base state; row highlights are overlays at base opacity 0.
    Timing:
      rows highlight in order, in at most eight groups (make_slots), so long tables do not flash; each highlight holds briefly, then clears.
    Alternatives:
      the sweep is a highlight, not a rebuild, so the table never reflows during the animation.
    Breaks if changed:
      every row needs one cell per column (refused); a highlight rectangle must stay inside its row.
    Example:
      table-compare.json   Tests: tests/test_type_coverage.py.
    """
    cols = spec.get("columns") or []
    rows = spec.get("rows", [])
    if not cols:
        sys.exit("table: needs at least one column")
    for k, r in enumerate(rows):
        if len(r) != len(cols):
            sys.exit(f"table: row {k + 1} has {len(r)} cells, expected {len(cols)}")
    align = spec.get("align", ["l"] * len(cols))
    if len(align) != len(cols):
        sys.exit("table: align must have one entry per column")
    if any(a not in ("l", "c", "r") for a in align):
        sys.exit("table: align entries must be l, c or r")
    dur = float(spec.get("dur", 8))
    highlight = spec.get("highlight", "sweep")
    fixed = spec.get("col_w")
    widths = []
    for j, head in enumerate(cols):
        longest = max([len(str(head))] + [len(str(r[j])) for r in rows])
        widths.append(int(fixed) if fixed else max(120, int(longest * 8.4 + 36)))
    MARGIN, ROW_H, HEAD_H = 40, 38, 40
    tz = spec.get("title_zone", 84 if spec.get("title") else 24)
    W = 2 * MARGIN + sum(widths)
    H = tz + HEAD_H + len(rows) * ROW_H + MARGIN
    body = [f'<rect x="{MARGIN}" y="{tz}" width="{F(W - 2 * MARGIN)}" height="{HEAD_H}" fill="{th["surface_key"]}"/>']
    xs = []
    x = MARGIN
    for w in widths:
        xs.append(x)
        x += w

    def cell(text, j, y, color, weight):
        left, w = xs[j], widths[j]
        if align[j] == "c":
            tx, anchor = left + w / 2, "middle"
        elif align[j] == "r":
            tx, anchor = left + w - 14, "end"
        else:
            tx, anchor = left + 14, "start"
        return (f'<text x="{F(tx)}" y="{F(y)}" text-anchor="{anchor}" font-family="{FONT}" font-size="14" '
                f'font-weight="{weight}" fill="{color}">{esc(text)}</text>')

    for j, head in enumerate(cols):
        body.append(cell(head, j, tz + 26, th["accent"], "700"))
    slots = None
    groups = min(len(rows), 8) if rows else 0
    if highlight == "sweep" and rows:
        slots, _ = make_slots(groups)
    for k, r in enumerate(rows):
        y0 = tz + HEAD_H + k * ROW_H
        if slots:
            on, off = slots[k * groups // len(rows)]
            body.append(f'<rect x="{MARGIN}" y="{F(y0)}" width="{F(W - 2 * MARGIN)}" height="{ROW_H}" fill="{th["accent"]}" opacity="0">'
                        f'<animate attributeName="opacity" calcMode="discrete" values="0;0.16;0;0" '
                        f'keyTimes="0;{T(on)};{T(off)};1" dur="{dur:g}s" repeatCount="indefinite"/></rect>')
        body.append(f'<path d="M{MARGIN},{F(y0)} H{F(W - MARGIN)}" stroke="{th["stroke_dim"]}" stroke-width="1" fill="none"/>')
        for j, text in enumerate(r):
            body.append(cell(str(text), j, y0 + 25, th["text"], "400"))
    body.append(f'<path d="M{MARGIN},{F(tz + HEAD_H + len(rows) * ROW_H)} H{F(W - MARGIN)}" stroke="{th["stroke_dim"]}" stroke-width="1" fill="none"/>')
    sb = [f"type=table  columns={len(cols)}  rows={len(rows)}  highlight={highlight}"]
    if slots:
        sb += [tdesc(f"row group {g + 1}", *slots[g]) for g in range(groups)]
    return part("".join(body), W, H, sb, False, "Table: " + ", ".join(cols))


def build_pie(spec, th, idp=""):
    """pie: a pie or donut chart; each slice sweeps in, one after another, and a legend gives the shares.

    Fields:
      slices (required; list of {label, value, color}; value must be positive); radius (120 px); donut (false;
      true draws a ring with a hole of 55 % of the radius); legend (true; false hides the legend); dur (loop
      seconds, default 8); title (eyebrow label); title_zone (84 if title else 24).
    Refuses:
      no slices: 'pie: needs at least one slice'. A value that is not positive:
      'pie: slice <label> must have a positive value'.
    Base state:
      the finished chart is the base state (each slice at its final length); the sweep starts from zero.
    Timing:
      slices reveal in order, each over about 0.12 of the loop, after the previous one has started.
    Alternatives:
      a pie is drawn as one thick stroked circle per slice (dasharray), not as arc paths: no trigonometry in the
      markup, and the shares add up exactly because the dash lengths are fractions of the circumference.
    Breaks if changed:
      the dash lengths must sum to the circumference (they do by construction); the ring starts at the top
      (rotate -90) and runs clockwise; the donut hole must stay the same proportion of the radius in base and animation.
    Example:
      pie-split.json   Tests: tests/test_type_coverage.py.
    """
    slices = spec.get("slices") or []
    if not slices:
        sys.exit("pie: needs at least one slice")
    for s in slices:
        if not (isinstance(s.get("value"), (int, float)) and s["value"] > 0):
            sys.exit(f"pie: slice {s.get('label', '?')} must have a positive value")
    R = float(spec.get("radius", 120))
    donut = bool(spec.get("donut", False))
    dur = float(spec.get("dur", 8))
    legend = spec.get("legend", True)
    tz = spec.get("title_zone", 84 if spec.get("title") else 24)
    total = sum(float(s["value"]) for s in slices)
    if donut:
        ri = 0.55 * R
        r_mid, width = (R + ri) / 2, R - ri
    else:
        r_mid, width = R / 2, R
    C = 2 * math.pi * r_mid
    cx, cy = 40 + R, tz + R + 10
    W = int(cx + R + 60 + (300 if legend else 0))
    H = int(tz + 2 * R + 40)
    palette = [s.get("color") or th["accent3"] for s in slices]
    body = []
    acc = 0.0
    win, _ = make_slots(len(slices), dwell=0.02, tail=0.06)
    for k, s in enumerate(slices):
        frac = float(s["value"]) / total
        seg = frac * C
        on, off = win[k]
        col = palette[k] if s.get("color") else [th["accent"], th["accent2"], th["accent3"], th["loop"]][k % 4]
        ks = f"0;{T(on)};{T(off)};1"
        body.append(f'<circle cx="{F(cx)}" cy="{F(cy)}" r="{F(r_mid)}" fill="none" stroke="{col}" stroke-width="{F(width)}" '
                    f'stroke-dasharray="{F(seg)} {F(C)}" stroke-dashoffset="{F(-acc * C)}" transform="rotate(-90 {F(cx)} {F(cy)})">'
                    f'<animate attributeName="stroke-dasharray" calcMode="spline" keyTimes="{ks}" '
                    f'keySplines="0.45 0 0.55 1;0.45 0 0.55 1;0 0 1 1" dur="{dur:g}s" repeatCount="indefinite" '
                    f'values="0 {F(C)};0 {F(C)};{F(seg)} {F(C)};{F(seg)} {F(C)}"/></circle>')
        if legend:
            ly = tz + 20 + k * 30
            lx = cx + R + 40
            body.append(f'<rect x="{F(lx)}" y="{F(ly - 12)}" width="14" height="14" rx="3" fill="{col}"/>'
                        f'<text x="{F(lx + 24)}" y="{F(ly)}" font-family="{FONT}" font-size="14" fill="{th["text"]}">'
                        f'{esc(str(s.get("label", "")))}  {100 * frac:.1f}%</text>')
        acc += frac
    sb = [f"type=pie  slices={len(slices)}  donut={donut}  shares sum to 100 %"]
    sb += [tdesc(f"slice {k + 1}", *win[k]) for k in range(len(slices))]
    return part("".join(body), W, H, sb, False, "Pie chart: " + ", ".join(str(s.get("label", "")) for s in slices))


def build_gantt(spec, th, idp=""):
    """gantt: task bars on a time axis; each bar grows in order, and its progress fill shows how far the task is.

    Fields:
      tasks (required; list of {name, start, end, progress (0-100)}); axis_max (default: the latest end; must not
      be smaller than it); unit (label on the axis, default 'days'); dur (loop seconds, default 8); title (eyebrow label);
      title_zone (84 if title else 24).
    Refuses:
      no tasks: 'gantt: needs at least one task'. end not after start: 'gantt: task <name> must end after it starts'.
      negative start: 'gantt: task <name> starts before 0'. progress outside 0-100:
      'gantt: task <name> progress must be between 0 and 100'. axis_max below the latest end:
      'gantt: axis_max is smaller than the latest end'.
    Base state:
      every bar is drawn at its final length with its progress fill; the grow-in starts from zero.
    Timing:
      tasks grow in list order, one slot each (make_slots), so the schedule is read as it unfolds.
    Alternatives:
      with axis_max set, adding a task that ends before axis_max leaves every existing bar where it was. By default
      axis_max follows the latest end, so adding a later task rescales every bar: set axis_max for a stable plan.
    Breaks if changed:
      a bar must stay inside the plot (the scale maps axis_max to the plot width); the progress fill can never be
      wider than its bar.
    Example:
      gantt-plan.json   Tests: tests/test_type_coverage.py.
    """
    tasks = spec.get("tasks") or []
    if not tasks:
        sys.exit("gantt: needs at least one task")
    for t in tasks:
        name = t.get("name", "?")
        if t["end"] <= t["start"]:
            sys.exit(f"gantt: task {name} must end after it starts")
        if t["start"] < 0:
            sys.exit(f"gantt: task {name} starts before 0")
        p = t.get("progress", 0)
        if not (0 <= p <= 100):
            sys.exit(f"gantt: task {name} progress must be between 0 and 100")
    latest = max(t["end"] for t in tasks)
    axis_max = spec.get("axis_max", latest)
    if axis_max < latest:
        sys.exit("gantt: axis_max is smaller than the latest end")
    unit = spec.get("unit", "days")
    dur = float(spec.get("dur", 8))
    tz = spec.get("title_zone", 84 if spec.get("title") else 24)
    LW, MARGIN, ROW_H, PLOT_W = 210, 40, 40, 620
    x0 = MARGIN + LW
    scale = PLOT_W / axis_max
    W = int(x0 + PLOT_W + MARGIN)
    H = int(tz + 34 + len(tasks) * ROW_H + 30)
    step = next(s for s in (1, 2, 5, 10, 20, 50, 100, 200, 500) if axis_max / s <= 10)
    body = []
    t_ = 0
    while t_ <= axis_max + 1e-9:
        gx = x0 + t_ * scale
        body.append(f'<path d="M{F(gx)},{tz + 26} V{F(tz + 34 + len(tasks) * ROW_H)}" stroke="{th["stroke_dim"]}" stroke-width="1" opacity="0.5"/>'
                    f'<text x="{F(gx)}" y="{tz + 20}" text-anchor="middle" font-family="{FONT}" font-size="11" fill="{th["muted"]}">{t_:g}</text>')
        t_ += step
    win, _ = make_slots(len(tasks))
    for k, t in enumerate(tasks):
        y = tz + 34 + k * ROW_H
        bx = x0 + t["start"] * scale
        bw = (t["end"] - t["start"]) * scale
        pw = bw * t.get("progress", 0) / 100
        on, off = win[k]
        ks = f"0;{T(on)};{T(off)};1"
        vals_w = f"0;0;{F(bw)};{F(bw)}"
        vals_p = f"0;0;{F(pw)};{F(pw)}"
        body.append(f'<text x="{MARGIN}" y="{F(y + 24)}" font-family="{FONT}" font-size="14" fill="{th["text"]}">{esc(str(t.get("name", "")))}</text>')
        body.append(f'<rect x="{F(bx)}" y="{F(y + 8)}" width="{F(bw)}" height="18" rx="4" fill="{th["surface_key"]}" stroke="{th["stroke"]}" stroke-width="1">'
                    f'<animate attributeName="width" calcMode="spline" keyTimes="{ks}" keySplines="0.16 1 0.3 1;0 0 1 1;0.16 1 0.3 1" '
                    f'values="{vals_w}" dur="{dur:g}s" repeatCount="indefinite"/></rect>')
        if pw > 0:
            body.append(f'<rect x="{F(bx)}" y="{F(y + 8)}" width="{F(pw)}" height="18" rx="4" fill="{th["accent"]}">'
                        f'<animate attributeName="width" calcMode="spline" keyTimes="{ks}" keySplines="0.16 1 0.3 1;0 0 1 1;0.16 1 0.3 1" '
                        f'values="{vals_p}" dur="{dur:g}s" repeatCount="indefinite"/></rect>')
    body.append(f'<text x="{MARGIN}" y="{tz + 20}" font-family="{FONT}" font-size="11" fill="{th["muted"]}">{esc(unit)}</text>')
    sb = [f"type=gantt  tasks={len(tasks)}  axis 0..{axis_max:g} {unit}"]
    sb += [tdesc(f"task {k + 1} ({t.get('name', '')})", *win[k]) for k, t in enumerate(tasks)]
    return part("".join(body), W, H, sb, False, "Gantt chart: " + ", ".join(str(t.get("name", "")) for t in tasks))


def build_code(spec, th, idp=""):
    """code: a code block with line numbers; the highlighted lines light in the order given.

    Fields:
      lines (required; list of strings, one per line); highlight (list of 1-based line numbers, lit in this order);
      language (label in the window bar, e.g. 'python'); caption (text under the block); size (font size, default 15);
      dur (loop seconds, default 10); title (eyebrow label).
    Refuses:
      no lines: 'code: needs at least one line'. A highlighted line outside the block:
      'code: highlight line N is outside 1..M'.
    Base state:
      all code is visible in the base state; each highlight is an overlay at base opacity 0.
    Timing:
      highlights light in order, one slot each (make_slots); each holds briefly, then clears.
    Alternatives:
      the highlight is a band behind the line, not a change of text colour, so the code is never re-rendered.
    Breaks if changed:
      a highlight band must sit behind the text (draw order); line height is constant, so line numbers and bands align.
    Example:
      code-highlight.json   Tests: tests/test_type_coverage.py.
    """
    lines = spec.get("lines") or []
    if not lines:
        sys.exit("code: needs at least one line")
    hl = list(spec.get("highlight", []))
    for n in hl:
        if not (1 <= int(n) <= len(lines)):
            sys.exit(f"code: highlight line {n} is outside 1..{len(lines)}")
    dur = float(spec.get("dur", 10))
    size = float(spec.get("size", 15))
    CW = size * 0.6
    LH = size * 1.6
    GUT = 46
    MARGIN = 20
    BAR = 40
    maxlen = max(len(str(l)) for l in lines)
    W = int(max(640, MARGIN * 2 + GUT + maxlen * CW + 40))
    top = BAR + 14
    H = int(top + len(lines) * LH + (70 if spec.get("caption") else 30))
    body = [f'<rect x="{MARGIN}" y="{MARGIN}" width="{W - 2 * MARGIN}" height="{H - 2 * MARGIN}" rx="14" fill="{th["surface"]}" stroke="{th["stroke_dim"]}" stroke-width="1.2"/>',
            f'<path d="M{MARGIN},{MARGIN + 26} V{MARGIN + 14} a14,14 0 0 1 14,-14 H{W - MARGIN - 14} a14,14 0 0 1 14,14 V{MARGIN + 26} Z" fill="{th["surface_key"]}"/>']
    if spec.get("language"):
        body.append(f'<text x="{W - MARGIN - 18}" y="{MARGIN + 22}" text-anchor="end" font-family="{FONT}" font-size="12" fill="{th["muted"]}">{esc(spec["language"])}</text>')
    win, _ = make_slots(max(len(hl), 1)) if hl else ([], 0)
    for k, n in enumerate(hl):
        i = int(n) - 1
        on, off = win[k]
        y = top + i * LH
        body.append(f'<rect x="{MARGIN + 2}" y="{F(y)}" width="{F(W - 2 * MARGIN - 4)}" height="{F(LH)}" fill="{th["accent"]}" opacity="0">'
                    f'<animate attributeName="opacity" calcMode="discrete" values="0;0.2;0;0" '
                    f'keyTimes="0;{T(on)};{T(off)};1" dur="{dur:g}s" repeatCount="indefinite"/></rect>')
    for i, line in enumerate(lines):
        y = top + i * LH + LH * 0.68
        body.append(f'<text x="{MARGIN + GUT - 12}" y="{F(y)}" text-anchor="end" font-family="{FONT}" font-size="{F(size * 0.85)}" fill="{th["muted"]}">{i + 1}</text>')
        body.append(f'<text x="{MARGIN + GUT}" y="{F(y)}" font-family="{FONT}" font-size="{F(size)}" fill="{th["text"]}" xml:space="preserve">{esc(str(line))}</text>')
    if spec.get("caption"):
        body.append(f'<text x="{MARGIN + 14}" y="{H - MARGIN - 18}" font-family="{SANS}" font-size="14" fill="{th["muted"]}">{esc(spec["caption"])}</text>')
    sb = [f"type=code  lines={len(lines)}  highlights={hl}"]
    sb += [tdesc(f"highlight line {int(n)}", *win[k]) for k, n in enumerate(hl)]
    return part("".join(body), W, H, sb, False, "Code block: " + str(lines[0])[:60])


THINGS_D = {"tree": build_tree, "table": build_table, "pie": build_pie, "gantt": build_gantt, "code": build_code}
