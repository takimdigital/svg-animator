# SMIL cheat sheet for SVG animation

## Contents
- Elements
- Timing attributes
- Keyframes: values, keyTimes, calcMode, keySplines
- animateMotion specifics
- Syncbase chaining
- Easing presets
- Gotchas

## Elements
| Element | Purpose |
|---|---|
| `<animate attributeName="r" values="4;8;4" dur="2s" repeatCount="indefinite"/>` | Animate any animatable attribute (`r`, `cx`, `opacity`, `fill`, `d`, `stroke-dashoffset`, `offset` on gradient stops, `stdDeviation`…) |
| `<animateTransform attributeName="transform" type="rotate" values="0 50 50;360 50 50" dur="4s" repeatCount="indefinite"/>` | `translate`, `scale`, `rotate`, `skewX`, `skewY`. Rotate takes `angle cx cy`. |
| `<animateMotion path="M0 0 H100" dur="4s" repeatCount="indefinite"/>` | Move the **parent** along a path. Add `rotate="auto"` to face the travel direction. |
| `<set attributeName="opacity" to="1" begin="2s"/>` | Discrete change at a given time (show/hide). |

An animation element animates its **parent**. Placing one directly under the root `<svg>` or inside `<defs>` animates nothing useful.

## Timing attributes
- `dur="10s"` (also `500ms`). Without `dur` nothing happens.
- `begin="2s"` delay; `begin="-1.2s"` pre-rolls (starts mid-cycle — the best way to stagger loops with no hidden start state).
- `repeatCount="indefinite"` or a number; `repeatDur` caps total time.
- `fill="freeze"` keeps the end value (one-shot animations). Default `remove` snaps back.
- `additive="sum"` adds to the existing value (combine with a base `transform`).

## Keyframes
- `values="a;b;c"` with optional `keyTimes="0;0.4;1"`: same count as values, first `0`, last `1` (for `linear`/`spline`), non-decreasing.
- `calcMode`: `linear` (default for animate), `discrete` (steps), `paced` (constant speed; numeric/motion only), `spline` (needs `keySplines`).
- `calcMode="spline"` needs `keySplines` with **count = values − 1**, each `"x1 y1 x2 y2"`, all within 0–1. Overshoot is invalid in the spec, so fake it with an extra keyframe (`1;1.12;1`).
- Loop seamlessly: first value == last value.

## animateMotion specifics
- Path coordinates are an **offset from the element's own position**. Draw the traveller at `cx="0" cy="0"` (or in a `<g>` with no transform) and let the path carry the absolute coordinates.
- `path="…"` directly on the element is the most robust. `<mpath href="#id"/>` also works; add `xlink:href` too only if you declare `xmlns:xlink`.
- Default `calcMode` is `paced` → constant speed over the whole path. Keep it for multi-segment paths. With `calcMode="linear"` you must supply `keyPoints` + `keyTimes` to control progress; otherwise segments can get equal *time* regardless of their length.
- `keyPoints="0;0.5;1"` + `keyTimes="0;0.3;1"` + `calcMode="linear"` gives exact "reach 50% of the path at 30% of the time" control — ideal for pausing at nodes.
- `rotate="auto"` / `"auto-reverse"` / a fixed angle.

## Syncbase chaining
`begin="a.end"`, `begin="a.begin+0.3s"`, `begin="a.end+0.2s"`, `begin="a.repeat(2)"`, lists with `;`: `begin="0s;b.end"`. For loops prefer **one master clock** (identical `dur` everywhere + `keyTimes`); `.end` chains in looping animations drift and are hard to debug.

## Easing presets (`keySplines`, one per interval)
| Feel | keySplines |
|---|---|
| ease-in-out | `0.42 0 0.58 1` |
| ease-out | `0 0 0.58 1` |
| ease-out cubic | `0.215 0.61 0.355 1` |
| ease-in-out cubic | `0.645 0.045 0.355 1` |
| ease-out expo (snappy) | `0.16 1 0.3 1` |
| ease-in (accelerate) | `0.42 0 1 1` |

## Gotchas
1. Element visible before `begin` → give it `opacity="0"` as base state (or use a negative `begin`).
2. `keyTimes` count ≠ `values` count → the animation is ignored in some engines.
3. `animate` on `d` needs the identical command structure/count in every keyframe.
4. SMIL cannot be switched off by `prefers-reduced-motion`; use CSS animations when that matters.
5. `begin` + `repeatCount="indefinite"`: only the *first* cycle waits; later cycles do not.
6. Animating `r`, `cx` etc. forces repaint; fine for tens of nodes, avoid hundreds.
7. Filters (`feGaussianBlur stdDeviation`) can animate but are expensive on large areas; keep ambient blur static.
8. `stroke-dasharray` draw-on: put `pathLength="1"` on the path so dash values run 0–1 regardless of real length; use `stroke-linecap="butt"` to avoid a stray dot at offset=1.
9. `href` vs `xlink:href`: modern browsers accept `href`; some tools still need `xlink:href` plus a declared `xmlns:xlink`.
10. IDs must be unique; `url(#id)` / `href="#id"` must resolve — the lint script checks both.
