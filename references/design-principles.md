# Design principles for SVG motion

Motion should communicate something (flow, state, emphasis, life). If it communicates nothing, cut it.

## Contents
- Choose the motion's job
- Timing ranges
- Easing
- Choreography
- Seamless loops
- Visual design
- Accessibility and performance
- Topic playbook

## Choose the motion's job
| Job | Typical motion |
|---|---|
| Show direction / flow | travellers along rails, dashed-line march (`stroke-dashoffset`) |
| Show state / liveness | slow pulse, breathing glow, blinking indicator (≤1 Hz) |
| Draw attention once | draw-on, scale-in with settle, shimmer pass |
| Add atmosphere | very slow drifting gradients/particles (10–30 s loops), low contrast |
| Explain a process | sequenced steps, one active element at a time |

One primary motion at a time; everything else is quiet. If three things move at full contrast, nothing reads.

## Timing ranges
- Micro (hover, toggles): 150–300 ms
- Enter/exit of a shape: 300–700 ms
- One-shot reveals (logos, titles): 0.8–2.5 s total
- Traveller loops across a diagram: 8–12 s
- Ambient background loops: 12–30 s
- Stagger between siblings: 40–120 ms
- Avoid flashing faster than 3 times per second.

## Easing
- Entering things **decelerate** (ease-out); leaving things **accelerate** (ease-in); things that move between two resting places use ease-in-out.
- Linear is right for: constant-speed travellers, spinners, scrolling backgrounds.
- Overshoot/settle (CSS `cubic-bezier(.34,1.56,.64,1)`, or an extra SMIL keyframe) for playful UI; never for serious data diagrams.
- Presets: see `smil-cheatsheet.md`.

## Choreography
- Anticipation → action → settle for characters/objects (small counter-move, main move, tiny overshoot).
- Overlap: parts of one object should not stop at the same instant (offset 60–100 ms).
- Sequence by reading order (left→right, top→bottom) unless causality says otherwise.
- Squash & stretch for bouncing things: scale ~±10% along the motion axis, conserve area.
- Secondary motion (shadow, glow, trailing dots) sells the primary one.

## Seamless loops
- First keyframe == last keyframe; `keyTimes` run 0→1.
- All elements that must stay in sync share the same `dur` (or an exact divisor).
- Hide resets: do the "snap back" while the element is invisible (opacity 0), never while visible.
- Pre-roll staggered loops with negative `begin`, so frame 0 already looks populated.

## Visual design
- 3–5 colors: background, surface, one accent, one muted text, optional secondary accent. Put them in CSS variables.
- Contrast: text ≥4.5:1; the traveller/accent must be the brightest element on a dark theme.
- Depth without clutter: a soft radial gradient behind the focal area, 1px low-opacity strokes on cards, tiny blur halos on the accent only.
- Consistent corner radius, stroke width and spacing scale across the whole graphic.
- Use `viewBox` + `width="100%"` + `preserveAspectRatio="xMidYMid meet"` so it scales; design on a round canvas (e.g. 1200×640, 800×800).
- Keep the first frame meaningful (it is what screenshots, social cards and reduced-motion users see).

## Accessibility and performance
- `role="img"`, `<title>`, `<desc>` describing the content and motion.
- Respect reduced motion where possible: CSS animations + `@media (prefers-reduced-motion: reduce){*{animation:none!important}}`. SMIL can't be disabled by CSS — keep SMIL loops gentle and slow, or offer a static variant if the user needs strict accessibility.
- Prefer animating `transform` and `opacity`; limit animated filters and very large blurs; keep total animated nodes modest (generate and cap particle counts).
- File size: aim <100 KB; round coordinates to 1 decimal; reuse with `<use>` and `<defs>`.

## Topic playbook (how to start when the user names a subject)
- **Abstract tech / systems**: dark background, thin strokes, glowing accent, flowing dots, grid or node-link layout.
- **Nature (water, sky, plants)**: layered gentle waves/parallax, slow sine drift, organic easing, soft gradients.
- **Characters/mascots**: simple geometric shapes, blink every 3–5 s, breathing scale ±2%, one signature gesture.
- **Icons / micro-interactions**: single idea, 300–600 ms, stroke draw-on or morph between two states.
- **Data/charts**: grow bars/lines once on enter, highlight one series, no looping noise.
- **Logos/titles**: draw-on → fill → shimmer; hold final state.
- **Loading/progress**: seamless linear or ease-in-out loops, 0.8–1.4 s.
- **Backgrounds/heroes**: ultra-low contrast, 15–30 s loops, no sharp motion near text.
