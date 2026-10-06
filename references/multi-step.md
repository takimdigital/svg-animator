# Multi-step choreography and text on a path

> Two techniques the cookbook did not cover: sequencing several phases so they
> cannot drift, and setting type on a curve. Both verified by rendering.

## 1 · Sequencing phases without drift

### Do not hand-write `begin="ref.end"`

SMIL can chain animations by reference:

```xml
<animate id="ph1" .../>
<animate begin="ph1.end" .../>
```

It is real and it works, but for a *finite* sequence it is the wrong tool, and
hand-deriving the offsets is where it goes wrong. An earlier attempt at this used
`begin="ph1.begin+2s"` with hand-guessed `keyTimes`, and produced a schedule where
only the first phase ever lit. Two linter errors caught it.

The reason: every phase then has its own `dur` and its own reference chain, so
nothing forces them onto a common timeline. Change one phase's duration and the
whole sequence shifts.

### Lay phases out on one master clock, then derive everything

Principle 4 already says one clock per graphic. Apply it literally and the
chaining problem disappears — no references needed at all:

```python
DUR, LIT, DIM, FADE = 12.0, 1.0, 0.28, 0.035
phases = [(0.00, 0.26), (0.28, 0.52), (0.54, 0.78), (0.80, 0.92)]

def sched(a, b):
    """One phase's keyTimes/values on the master clock. Starts at 0, ends at 1."""
    if a - FADE <= 0.0:                       # first phase: already lit at t=0
        pts = [(0.0, LIT), (b, LIT), (min(1.0, b + FADE), DIM), (1.0, DIM)]
    else:
        pts = [(0.0, DIM), (a - FADE, DIM), (a, LIT), (b, LIT),
               (min(1.0, b + FADE), DIM), (1.0, DIM)]
    ks, vs, last = [], [], -1.0
    for k, v in pts:
        k = min(max(k, 0.0), 1.0)
        if k < last:                          # never let keyTimes go backwards
            k = last
        ks.append(k); vs.append(v); last = k
    ks[0], vs[0] = 0.0, vs[0]                 # linter: must start at 0
    ks[-1], vs[-1] = 1.0, vs[-1]              # linter: must end at 1
    return ks, vs
```

Produces, for four phases:

```
build  keyTimes 0.000 0.260 0.295 1.000   values 1.00 1.00 0.28 0.28
test   keyTimes 0.000 0.245 0.280 0.520 0.555 1.000   values 0.28 0.28 1.00 1.00 0.28 0.28
stage  keyTimes 0.000 0.505 0.540 0.780 0.815 1.000   values 0.28 0.28 1.00 1.00 0.28 0.28
ship   keyTimes 0.000 0.765 0.800 0.920 0.955 1.000   values 0.28 0.28 1.00 1.00 0.28 0.28
```

Three rules the linter enforces, all of which the first attempt broke:

1. `keyTimes` must start at `0`
2. `keyTimes` must be non-decreasing
3. `keyTimes` must end at `1`

And one it does not: **fade back to `DIM` shortly after the window ends** rather
than stretching the last keyframe to 1, or the phase stays lit for the rest of
the loop. The linter has a check for exactly this and it fires on the naive
version.

Verified: seven sampled frames show `build → test → stage → ship` lighting in
sequence, all four dim again at t=11.9 s (the rest pose). Lints 0/0.

### Make the traveller dwell, not glide

A dot that moves at constant speed across phases the reader is trying to follow
is a legibility bug. `keyPoints` + `keyTimes` lets it hold position inside each
phase:

```python
pts, kts = [], []
for i in range(len(rows)):
    a, b = phases[i]
    x = i / (len(rows) - 1)
    pts += [x, x]                 # same position at both ends of the phase
    kts += [a, b]                 # so it sits still for the phase's duration
```

```xml
<animateMotion dur="12s" calcMode="linear"
              keyPoints="0.000;0.000;0.333;0.333;0.667;0.667;1.000;1.000"
              keyTimes="0.000;0.260;0.280;0.520;0.540;0.780;0.800;0.920"
              repeatCount="indefinite" path="M20 150 L450 150"/>
```

Eight keyframes: arrive, hold, move, hold. `keyPoints` must stay within `0..1`
and stay non-decreasing, and `keyTimes` must start at 0 — the linter checks all
three.

### When syncbase references *are* right

Use `begin="..."` references for **event** sync, not for a fixed schedule:

| form | fires when |
|---|---|
| `begin="other.begin"` | that animation starts |
| `begin="other.end"` | it finishes its active duration |
| `begin="other.begin+2s"` | two seconds after it starts |
| `begin="other.repeat(2)"` | on its **third** iteration |

`repeat(n)` is the one the cookbook never mentions and it is how you build
"every third cycle does something different" — a recurring sweep, a periodic
double-pulse. For a fixed loop, one master clock is simpler and cannot drift.

## 2 · `textPath` — text on a curve

One attribute puts a wordmark on a circular badge, a ribbon or an arc. No glyph
outlines, no per-character positioning.

```xml
<defs>
  <path id="arc" d="M50 170 A120 120 0 0 1 290 170" fill="none"/>
</defs>

<text font-family="'JetBrains Mono',ui-monospace,monospace" font-size="16"
      font-weight="700" letter-spacing="0.8" fill="url(#g)">
  <textPath href="#arc" startOffset="50%" text-anchor="middle">SVG · TEXT · ON · A · PATH</textPath>
</text>
```

- `href="#arc"` — the path to follow. `fill="none"` on the path itself; you want
  the geometry, not a visible line
- `startOffset="50%" text-anchor="middle"` — centre the string on the path
- `side="left"` flips which side of a vertical path the text sits on
- the `<textPath>` inherits `font-size`, `letter-spacing` and `fill` from its parent
  `<text>`, so it is styleable like any other text

**It also animates**, because the path can move:

```xml
<animateMotion dur="6s" repeatCount="indefinite"
               path="M50 170 A120 120 0 1 1 290 170"/>
```

Verified: renders centred on the arc, all 25 characters inside the 240 px ring,
lints 0/0.

### Size it so the string actually fits

This is the one thing that goes wrong. A half-circle of radius `r` is only
`π·r` long — about 377 px at `r=120` — and letter-spacing is easy to forget when
estimating. Measured, not estimated:

| font-size | letter-spacing | rendered width | fits the arc? |
|---|---|---|---|
| 19 | 2.0 | 265 px | no, overruns both ends |
| 16 | 0.8 | 241 px | yes |

Two ways to get it right, and the second is better:

1. **Estimate** — `chars × (font_size × 0.6 + letter_spacing) ≤ 0.94 × πr`
2. **Measure** — `textPath.getBBox()` in the browser and check it stays inside
   the path's x-range. About ten lines of Playwright, and it is what caught the
   overrun here.

The `0.6` advance ratio is the same crude constant the label-width linter check
uses, calibrated for the mono stack. Treat it as a starting point and confirm by
measurement when the text must fit exactly.

## See also

- `references/physics.md` — motion that should obey a law
- `references/motion-vocabulary.md` — the verb → technique index
- `references/patterns.md` — copy-ready snippets
- `references/static-first.md` — the rule that makes frame 0 count