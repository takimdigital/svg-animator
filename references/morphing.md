# Morphing shapes that do not share a command structure

> The one thing plain SMIL cannot do on its own, solved without a library.

## The rule you will hit first

`<animate attributeName="d">` interpolates **only** when both paths have the
same structure. SVG 2, on path data:

> "Path data strings are interpolated smoothly when the path data strings have
> the same structure, (i.e. exactly the same number and types of path data
> commands which are in the same order). If an animation is specified and the
> lists of path data commands do not have the same structure, then the values
> must be interpolated using the **discrete** animation type."

So `M L L L Z` (a square) does **not** tween to `M L L Z` (a triangle). It
snaps. Verified in a browser: a diamond and a line jump between frames with no
in-between state, which is exactly what "discrete" means.

This is the single most common morph bug, and it is invisible in a linter
because the markup is well-formed.

## What GSAP does, and what it costs

GSAP's MorphSVGPlugin handles mismatched structures, plus `type:"rotational"`
(interpolate angle and length instead of raw coordinates) and `curveMode:true`.
It is excellent. It also requires GSAP and JavaScript — and an SVG carrying
`<script>` **stops animating inside a README `<img>`**, which is the entire
point of this skill.

So: don't reach for a library, fix it at author time.

## The method

Three steps, all in `scripts/morph_path.py`:

1. **Flatten** both paths to polylines. Curves become line segments; arcs go
   through the endpoint-to-centre parameterisation from the SVG implementation
   notes. Relative commands (`m`, `l`, `h`, `v`) are made absolute first.
2. **Resample** both to the *same number of points*, evenly by arc length.
3. **Re-emit** both as one uniform signature: `M` + (n−1) `C` + `Z`, using
   Catmull-Rom through the points.

Identical signatures are the only case SMIL interpolates, so that is exactly what
you hand it:

```python
from morph_path import morph_pair, signature

a, b = morph_pair(
    "M50 4 L61 37 L96 37 L68 58 L79 93 L50 72 L21 93 L32 58 L4 37 L39 37 Z",  # star
    "M50 6 A44 44 0 1 1 49.9 6 Z",                                            # circle
    n=34,
)
assert signature(a) == signature(b)          # M + 34 C's: the only shape that tweens
```

```xml
<path d="…" fill="#A78BFA">
  <animate attributeName="d" values="A;B;A" keyTimes="0;0.5;1"
           dur="13s" repeatCount="indefinite"/>
</path>
```

No library, no JavaScript, works in `<img>`, works in `compose`, passes the linter.

## Align the correspondence, or the morph dives through the middle

Resampling pairs points by **equal arc-length fraction**, which fixes the
correspondence at whatever point each path happens to start. That is usually
wrong: a circle and a heart that both begin near the top still pair the
circle's right side with the heart's left notch, and the shape collapses to a
sliver on the way across.

`_best_offset()` tries every cyclic shift of the second point list and keeps the
one with the least total travel. Measured over the six pairs in
`assets/specs/morph-shapes.json`:

| pair | naive | aligned | |
|---|---|---|---|
| circle → heart | 7377 | 102 | **99 % better** |
| heart → bolt | 3270 | 1954 | 40 % better |
| drop → cross | 293 | 227 | 23 % better |
| cross → star | 246 | 201 | 18 % better |
| **total** | **12985** | **4283** | **67 % better** |

Twelve lines, no runtime cost, and it is the difference between a morph that
looks deliberate and one that looks like a glitch. This is on by default; pass
`align=False` to keep the raw correspondence.

## What it still cannot do

**Shapes with a hole.** A ring, a donut, the bowl of an `o` — anything with two
subpaths — has its outer and inner contours flattened into *one* polyline, and
the result is wrong at every single frame rather than obviously broken. A
refusal is much better than that, so `morph_pair` raises:

```
morph_pair handles one subpath per shape, not 2 and 1. A ring or any shape with
a hole pairs its outer and inner contours into a single polyline, which looks
wrong at every frame instead of failing visibly.
```

Split the shape and animate the pieces, or use a mask.

**Mid-morph aesthetics are still approximate.** Arc-length pairing produces a
tween, not a designed in-between. Some pairs read beautifully (star → circle,
circle → heart once aligned); others still pinch — `heart → bolt` in the shipped
example passes through a thin sliver. GSAP's `type:"rotational"` fixes that by
interpolating angle and length instead of raw x/y. If you need that, you need
GSAP, and you have chosen a different target. **Look at the frames and pick
pairs that read well** — that is what the shipped spec does.

**File size.** Each sample is roughly 20 characters of path data, so cost grows
linearly: `n=34` is about 1.4 KB per path, `n=96` about 3.9 KB. Because
`values` holds the whole chain, a 6-cell cycle stores 12 paths. The shipped
example is 39 KB and the gallery tile 80 KB, against a's budget is ~100 KB.

## The generator type

`type: "morph"` builds the whole thing on one master clock:

```json
{
  "type": "morph",
  "theme": "violet",
  "dur": 13,
  "cols": 3,
  "cell": 176,
  "samples": 34,
  "hold": 0.66,
  "forms": ["star", "circle", "heart", "bolt", "drop", "cross"]
}
```

| field | meaning |
|---|---|
| `forms` | which named forms, in morph order; the last wraps to the first |
| `samples` | points per path (`n` above). Lower is smaller and choppier |
| `hold` | fraction of its slot each cell spends visibly morphing |
| `cols`, `cell`, `gap`, `pad` | grid geometry |

Twelve named forms ship in `scripts/things_morph.py`: `star`, `circle`, `heart`,
`square`, `bolt`, `drop`, `ring`, `cross`, `leaf`, `wave`, `arrow`, `hexagon`.

The builder asserts `signature(a) == signature(b)` for every pair and exits
loudly if not. Without that check a resampler regression would produce a file
that lints clean, verifies clean, and simply does not move — the hardest kind of
bug to notice by eye.

## See also

- `references/multi-step.md` — sequencing phases, `keyPoints` dwell, `textPath`
- `references/physics.md` — when the motion should obey a law instead
- `scripts/morph_path.py` — the module, runnable: `python scripts/morph_path.py "d1" "d2"`
- `assets/examples/morph-shapes.svg` — six forms, lints and verifies clean
