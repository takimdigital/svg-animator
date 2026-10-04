# Pattern library (copy, then adapt)

All snippets are self-contained fragments. Colors are placeholders — pull them from the palette block. Durations should be derived from the master clock chosen in the storyboard.

## Contents
1. Draw-on stroke
2. Ripple / pulse
3. Spinner
4. Orbit
5. Bounce with squash & stretch (CSS)
6. Flow dots along a path (trail + direction)
7. Path morph
8. Bars growing (chart)
9. Gradient shimmer
10. Clip reveal / wipe
11. Staggered text or icons
12. Wave / liquid
13. Particles & starfields (generate, don't hand-write)
14. Logo reveal (stroke → fill)
15. Hover state (inline only)
16. Sequenced chain

---

## 1. Draw-on stroke
```svg
<path d="M20 80 C 60 10, 140 10, 180 80" pathLength="1" fill="none"
      stroke="#E8C99A" stroke-width="3" stroke-linecap="butt"
      stroke-dasharray="1" stroke-dashoffset="1">
  <animate attributeName="stroke-dashoffset" values="1;0;0;1"
           keyTimes="0;0.4;0.8;1" dur="5s" repeatCount="indefinite"/>
</path>
```
Draws, holds, then erases. Use `values="1;0"` + `fill="freeze"` for one-shot.

## 2. Ripple / pulse
```svg
<g fill="none" stroke="#7FD1FF" stroke-width="2">
  <circle cx="100" cy="100" r="6" opacity="0">
    <animate attributeName="r" values="6;44" dur="2.4s" begin="-0s" repeatCount="indefinite"/>
    <animate attributeName="opacity" values="0.9;0" dur="2.4s" repeatCount="indefinite"/>
  </circle>
  <circle cx="100" cy="100" r="6" opacity="0">
    <animate attributeName="r" values="6;44" dur="2.4s" begin="-1.2s" repeatCount="indefinite"/>
    <animate attributeName="opacity" values="0.9;0" dur="2.4s" begin="-1.2s" repeatCount="indefinite"/>
  </circle>
</g>
```
Negative `begin` offsets the second ring by half a cycle with no hidden start.

## 3. Spinner
```svg
<g>
  <circle cx="50" cy="50" r="20" fill="none" stroke="#2A2F36" stroke-width="5"/>
  <path d="M50 30 A20 20 0 0 1 70 50" fill="none" stroke="#E8C99A" stroke-width="5" stroke-linecap="round">
    <animateTransform attributeName="transform" type="rotate" values="0 50 50;360 50 50" dur="1s" repeatCount="indefinite"/>
  </path>
</g>
```

## 4. Orbit
```svg
<circle cx="200" cy="200" r="70" fill="none" stroke="#fff" stroke-opacity=".12"/>
<g>
  <animateTransform attributeName="transform" type="rotate" values="0 200 200;360 200 200" dur="12s" repeatCount="indefinite"/>
  <circle cx="270" cy="200" r="8" fill="#E8C99A"/>
</g>
```
Different `dur` per orbit gives parallax; counter-rotate a child group to keep a label upright.

## 5. Bounce with squash & stretch (CSS)
```svg
<style>
  .ball{transform-box:fill-box;transform-origin:50% 100%;animation:bounce 1.2s cubic-bezier(.3,0,.4,1) infinite}
  @keyframes bounce{0%,100%{transform:translateY(0) scale(1.12,.88)}50%{transform:translateY(-70px) scale(.94,1.08)}}
</style>
<ellipse class="ball" cx="100" cy="150" rx="18" ry="18" fill="#E8C99A"/>
<ellipse cx="100" cy="172" rx="18" ry="4" fill="#000" opacity=".3"/>
```
Add a shadow that shrinks as the ball rises for weight.

## 6. Flow dots along a path (trail + direction)
```svg
<path id="rail" d="M40 100 C 160 20, 240 180, 360 100" fill="none" stroke="#C9A06A" stroke-opacity=".35" stroke-width="1.6"/>
<!-- three dots, evenly spaced in time via negative begin; all share one dur so they stay in formation -->
<g fill="#E8C99A">
  <circle r="4"><animateMotion dur="6s" begin="0s"    repeatCount="indefinite" path="M40 100 C 160 20, 240 180, 360 100"/></circle>
  <circle r="3" opacity=".6"><animateMotion dur="6s" begin="-0.25s" repeatCount="indefinite" path="M40 100 C 160 20, 240 180, 360 100"/></circle>
  <circle r="2" opacity=".3"><animateMotion dur="6s" begin="-0.5s"  repeatCount="indefinite" path="M40 100 C 160 20, 240 180, 360 100"/></circle>
</g>
```
Repeat the same `d` in each `path=` (keep a single source of truth by generating the file with a script when there are many). For an arrow-shaped traveller use `rotate="auto"` and a triangle drawn pointing +x.

## 7. Path morph
```svg
<path fill="#E8C99A">
  <animate attributeName="d" dur="4s" repeatCount="indefinite"
           values="M20 60 Q 60 10 100 60 T 180 60 L180 100 L20 100 Z;
                   M20 60 Q 60 110 100 60 T 180 60 L180 100 L20 100 Z;
                   M20 60 Q 60 10 100 60 T 180 60 L180 100 L20 100 Z"/>
</path>
```
Every keyframe must have the **same commands in the same order**. For unrelated shapes, rebuild both with the same number of cubic segments.

## 8. Bars growing (chart)
```svg
<g transform="translate(0,200)" fill="#7FD1FF">
  <rect x="20" width="24" y="-120" height="120"><animate attributeName="height" values="0;120" dur="0.9s" fill="freeze" begin="0.1s" calcMode="spline" keyTimes="0;1" keySplines="0.16 1 0.3 1"/><animate attributeName="y" values="0;-120" dur="0.9s" fill="freeze" begin="0.1s" calcMode="spline" keyTimes="0;1" keySplines="0.16 1 0.3 1"/></rect>
</g>
```
`y` and `height` must animate together so the bar grows upward. Stagger bars by 80–120 ms.

## 9. Gradient shimmer
```svg
<linearGradient id="shine" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="120" y2="0">
  <stop offset="0" stop-color="#fff" stop-opacity="0"/>
  <stop offset=".5" stop-color="#fff" stop-opacity=".5"/>
  <stop offset="1" stop-color="#fff" stop-opacity="0"/>
  <animateTransform attributeName="gradientTransform" type="translate" values="-160 0;360 0" dur="3s" repeatCount="indefinite"/>
</linearGradient>
<rect x="20" y="20" width="320" height="60" rx="10" fill="url(#shine)"/>
```
Draw it over a base shape, optionally clipped to it.

## 10. Clip reveal / wipe
```svg
<clipPath id="wipe"><rect x="0" y="0" width="0" height="200">
  <animate attributeName="width" values="0;400" dur="1.2s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="0.645 0.045 0.355 1"/>
</rect></clipPath>
<g clip-path="url(#wipe)"> …artwork… </g>
```

## 11. Staggered text or icons
```svg
<g font-family="ui-sans-serif,system-ui,sans-serif" font-size="28" fill="#F0EAE0">
  <text x="20"  y="60" opacity="0">D<animate attributeName="opacity" values="0;1" dur="0.3s" begin="0.0s" fill="freeze"/></text>
  <text x="40"  y="60" opacity="0">A<animate attributeName="opacity" values="0;1" dur="0.3s" begin="0.08s" fill="freeze"/></text>
  <text x="62"  y="60" opacity="0">T<animate attributeName="opacity" values="0;1" dur="0.3s" begin="0.16s" fill="freeze"/></text>
</g>
```
For long text prefer the clip wipe (#10); generate letter-by-letter markup with a script only when needed.

## 12. Wave / liquid
Two sine paths with identical command structure, morphed back and forth (pattern 7), plus a second wave offset by half a period at lower opacity for depth. Clip to the container shape.

## 13. Particles & starfields
Don't hand-write dozens of circles. Generate with a seeded script so it is reproducible:
```python
import random; random.seed(7)
out=[]
for i in range(40):
    x,y=random.uniform(0,1200),random.uniform(0,640); r=random.uniform(.6,2.2)
    d=random.uniform(4,9); b=-random.uniform(0,d)
    out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="#fff" opacity="0.2">'
               f'<animate attributeName="opacity" values="0.15;0.9;0.15" dur="{d:.1f}s" begin="{b:.1f}s" repeatCount="indefinite"/></circle>')
print("\n".join(out))
```
Cap at ~60 SMIL nodes; beyond that use CSS animations on a group or a pre-rendered pattern.

## 14. Logo reveal (stroke → fill)
Outline path with draw-on (#1), then animate `fill-opacity` 0→1 starting when the stroke finishes (`begin="1.2s"`, `fill="freeze"`), finally a one-time shimmer (#9). Keep total under 2.5 s for one-shots.

## 15. Hover state (inline SVG only)
```svg
<style>.card{transition:transform .25s cubic-bezier(.16,1,.3,1)}.card:hover{transform:translateY(-4px)}</style>
```
Does nothing inside `<img>` or most README embeds — say so.

## 16. Sequenced chain
```svg
<circle id="a" r="5" cx="40" cy="60" opacity="0"><animate id="a1" attributeName="opacity" values="0;1" dur="0.3s" begin="0.5s" fill="freeze"/></circle>
<circle id="b" r="5" cx="120" cy="60" opacity="0"><animate attributeName="opacity" values="0;1" dur="0.3s" begin="a1.end+0.2s" fill="freeze"/></circle>
```
One-shot sequences only; for loops use a master clock with `keyTimes`.
