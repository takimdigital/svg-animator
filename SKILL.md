---
name: svg-animator
description: Design, build, combine, fix and verify animated SVGs on any topic — README/GitHub diagrams (architecture flows, hub-and-spoke, phase panels, timelines, networks, layered stacks, CI/CD cycles, sequence diagrams, terminal demos, stat tiles, charts, banners) AND non-diagram things (loaders/spinners, logo reveals, kinetic text, gauges and rings, radar charts, animated backgrounds, micro-animated icons, illustrated scenes, odometer counters, generative art), combined on one clock, plus any custom icon, mascot, scene, path/stroke animation, morphing or particles built by hand. Use whenever the user asks for an animated SVG, SVG animation, "animate this", a loader/logo/banner/diagram/dashboard/background, several visuals combined, a README or docs visual, a moving/pulsing/drawing/looping vector graphic, or pastes an SVG whose animation is broken (dot not following the line, wrong arrows, glows out of sync) — even if they never say SMIL or CSS.
---

# SVG Animator

Goal: ship animated SVGs that are **correct, self-contained and designed**, for GitHub READMEs, docs, sites and slides. One `.svg` file, no JavaScript, no external assets.

SVG animation fails silently — a wrong `keyTimes`, a `begin` delay or a line through a card still "runs" but looks wrong. So this skill works by **computing instead of guessing, and verifying by looking**.

## The seven principles (apply to every SVG)
1. **Static-first.** Frame 0 must already be a complete, good-looking graphic. Base shapes are always visible; motion is added as *overlays* that start at `opacity="0"` (glows, dots, fills). If animation doesn't run (mobile app, preview, PDF) the viewer still sees the full picture.
2. **Compute, don't guess.** Layout, rail endpoints and every keyTime come from a spec/script or from `lint_svg_anim.py` output. Never type "0.46" because it feels right.
3. **Motion follows drawn lines.** Dots travel on rails that exist; each rail touches its cards; nothing crosses a card or text unless that is the intended effect.
4. **One master clock.** One loop length; every phase is a fraction of it; secondary pulses use `dur/2`, `dur/4`; leave ~10 % rest at the end of the loop.
5. **Self-contained.** System font stacks, inline everything, no scripts, no `xlink`/`mpath` unless needed (inline `path=`).
6. **Verify by looking.** Lint, then render frames and *view* them. Say what you saw.
7. **Report honestly.** State what was verified and what was not. Comments in the SVG restate lint/frame results, never intentions.

## The pipeline (one skill, one command)
```
BRIEF → ROUTE → SPEC / STORYBOARD → BUILD → LINT → FRAMES → FIX LOOP → DELIVER
```
| Stage | What happens | Tool / reference |
|---|---|---|
| 1 Brief | Subject, destination (README, docs, site, slides), theme, loop vs one-shot. Infer defaults, state them in one line. | — |
| 2 Route | Diagram layout (A), hand-built artwork (B) or fix (C). | table below |
| 3 Spec / storyboard | JSON spec (A) or a timeline comment: master clock, beats as fractions, which element moves when (B/C). | `assets/specs/`, `references/readme-diagrams.md`, `references/motion-vocabulary.md` |
| 4 Build | Generate from the spec — one type or a `compose` (A) — or draw the still first, then animate (B). | `scripts/gen_diagram.py`, `references/drawing-fundamentals.md`, `references/patterns.md` |
| 5 Lint | Structure, timing, rails touching cards, dot path = rail, glow windows. | `scripts/lint_svg_anim.py` |
| 6 Frames | PNGs at 0, every slot/phase midpoint, 95 %; **view them**. | `scripts/render_frames.py` |
| 7 Fix loop | Repeat 4–6 until 0 lint errors, every warning fixed at its root cause or justified, frames look right. | `references/debugging.md` |
| 8 Deliver | Save next to the user's project (or your outputs dir), README embed line, attach the file, honest summary. | below |

Stages 4(for specs)–6 run with **one command**:
```
python scripts/run_pipeline.py INPUT --out-dir ./run --name <name> [--deliver ./out]
```
`INPUT` = a JSON spec (builds, lints, renders) or a hand-written `.svg` (lints, renders). It prints each stage, picks the frame times itself, writes a contact sheet, and ends with `RESULT: PASS / PASS WITH WARNINGS / FAIL`. Delivery is skipped on FAIL. Omit `--deliver` to keep the file in `--out-dir`. A PASS only means the file is structurally sound: you still have to look at the frames.

## Step 0 — Route the request

