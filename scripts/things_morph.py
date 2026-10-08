"""`morph` - shape morphing between forms that share no command structure.

The point of this type is the thing plain SMIL cannot do on its own.

`<animate attributeName="d">` interpolates only when both paths have the same
structure - same commands, same order, same count. SVG 2 says so outright, and
otherwise it falls back to *discrete*, which means the shape snaps between
frames. Verified in a browser: a diamond and a line jump rather than tween.

GSAP's MorphSVG handles mismatched structures, but it needs GSAP and it needs
JavaScript, so the file stops animating inside a README `<img>`.

This builder closes that gap at author time. `morph_path.py` flattens both
shapes to polylines, resamples them to the same number of points by arc length,
and re-emits both as one uniform `M + n*C + Z` signature. Identical signatures
are the only case SMIL interpolates, so that is exactly what we hand it. No
library, no JavaScript, works in `<img>`.

The forms below are deliberately unlike each other - different command counts,
curves against polylines. If the resampling were not working they would not
tween, which is the point. The signature guarantee is asserted at build time
rather than assumed, because a silent failure here looks like a shape that
merely fails to move.
"""
import math
import sys

from diagram_common import FONT, F, esc, part
from morph_path import morph_pair, signature

# Named forms in a 100x100 box. One subpath each: a shape with a hole (ring,
# donut, the bowl of an o) pairs its two contours into a single polyline and
# looks wrong at every frame, so morph_path.py refuses those outright.
FORMS = {
    "star": "M50 4 L61 37 L96 37 L68 58 L79 93 L50 72 L21 93 L32 58 L4 37 L39 37 Z",
    "circle": "M50 6 A44 44 0 1 1 49.9 6 Z",
    "heart": ("M50 90 C20 68 4 48 4 31 C4 15 16 5 30 5 C40 5 46 11 50 19 "
              "C54 11 60 5 70 5 C84 5 96 15 96 31 C96 48 80 68 50 90 Z"),
    "square": "M6 6 L94 6 L94 94 L6 94 Z",
    "bolt": "M56 4 L22 54 L44 54 L38 96 L78 42 L54 42 Z",
    "drop": "M50 6 C72 34 88 52 88 66 A38 38 0 0 1 12 66 C12 52 28 34 50 6 Z",
    "ring": "M50 8 A42 42 0 1 1 49.9 8 Z M50 26 A24 24 0 1 0 50.1 26 Z",  # 2 subpaths: refused
    "cross": "M38 6 L62 6 L62 38 L94 38 L94 62 L62 62 L62 94 L38 94 L38 62 L6 62 L6 38 L38 38 Z",
    "leaf": "M50 6 C82 26 88 58 50 94 C12 58 18 26 50 6 Z",
    "wave": "M4 60 C18 30 32 30 50 60 C68 90 82 90 96 60",
    "arrow": "M6 50 L70 50 L70 26 L96 50 L70 74 L70 50 Z",
    "hexagon": "M50 4 L90 27 L90 73 L50 96 L10 73 L10 27 Z",
}


def build_morph(spec, th, idp=""):
    forms = spec.get("forms") or ["star", "circle", "heart", "bolt"]
    for f in forms:
        if f not in FORMS:
            sys.exit("unknown form %r; choose from %s" % (f, sorted(FORMS)))
    n = int(spec.get("samples", 34))
    dur = float(spec.get("dur", 12))
    # A cycle: each form morphs into the next, the last wraps back to the first.
    chain = []
    for i, f in enumerate(forms):
        g = forms[(i + 1) % len(forms)]
        a, b = morph_pair(FORMS[f], FORMS[g], n)
        if signature(a) != signature(b):
            # Without this the shape would silently stop morphing and the only
            # symptom would be that it "looks static", which is easy to miss.
            sys.exit("morph_path.py returned mismatched signatures for %s -> %s; "
                     "that is a bug in the resampler, not in the spec" % (f, g))
        chain.append((a, b))

    cols = int(spec.get("cols", 2))
    rows = int(math.ceil(len(forms) / float(cols)))
    cell = int(spec.get("cell", 190))
    gap = int(spec.get("gap", 26))
    pad = int(spec.get("pad", 28))
    top = spec.get("title_zone", 84 if spec.get("title") else pad)
    label_h = int(spec.get("label_h", 28))

    W = pad * 2 + cols * cell + (cols - 1) * gap
    H = top + rows * (cell + label_h) + (rows - 1) * gap + pad

    # One master clock. Each cell owns a slot, holds its pair for most of that
    # slot, and rests at its own first value so the loop restarts clean.
    hold = float(spec.get("hold", 0.66))
    slot = 1.0 / len(forms)
    fade = min(0.05, slot * 0.16)

    body = []
    for i, f in enumerate(forms):
        r, c = divmod(i, cols)
        x = pad + c * (cell + gap)
        y = top + r * (cell + label_h + gap)
        a, b = chain[i]
        t0 = i * slot
        t1 = min(1.0, t0 + hold * slot)

        pairs = [(0.0, a)]
        if t0 - fade > 1e-6:
            pairs.append((round(t0 - fade, 4), a))
        pairs.append((round(t0, 4), a))
        pairs.append((round(t1, 4), b))
        if t1 + fade < 1.0 - 1e-6:
            pairs.append((round(t1 + fade, 4), b))
        pairs.append((1.0, a))

        # keyTimes: start at 0, never decrease, end at 1, no duplicates
        kts, vals, last, seen = [], [], -1.0, set()
        for k, v in pairs:
            k = round(max(k, last, 0.0), 4)
            if k in seen and k != 1.0:
                continue
            seen.add(k)
            kts.append(k)
            vals.append(v)
            last = k
        if kts[0] != 0.0:
            kts.insert(0, 0.0)
            vals.insert(0, vals[0])
        if kts[-1] != 1.0:
            kts.append(1.0)
            vals.append(vals[-1])

        body.append(
            '  <g transform="translate(%s,%s)">\n'
            '    <rect width="%s" height="%s" rx="%s" fill="%s" stroke="%s" stroke-opacity="0.4"/>\n'
            '    <path d="%s" fill="%s" fill-opacity="0.92">\n'
            '      <animate attributeName="d" values="%s" keyTimes="%s" dur="%ss" repeatCount="indefinite"/>\n'
            '    </path>\n'
            '    <text x="%s" y="%s" text-anchor="middle" font-family="%s" font-size="13"'
            ' font-weight="700" fill="%s" opacity="0.8">%s</text>\n'
            '  </g>'
            % (F(x), F(y), F(cell), F(cell), F(cell * 0.13),
               th["surface"], th["stroke_dim"], a, th["accent"],
               ";".join(vals), ";".join(F(k) for k in kts), F(dur),
               F(cell // 2), F(cell + 20), FONT, th["muted"], esc(f)))

    desc = ("Shape morphing across %d forms that share no path-command structure "
            "(%s). Each path is flattened, resampled by arc length and re-emitted as "
            "one uniform M + C + Z signature, which is the only form SMIL interpolates. "
            "No library and no JavaScript, so it runs inside a README image."
            % (len(forms), ", ".join(forms)))
    sb = ["type=morph  forms=%d  samples=%d  period=%gs  (each cell owns 1/%d of the "
          "master clock and rests at its own first value)" % (len(forms), n, dur, len(forms))]
    return part("\n".join(body) + "\n", W, H, sb, False, desc)


EXTRA_MORPH = {"morph": build_morph}
