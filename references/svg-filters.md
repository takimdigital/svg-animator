# SVG filters — organic motion with no JavaScript

> The largest untapped source of motion in this skill. A filtered shape can
> liquefy, boil, smear and breathe in ways that path keyframes cannot express at
> all. Every filter primitive here is animatable by SMIL, so none of it needs a
> script — which is what makes it legal in a README (`references/static-first.md`).

## The one trick that unlocks the rest

Filter primitives form a **pipeline**. Each takes the previous result, names it
with `result`, and passes it on:

```
SourceGraphic → feTurbulence → feDisplacementMap → SourceGraphic
                  (noise)         (warp by it)
```

`in` is what you consume, `in2` is the second input, `result` names an
intermediate. Get comfortable with those three words and the whole filter spec
becomes readable.

## feTurbulence + feDisplacementMap: the wobble

`feTurbulence` generates Perlin noise. `feDisplacementMap` uses that noise to push
the pixels of `SourceGraphic` around:

```
P'(x,y) ← P(x + scale·(XC(x,y) − 0.5), y + scale·(YC(x,y) − 0.5))
```

`xChannelSelector` / `yChannelSelector` say which noise channel pushes which axis.
`R`/`G` is the usual pairing.

**All three interesting attributes are animatable**, which is the part that is
easy to miss and the reason this belongs in an SVG-only skill:

```xml
<filter id="wob" x="-30%" y="-30%" width="160%" height="160%"
        color-interpolation-filters="sRGB">
  <feTurbulence type="fractalNoise" baseFrequency="0.018" numOctaves="3"
                seed="2" result="n">
    <animate attributeName="baseFrequency" values="0.018;0.032;0.018"
             dur="7s" repeatCount="indefinite"/>
    <animate attributeName="seed" values="2;7;12;2"
             dur="7s" repeatCount="indefinite"/>
  </feTurbulence>
  <feDisplacementMap in="SourceGraphic" in2="n" scale="26"
                     xChannelSelector="R" yChannelSelector="G">
    <animate attributeName="scale" values="18;34;18"
             dur="7s" repeatCount="indefinite"/>
  </feDisplacementMap>
</filter>
```

Three knobs, three SMIL animations, no script:

| attribute | what it does | animate it for |
|---|---|---|
| `baseFrequency` | feature size. **lower = bigger, smoother** | the slow swell of a boil |
| `seed` | a different noise field entirely | new turbulence each cycle; `values="2;7;12;2"` returns to start so the loop is seamless |
| `scale` | displacement strength in px | the amplitude of the wobble |

`type="fractalNoise"` is smoother and more organic; `type="turbulence"` gives
sharper, more directional structure.

Verified: a circle, a square and a triangle all visibly liquefy and reform over
four sampled frames. Lints `0 error(s), 0 warning(s)`.

**Every JS tutorial on this effect drives it with `setAttribute` in a
`requestAnimationFrame` loop.** That works, but it cannot be used in a README
`<img>` embed, because an image runs in secure animated mode and executes nothing.
SMIL gets the same effect in three attributes.

### Performance ceilings — these are real

Animated turbulence is the most expensive thing in this skill.

| rule | why |
|---|---|
| `numOctaves ≤ 3` on an **animated** node | each octave is another noise evaluation per frame. This is the single biggest cliff |
| keep `scale ≤ 18` in Safari | higher values produce visible artefacts, not just more wobble |
| always set the filter region `x`/`y`/`width`/`height` | the default is the source's tight bbox, so a wobbling edge gets **clipped**. `-30% / 160%` is a sane starting point |
| `color-interpolation-filters="sRGB"` | filters default to `linearRGB`, which visibly shifts colours mid-wobble |
| scope to the shape, never a group containing a full canvas | the filter runs per pixel of its input |

If a piece needs turbulence on more than one or two elements, animate one filter
and reference it, rather than defining a filter per element.

## The primitives worth knowing

Ordered roughly by how often they earn their place.

| primitive | gives you |
|---|---|
| `feGaussianBlur` | soft edges, glow, depth. `stdDeviation` animates |
| `feOffset` | drop shadow, or a duplicate displaced for depth |
| `feBlend` | combines two inputs. `mode="multiply"` for grain and texture, `"screen"` for light |
| `feColorMatrix` | recolour, desaturate (`type="saturate" values="0"`), invert |
| `feComponentTransfer` | per-channel curves via `feFuncR/G/B/A`. This is how you posterise or push contrast |
| `feComposite` | mask one input with another. `operator="in"` clips |
| `feDisplacementMap` | warp by another input's pixels. Pairs with `feTurbulence` |
| `feMorphology` | `operator="dilate"`/`"erode"` grows or shrinks a shape. Animating it makes edges breathe |
| `feTurbulence` | the noise source |
| `feTile` | repeats an input to fill the region |

### Three pipelines worth memorising

**Frosted glass / refraction.** `feTurbulence` → `feDisplacementMap` on a
duplicated scene layer gives refraction; `feBlend mode="screen"` on a pseudo-element
gives chromatic edge fringing; a `backdrop-filter` surface does the frost. Widely
used in 2025-26 UI. Same primitives as the wobble, different emphasis.

**Grain.** `feTurbulence type="fractalNoise" baseFrequency="0.65" numOctaves="3"
stitchTiles="stitch"` → `feColorMatrix type="saturate" values="0"` →
`feComponentTransfer` with a low `feFuncA slope` → `feBlend mode="multiply"`. Adds
a film texture that stops flat vector fills looking cheap.

**Scanlines.** Same noise but `baseFrequency="0 0.8"` (frequency on one axis only)
→ desaturate → `feBlend mode="multiply"`.

## Glow without a filter

Most "glow" needs no filter at all. `feGaussianBlur` on a copy of a shape, or the
existing `glow_overlay()` helper, is cheaper and sharper. Reach for a filter when
you need *distortion*, not when you need *softness*.

## Static-first and reduced motion

A filtered shape in its base state is already the undistorted shape, so filters
inherit static-first for free — **unless** the filter itself is the only thing
making an element visible, which is a design smell.

`scripts/static_twin.py` strips `<animate>` elements but leaves filter
definitions in `<defs>` untouched, so a twin still renders distorted-but-static.
That is correct behaviour: the reduced-motion user gets the shape, without the
boiling.

Remember from `references/static-first.md`: CSS cannot switch SMIL off, so
`prefers-reduced-motion` still means shipping a static twin via `<picture>`.

## Checklist

- [ ] Filter region widened beyond the source bbox, or the effect clips
- [ ] `color-interpolation-filters="sRGB"` on anything with colour
- [ ] `numOctaves ≤ 3` if the turbulence is animated
- [ ] Every animated attribute ends its `values` list where it started, so the loop is seamless
- [ ] Base state is the undistorted shape
- [ ] Looked at several timestamps, not just frame 0 — filters fail by *distorting*, which a still may hide

## See also

- `references/patterns.md` — copy-ready snippets (glow, draw-on, morph)
- `references/physics.md` — for motion that should obey a law rather than a wave
- `references/static-first.md` — the rule that makes frame 0 count
- `references/drawing-fundamentals.md` — filters are listed among the recipes