| The user wants… | Mode |
|---|---|
| Any of the generator types — **diagrams** (flow, radial, phases, timeline, network, layers, cycle, sequence, terminal, cards, chart, banner) or **things** (loader, logo, text, gauge, radar, backdrop, icons, scene, counter, art) — **or several together** | **A — generator** (`scripts/gen_diagram.py`, 22 types + `compose`; catalogs: `references/diagram-types.md`, `references/animated-things.md`) |
| Anything the generator doesn't cover: a specific mascot/character, custom icon, bespoke scene, unusual shape or effect | **B — hand-build** from primitives + patterns |
| An existing SVG that is broken or needs changes | **C — fix** |
| A generator diagram plus custom art (mascot, logo, special shape) | **A then B** (`references/combinations.md` §4) |

If the request is vague ("make me something cool"), pick sensible defaults, state them in one line, and build; ask at most one question and only if the answer changes the build (destination, theme, content).

## Mode A — Diagram from a spec (fastest, most reliable)
1. **Pick the type**: diagrams → table in `references/diagram-types.md` §1 (`flow radial phases timeline network layers cycle sequence terminal cards chart banner`); things → `references/animated-things.md` §1 (`loader logo text gauge radar backdrop icons scene counter art`); several → `compose`.
2. **Write a JSON spec** (examples for every type in `assets/specs/`; every field in `references/diagram-types.md` §3 and `references/animated-things.md`) with the user's real labels; choose a theme (`ember ocean forest mono paper violet sunset`) or override colours.
3. **Run** `python scripts/run_pipeline.py spec.json --out-dir ./run --name <name>` → build + lint + frames.
4. **View** the PNGs / contact sheet; fix the **spec** (not the SVG) and re-run until clean.
5. **Combine** when the request has several visuals: `type: "compose"` with `layout` (`stack` | `row` | `grid`) and per-part `window:[a,b]` so parts play together, one after another, or as a cascade (`references/combinations.md`).
6. If no type expresses what the user needs, generate the closest one, hand-edit with `references/readme-diagrams.md` §1/§3, then run the pipeline on the edited `.svg`.

## Mode B — Hand-build anything
1. **Brief.** Subject, mood/style, palette, canvas, loop vs one-shot, destination. Infer defaults.
2. **Decompose** (`references/motion-vocabulary.md`): nouns → shapes, verbs → motion, clock, rest pose. Example: "coffee cup with steam" = cup/handle/saucer paths + 3 steam strands that *rise, fade, sway*, phased with negative `begin`.
3. **Draw** the still first using `references/drawing-fundamentals.md` (canvas, primitives, paths, symmetry with `<use>`, gradients, recipes for common objects). Group by what moves together; draw pivots at (0,0).
4. **Animate** with the cookbook (`references/motion-vocabulary.md`, `references/patterns.md`, `references/smil-cheatsheet.md`, `references/css-animation.md`). Default to SMIL + a small `<style>` block; use CSS for rotation/scale around the element's own centre, stagger and `prefers-reduced-motion`; SMIL for path motion, morphing and attribute animation.
5. **Generate repetition** (particles, bars, stars, tiles) with a seeded script rather than typing coordinates.
6. **Verify** (below). Start from `assets/template.svg` if useful.

Build rules (each prevents a bug seen in practice):
- Layer order: background → rails/connectors → nodes → labels → travellers/glows. Decide and comment whether travellers are over or under cards.
- Rails start on the source edge and end on the target edge (or 3–4 px before it when an arrowhead is used: with `refX` at the tip, the tip lands on the path end). Branch curves use horizontal tangents: `C mx,y1 mx,y2 x2,y2`. If cards leave no gutter, **move the cards**; never invent floating stubs.
- Arrowheads: filled `<path>` markers, `markerUnits="userSpaceOnUse"`, `orient="auto"`; or none at all, with direction shown by the travelling dot.
- Hidden until started: anything with `begin` or a fade-in has `opacity="0"` as base; use negative `begin` to pre-roll loops.
- Travellers: relay dots with `keyPoints`/`keyTimes` slots (`references/readme-diagrams.md` T5), or one `paced` path; never `calcMode="linear"` over a multi-segment path without `keyPoints`.
- Glow/opacity windows end with a final `…;0;0` keyframe and `keyTimes` ending at 1 — never "fix" a lint warning by stretching the last keyTime.
- CSS rotation/scale needs `transform-box: fill-box; transform-origin: center`; SMIL rotation needs `cx cy`.
- Loop seamlessly: first = last value, same `dur` for synced parts, reset while invisible.
- Colours in variables/one palette; `role="img"`, `<title>`, `<desc>`, `aria-label`; own rounded background rect for README use.
- Cap complexity: blur filters only on small overlays; ~60 SMIL nodes is plenty; file < 100 KB.

