# Drawing fundamentals (how to draw anything in SVG)

For requests where there is no generator layout: icons, logos, mascots, scenes, objects, charts, abstract art. Learn the primitives, compose with a grid, then animate.

## Contents
1. Canvas and coordinates
2. Primitives
3. Paths (the universal tool)
4. Composition: grid, symmetry, reuse
5. Color, gradients, depth
6. Strokes and text
7. Clip, mask, filters, patterns
8. Recipes for common objects
9. Making a drawing "animatable"

## 1. Canvas and coordinates
- `viewBox="0 0 W H"` defines the drawing space; `width="100%"` lets it scale. Origin top-left, **y grows downward**, angles clockwise.
- Pick a canvas by use: icon `24×24` or `48×48`; logo/mark `200×200`; banner/README `1200×420–640`; scene `800×600`; square `800×800`.
- Work on round numbers and a grid (multiples of 4 or 8); it makes alignment and animation maths trivial.
- Give every object that will move its own `<g id="…">`, drawn around **its own center** (e.g. a wheel drawn at `cx=0,cy=0` inside `<g transform="translate(x y)">`) so rotation/scale origins are obvious.

## 2. Primitives
```svg
<rect x="10" y="10" width="80" height="40" rx="8"/>
<circle cx="50" cy="50" r="20"/>
<ellipse cx="50" cy="50" rx="30" ry="12"/>
<line x1="0" y1="0" x2="100" y2="0" stroke="#fff"/>
<polyline points="0,40 20,10 40,30" fill="none" stroke="#fff"/>
<polygon points="50,5 95,90 5,90"/>
<path d="…"/>
<text x="50" y="50" text-anchor="middle">Label</text>
```
Defaults to remember: fill is black, stroke is none. Set `fill="none"` for line art.

## 3. Paths
Commands (UPPERCASE absolute, lowercase relative): `M x y` move · `L x y` line · `H x` / `V y` axis lines · `C x1 y1 x2 y2 x y` cubic Bézier · `S` smooth cubic · `Q x1 y1 x y` quadratic · `T` smooth quadratic · `A rx ry rot large sweep x y` arc · `Z` close.
- **Smooth curve recipe**: cubic with horizontal tangents at both ends: `M x1,y1 C mx,y1 mx,y2 x2,y2` (S-curve). Vertical tangents: `C x1,my x2,my x2,y2`.
- **Circle from arcs**: `M cx-r,cy a r,r 0 1,0 2r,0 a r,r 0 1,0 -2r,0`.
- **Rounded blob**: 4 cubic segments with control points offset by `0.552·r` from the extremes (the circle approximation).
- **Sine wave**: `M0,y Q w/4,y-a w/2,y T w,y` (T repeats the reflection; chain more `T` for more periods).
- **Arcs**: large-arc flag chooses the long way round, sweep flag chooses clockwise (1) or counter-clockwise (0).
- Keep morph targets structurally identical (same commands in the same order) so they can be animated.

## 4. Composition
- **Symmetry**: draw one half, then `<use href="#half" transform="translate(W 0) scale(-1 1)"/>`.
- **Repetition**: `<defs><g id="tick">…</g></defs>` + several `<use href="#tick" transform="rotate(30 cx cy)"/>` (clock ticks, petals, rays).
- **Layering** (back to front): background, far elements (large, low contrast), midground, focal subject, highlights/labels. Depth cues: smaller + lighter + blurrier = farther.
- **Negative space**: leave ≥ 8 % margin; the subject should occupy ~60–70 % of the canvas.
- **Hierarchy**: one focal element with the highest contrast and saturation; everything else quieter.

## 5. Color, gradients, depth
- Palette of 3–5: background, surface, one accent, one text, one muted. Define as CSS variables in `<style>` or reuse a generator theme.
- `linearGradient` for surfaces and metallic sheen; `radialGradient` for glow/aurora (stop-opacity 0 at the edge gives soft falloff with no blur filter).
```svg
<linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#E8C99A"/><stop offset="1" stop-color="#B08D57"/></linearGradient>
```
- Contrast: text ≥ 4.5:1; icons ≥ 3:1. Use opacity (0.1–0.5) for secondary lines and shadows rather than new colours.
- Shadows: a dark ellipse at 20–30 % opacity under objects; highlights: a small lighter shape offset toward the light.

## 6. Strokes and text
- `stroke-width`, `stroke-linecap="round|butt|square"`, `stroke-linejoin="round|miter"`; consistent widths across a set of icons (e.g. 2 on a 24 grid).
- Dashes: `stroke-dasharray="6 8"`; `pathLength="1"` normalises length for draw-on effects.
- Text: system font stacks only (no external fonts). `text-anchor="middle"` centres; `dominant-baseline="middle"` vertically centres (not supported identically everywhere; prefer explicit `y` offsets). For logo lettering convert glyphs to paths so it renders identically.
- Leave 10–15 % slack in text boxes: fallback fonts have different widths.

## 7. Clip, mask, filters, patterns
- `clipPath` (hard edge) to reveal/limit shapes; animate the clip rect for wipes.
- `mask` with gradients for soft fades.
- Filters: `feGaussianBlur` for glow; `feDropShadow` for shadows; `feTurbulence`+`feDisplacementMap` for liquid/heat distortion (heavy — small areas only).
- `<pattern>` for dots/grids/hatching (static or with an animated `patternTransform`).
- Apply filters to small elements; never to a full-canvas group that also animates.

## 8. Recipes for common objects (build from primitives)
- **Cup**: rounded rect/path body + ellipse top + arc handle (stroke only) + saucer ellipse + steam paths above.
- **Rocket**: path body (pointed ellipse), circle window, two triangles for fins, flame = teardrop path that scales on y.
- **Cloud**: union of 3–4 circles + a rounded rect base, one fill.
- **Gear**: circle + N small rects rotated with `<use>`; hole = circle in background colour (or `fill-rule="evenodd"`).
- **Sun**: circle + 12 ray lines via `<use>` rotated 30°.
- **Planet + ring**: circle + ellipse ring behind (half) and front (half) using two clipped copies.
- **Person/mascot**: circle head, rounded-rect body, circle eyes (blink = scaleY), limbs as thick round-cap strokes.
- **Chart**: axis lines, `rect` bars from a data array (generate with a script), labels at fixed offsets, polylines for series.
- **UI card/phone**: rounded rects with 1 px low-opacity strokes, grey bars as text placeholders.
- **Map pin / badge / shield**: single path with `C` curves; inner glyph as a smaller shape.

For repetitive or data-driven artwork (many bars, stars, grid dots, particles) **generate the SVG with a script** (Python f-strings, seeded randomness) instead of hand-writing coordinates.

## 9. Making a drawing "animatable"
- Group by **what moves together**; give ids.
- Draw moving parts around their pivot at (0,0) then `translate` them into place; or set `transform-box: fill-box; transform-origin: …` in CSS.
- Keep a "rest pose" that is a complete, good-looking still frame.
- Separate shadows/glows from objects so they can animate independently (shadow shrinks when the object rises).
- Prefer stroked paths for things that should "draw on" or "flow".
