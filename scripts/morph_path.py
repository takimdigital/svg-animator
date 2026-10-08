#!/usr/bin/env python3
"""Morph between two paths that do not share a command structure, with no library.

The problem
-----------
`<animate attributeName="d">` interpolates only when both paths have the *same
structure* - exactly the same commands, in the same order, of the same type.
From the SVG 2 spec:

  "Path data strings are interpolated smoothly when the path data strings have
   the same structure, (i.e. exactly the same number and types of path data
   commands which are in the same order). If an animation is specified and the
   lists of path data commands do not have the same structure, then the values
   must be interpolated using the discrete animation type."

So a square cannot smoothly morph into a triangle - it *snaps*. Verified in a
browser: a diamond/line pair jumps between frames rather than tweening.

GSAP's MorphSVG solves this and is excellent, but it needs GSAP, and it needs
JavaScript - which means the file stops working inside a README `<img>`.
This module solves the same problem in the only place a self-contained `.svg`
can: at author time, in Python.

The method
----------
  1. flatten both paths to polylines (curves and arcs included)
  2. resample both to the same number of points, by arc length
  3. re-emit both as one uniform signature: `M` + (n-1) `C` + `Z`

Two paths with the same signature interpolate perfectly, because that is the
only case SMIL supports. This is the ~80% of MorphSVG that fits in a README.

Usage
-----
As a library, which is how the generator uses it:

    from morph_path import morph_pair
    a, b = morph_pair("M50 5 L61 38 ... Z", "M50 8 A42 42 0 1 1 49.9 8 Z")
    # -> both are "M ... C ... C ... Z" with identical command counts

As a command, to inspect a pair before using it:

    python scripts/morph_path.py square.svg triangle.svg
    python scripts/morph_path.py --spec '{"a": "M0 0 ...", "b": "..."}'

No dependencies: pure Python 3, including its own bezier and arc flattening,
because the alternative (the browser's getPointAtLength) is unavailable in the
generator's CI job, and a generator that needs a browser is not reproducible.
"""
import math
import re

# Leading whitespace matters: "M 50 5 L 61 38" has a space between the command
# letter and its numbers, and pattern.match() anchors at the position, so a
# pattern that starts at a digit silently matches nothing at all.
NUM = re.compile(r"\s*(-?\d*\.?\d+(?:[eE][-+]?\d+)?)")
CMD = re.compile(r"[MmLlHhVvCcSsQqTtAaZz]")


# ---------------------------------------------------------------- parsing

def parse(d):
    """-> [(command_letter, [floats]), ...] with relative commands made absolute."""
    out = []
    for m in CMD.finditer(d):
        letter = m.group(0)
        j = m.end()
        # consume the numbers that belong to this command
        nums = []
        while True:
            k = NUM.match(d, j)
            if not k:
                break
            nums.append(float(k.group(1)))
            j = k.end()
        up = letter.upper()
        step = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6, "S": 4, "Q": 4,
                "T": 2, "A": 7, "Z": 0}[up]
        if step and (len(nums) % step):
            nums = nums[:len(nums) - (len(nums) % step)]
        # Z carries no numbers, so the group loop below would drop it entirely
        # and the shape would silently stop being closed.
        if up == "Z":
            out.append(("Z", []))
        else:
            groups = [nums[k:k + step] for k in range(0, len(nums), step)] if step else []
            for g in groups:
                out.append((letter, g))
    # absolutise everything against the running cursor
    res = []
    cur = (0.0, 0.0)
    start = (0.0, 0.0)
    prev_c2 = None
    prev_q = None
    for letter, g in out:
        up = letter.upper()
        if up == "Z":
            res.append(("Z", []))
            cur = start
            prev_c2 = prev_q = None
            continue
        if up == "M":
            p = _abs(letter, g[:2], cur)
            res.append(("L", [p[0], p[1]]))
            cur = p
            start = p
            prev_c2 = prev_q = None
        elif up == "L":
            p = _abs(letter, g[:2], cur)
            res.append(("L", [p[0], p[1]]))
            cur = p
            prev_c2 = prev_q = None
        elif up == "H":
            x = g[0] + cur[0] if letter.islower() else g[0]
            res.append(("L", [x, cur[1]]))
            cur = (x, cur[1])
            prev_c2 = prev_q = None
        elif up == "V":
            y = g[0] + cur[1] if letter.islower() else g[0]
            res.append(("L", [cur[0], y]))
            cur = (cur[0], y)
            prev_c2 = prev_q = None
        elif up == "C":
            p1 = _abs(letter, g[0:2], cur)
            p2 = _abs(letter, g[2:4], cur)
            p3 = _abs(letter, g[4:6], cur)
            res.append(("C", [p1, p2, p3]))
            cur = p3
            prev_c2 = p2
            prev_q = None
        elif up == "S":
            p2 = _abs(letter, g[0:2], cur)
            p3 = _abs(letter, g[2:4], cur)
            p1 = (2 * cur[0] - prev_c2[0], 2 * cur[1] - prev_c2[1]) if prev_c2 else cur
            res.append(("C", [p1, p2, p3]))
            cur = p3
            prev_c2 = p2
            prev_q = None
        elif up == "Q":
            q = _abs(letter, g[0:2], cur)
            p = _abs(letter, g[2:4], cur)
            res.append(("Q", [q, p]))
            cur = p
            prev_q = q
            prev_c2 = None
        elif up == "T":
            p = _abs(letter, g[0:2], cur)
            q = (2 * cur[0] - prev_q[0], 2 * cur[1] - prev_q[1]) if prev_q else cur
            res.append(("Q", [q, p]))
            cur = p
            prev_q = q
            prev_c2 = None
        elif up == "A":
            rx, ry, rot, laf, sf, x, y = g[:7]
            p = _abs(letter, [x, y], cur)
            res.append(("A", [rx, ry, rot, laf, sf, p[0], p[1]]))
            cur = p
            prev_c2 = prev_q = None
    return res


