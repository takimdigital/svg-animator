# Motion vocabulary: effect → technique

When a request describes an effect in words, find the verb here, copy the technique, adapt numbers to the master clock. If an effect is not listed, decompose it (section "Decomposition method") into verbs that are.

## Contents
- Decomposition method (worked example)
- Timing recipes
- Cookbook by verb
- Combining effects

---

## Decomposition method
1. **Nouns → shapes.** What objects exist? (cup, steam, saucer.) Sketch each as primitives/paths.
2. **Verbs → motion.** What does each object do? (steam *rises*, *fades*, *sways*.) Map each verb to a row below.
3. **Clock.** Choose the loop length; assign each verb a phase/offset; stagger copies with **negative `begin`** so frame 0 is already alive.
4. **Rest pose.** The still frame must look finished.
5. **Check** with lint + frames.

**Worked example — "animated coffee cup with steam":**
- Shapes: cup body path, handle (stroked arc), saucer ellipse, 3 steam paths (wavy `Q/T` strokes, round caps).
- Verbs: steam *rises* (translate Y −24), *fades* (opacity 0→.7→0), *sways* (translate X ±3) ; liquid *shimmers* (tiny highlight slides).
- Clock: 4 s loop; steam strands phased by `begin="0s"`, `"-1.3s"`, `"-2.6s"`.
- Code: each strand `<path … stroke-dasharray>` + `animateTransform translate "0 0;0 -24"` + `animate opacity "0;.7;0"` (`keyTimes="0;0.3;1"`).

---

## Timing recipes
- **Stagger** N copies evenly: `begin="-{i·dur/N}s"` (pre-rolled loop, no hidden start) or `begin="{i·0.08}s"` for one-shot entrances.
- **Hold then move**: `keyTimes="0;0.4;0.6;1"` with `values="a;a;b;b"`.
- **Ping-pong**: `values="a;b;a"`.
- **Loop with rest**: use the first 90 % of the clock for action; the last 10 % stays still.
- **Sync secondary pulses** to the loop: use `dur/2`, `dur/4`, never arbitrary values.
- **Easing**: `calcMode="spline"` + `keySplines` (count = values−1), presets in `smil-cheatsheet.md`; CSS `cubic-bezier()` can overshoot.

---

## Cookbook by verb

