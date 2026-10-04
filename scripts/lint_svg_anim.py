#!/usr/bin/env python3
"""Lint an animated SVG and report geometry/timing facts.

Usage:  python lint_svg_anim.py file.svg [--quiet]

Checks (ERROR = broken, WARN = probably wrong, INFO = useful fact):
  * paste artifacts (\\<svg, \\:, markdown-linked namespaces, smart quotes)
  * XML well-formedness, duplicate ids, unresolved href / url(#id)
  * animate / animateTransform / animateMotion / set attribute sanity
    (dur, attributeName, values vs keyTimes vs keySplines, motion path)
  * elements with a begin delay that are visible before they start
  * linear calcMode on multi-segment motion paths (uneven speed)
  * connectors (paths with markers) that pass through, or end inside, a card
  * for each animateMotion: when it enters/leaves each rect (fractions of the
    loop) and whether the traveller is drawn above or below the rect
Exit code 1 if any ERROR is found.
"""
import math
import re
import sys
import xml.etree.ElementTree as ET

SVG = "http://www.w3.org/2000/svg"
XLINK = "http://www.w3.org/1999/xlink"
ANIM_TAGS = {"animate", "animateTransform", "animateMotion", "set"}
NUM = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")
TOKEN = re.compile(r"[MmLlHhVvCcSsQqTtAaZz]|[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")

problems = []  # (level, message)


def report(level, msg):
    problems.append((level, msg))


def local(tag):
    return tag.split("}", 1)[1] if "}" in tag else tag


def fnum(s, default=None):
    try:
        return float(str(s).strip().rstrip("px"))
    except (TypeError, ValueError):
        return default


def parse_time(s):
    """Return seconds, or None for syncbase/indefinite/unparseable."""
    if s is None:
        return None
    s = s.strip()
    m = re.fullmatch(r"([-+]?\d*\.?\d+)(ms|s)?", s)
    if not m:
        return None
    v = float(m.group(1))
    return v / 1000.0 if m.group(2) == "ms" else v


# ----------------------------------------------------------------- path maths
def parse_path(d):
    """Return list of polylines (list of (x,y)) sampled from path data, and a flag
    saying whether the path contained arcs (approximated by a straight chord)."""
    tokens = TOKEN.findall(d)
    i = 0
    cmd = None
    x = y = 0.0
    sx = sy = 0.0
    pts = []
    segs = 0
    arcs = False
    last_ctrl = None
    last_cmd = None

    def nums(n):
        nonlocal i
        vals = []
        for _ in range(n):
            if i >= len(tokens) or tokens[i].isalpha():
                raise ValueError("bad path data")
            vals.append(float(tokens[i]))
            i += 1
        return vals

    def cubic(p0, p1, p2, p3, n=24):
        out = []
        for k in range(1, n + 1):
            t = k / n
            mt = 1 - t
            out.append((
                mt**3 * p0[0] + 3 * mt * mt * t * p1[0] + 3 * mt * t * t * p2[0] + t**3 * p3[0],
                mt**3 * p0[1] + 3 * mt * mt * t * p1[1] + 3 * mt * t * t * p2[1] + t**3 * p3[1],
            ))
        return out

    def quad(p0, p1, p2, n=24):
        out = []
        for k in range(1, n + 1):
            t = k / n
            mt = 1 - t
            out.append((mt * mt * p0[0] + 2 * mt * t * p1[0] + t * t * p2[0],
                        mt * mt * p0[1] + 2 * mt * t * p1[1] + t * t * p2[1]))
        return out

    while i < len(tokens):
        if tokens[i].isalpha():
            cmd = tokens[i]
            i += 1
            if cmd in "Zz":
                pts.append((sx, sy))
                x, y = sx, sy
                segs += 1
                last_cmd = cmd
                continue
        elif cmd is None:
            raise ValueError("path data must start with a command")
        rel = cmd.islower()
        c = cmd.upper()
        if c == "M":
            a, b = nums(2)
            x, y = (x + a, y + b) if rel else (a, b)
            sx, sy = x, y
            pts.append((x, y))
            cmd = "l" if rel else "L"  # implicit lineto after moveto
        elif c == "L":
            a, b = nums(2)
            x, y = (x + a, y + b) if rel else (a, b)
            pts.append((x, y))
            segs += 1
        elif c == "H":
            (a,) = nums(1)
            x = x + a if rel else a
            pts.append((x, y))
            segs += 1
        elif c == "V":
            (b,) = nums(1)
            y = y + b if rel else b
            pts.append((x, y))
            segs += 1
        elif c == "C":
            a = nums(6)
            if rel:
                a = [a[0] + x, a[1] + y, a[2] + x, a[3] + y, a[4] + x, a[5] + y]
            pts.extend(cubic((x, y), (a[0], a[1]), (a[2], a[3]), (a[4], a[5])))
            last_ctrl = (a[2], a[3])
            x, y = a[4], a[5]
            segs += 1
        elif c == "S":
            a = nums(4)
            if rel:
                a = [a[0] + x, a[1] + y, a[2] + x, a[3] + y]
            if last_cmd in ("C", "S") and last_ctrl:
                c1 = (2 * x - last_ctrl[0], 2 * y - last_ctrl[1])
            else:
                c1 = (x, y)
            pts.extend(cubic((x, y), c1, (a[0], a[1]), (a[2], a[3])))
            last_ctrl = (a[0], a[1])
            x, y = a[2], a[3]
            segs += 1
        elif c == "Q":
            a = nums(4)
            if rel:
                a = [a[0] + x, a[1] + y, a[2] + x, a[3] + y]
            pts.extend(quad((x, y), (a[0], a[1]), (a[2], a[3])))
            last_ctrl = (a[0], a[1])
            x, y = a[2], a[3]
            segs += 1
        elif c == "T":
            a = nums(2)
            if rel:
                a = [a[0] + x, a[1] + y]
            if last_cmd in ("Q", "T") and last_ctrl:
                c1 = (2 * x - last_ctrl[0], 2 * y - last_ctrl[1])
            else:
                c1 = (x, y)
            pts.extend(quad((x, y), c1, (a[0], a[1])))
            last_ctrl = c1
            x, y = a[0], a[1]
            segs += 1
        elif c == "A":
            a = nums(7)
            arcs = True
            x, y = (x + a[5], y + a[6]) if rel else (a[5], a[6])
            pts.append((x, y))
            segs += 1
        else:
            raise ValueError("unsupported command " + cmd)
        last_cmd = c
    return pts, segs, arcs