def _abs(letter, g, cur):
    if letter.islower():
        return (g[0] + cur[0], g[1] + cur[1])
    return (g[0], g[1])


# ------------------------------------------------------------- flattening

def _bezier(p0, p1, p2, p3, steps=24):
    out = []
    for i in range(1, steps + 1):
        t = i / steps
        u = 1 - t
        x = u * u * u * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t * t * t * p3[0]
        y = u * u * u * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t * t * t * p3[1]
        out.append((x, y))
    return out


def _arc(p0, rx, ry, rot, laf, sf, p1, steps=28):
    """Endpoint -> centre parameterisation, per the SVG implementation notes."""
    if rx == 0 or ry == 0 or (abs(p0[0] - p1[0]) < 1e-9 and abs(p0[1] - p1[1]) < 1e-9):
        return [p1]
    rx, ry = abs(rx), abs(ry)
    phi = math.radians(rot)
    cosp, sinp = math.cos(phi), math.sin(phi)
    dx2, dy2 = (p0[0] - p1[0]) / 2.0, (p0[1] - p1[1]) / 2.0
    x1p = cosp * dx2 + sinp * dy2
    y1p = -sinp * dx2 + cosp * dy2
    lam = (x1p * x1p) / (rx * rx) + (y1p * y1p) / (ry * ry)
    if lam > 1:
        s = math.sqrt(lam)
        rx, ry = rx * s, ry * s
    num = rx * rx * ry * ry - rx * rx * y1p * y1p - ry * ry * x1p * x1p
    den = rx * rx * y1p * y1p + ry * ry * x1p * x1p
    co = math.sqrt(max(0.0, num / den)) if den else 0.0
    if laf == sf:
        co = -co
    cxp = co * rx * y1p / ry
    cyp = -co * ry * x1p / rx
    cx = cosp * cxp - sinp * cyp + (p0[0] + p1[0]) / 2.0
    cy = sinp * cxp + cosp * cyp + (p0[1] + p1[1]) / 2.0

    def ang(ux, uy, vx, vy):
        dot = ux * vx + uy * vy
        ln = math.hypot(ux, uy) * math.hypot(vx, vy)
        a = math.acos(max(-1.0, min(1.0, dot / ln))) if ln else 0.0
        return -a if ux * vy - uy * vx < 0 else a

    th1 = ang(1, 0, (x1p - cxp) / rx, (y1p - cyp) / ry)
    dth = ang((x1p - cxp) / rx, (y1p - cyp) / ry,
              (-x1p - cxp) / rx, (-y1p - cyp) / ry)
    if not sf and dth > 0:
        dth -= 2 * math.pi
    elif sf and dth < 0:
        dth += 2 * math.pi
    out = []
    for i in range(1, steps + 1):
        th = th1 + dth * i / steps
        ex = cosp * rx * math.cos(th) - sinp * ry * math.sin(th) + cx
        ey = sinp * rx * math.cos(th) + cosp * ry * math.sin(th) + cy
        out.append((ex, ey))
    return out