**Appear / fade** — `<animate attributeName="opacity" values="0;1" dur=".6s" fill="freeze"/>` (base `opacity="0"`).
**Slide in** — `<animateTransform attributeName="transform" type="translate" values="-40 0;0 0" dur=".7s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="0.16 1 0.3 1"/>` + fade.
**Pop / scale** — scale around centre: put the object in `<g transform="translate(cx cy)">` drawn at origin, then `animateTransform type="scale" values="0;1.12;1" keyTimes="0;0.6;1"`.
**Spin** — `type="rotate" values="0 cx cy;360 cx cy" dur="2s" repeatCount="indefinite"` (linear, no easing).
**Orbit** — a group rotating around the centre containing the satellite offset from the centre; counter-rotate the satellite's child to keep it upright.
**Swing / pendulum** — `type="rotate" values="-25 cx cy;25 cx cy;-25 cx cy"` + spline easing (ease-in-out) for natural deceleration at the extremes.
**Bounce** — translate Y with ease-out on the way up, ease-in on the way down; add squash/stretch via scale (≈ ±10 %), shadow shrinks at the apex.
**Float / bob** — translate Y `0;-6;0`, 3–5 s, ease-in-out; offset siblings with negative begin.
**Breathe** — scale `1;1.03;1`, 4 s; opacity `.85;1;.85`.
**Pulse / heartbeat** — scale `1;1.15;1;1.08;1` with `keyTimes="0;0.15;0.3;0.45;1"` then rest.
**Ripple / sonar** — circle r `r0→r1`, opacity `.55→0`, stroke-width `2.4→.4`; 3 copies with `begin="0s"`, `-dur/3`, `-2dur/3`.
**Blink** — eyes `scaleY` `1;1;0.1;1` with `keyTimes="0;0.92;0.96;1"` over 4 s.
**Shake / wobble** — rotate `0;-4;4;-3;3;0` over 0.5 s, triggered once per loop with a long rest.
**Twinkle** — opacity `.2;1;.2` with random `dur` 2–5 s and random negative `begin` (generate with a seeded script).
**Draw-on** — `pathLength="1" stroke-dasharray="1" stroke-dashoffset="1"` + animate offset `1→0`; butt caps.
**Erase** — offset `0→1` (reverse), or `0→-1` to erase from the start side.
**Flowing dashes (data stream / marching ants)** — `stroke-dasharray="6 8"` + animate `stroke-dashoffset` `0→-14` (the dash period) linear, infinite: lines look like they carry flow.
**Progress ring** — circle with `pathLength="100" stroke-dasharray="100" stroke-dashoffset="100"`, rotate −90°, animate offset `100→25`; label text via `<animate attributeName="opacity">` swaps.
**Loading bar** — rect width `0→W` with spline ease, then fade; or an indeterminate highlight sliding across a track (gradient `gradientTransform` translate).
**Typewriter** — clip rect over the text, width animated in `calcMode="discrete"` steps (`keyTimes` evenly spaced) + blinking cursor rect.
**Counter / text swap** — several `<text>` elements, each `opacity` animated with `calcMode="discrete"` so exactly one is visible at a time (`values="1;0;0;0"` shifted per element).
**Morph** — animate `d` with identical command structure in every keyframe; spline easing; ≤ 4 s.
**Wave / liquid** — two sine paths (same commands) morphing back and forth, second wave offset by half a period and lower opacity; clip to the container.
**Flow along a path** — `animateMotion path=…` (see relay travellers in `readme-diagrams.md`); `rotate="auto"` for arrows/vehicles.
**Relay / pipeline signal** — one dot per rail with `keyPoints` + `keyTimes` slots (`readme-diagrams.md` T5).
**Glow pulse** — duplicate outline with `filter="url(#glow)"`, opacity `0;0;.95;0;0` aligned to arrival times.
**Sweep (radar / clockwise highlight)** — group rotate `0→360` around the hub with a gradient wedge; or sequential glows with `start_i = i/N`.
**Wipe / reveal** — animate a `clipPath` rect width/height (spline ease); or `mask` with moving gradient.
**Shimmer / sheen** — `linearGradient gradientUnits="userSpaceOnUse"` with white 50 % centre stop, animate `gradientTransform` translate across the shape; 3 s, rest between passes.
**Colour shift** — animate `fill`/`stop-color` between 2–3 palette colours (`values="#a;#b;#a"`).
**Parallax drift** — 2–3 layers translating X by `20/40/80` px at `60/40/25` s loops (far = slower); wrap with duplicated content for seamless tiling.
**Rain / snow / falling** — lines or circles with `animateTransform translate 0 -20 → 0 H+20`, random `dur` 1–3 s and random negative `begin` (seeded script), opacity .3–.8.
**Rising particles / smoke / steam** — translate Y negative + opacity `0;.7;0`, scale up slightly, staggered negative begins.
**Fire flicker** — 2–3 teardrop paths scaling Y `0.9;1.1;0.95` at different durations (0.4–0.9 s) + colour layers (red→orange→yellow).
**Equalizer bars** — bars with `<animate attributeName="height">` and `y` together, each with its own `dur` (0.5–1.2 s) and negative begin.
**Gears** — adjacent gears rotate opposite ways with durations in the ratio of their tooth counts.
**Clock hands** — hands rotate `0→360` with `dur` 60 s / 3600 s (or 12 s / 1 s for a demo), linear.
**Scan line / spotlight** — a thin gradient rect translating across the artwork; clip to the artwork.
**Network pulse** — nodes (circles) with sequential glow + edges with dash march; or relay dots along edges.
**Chart grow** — bars: animate `height` and `y` together (spline ease), 80–120 ms stagger; lines: draw-on; numbers: swap with discrete opacity.
**Hover/press (inline SVG only)** — CSS `:hover` with `transition`; does nothing inside `<img>`.

---

## Combining effects (rules of thumb)
- One hero motion at a time; everything else ambient and quiet.
- Animate different attributes on different elements instead of stacking many animations on one element; if two animations target `transform`, nest `<g>`s.
- Keep ambient loops long (12–30 s) and low contrast; keep hero loops 2–10 s.
- Generate repetitive animation with a seeded script (reproducible), and cap the node count (~60 SMIL nodes is plenty).
- Always verify the rest pose (frame 0) and the loop seam (frame at 99 % vs 0 %).
