# CSS animation inside SVG

Use CSS when you need transforms around an element's own center, staggering via custom properties, hover/focus states, or `prefers-reduced-motion`. CSS animations run inside `<img>` (hover/focus do not — no pointer events).

## Skeleton
```svg
<style>
  :root { --gold:#E8C99A; --bg:#0A0C0E; --t:10s; }
  .spin   { transform-box: fill-box; transform-origin: center; animation: spin var(--t) linear infinite; }
  .pulse  { transform-box: fill-box; transform-origin: center; animation: pulse 2.4s ease-in-out infinite; }
  .stagger > * { animation: rise .8s cubic-bezier(.16,1,.3,1) both; animation-delay: calc(var(--i) * 80ms); }
  @keyframes spin  { to { transform: rotate(360deg); } }
  @keyframes pulse { 0%,100% { transform: scale(1); opacity:.8 } 50% { transform: scale(1.12); opacity:1 } }
  @keyframes rise  { from { opacity:0; transform: translateY(12px) } to { opacity:1; transform:none } }
  @media (prefers-reduced-motion: reduce) { * { animation: none !important; } }
</style>
```

## Rules
- **Always** `transform-box: fill-box; transform-origin: center` (or explicit `50% 50%`) on elements you rotate/scale; otherwise the origin is the SVG's top-left.
- Stagger with `style="--i:3"` on each child and `animation-delay: calc(var(--i)*80ms)`.
- Use `animation-fill-mode: both` for enter animations so the pre-start state is the `from` frame.
- Negative `animation-delay` pre-rolls a loop just like SMIL negative `begin`.
- CSS `cubic-bezier()` **can** overshoot (`cubic-bezier(.34,1.56,.64,1)`), unlike SMIL `keySplines`.
- Offset-path motion (`offset-path: path(...)`) exists but is less portable than `animateMotion`; prefer SMIL for path travel.
- CSS variables make theming one edit: define the palette on `:root`, reference with `fill="var(--gold)"` or via classes. Provide a dark/light switch with `@media (prefers-color-scheme: dark)`.
- Put the `<style>` block inside the SVG (after `<defs>` or at top). No `@import`, no external font links.
- Respect reduced motion: include the media block above whenever CSS animation is used for loops.