def flatten(d, curve_steps=24):
    """-> (points, closed). Points are absolute (x, y)."""
    segs = parse(d)
    pts = []
    cur = (0.0, 0.0)
    start = (0.0, 0.0)      # start of the current subpath, where Z returns to
    closed = False
    for idx, (cmd, g) in enumerate(segs):
        if cmd == "L":
            cur = (g[0], g[1])
            pts.append(cur)
            if idx == 0:
                start = cur
        elif cmd == "C":
            # a bare C with no preceding point starts a new subpath at the origin
            if idx == 0 and not pts:
                pts.append(cur)
                start = cur
            p1, p2, p3 = g[0], g[1], (g[2][0], g[2][1])
            pts.extend(_bezier(cur, p1, p2, p3, curve_steps))
            cur = p3
        elif cmd == "Q":
            if idx == 0 and not pts:
                pts.append(cur)
                start = cur
            q, p = g[0], (g[1][0], g[1][1])
            c1 = (cur[0] + 2.0 / 3 * (q[0] - cur[0]), cur[1] + 2.0 / 3 * (q[1] - cur[1]))
            c2 = (p[0] + 2.0 / 3 * (q[0] - p[0]), p[1] + 2.0 / 3 * (q[1] - p[1]))
            pts.extend(_bezier(cur, c1, c2, p, curve_steps))
            cur = p
        elif cmd == "A":
            if idx == 0 and not pts:
                pts.append(cur)
                start = cur
            p1 = (g[5], g[6])
            pts.extend(_arc(cur, g[0], g[1], g[2], int(g[3]), int(g[4]), p1))
            cur = p1
        elif cmd == "Z":
            closed = True
            cur = start
    if not pts:
        pts = [start]
    return pts, closed


# ------------------------------------------------------------- resampling

def _lengths(pts, closed):
    seq = list(pts) + ([pts[0]] if closed else [])
    seg = [math.hypot(seq[i + 1][0] - seq[i][0], seq[i + 1][1] - seq[i][1])
           for i in range(len(seq) - 1)]
    return seq, seg, sum(seg)


def resample(d, n, curve_steps=24):
    """-> n points spread evenly by arc length along d."""
    pts, closed = flatten(d, curve_steps)
    if len(pts) < 2:
        return [pts[0]] * n, closed
    seq, seg, total = _lengths(pts, closed)
    if total <= 0:
        return [pts[0]] * n, closed
    out = []
    j = 0
    acc = 0.0
    for k in range(n):
        target = total * k / (n - 1) if n > 1 else 0.0
        while j < len(seg) - 1 and acc + seg[j] < target:
            acc += seg[j]
            j += 1
        if seg[j] <= 0:
            out.append(seq[j])
            continue
        t = (target - acc) / seg[j]
        a, b = seq[j], seq[j + 1]
        out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    return out, closed


# ------------------------------------------------------------- re-emitting

def to_uniform(points, closed=True):
    """Catmull-Rom through points, emitted as a single M + n C [+ Z] signature."""
    p = list(points)
    if closed:
        ext = [p[-1]] + p + [p[0], p[1]]
    else:
        ext = [p[0]] + p + [p[-1]]
    if len(ext) < 4:
        d = "M %.2f %.2f" % (p[0][0], p[0][1])
        return d + (" Z" if closed else "")

    def f(v):
        return ("%.2f" % v).rstrip("0").rstrip(".")

    d = "M %s %s" % (f(ext[1][0]), f(ext[1][1]))
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6.0, p1[1] + (p2[1] - p0[1]) / 6.0)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6.0, p2[1] - (p3[1] - p1[1]) / 6.0)
        d += " C %s %s %s %s %s %s" % (f(c1[0]), f(c1[1]), f(c2[0]), f(c2[1]),
                                       f(p2[0]), f(p2[1]))
    return d + (" Z" if closed else "")


