# Animated diagrams: architecture, pipelines, flows

Diagrams are where SVG animation most often looks "almost right": a dot that fades before it arrives, arrows that point the wrong way, lines that run through labels. Follow this order.

## Contents
1. Layout first (static diagram must already be correct)
2. Connectors and arrowheads
3. Signal (traveller) choreography
4. Node glow windows
5. Feedback / return loops
6. Z-order decision: over or under the cards
7. Text collisions
8. Checklist

## 1. Layout first
Get the static picture right before any `<animate>`:
- Put nodes on a grid. Leave **at least 40px gutters** between cards that need an arrow; arrows and curves need room to arrive from *outside* the card. If two cards touch or have <20px between them, move one.
- Keep the main flow on one baseline (e.g. y=300) so the traveller path is a straight line you can reason about.
- Branches that leave a node should start at the node's edge and end at the next node's near edge — never at the far edge or inside it.

## 2. Connectors and arrowheads
- Each connector path **starts exactly on** the source edge and **ends on, or 3–4 px before,** the target edge. With `refX` at the arrow tip, the tip lands on the path end, so an 8 px gap looks detached from the card. Plain rails (no arrowheads) end exactly on the edge.
- Define arrowheads as filled paths in `<marker>` with `markerUnits="userSpaceOnUse"`, `orient="auto"`, `refX="9"` on a 10-unit viewBox whose tip is at x=10 (stroke-only markers vanish in several renderers).
- For curves, make the **last control point level with the end point and outside the target** (e.g. `C 1024 288, 1024 175, 1046 175` into a card whose edge is x=1050) so the final tangent points straight into the card. A control point inside the target card makes the head face backwards.
- Do not let any connector sample inside a card: the lint script reports `connector passes through card`.
- Soft/secondary links: lower opacity, same geometry rules.

## 3. Signal (traveller) choreography
**Preferred for pipelines: relay travellers** — one dot per rail, parked invisible outside its time slot, using `keyPoints`+`keyTimes` (see `readme-diagrams.md` T5, and `scripts/gen_diagram.py`, which computes all of it). It handles fan-out/fan-in, keeps dots off the cards, and makes glow timing exact. The single-spine approach below is only for simple straight pipelines.
- One master clock: pick `dur` for the full loop (8–12 s for diagrams) and use it for the traveller and every glow.
- Use **one `path=` on `animateMotion`** for the main pipeline. A single straight `H` segment (`M158 300 H925`) has trivially constant speed; for multi-segment/curved paths keep the default `paced`.
- Fraction of the loop when the traveller reaches x is `(x − x0) / (x1 − x0)` on a straight path; for curves, let `python scripts/lint_svg_anim.py file.svg` print enter/exit fractions per rect.
- Opacity: fade in over the first ~3% and out over the last ~4% only. A gradual fade across the loop makes the traveller disappear before it reaches the last cards.
- Add a soft halo (a larger circle at ~18% opacity) in the same `<g>` as the dot; animate the *group* (`animateMotion` + `animate opacity` on `<g>`) so halo and dot stay together. Give the group `opacity="0"` as its base state.
- To extend the story past the last node, add short secondary travellers on branch rails with `begin` offsets equal to the main arrival time (use `begin="Xs"` with a hidden base state).

## 4. Node glow windows
For each node outline overlay (a `fill="none"` rect with the same geometry):
```
values="0;0;0.9;0.9;0"  keyTimes="0; enter-0.02; enter+0.01; exit; exit+0.1"
```
`enter`/`exit` are the traveller's fractions from the lint report. Glow should be **on while the traveller is inside** and fade shortly after it leaves. The last window must finish by `keyTime=1` so the loop restarts clean.

## 5. Feedback / return loops
- Draw loops as dashed, lower-contrast curves, using arrowheads at the *destination* only.
- Route loops **around** nodes, not across them: split a loop into two rails that end/start at the intermediate node's edges (e.g. `Outputs → Maintainer`, `Maintainer → Core`).
- The loop's traveller may use one combined `path=` that crosses the intermediate card's width on the baseline between that card's text lines; use `calcMode` default `paced`.
- Start it with a `begin` delay offset from the main signal **and** `opacity="0"` base so it never flashes at (0,0).

## 6. Z-order decision: over or under the cards
Decide intentionally and write it in a comment:
- **Under the cards** (traveller group placed *before* the node group): the dot is visible only on rails, disappears behind a card, and reappears on the next rail; the card glow shows "processing". Cleanest when cards are opaque. Choose this when the user says the dot should "follow the line" rather than cross cards.
- **Over the cards** (placed after the nodes): the dot visibly crosses each card. Choose this when the user wants it to "pass through" the cards. Then route it along a line that avoids text (see §7).
When asked for one and unsure, build "under" and offer "over" in one sentence — the change is just moving the group.

## 7. Text collisions
The traveller baseline should run **between** text lines inside cards. Plan card text with a gap around the baseline (e.g. title above, list below). The lint script lists which rect each motion path crosses; check the frames at the crossing times for overlaps with text.

## 8. Checklist
- [ ] Static layout correct, gutters ≥40px where arrows go
- [ ] Every arrow tip touches its target edge, last tangent points into it
- [ ] No connector samples inside a card
- [ ] One master `dur`; all keyTimes derived from lint fractions
- [ ] Traveller visible for the entire intended span
- [ ] Base `opacity="0"` on anything with `begin`
- [ ] Z-order choice documented
- [ ] `<title>` and `<desc>` describe the flow in words
- [ ] Frames at 0 %, ~25 %, ~50 %, ~75 % checked

## 9. Failure modes seen in practice (do not repeat)
1. **Invented "gap rails" instead of fixing the layout.** Two tiny arrows at x=1075 sat between the Outputs card and the LLM/Deckhand cards but touched neither source: Outputs had no outgoing arrow at all. If cards touch or leave no room, **move the cards** (shrink widths, shift right) and draw real connectors from the source edge to the target edge. The lint reports `connector … floats`.
2. **Half-loop signal.** A feedback loop drawn as two rails (A→M, M→B) but the traveller's `path` covers only the first rail, so the dot stops at the Maintainer and jumps back. The traveller path must be the **whole chain** (`A→M` + straight run across M + `M→B`), checked against the dashed rails.
3. **Glows that never turn off.** Stretching the last `keyTime` to 1 made each glow fade over 67% of the loop; all three cards were lit simultaneously. Use `values="0;0;.9;.9;0;0"` with `keyTimes="0;t_on-.03;t_on;t_off;t_off+.1;1"`. The lint reports `ramps from … across the last N% of the loop`.
4. **Regressing an accepted decision.** The dot was moved *under* the cards because the user asked it to follow the line; a later rebuild put it back *over* the cards and across text. Carry accepted decisions forward and re-check them with the lint's OVER/UNDER line.
5. **Self-certifying comments.** A storyboard that claims compliance ("connectors end 8px outside", "20px gutters") without the numbers being derived. Comments must restate lint/frame results, not intentions.
6. **Opacity/begin hygiene was fine, geometry was not**: passing the checks you remember is not enough — run the lint and view frames every time.