## Mode C — Fix an existing SVG
1. Clean paste artifacts (`\<svg`, `xlink\:href`, `xmlns="[http://…](…)"`, smart quotes).
2. Read all of it; list every animation and target before editing.
3. Run the lint; diagnose with `references/debugging.md` (symptom → cause → fix).
4. **Start from the latest accepted version in the conversation, not the original paste**, and keep every decision the user already approved (e.g. "dot follows the line, not through cards"). Before sending, list those decisions and confirm each still holds.
5. Change the minimum; explain each fix in one line; re-verify.

## Combining things
- **Within one graphic**: named effect recipes (signal flow, sonar, request/response, orbit, reveal-and-hold, shimmer, aurora…) → `references/combinations.md` §1.
- **Several diagrams in one image**: `compose` (README hero = banner + cards + flow; product hero = logo + counters + icons; status board = gauges + radar + loaders + layers; launch story = text → rocket scene → counters) → `references/combinations.md` §2–3.
- **Generator + custom art**: generate, insert hand-built `<g>` elements, keep the clock, lint again → §4.
- **Rules**: one hero motion at a time; slow low-contrast ambient motion; same theme across a README; ≤ 4 parts per compose; raise `dur` (12–18 s) when parts play one after another.

## Verify (never skip)
Run `python scripts/run_pipeline.py file.svg --out-dir ./run` (or its parts: `lint_svg_anim.py`, `render_frames.py`).
1. Fix every ERROR; fix WARNs at the **root cause** (the lint also reports when each dot enters/leaves each card, whether rails touch cards, and whether dot paths equal rails).
2. `view` frames at: 0 (the still looks complete), each slot/arrival, ~95 % (loop seam).
3. Check: dots on rails, only the intended card glowing, arrows reaching targets, no overlap with text, rest pose good.
4. If Playwright/Chromium is unavailable, say frames were not checked.

## Deliver
- Save as `<descriptive-name>.svg` in your outputs directory and attach/present it (use whichever mechanism your harness provides). Don't paste the whole SVG into chat.
- For READMEs give the embed line: `![alt](docs/<name>.svg)` or `<img src="docs/<name>.svg" alt="…" width="100%">`, and the caveats that apply (no hover/JS in `<img>`; theme-independent background; static fallback = frame 0). Details in `references/readme-diagrams.md` §4.
- Reply briefly: what moves, loop length, assumptions, 2–3 knobs to tweak (`dur`, theme/colours, label text). Mention anything not verified.

## Reference map
- `references/diagram-types.md` — 12 diagram types + compose: when to use, every spec field, sizing rules
- `references/animated-things.md` — 10 non-diagram types (loader, logo, text, gauge, radar, backdrop, icons, scene, counter, art): spec fields, clock behaviour
- `references/combinations.md` — effect recipes, compose recipes, choreography (sequential/cascade/call-response), theme pairing, what not to mix
- `references/readme-diagrams.md` — the 12 techniques behind README-grade diagrams, README/GitHub destinations
- `references/diagrams.md` — diagram rules, layout, arrows, glow windows, failure modes
- `references/motion-vocabulary.md` — effect → technique cookbook (40+ verbs), decomposition method, timing recipes
- `references/drawing-fundamentals.md` — canvas, primitives, paths, composition, colour, filters, object recipes
- `references/patterns.md` — copy-ready animated snippets
- `references/smil-cheatsheet.md`, `references/css-animation.md` — syntax and gotchas
- `references/design-principles.md` — timing, easing, loops, palette, accessibility
- `references/debugging.md` — symptom → cause → fix
- `scripts/run_pipeline.py` (whole pipeline), `scripts/gen_diagram.py` (+ `diagram_common.py`, `diagram_extra.py`, `things_a.py`, `things_b.py`), `scripts/lint_svg_anim.py`, `scripts/render_frames.py`
- `assets/template.svg`, `assets/specs/*.json`, `assets/examples/*.svg` (generated, lint-clean references)

## Skill layout
```
svg-animator/
├── SKILL.md                      this file (pipeline + rules)
├── references/                   read on demand
│   ├── diagram-types.md          12 diagram types + compose: catalog and spec fields
│   ├── animated-things.md        10 non-diagram types: catalog and spec fields
│   ├── combinations.md           mixing effects, diagrams, themes, timing
│   ├── readme-diagrams.md        12 techniques, GitHub/README destinations
│   ├── diagrams.md               diagram rules + failure modes
│   ├── motion-vocabulary.md      effect → technique cookbook, decomposition method
│   ├── drawing-fundamentals.md   canvas, primitives, paths, composition, colour, objects
│   ├── patterns.md · smil-cheatsheet.md · css-animation.md
│   ├── design-principles.md · debugging.md
├── scripts/                      run, don't read
│   ├── run_pipeline.py · gen_diagram.py · diagram_common.py · diagram_extra.py · things_a.py · things_b.py
│   ├── lint_svg_anim.py · render_frames.py
├── assets/
│   ├── template.svg · specs/*.json · examples/*.svg
└── evals/evals.json
```