def _best_offset(pa, pb):
    """Index shift of pb that minimises total travel from pa.

    Resampling pairs points by equal arc-length fraction, which fixes the
    correspondence at whatever point each path happens to start. A circle and a
    heart that both "start at the top" still pair the circle's right side with
    the heart's left notch, and the pair passes through a collapsed blob on the
    way. Trying every cyclic shift and keeping the cheapest fixes that for about
    a dozen lines and costs nothing at runtime.

    Returns (offset, mean_squared_travel).
    """
    n = len(pa)
    if n != len(pb) or n == 0:
        return 0, 0.0
    best_k, best_cost = 0, None
    for k in range(n):
        cost = 0.0
        for i in range(n):
            dx = pa[i][0] - pb[(i + k) % n][0]
            dy = pa[i][1] - pb[(i + k) % n][1]
            cost += dx * dx + dy * dy
        if best_cost is None or cost < best_cost:
            best_cost, best_k = cost, k
    return best_k, (best_cost / n if best_cost is not None else 0.0)


def subpaths(d):
    """How many separate subpaths d contains (each M starts one)."""
    n = 0
    for m in CMD.finditer(d):
        if m.group(0) in "Mm":
            n += 1
    return max(1, n)


def morph_pair(d_a, d_b, n=48, curve_steps=24, align=True):
    """-> (a', b') both in one identical command signature, ready for <animate d>.

    n is the number of samples per path. Higher is smoother and costs file
    size roughly linearly: 48 is ~1.9 KB per path, 96 is ~3.8 KB.

    align=True picks the cyclic shift of b that minimises total travel, which is
    what stops a morph diving through the middle of its own bounding box. Set it
    False to keep the raw arc-length correspondence.
    """
    # A multi-subpath path is out of scope, and quietly so: flattening a ring
    # (outer circle, then inner circle reversed) into one polyline produces a
    # shape that is wrong at every frame rather than obviously broken. Refuse
    # instead, so the caller is told rather than handed garbage.
    if subpaths(d_a) > 1 or subpaths(d_b) > 1:
        raise ValueError(
            "morph_pair handles one subpath per shape, not %d and %d. A ring or "
            "any shape with a hole pairs its outer and inner contours into a "
            "single polyline, which looks wrong at every frame instead of "
            "failing visibly. Split it, or animate the pieces separately."
            % (subpaths(d_a), subpaths(d_b)))

    pa, ca = resample(d_a, n, curve_steps)
    pb, cb = resample(d_b, n, curve_steps)

    # A closed shape ends with Z and an open one does not, so the two can never
    # share a command signature, which is the only form SMIL interpolates. Found
    # by tests/test_morph_path.py after a closed star was paired with an open
    # wave: the pair came out "MCCCZ" against "MCCC" and silently snapped.
    if ca != cb:
        raise ValueError(
            "one shape is closed (ends with Z) and the other is not, so they "
            "cannot share a command signature and the morph would snap instead "
            "of tween. Close the open path with Z, or open the closed one.")
    if align and ca == cb and len(pa) == len(pb):
        k, _ = _best_offset(pa, pb)
        if k:
            pb = pb[k:] + pb[:k]
    return to_uniform(pa, ca), to_uniform(pb, cb)


def signature(d):
    """-> the command letters in order, for asserting two paths match."""
    return "".join(m.group(0) for m in CMD.finditer(d))


def main():
    import argparse
    import json

    ap = argparse.ArgumentParser()
    ap.add_argument("a", help="path data for the first shape, or a spec json with keys a and b")
    ap.add_argument("b", nargs="?", help="path data for the second shape")
    ap.add_argument("--n", type=int, default=48)
    ap.add_argument("--show", action="store_true", help="print the pair's path data")
    a = ap.parse_args()

    if a.b:
        d1, d2 = a.a, a.b
    else:
        spec = json.loads(a.a)
        d1, d2 = spec["a"], spec["b"]

    x, y = morph_pair(d1, d2, a.n)
    same = signature(x) == signature(y)
    print("  a' %6d chars  %d commands" % (len(x), len(signature(x))))
    print("  b' %6d chars  %d commands" % (len(y), len(signature(y))))
    print("  signatures match: %s   (this is what makes SMIL interpolate)" % same)
    if not same:
        print("  WARNING: signatures differ, so the morph will snap rather than tween")
    if a.show:
        print("\n  a' = %s\n" % x)
        print("  b' = %s" % y)
    return 0 if same else 1


if __name__ == "__main__":
    raise SystemExit(main())