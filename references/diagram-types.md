# Diagram type catalog (what to pick, and every spec field)

> Covers the 12 **diagram** types and `compose`. The 10 **non-diagram** types (loader, logo, text, gauge, radar, backdrop, icons, scene, counter, art) are in `animated-things.md`; both lists can be mixed freely in a `compose`.

`python scripts/gen_diagram.py spec.json out.svg [--theme …]` or `python scripts/run_pipeline.py spec.json …`.
Every type is **static-first** (frame 0 is complete), computed (no hand-typed keyTimes), lint-clean, README-safe (no JS, no external assets).

## Contents
1. Choosing a type
2. Common keys and themes
3. Types: flow · radial · phases · timeline · network · layers · cycle · sequence · terminal · cards · chart · banner
4. compose (combinations)
5. Sizing and text-fit rules

---

## 1. Choosing a type

| The content is… | Use | Why |
|---|---|---|
| a pipeline / data flow / architecture with fan-out and fan-in | `flow` | columns, S-curve rails, relay dots, optional feedback loop |
| a hub that feeds / owns many modules | `radial` | sonar rings + clockwise sweep |
| steps of a method, each with sub-steps | `phases` | panels light in order, chips inside |
| dated milestones / roadmap / history | `timeline` | spine + alternating cards, progress dot |
| an arbitrary graph (services, dependencies, mesh) | `network` | pulses spread by BFS from start nodes |
| tiers (client → API → services → data) with request/response | `layers` | down dot = request, up dot = response |
| a repeating loop (CI/CD, feedback, lifecycle) | `cycle` | dot orbits the ring |
| who calls whom, in what order | `sequence` | lifelines + messages, packet per message |
| a CLI demo / quick start | `terminal` | typewriter commands + output |
| headline numbers / feature tiles | `cards` | glow wave |
| trends / comparisons | `chart` (`bar` / `line`) | grows in, highlights max |
| the README header | `banner` | shimmer title, tags, particles |
| several of the above together | `compose` | one canvas, one clock, optional time windows |

If none fits, generate the closest type and hand-edit (see `readme-diagrams.md` §3), or build with Mode B.

## 2. Common keys and themes
`type`, `title` (small eyebrow label), `aria`, `desc`, `dur` (loop seconds), `theme`, `colors` (override any token), `aurora` (true/false), `aurora_blur` (0 = off), `title_zone` (px reserved above the content).
Themes: `ember` (warm), `ocean`, `forest`, `mono`, `paper` (light), `violet`, `sunset`. Tokens you can override in `colors`: `bg surface surface_key stroke stroke_dim rail arrow accent accent2 accent3 loop text text_key muted eyebrow dot`.
`key: true` on a node/item = accent-highlighted (entry point, orchestrator, result).

## 3. Types

### flow
```json
{"type":"flow","dur":10,"arrows":true,
 "columns":[[{"id":"a","label":"User","sub":"intent"}],[{"id":"b","label":"CORE","key":true}],[{"id":"c","label":"X"},{"id":"d","label":"Y"}]],
 "edges":"auto",
 "feedback":{"id":"m","label":"Maintainer","sub":"inbox → release","from":"c","to":"b"}}
```
`columns` left→right (nodes in a column stack, centred). `edges`: `"auto"` (all pairs of adjacent columns) or `[["a","b"],…]` (left→right only). `arrows` true/false. `feedback` adds a node below and two dashed rails (`from`→node→`to`) travelled after the main hops. Knobs: `gap_x gap_y node_h margin`. Example: `assets/specs/flow-with-feedback.json`.

### radial
`center:{label,sub}`, `items:[{title,count,lines:[…]}]` (3–12 items), optional `radius`, `core_r`. Cards on a ring, spokes to card edges, 3 sonar rings under the cards, clockwise glow sweep. Example: `radial-hub.json`.

### phases
`phases:[{name,sub,chips:[…],color?}]` (2–6), optional `chip_x`, `width`. Panel colours shift across phases automatically. Example: `phases-method.json`.

### timeline
`items:[{tag,label,sub,key}]` (2–10). Cards alternate above/below a spine; stems connect dot↔card; the progress dot travels segment by segment and each milestone lights on arrival. Knobs: `card_w spacing alternate`. Example: `timeline-roadmap.json`.

