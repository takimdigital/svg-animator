# Debugging catalog: symptom → cause → fix

Run `python scripts/lint_svg_anim.py file.svg` first; many rows below are detected automatically. Then capture frames with `scripts/render_frames.py` to confirm the fix.

| Symptom | Likely cause | Fix |
|---|---|---|
| Whole SVG fails to load / blank | Paste artifacts: `\<svg`, `xlink\:href`, `xmlns="[http://…](http://…)"`, smart quotes; unbound `xlink:` prefix; unclosed tags | Clean the text; declare `xmlns:xlink="http://www.w3.org/1999/xlink"` if `xlink:href` is used; validate as XML |
| Traveller never moves | `animateMotion` is not a child of the traveller, missing `dur`, missing `path`/`mpath`, `mpath` target id not found | Make it a child of the circle/group, add `dur` and `path="…"` |
| Traveller disappears before reaching the end | Opacity animation fades over the whole loop (e.g. `0;1;1;0.2;0` evenly spaced) | Keep opacity 1 for the visible span; fade only in the first ~3% and last ~4% using `keyTimes` |
| Traveller speeds up/slows down; glows fire at wrong moments | Multi-segment path with `calcMode="linear"` (equal time per segment) | Default `paced`, or a single segment, or `keyPoints`+`keyTimes`; recompute glow `keyTimes` from the lint fractions |
| Dot sits at the corner (0,0) before it starts | Element has `begin` delay but is visible by default | Base `opacity="0"`; animate opacity in; or use negative `begin` |
| Dot "jumps" at the end of each loop | Last value ≠ first value, or reset while visible | Make first/last equal; reset while at opacity 0 |
| Dot crosses text or cards when it should follow rails | Motion path is a straight line drawn through cards | Route the path along the rails and place the traveller group **before** the nodes (hidden behind cards) — or move the baseline between text lines |
| Dot is not visible over cards | Traveller is drawn before the node group (cards are opaque) | Move the traveller group after the nodes if it should cross them |
| Arrowhead invisible | Stroke-only marker | Use a filled `<path>` marker, `markerUnits="userSpaceOnUse"` |
| Arrowhead points away from the card / sits inside it | Connector ends at the card's far edge or the curve's last control point is inside the card | End on the target edge (or 3–4 px before it for arrowheads), final control point level with the end and outside the card; move cards if there is no gutter |
| Connector passes through a card or label | Path routed through the node (e.g. a loop at y=575 through a card at y=520–590) | Split into two rails that end at the node's edges; route curves around |
| Glow outline lights at the wrong time | `keyTimes` guessed | Compute enter/exit fractions with the lint report; set `values="0;0;.9;.9;0"` accordingly |
| Rotation orbits the wrong point | `transform-origin` defaults to the SVG origin (CSS) or missing `cx cy` (SMIL) | CSS: `transform-box:fill-box; transform-origin:center`. SMIL: `values="0 cx cy;360 cx cy"` |
| Stroke draw-on shows a dot at the start | Round caps with zero-length dash | `stroke-linecap="butt"` for the draw, or start opacity at 0 |
| Path morph jumps or breaks | Different command count/order between keyframes | Rebuild shapes with identical command structure |
| Animation ignored in one browser | `keyTimes`/`values` mismatch, bad `keySplines` count (must be values−1) | Fix counts; keep all keySplines components in 0–1 |
| Gradient shimmer doesn't move | Gradient uses `objectBoundingBox` units with a pixel translate | Set `gradientUnits="userSpaceOnUse"` and animate `gradientTransform` |
| Works inline but not as `<img>`/README | JS, hover, external fonts/images, `<foreignObject>` | Use SMIL/CSS only, system fonts, inline everything |
| Loops feel jittery/slow | Many animated filters/blurs or hundreds of SMIL nodes | Animate transform/opacity, cap node count, keep blur static |
| Several cards glow at the same time / glow never turns off | Last `keyTime` stretched to 1 so the fade lasts most of the loop | Add a final keyframe at the end value: `values="0;0;.9;.9;0;0"`, `keyTimes="0;a;b;c;d;1"` |
| Arrows hover in empty space, a card has no outgoing arrow | "Stub" connectors drawn in a gap instead of from the source edge | Move the cards to create gutters; draw connector from source edge to target edge |
| Signal dot stops half way around a loop and jumps back | `animateMotion` path covers only one rail of a multi-rail loop | One path covering the whole chain, crossing the intermediate card on a text-free line |
| Previously agreed behaviour changed after a rebuild | Rebuilt from the original paste instead of the last accepted version | Start from the latest accepted file; re-verify each user decision |
| Text overlaps a moving element | Baseline not planned around text | Leave a gap in card text around the traveller baseline; move text, not the path |
| Two animations on one attribute fight | Both target `transform` or `opacity` without `additive` | Combine into one keyframe list, or wrap in separate nested `<g>`s |

## Debug procedure
1. Lint → fix ERRORs.
2. Render frames at 0, 25, 50, 75 % of the master clock and at the moments a traveller enters/exits each node.
3. If only one element misbehaves, isolate it (copy into a minimal SVG) and add animations back one at a time.
4. Re-run lint and frames after every fix; change one thing at a time.
