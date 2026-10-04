# README-grade animated diagrams

How professional animated architecture/flow SVGs for GitHub READMEs and docs are built, extracted from real examples (a 6-column signal flow with fan-out/fan-in, an 8-cluster "sonar" constellation, and a 4-phase methodology panel). Use the generator (`scripts/gen_diagram.py`) for these layouts; use this file to understand it, extend it, or hand-build a variant.

## Contents
1. The twelve techniques
2. Generator spec reference
3. Hand-building checklist
4. Destinations: GitHub README and elsewhere
5. Performance and compatibility
6. Imperfections in the reference examples (don't copy)

---

## 1. The twelve techniques

**T1 — Static-first.** Every base shape (cards, rails, labels) is fully drawn and visible with no animation. All motion is *overlays* with `opacity="0"` as base: glow outlines, dots, fills. If SMIL doesn't run (GitHub mobile, link previews, PDF export, email) the viewer still sees a complete diagram. Never animate the visibility of the base shapes.

**T2 — Generated from data.** Coordinates, rail endpoints and keyTimes come from a spec and a script. Numbers like `0.090;0.140;0.250` are computed, never typed by feel. Hand-written SVGs of this kind drift out of sync; generated ones can't.

**T3 — Rails live in the gutters and touch the cards.** Columns are separated by 76–90 px gutters. Each rail starts exactly on the source card's edge and ends on (or 3–4 px before, with an arrowhead) the target card's edge. Nothing crosses a card. Card width follows its text (≈ chars × 10.8 px at 18 px mono, plus padding); cards in a column are centred on the column axis.

**T4 — Branch curves with horizontal tangents.** Fan-out/fan-in rails are S-curves `M x1,y1 C mx,y1 mx,y2 x2,y2` with `mx = (x1+x2)/2`: both ends are horizontal, so the curve leaves and arrives perpendicular to the card edges, and the three branches look like one system. Same-height rails are straight lines.

**T5 — Relay travellers (one dot per rail).** Instead of one dot crossing everything on a spine, each rail gets its own dot that is parked invisible at the rail start, travels during its time slot, and is parked invisible at the end:
```svg
<circle r="4.6" fill="#FFF3EC" opacity="0">
  <animateMotion dur="6s" repeatCount="indefinite" calcMode="linear"
                 keyTimes="0;0.02;0.14;1" keyPoints="0;0;1;1" path="M177,212 L267,212"/>
  <animate attributeName="opacity" dur="6s" repeatCount="indefinite"
           keyTimes="0;0.01;0.04;0.12;0.14;1" values="0;0;1;1;0;0"/>
</circle>
```
`keyPoints` maps time to progress along the path (0 until the slot opens, 1 after it closes). This gives exact timing independent of path length, supports fan-out (several rails share one slot) and fan-in, and keeps the dot from ever crossing a card. A soft halo (`r≈11`, blurred, 50 % opacity) rides with it.

**T6 — Glow pulses tied to arrivals.** Each card has a duplicate outline `<rect fill="none" stroke=accent stroke-width="2.6" filter="url(#glow)" opacity="0">` animated `values="0;0;0.95;0;0"` with `keyTimes="0;arrival-0.05;arrival;arrival+0.11;1"`: it swells while the dot approaches, peaks on arrival, decays after. The final pair of values is `0;0` so the glow is fully off before the loop restarts (this is the correct way to satisfy "keyTimes end at 1").

**T7 — One master clock with a rest.** Everything shares `dur` (6–10 s). Hops are slots on that clock: `start≈0.02`, equal slot length, a short dwell (`≈0.03`) between slots, last glow decaying by ≈0.91, leaving ≈9 % dark so the loop restart isn't abrupt.

**T8 — Sonar + sweep (radial layout).** Hub in the centre, N cards on a ring (`R≈256`, angle `−90° + 360°·i/N`). Spokes run from the hub circle to the *card edge* (ray/rectangle intersection). Three expanding rings `r: core→R+12`, `opacity .55→0`, `stroke-width 2.4→.4`, phased by negative `begin` (`0`, `−dur/3`, `−2dur/3`) so the first frame is already populated; rings are drawn **under** the cards. Cards glow in a clockwise sweep, `start_i = i/N`.

**T9 — Sequential panels (phases layout).** Panels stacked with a left rail and node dots. Each phase has an on-window (`≈0.17` of the loop) offset by `pitch≈0.22`; inside it the panel gets a 11 % tinted fill, an outline glow and its rail dot, and its chips light up staggered by `0.018` each. Colour shifts across phases (light→deep) so progress is visible.

**T10 — Aurora background.** Three large radial-gradient ellipses (warm / ember / amber), each drifting 24–30 s on different, non-dividing durations so the background never visibly repeats; translate only (cheap). The gradient's own alpha falloff already softens the edge, so an extra `feGaussianBlur` is optional (and expensive).

**T11 — A coherent token set.** All diagrams in one README share the same palette variables (bg, surface, key-surface, stroke, rail, accent ×3, text, muted, eyebrow), the same system-mono font stack with fallbacks, the same eyebrow label (small, letter-spaced, top-left) and the same `rx=16` rounded background rect, so they read as one family. Key nodes (entry/orchestrator/result) get the accent stroke (1.7) and a warmer fill; ordinary nodes get a muted stroke (1.1).

**T12 — Accessibility and portability.** `role="img"`, `aria-label` describing the flow in words, `<title>`, `<desc>`; no JavaScript, no external fonts/images, no `xlink`, no `mpath` (inline `path=`); `viewBox` + `width="100%"` so it scales; own background rect so it looks right on both light and dark GitHub themes.

---

## 2. Generator spec reference

> This section documents the first three layouts. **The full catalog (12 types + `compose`) with every spec field is in `references/diagram-types.md`; combination recipes are in `references/combinations.md`.**

```
python scripts/gen_diagram.py spec.json out.svg [--theme ember|ocean|forest|mono|paper]
```
Common keys: `type` (`flow`|`radial`|`phases`), `title` (eyebrow text), `aria`, `desc`, `dur` (seconds), `theme`, `colors` (override any token), `aurora` (true/false), `aurora_blur` (0 = off).

**flow**
```json
{"type":"flow","dur":10,"arrows":true,
 "columns":[[{"id":"a","label":"User","sub":"intent"}],
            [{"id":"b","label":"CORE","sub":"502 concepts","key":true}],
            [{"id":"c","label":"X"},{"id":"d","label":"Y"}]],
 "edges":"auto",
 "feedback":{"id":"m","label":"Maintainer","sub":"inbox → release","from":"c","to":"b"}}
```
- `columns`: left→right; nodes in a column are stacked and centred. `key:true` = accent node. Optional per node: `color`, `label_size`.
- `edges`: `"auto"` (every node of a column → every node of the next) or `[["a","b"],…]` (left→right only).
- `arrows`: `true` draws filled arrowheads (rail ends 4 px before the edge); `false` = plain rails, direction shown by motion only.
- `feedback`: adds a node below plus two dashed rails (`from` → node → `to`) and a return traveller scheduled after the main hops.
- Layout knobs: `gap_x` (84), `gap_y` (46), `node_h` (62), `margin`, `title_zone`.

**radial**: `center:{label,sub}`, `items:[{title,count,lines:[…]}]`, optional `radius`, `core_r`.
**phases**: `phases:[{name,sub,chips:[…],color?}]`, optional `chip_x`, `width`.

The script prints the schedule and embeds it as a comment. After generating: **lint, then render frames, then look at them.**

When the spec cannot express what the user wants (curved layouts, many-to-many with crossings, custom shapes), generate the closest layout, then edit the output by hand following the techniques above, and lint again — never skip the lint after a manual edit.

---

## 3. Hand-building checklist (no generator)
1. Sketch the grid: columns/rows, gutters ≥ 76 px where rails go; node sizes from text length.
2. Compute every rail from node edges (start on the edge; end on the edge or 3–4 px before for arrowheads). Branch rails = S-curve rule (T4).
3. Choose the master clock; list slots; compute each node's arrival time from its incoming slot.
4. Write base shapes first, then overlays at `opacity="0"`: glows (T6), relay dots (T5), rings/sweeps if radial.
5. Give classes: `class="rail"` on rails so `lint_svg_anim.py` can check that every rail touches a card and that each dot path equals a rail path.
6. Lint → render frames at 0, each slot start, each node arrival, and 95 % → view them.

---

## 4. Destinations

**GitHub README** (the main target)
- Commit the file in the repo (e.g. `docs/architecture.svg`) and embed with a relative path: `![Architecture](docs/architecture.svg)` or `<img src="docs/architecture.svg" alt="…" width="100%">`.
- SMIL and CSS animations play in README images; scripts, external fonts/images and `foreignObject` content do not. Hover and focus never work in `<img>`.
- GitHub's light/dark theme is **not** visible inside an SVG loaded as an image (`prefers-color-scheme` reflects the OS, not the GitHub setting). Give the SVG its own background (the `rx=16` rect) so it looks right on both themes, or ship two files and use `<picture>` with `<source media="(prefers-color-scheme: dark)" srcset="…-dark.svg">`.
- Opening the `.svg` file in the GitHub UI shows the animated image; keep each file under ~100 KB (the generator's outputs are ≈ 13–15 KB).
- Alt text matters: write what the diagram says, not "diagram".

**Docs sites / blogs**: use `<img>` (animations run); inline `<svg>` also allows hover/JS but must have unique ids (`glow`, `arrow` clash between inline SVGs on one page — prefix ids with the diagram name).
**Slides (PowerPoint/Keynote/Google Slides)**: animation is not preserved; export a still frame (`render_frames.py`) or a GIF/MP4 from frames.
**Email / PyPI / npm / Notion**: usually static or stripped; supply a PNG fallback from `render_frames.py`.
**Social cards**: render frames to PNG; SVG animation is not supported.

---

## 5. Performance and compatibility
- Blur filters are the expensive part. Use `filter="url(#glow)"` only on small overlays (card outlines, dots). Don't blur the whole aurora group while its children animate (the blur is recomputed every frame); the gradient alone gives a soft edge.
- Prefer translate/opacity animation; keep total SMIL nodes in the low hundreds (the 6-column flow uses ≈ 60).
- Fonts: use a monospace stack with fallbacks (`'JetBrains Mono','Cascadia Mono','Menlo','Consolas',monospace`); text width differs per fallback, so leave ≥ 12 px padding in cards.
- Test the first frame: it is what static viewers show.
- Respect motion sensitivity: SMIL cannot be disabled by CSS; keep loops slow (≥ 6 s), low-contrast ambient motion, no flashing.

---

## 6. Imperfections in the reference examples (don't copy)
- Pulses with `dur="1.4s"` / `2.8s` inside a 6 s loop don't divide the master clock, so they drift against it. Use `dur/4`, `dur/2` (the generator does).
- The aurora group is blurred with `feGaussianBlur stdDeviation≈80` while its ellipses animate; the gradients already fade to 0, so the filter is mostly redundant and costly.
- No arrowheads: direction is only visible while the animation runs. Use `"arrows": true` when the static frame must show direction too.
- Large aurora durations (24/27/30 s) are fine for ambient drift but are not whole divisors of the loop (the lint prints an INFO; that is expected).