def polyline_length(pts):
    return sum(math.dist(pts[k], pts[k + 1]) for k in range(len(pts) - 1))


def inside(p, rect, margin=0.0):
    x, y, w, h = rect
    return x + margin < p[0] < x + w - margin and y + margin < p[1] < y + h - margin


def resample(pts, step=1.0):
    """Evenly resample polyline by arc length; returns list of (point, fraction)."""
    total = polyline_length(pts)
    if total == 0:
        return [(pts[0], 0.0)]
    out = []
    acc = 0.0
    out.append((pts[0], 0.0))
    for k in range(len(pts) - 1):
        a, b = pts[k], pts[k + 1]
        seg = math.dist(a, b)
        if seg == 0:
            continue
        n = max(1, int(seg / step))
        for j in range(1, n + 1):
            t = j / n
            p = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
            out.append((p, (acc + seg * t) / total))
        acc += seg
    return out


# ----------------------------------------------------------------- main lint
def lint_one(path, quiet=False):
    """Lint a single file. Returns (error_count, warning_count)."""
    global problems
    problems = []          # per-file state; see main() for why this is reset
    try:
        text = open(path, encoding="utf-8").read()
    except OSError as e:
        report("ERROR", f"cannot read file: {e}")
        finish(path, quiet)
        return 1, 0

    # 1. paste artifacts ------------------------------------------------
    if re.search(r"\\[<>:]", text):
        report("ERROR", "backslash-escaped characters found (e.g. '\\<svg' or 'xlink\\:href') — paste artifact, remove the backslashes")
    if re.search(r"\]\(https?://", text):
        report("ERROR", "markdown link syntax inside the file (e.g. xmlns=\"[http://…](http://…)\") — replace with the plain URL")
    if re.search(r"[“”‘’]", text):
        report("WARN", "smart quotes found; XML attributes need straight quotes")

    # 2. parse ---------------------------------------------------------
    try:
        root = ET.fromstring(text.encode("utf-8"))
    except ET.ParseError as e:
        report("ERROR", f"not well-formed XML: {e}")
        return tally(path, quiet)
    if local(root.tag) != "svg":
        report("ERROR", "root element is not <svg>")
        return tally(path, quiet)

    parent = {c: p for p in root.iter() for c in p}
    order = {el: i for i, el in enumerate(root.iter())}
    vb = root.get("viewBox")
    vbw = vbh = None
    if not vb:
        report("WARN", "no viewBox on <svg>: graphic will not scale")
    else:
        vals = [float(v) for v in NUM.findall(vb)]
        if len(vals) == 4:
            vbw, vbh = vals[2], vals[3]
    if not root.get("role") and not root.get("aria-label"):
        report("INFO", "no role=\"img\"/aria-label on <svg> (add role, <title>, <desc> for accessibility)")
    if not any(local(c.tag) == "title" for c in root):
        report("INFO", "no <title> element")

    # 3. ids and references -------------------------------------------
    ids = {}
    for el in root.iter():
        i = el.get("id")
        if i:
            if i in ids:
                report("ERROR", f"duplicate id '{i}'")
            ids[i] = el
    ref_re = re.compile(r"url\(\s*['\"]?#([^)'\"\s]+)")
    for el in root.iter():
        for k, v in el.attrib.items():
            if local(k) == "href" and v.startswith("#") and v[1:] not in ids:
                report("ERROR", f"{local(el.tag)} href '{v}' does not match any id")
            for m in ref_re.finditer(v):
                if m.group(1) not in ids:
                    report("ERROR", f"{k}=\"{v}\" references missing id '{m.group(1)}'")
        if local(el.tag) == "style" and el.text:
            for m in ref_re.finditer(el.text):
                if m.group(1) not in ids:
                    report("ERROR", f"<style> references missing id '{m.group(1)}'")
    for el in root.iter():
        if local(el.tag) == "marker":
            shapes = [c for c in el.iter() if local(c.tag) in ("path", "polygon", "polyline", "circle", "rect")]
            if shapes and all(c.get("fill") == "none" for c in shapes):
                report("WARN", f"marker '{el.get('id')}' is stroke-only (fill=none): invisible in several renderers; use a filled path")
            if el.get("markerUnits") != "userSpaceOnUse":
                report("INFO", f"marker '{el.get('id')}' scales with stroke width (no markerUnits=userSpaceOnUse)")
    if any(local(el.tag) == "script" for el in root.iter()):
        report("WARN", "<script> present: will not run inside <img>/README embeds")
    if any(local(el.tag) == "foreignObject" for el in root.iter()):
        report("WARN", "<foreignObject> present: poorly supported outside browsers")
    for el in root.iter():
        for k, v in el.attrib.items():
            if local(k) == "href" and re.match(r"https?://", v):
                report("WARN", f"external resource referenced: {v[:60]} (use data: URIs / inline)")
    style_text = " ".join((el.text or "") for el in root.iter() if local(el.tag) == "style")
    if "@import" in style_text or "fonts.googleapis" in style_text:
        report("WARN", "external font/CSS import found; will not load in <img> contexts")
    has_css_anim = "@keyframes" in style_text
    if has_css_anim and "prefers-reduced-motion" not in style_text:
        report("INFO", "CSS animations without a prefers-reduced-motion block")

    # 4. animation elements ------------------------------------------
    anim_count = 0
    durations = set()
    dur_list = []
    for el in root.iter():
        tag = local(el.tag)
        if tag not in ANIM_TAGS:
            continue
        anim_count += 1
        par = parent.get(el)
        pname = local(par.tag) if par is not None else "?"
        label = f"<{tag}> in <{pname}{(' id=' + par.get('id')) if par is not None and par.get('id') else ''}>"
        if par is root or pname in ("defs", "svg"):
            report("WARN", f"{label}: animates the root/defs; probably misplaced")
        if tag != "animateMotion" and not el.get("attributeName") and not (tag == "animateTransform"):
            report("ERROR", f"{label}: missing attributeName")
        if tag == "animateTransform" and not el.get("type"):
            report("ERROR", f"{label}: animateTransform needs type=")
        dur = el.get("dur")
        if tag != "set" and not dur:
            report("ERROR", f"{label}: no dur — nothing will animate")
        if dur and dur != "indefinite":
            t = parse_time(dur)
            if t is None:
                report("ERROR", f"{label}: bad dur '{dur}'")
            else:
                durations.add(t)
                dur_list.append(t)
        values = el.get("values")
        vlist = [v.strip() for v in values.split(";") if v.strip() != ""] if values else None
        kt = el.get("keyTimes")
        ktl = [float(v) for v in NUM.findall(kt)] if kt else None
        ks = el.get("keySplines")
        calc = el.get("calcMode")
        if ktl is not None:
            if vlist is not None and len(ktl) != len(vlist):
                report("ERROR", f"{label}: keyTimes count ({len(ktl)}) != values count ({len(vlist)})")
            if any(b < a for a, b in zip(ktl, ktl[1:])):
                report("ERROR", f"{label}: keyTimes not non-decreasing")
            if ktl and abs(ktl[0]) > 1e-9:
                report("ERROR", f"{label}: keyTimes must start at 0")
            if ktl and calc != "discrete" and abs(ktl[-1] - 1) > 1e-9 and tag != "animateMotion":
                report("WARN", f"{label}: keyTimes should end at 1 (ends at {ktl[-1]})")
        if calc == "spline":
            if not ks:
                report("ERROR", f"{label}: calcMode=spline without keySplines")
            else:
                groups = [g for g in ks.split(";") if g.strip()]
                n = (len(vlist) if vlist else (len(ktl) if ktl else None))
                if n is not None and len(groups) != n - 1:
                    report("ERROR", f"{label}: keySplines count ({len(groups)}) should be values-1 ({n - 1})")
                for g in groups:
                    nums_ = [float(v) for v in NUM.findall(g)]
                    if len(nums_) != 4 or any(v < 0 or v > 1 for v in nums_):
                        report("ERROR", f"{label}: keySplines entry '{g.strip()}' must be 4 numbers in 0..1")
        if tag == "animate" and el.get("attributeName") == "opacity" and vlist and ktl is None and len(vlist) > 3 and dur:
            fl = [fnum(v) for v in vlist]
            if all(v is not None for v in fl) and min(fl[1:-1] or [1]) < 0.5 and len(fl) >= 4:
                report("INFO", f"{label}: opacity keyframes evenly spaced with values {vlist}; confirm the object stays visible for the whole span it is meant to be seen")
        if tag == "animate" and el.get("attributeName") in ("opacity", "stroke-opacity", "fill-opacity") and vlist and ktl and len(vlist) == len(ktl) and len(vlist) >= 3:
            fl = [fnum(v) for v in vlist]
            if all(v is not None for v in fl) and abs(ktl[-1] - 1) < 1e-9:
                gap = 1 - ktl[-2]
                plateau = len(fl) >= 4 and abs(fl[-3] - fl[-2]) < 1e-9 and fl[-2] > 0.3
                if plateau and fl[-2] - fl[-1] > 0.3 and gap > 0.25:
                    report("WARN", f"{label}: {el.get('attributeName')} holds {fl[-2]:g} then ramps to {fl[-1]:g} across the last {gap*100:.0f}% of the loop, so the object stays lit/visible long after its window. Do not just stretch the last keyTime to 1: add a final keyframe at the end value (e.g. values='...;{fl[-2]:g};0;0' keyTimes='...;t_off;1') so the fade finishes shortly after the window")
        if tag == "animateMotion" and el.get("keyPoints"):
            kpl = [float(v) for v in NUM.findall(el.get("keyPoints"))]
            if ktl is None:
                report("ERROR", f"{label}: keyPoints without keyTimes")
            elif len(kpl) != len(ktl):
                report("ERROR", f"{label}: keyPoints count ({len(kpl)}) != keyTimes count ({len(ktl)})")
            if calc != "linear":
                report("WARN", f"{label}: keyPoints is only honoured with calcMode=\"linear\" (or spline/discrete); with the default 'paced' it is ignored")
            if any(v < 0 or v > 1 for v in kpl):
                report("ERROR", f"{label}: keyPoints must be within 0..1")
        # begin delay + visible base state
        begin = el.get("begin")
        if begin and par is not None and tag in ("animateMotion", "animateTransform", "animate", "set"):
            bt = parse_time(begin.split(";")[0]) if begin else None
            if bt is not None and bt > 0:
                hidden = par.get("opacity") in ("0", "0.0") or par.get("visibility") == "hidden" or par.get("display") == "none"
                touches_opacity = tag == "animate" and el.get("attributeName") == "opacity"
                if not hidden and not touches_opacity:
                    report("WARN", f"{label}: begin='{begin}' but parent is visible before it starts (set opacity=\"0\" on the parent, or use a negative begin)")
        if tag == "animateMotion":
            mp = None
            d = el.get("path")
            if not d:
                for c in el:
                    if local(c.tag) == "mpath":
                        href = c.get("href") or c.get("{%s}href" % XLINK)
                        if not href or href[1:] not in ids:
                            report("ERROR", f"{label}: mpath target {href} not found")
                        else:
                            d = ids[href[1:]].get("d")
                            mp = href
                if not d and mp is None:
                    report("ERROR", f"{label}: no path= and no mpath — nothing to follow")
            if d:
                try:
                    pts, segs, arcs = parse_path(d)
                    if segs > 1 and calc == "linear" and not el.get("keyPoints"):
                        report("WARN", f"{label}: calcMode=linear on a {segs}-segment path without keyPoints — segments may get equal time (uneven speed). Use default paced, one segment, or keyPoints+keyTimes")
                    if arcs:
                        report("INFO", f"{label}: path contains arcs; crossing report approximates them as chords")
                except ValueError as e:
                    report("WARN", f"{label}: could not parse path ({e}); geometry report skipped")

    if anim_count == 0 and not has_css_anim:
        report("WARN", "no SMIL animation elements and no CSS keyframes found")
    if anim_count > 150:
        report("WARN", f"{anim_count} SMIL animation nodes — may be heavy; generate fewer or use CSS")
    if durations:
        report("INFO", f"{anim_count} SMIL animations; distinct durations: {sorted(durations)}")
        from collections import Counter
        master = Counter(dur_list).most_common(1)[0][0]
        odd = set()
        for d_ in durations:
            if d_ == master or d_ < 0.5:
                continue
            ratio = master / d_ if d_ < master else d_ / master
            if abs(ratio - round(ratio)) > 1e-6:
                odd.add(d_)
        if odd:
            report("INFO", f"master clock looks like {master:g}s; durations {sorted(odd)} are not whole divisors/multiples of it: fine for ambient drift (aurora), but pulses that must stay in sync with the loop should use master/2, master/4 ...")
    if len(text) > 200_000:
        report("WARN", f"file is {len(text)//1024} KB; consider trimming")

    # 5. geometry: rects, connectors, motion crossings ------------------
    TR = re.compile(r"translate\(\s*([-+\d.eE]+)[\s,]*([-+\d.eE]+)?\s*\)")

    def anc_offset(el):
        """Cumulative translate of all ancestors; None if any ancestor has a non-translate transform."""
        tx = ty = 0.0
        p = parent.get(el)
        while p is not None:
            tr = p.get("transform")
            if tr:
                m = TR.fullmatch(tr.strip())
                if not m:
                    return None
                tx += float(m.group(1))
                ty += float(m.group(2) or 0)
            p = parent.get(p)
        return (tx, ty)

    def has_transform_ancestor(el):
        return anc_offset(el) is None

    def shift_pts(el, pts_):
        o = anc_offset(el)
        if not o or (o[0] == 0 and o[1] == 0):
            return pts_
        return [(x_ + o[0], y_ + o[1]) for x_, y_ in pts_]

    def in_defs(el):
        p = parent.get(el)
        while p is not None:
            if local(p.tag) in ("defs", "marker", "clipPath", "mask", "pattern", "symbol"):
                return True
            p = parent.get(p)
        return False

    rects = []
    skipped_transform = 0
    for el in root.iter():
        if local(el.tag) != "rect" or in_defs(el):
            continue
        w, h = fnum(el.get("width")), fnum(el.get("height"))
        if not w or not h:
            continue
        x, y = fnum(el.get("x"), 0.0), fnum(el.get("y"), 0.0)
        if vbw and w >= 0.9 * vbw and h >= 0.9 * vbh:
            continue  # full-bleed background
        o_ = anc_offset(el)
        if o_ is None or el.get("transform"):
            skipped_transform += 1
            continue
        x, y = x + o_[0], y + o_[1]
        rects.append({"el": el, "rect": (x, y, w, h), "outline": el.get("fill") in ("none", None) and el.get("stroke") is not None})
    if skipped_transform:
        report("INFO", f"{skipped_transform} rect(s) skipped in geometry checks (rotate/scale/matrix transform on rect or ancestor; plain translate() groups are supported)")

    def rname(r):
        el = r["el"]
        pid = el.get("id")
        if not pid:
            p = parent.get(el)
            while p is not None and not p.get("id"):
                p = parent.get(p)
            pid = p.get("id") if p is not None else None
        x, y, w, h = r["rect"]
        return f"{pid or 'rect'}[{x:g},{y:g},{w:g}x{h:g}]{' (outline)' if r['outline'] else ''}"

    solid = [r for r in rects if not r["outline"]]

    # connectors: paths carrying markers
    for el in root.iter():
        if local(el.tag) != "path" or in_defs(el):
            continue
        if not (el.get("marker-end") or el.get("marker-start")) and not any(
            p is not None and (p.get("marker-end") or p.get("marker-start")) for p in [parent.get(el)]
        ):
            continue
        d = el.get("d")
        if not d or has_transform_ancestor(el):
            continue
        try:
            pts, segs, arcs = parse_path(d)
        except ValueError:
            continue
        if len(pts) < 2:
            continue
        pts = shift_pts(el, pts)
        samples = resample(pts, 1.5)
        cname = el.get("id") or d[:28]
        for r in solid:
            hits = [f for (p, f) in samples if inside(p, r["rect"], 1.5)]
            if hits:
                if inside(pts[-1], r["rect"], 1.5):
                    report("WARN", f"connector '{cname}' ends INSIDE {rname(r)}: arrow tip is in the card; end ~8px before its edge")
                else:
                    report("WARN", f"connector '{cname}' passes through {rname(r)} (between {min(hits):.2f}-{max(hits):.2f} of its length): re-route around the card; a curve that bulges into the target makes the arrowhead face backwards")
        # tip distance to nearest rect edge
        tip = pts[-1]
        best = None
        for r in solid:
            x, y, w, h = r["rect"]
            dx = max(x - tip[0], 0, tip[0] - (x + w))
            dy = max(y - tip[1], 0, tip[1] - (y + h))
            dist = math.hypot(dx, dy)
            if best is None or dist < best[0]:
                best = (dist, r)
        if best and el.get("marker-end"):
            if best[0] > 16:
                report("INFO", f"connector '{cname}': arrow tip is {best[0]:.0f}px from the nearest card ({rname(best[1])}); fine if it targets a non-rect shape, otherwise it floats")

    # connectors whose START is attached to nothing (floating stubs)
    def rect_dist(pnt, rc):
        x, y, w, h = rc
        dx = max(x - pnt[0], 0, pnt[0] - (x + w))
        dy = max(y - pnt[1], 0, pnt[1] - (y + h))
        return math.hypot(dx, dy)

    conns = []
    for el in root.iter():
        if local(el.tag) != "path" or in_defs(el) or has_transform_ancestor(el):
            continue
        marked = el.get("marker-end") or el.get("marker-start") or (parent.get(el) is not None and (parent.get(el).get("marker-end") or parent.get(el).get("marker-start")))
        d = el.get("d")
        if not marked or not d or "msg" in (el.get("class") or "").split():
            continue
        try:
            pts, _, _ = parse_path(d)
        except ValueError:
            continue
        if len(pts) >= 2:
            conns.append((el, shift_pts(el, pts)))
    for el, pts in conns:
        start, end = pts[0], pts[-1]
        near_rect = min((rect_dist(start, r["rect"]) for r in solid), default=None)
        near_conn = min((min(math.dist(start, o[0]), math.dist(start, o[-1])) for e2, o in conns if e2 is not el), default=None)
        if (near_rect is None or near_rect > 14) and (near_conn is None or near_conn > 3):
            cname = el.get("id") or el.get("d")[:28]
            report("WARN", f"connector '{cname}' starts at ({start[0]:g},{start[1]:g}) which touches no card (nearest {('%.0fpx' % near_rect) if near_rect is not None else 'n/a'}) and no other connector: it floats. Connect it to its source card edge, or move the cards so a real connector fits")

    # class="rail" connectors: plain lines between shapes, both ends must touch a card or hub
    circles = []
    for el in root.iter():
        if local(el.tag) != "circle" or in_defs(el) or has_transform_ancestor(el):
            continue
        r_ = fnum(el.get("r"))
        o_ = anc_offset(el)
        if o_ is None or el.get("filter") or el.get("opacity") == "0" or any(local(c.tag) == "animateMotion" for c in el):
            continue  # glow overlays and travellers are not hubs
        if r_ and r_ >= 6 and el.get("fill") not in ("none", None):
            circles.append((fnum(el.get("cx"), 0.0) + o_[0], fnum(el.get("cy"), 0.0) + o_[1], r_))

    def shape_gap(pnt):
        best = None
        for r_ in solid:
            g_ = rect_dist(pnt, r_["rect"])
            best = g_ if best is None else min(best, g_)
        for (cx_, cy_, rr) in circles:
            g_ = abs(math.dist(pnt, (cx_, cy_)) - rr)
            best = g_ if best is None else min(best, g_)
        return best

    rail_paths = []
    for el in root.iter():
        if local(el.tag) != "path" or in_defs(el) or has_transform_ancestor(el):
            continue
        if "rail" not in (el.get("class") or "").split() and "rail" not in (el.get("id") or ""):
            continue
        try:
            rpts, _, _ = parse_path(el.get("d") or "")
        except ValueError:
            continue
        if len(rpts) < 2:
            continue
        rpts = shift_pts(el, rpts)
        rail_paths.append((el, rpts))
        has_mk = bool(el.get("marker-end"))
        for lab, pnt, tol in (("start", rpts[0], 3.0), ("end", rpts[-1], 8.0 if has_mk else 3.0)):
            g_ = shape_gap(pnt)
            if g_ is not None and g_ > tol:
                report("WARN", f"rail {lab} ({pnt[0]:g},{pnt[1]:g}) is {g_:.0f}px from the nearest card/hub: it floats (rails must touch their cards)")
        for r_ in solid:
            if any(inside(pp, r_["rect"], 2.0) for pp, _ in resample(rpts, 2.0)):
                report("WARN", f"rail '{(el.get('d') or '')[:30]}' passes through {rname(r_)}")
    if rail_paths:
        report("INFO", f"{len(rail_paths)} rail(s) checked: every endpoint touches a card/hub unless warned above")

    # sequence diagrams: class="life" lifelines and class="msg" messages
    lifes, msg_paths = [], []
    for el in root.iter():
        if local(el.tag) != "path" or in_defs(el):
            continue
        cls = (el.get("class") or "").split()
        if "life" not in cls and "msg" not in cls:
            continue
        try:
            lp, _, _ = parse_path(el.get("d") or "")
        except ValueError:
            continue
        if len(lp) < 2:
            continue
        lp = shift_pts(el, lp)
        (lifes if "life" in cls else msg_paths).append((el, lp))

    def on_life(pnt, tol):
        return any(abs(pnt[0] - lp[0][0]) <= tol and min(lp[0][1], lp[-1][1]) - 3 <= pnt[1] <= max(lp[0][1], lp[-1][1]) + 3 for _, lp in lifes)

    if lifes and msg_paths:
        for el, mp in msg_paths:
            if not on_life(mp[0], 3.0):
                report("WARN", f"message starting at ({mp[0][0]:g},{mp[0][1]:g}) does not start on a lifeline")
            if not on_life(mp[-1], 8.0):
                report("WARN", f"message ending at ({mp[-1][0]:g},{mp[-1][1]:g}) does not end on (or 4px before) a lifeline")
        report("INFO", f"{len(msg_paths)} message(s) checked against {len(lifes)} lifeline(s)")

    # motion crossings
    for el in root.iter():
        if local(el.tag) != "animateMotion":
            continue
        par = parent.get(el)
        d = el.get("path")
        if not d:
            for c in el:
                if local(c.tag) == "mpath":
                    href = c.get("href") or c.get("{%s}href" % XLINK)
                    if href and href[1:] in ids:
                        d = ids[href[1:]].get("d")
        if not d:
            continue
        try:
            pts, segs, arcs = parse_path(d)
        except ValueError:
            continue
        if len(pts) < 2:
            continue
        pts = shift_pts(el, pts)
        if (rail_paths or msg_paths) and el.get("path"):
            if not any(math.dist(rp[0], pts[0]) <= 8 and math.dist(rp[-1], pts[-1]) <= 8 for _, rp in (rail_paths + msg_paths)):
                report("WARN", f"animateMotion path starting at ({pts[0][0]:g},{pts[0][1]:g}) matches no rail: the dot will travel somewhere no line is drawn (it should reuse a rail's exact path)")
        # accumulated parent translate is unknown; assume the traveller is drawn at (0,0)
        samples = resample(pts, 1.0)
        plen = polyline_length(pts)
        pname = (par.get("id") if par is not None and par.get("id") else (local(par.tag) if par is not None else "?"))
        # find the topmost ancestor that is a child of root for z-order
        top = par
        while top is not None and parent.get(top) is not root and parent.get(top) is not None:
            top = parent.get(top)
        idx = order.get(top, 0)
        lines = []
        for r in rects:
            fr = [f for (p, f) in samples if inside(p, r["rect"], 0.0)]
            if not fr:
                continue
            kind = ""
            if not r["outline"]:
                above = idx > order.get(r["el"], 0)
                kind = " traveller drawn OVER it (visible inside)" if above else " traveller drawn UNDER it (hidden inside)"
            lines.append(f"    {rname(r)}: enters {min(fr):.3f}, exits {max(fr):.3f}{kind}")
        dur = el.get("dur", "?")
        report("INFO", f"animateMotion on '{pname}' (dur={dur}, path length {plen:.0f}px, {segs} segment(s), calcMode={el.get('calcMode') or 'paced(default)'}):" + ("\n" + "\n".join(lines) if lines else " no rect crossings"))

    # 6. text fit -------------------------------------------------------
    # Catches the blind spot where a node's label is wider than the shape it
    # sits in. references/diagram-types.md 5 documents the limit (mono width
    # ~0.6 x font-size per char, cards add ~34px padding, subs <= 26 chars)
    # but nothing enforced it, so a long sub silently drew through its shape
    # while the linter reported 0 errors and 0 warnings.
    CH_W = 0.63      # mean glyph advance / font-size for the mono stack
    MARGIN = 6.0     # breathing room required either side of a label
    MIN_W, MIN_H = 36.0, 20.0   # below this a shape is decoration, not a container

    def font_size(el):
        fs = fnum(el.get("font-size"))
        if fs:
            return fs
        return 18.0 if el.get("font-weight") in ("600", "700", "bold") else 12.0

    def text_width(el):
        """Estimated rendered width of a <text>, honouring textLength."""
        if el.get("textLength"):
            return fnum(el.get("textLength"))
        return len("".join(el.itertext()).strip()) * font_size(el) * CH_W

    # Shapes a label could sit inside, as (label, box, inner_width). Full-bleed
    # backgrounds and anything too small to be a card are excluded, matching the
    # geometry checks above.
    shapes = []
    for el in root.iter():
        if in_defs(el):
            continue
        o_ = anc_offset(el)
        if o_ is None or el.get("transform"):
            continue
        if local(el.tag) == "rect":
            w, h = fnum(el.get("width")), fnum(el.get("height"))
            if not (w and h) or w < MIN_W or h < MIN_H:
                continue
            if vbw and w >= 0.9 * vbw and h >= 0.9 * vbh:
                continue
            x = o_[0] + fnum(el.get("x"), 0.0)
            y = o_[1] + fnum(el.get("y"), 0.0)
            shapes.append((f"card at ({x:.0f},{y:.0f}) {w:.0f}x{h:.0f}",
                           (x, y, x + w, y + h), w - 2 * MARGIN, None, None))
        elif local(el.tag) == "circle":
            r_ = fnum(el.get("r"))
            if not r_ or 2 * r_ < MIN_W:
                continue
            cx = o_[0] + fnum(el.get("cx"), 0.0)
            cy = o_[1] + fnum(el.get("cy"), 0.0)
            shapes.append((f"circle at ({cx:.0f},{cy:.0f}) r={r_:.0f}",
                           (cx - r_, cy - r_, cx + r_, cy + r_), 2 * r_ - 2 * MARGIN, cx, cy))

    for el in root.iter():
        if local(el.tag) != "text" or in_defs(el):
            continue
        body = "".join(el.itertext()).strip()
        if not body:
            continue
        o_ = anc_offset(el)
        if o_ is None:
            continue
        ty = o_[1] + fnum(el.get("y"), 0.0)
        tx = o_[0] + fnum(el.get("x"), 0.0)
        tw = text_width(el)
        # Containment uses the ANCHOR point, not the label's visual midpoint:
        # for text-anchor="middle" the anchor x is the shape's own centre, and a
        # badly overflowing label's midpoint can land well outside the shape it
        # is centred on -- which would hide exactly the case we want to catch.
        # The tightest containing shape wins; for a circle the usable width is
        # the chord at the label's baseline, not the diameter.
        host = None
        for name, (x0, y0, x1, y1), inner, cx_, cy_ in shapes:
            if inner <= 0 or not (x0 <= tx <= x1 and y0 <= ty <= y1):
                continue
            usable = inner
            if cx_ is not None:
                dy = abs(ty - cy_)
                if dy >= (y1 - y0) / 2:
                    continue
                chord = 2.0 * math.sqrt(max(((x1 - x0) / 2) ** 2 - dy ** 2, 0.0))
                usable = chord - 2 * MARGIN
            if host is None or usable < host[1]:
                host = (name, usable)
        if host and tw > host[1]:
            report("WARN", f"<text> '{body[:40]}' needs ~{tw:.0f}px but its {host[0]} "
                           f"gives ~{host[1]:.0f}px - the label will draw through the shape")

    return tally(path, quiet)