### network
```json
{"type":"network","layout":"circle","start":["gw"],
 "nodes":[{"id":"gw","label":"gateway","key":true},{"id":"api","label":"api","sub":"graphql"}],
 "edges":[["gw","api"]]}
```
`layout`: `circle` (default) | `grid` (`cols`) | explicit `x`,`y` on every node. `start`: node ids where the pulse begins; waves follow BFS depth. Bidirectional pairs are drawn as two offset lines. The generator warns when an edge crosses a node: reorder nodes or give explicit coordinates. Example: `network-services.json`.

### layers
`layers:[{name,sub,chips:[…],key}]` (2–7), optional `width`, `gap_y`, `arrows`. Request dot goes down the right lane, response dot comes back up the other lane; each layer and its chips light as the dot arrives. Example: `layers-stack.json`.

### cycle
`steps:[{label,sub,key}]` (3–10), optional `center:{label,sub}`, `radius`, `deco`, `arrows`. Arcs run clockwise between cards; one dot per arc; the loop closes back to step 0. Example: `cycle-cicd.json`.

### sequence
`actors:[{id,label,sub,key}]`, `messages:[{from,to,label,kind:"call"|"return"}]`, optional `spacing`, `pitch`. Returns are dashed. Self-messages are not supported. Example: `sequence-login.json`.

### terminal
`lines:[{kind:"cmd"|"out"|"ok"|"err"|"dim", text}]`, optional `window_title`, `cps` (typing speed, chars/s), `width`. All text is drawn in the base state; window-coloured cover rectangles hide the untyped part while it runs, so a non-animating viewer sees the finished session. Pacing is stretched to fill ~80 % of the loop; the whole body fades out before the loop restarts. Character width assumes a 0.6 em monospace; very different fallback fonts may misalign the cover by a pixel or two. Example: `terminal-demo.json`.

### cards
`items:[{value,label,sub,key}]`, `cols` (default min(n,4)), `tile_w`, `tile_h`. A glow wave moves across the tiles in reading order. Example: `cards-stats.json`.

### chart
```json
{"type":"chart","kind":"bar","unit":"%","highlight":"max","data":[{"label":"W1","value":120}]}
```
`kind`: `bar` (grow in with spring-like ease, value labels fade in, max bar highlighted; `highlight` index or `"max"`) | `line` (line draws on, area reveals, points pop). Base attributes are the finished chart; animation starts from zero. Knobs: `width height`. Examples: `chart-bars.json`, `chart-line.json`.

### banner
`heading`, `subtitle`, `tags:[…]`, `width` (1200), `height` (360), `font` (`sans`|`mono`), `title_size`, `x`, `particles` (24), `seed`. Shimmer passes across the heading (seamless gradient loop), dashed rings rotate, particles drift. `title` is the small eyebrow label. Example: `banner-readme.json`.

## 4. compose (combinations)
```json
{"type":"compose","layout":"stack","dur":12,"theme":"ember","gap":18,"margin":20,
 "parts":[
  {"type":"banner","heading":"…","height":300,"width":1160},
  {"type":"cards","items":[…],"window":[0,0.5]},
  {"type":"flow","title":"architecture","columns":[…],"window":[0.15,1]}]}
```
- `layout`: `stack` (vertical, centred) | `row` (horizontal) | `grid` (`cols`).
- All parts share one canvas, one background/aurora, one master clock (`dur` of the compose overrides the parts').
- `window:[a,b]` remaps a part's whole schedule into that fraction of the loop; outside it the part is at rest (still fully drawn). Use disjoint windows to play parts **one after another** (story), overlapping windows for **cascades**, `[0,1]` for **all at once** (dashboard).
- Per-part `theme`/`colors` allowed (arrowheads follow the root theme).
- Part `title` becomes a section caption inside the part; part `title_zone` controls its spacing.
- Parts cannot be nested compose. Ids are prefixed per part, so any type can appear several times.
- Examples: `compose-readme-hero.json` (banner + cards + flow), `compose-story.json` (flow then sequence), `compose-dashboard.json` (2×2 grid, mixed themes).

## 5. Sizing and text-fit rules
- Mono text width ≈ 0.6 × font size per character; cards add ~34 px padding. Keep labels ≤ 16 characters for 18 px labels (the generator switches to 15 px beyond that) and subs ≤ 26 characters.
- Wide specs scale down in READMEs (`width="100%"`): keep text ≥ 11 px at the generated size, i.e. canvases up to ~1300 px wide.
- A single loop should have ≤ ~9 sequential slots; more hops are rejected ("too many hops") — raise `dur`, split with `compose`, or use fewer columns.