def tally(path, quiet=False):
    """Print this file's summary and return its (errors, warnings)."""
    finish(path, quiet)
    errs = sum(1 for l, _ in problems if l == "ERROR")
    warns = sum(1 for l, _ in problems if l == "WARN")
    return errs, warns


def finish(path, quiet=False):
    errs = [m for l, m in problems if l == "ERROR"]
    warns = [m for l, m in problems if l == "WARN"]
    infos = [m for l, m in problems if l == "INFO"]
    for level in ("ERROR", "WARN", "INFO"):
        if quiet and level == "INFO":
            continue
        for l, m in problems:
            if l == level:
                print(f"{level}: {m}")
    print(f"\n{path}: {len(errs)} error(s), {len(warns)} warning(s), {len(infos)} note(s)")
    return 1 if errs else 0


def main(argv):
    """Lint every file given on the command line.

    Accepts many paths at once, because the documented workflow
    (`lint_svg_anim.py $(git diff --name-only '*.svg')`) passes a list. An
    earlier version read only argv[1] and silently ignored the rest while
    still exiting 0, so a multi-file invocation appeared to pass having
    checked one file.

    Exit code is non-zero if ANY file has an error.
    """
    args = [a for a in argv[1:] if not a.startswith("-")]
    quiet = "--quiet" in argv
    if not args:
        print(__doc__)
        return 2

    total_e = total_w = 0
    failed = []
    for path in args:
        if len(args) > 1:
            print(f"=== {path}")
        e, w = lint_one(path, quiet)
        total_e += e
        total_w += w
        if e:
            failed.append(path)

    if len(args) > 1:
        print(f"\n{'-' * 60}")
        print(f"{len(args)} file(s): {total_e} error(s), {total_w} warning(s) total")
        if failed:
            print("files with errors: " + ", ".join(failed))
    return 1 if total_e else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
