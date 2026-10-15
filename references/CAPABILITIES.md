# Capabilities: what this skill can make, and what it cannot

Read this first. It is the map. Every row names the file that does the work and an example you can open.
If something is not in this map, it is not a promise; follow `references/learning.md`.

## Contents
1. Routes
2. The 38 generator types (diagrams and things)
3. Variants inside a type
4. Whole READMEs (the page kit)
5. Checks you can run
6. What is NOT possible, or not verified

---

## 1. Routes

| You want | Route | Start with |
|---|---|---|
| a graphic that matches a type below | **A · generator** | `assets/specs/<type>-*.json` |
| a graphic no type covers | **B · hand-build** | `references/drawing-fundamentals.md`, `references/motion-vocabulary.md` |
| a broken SVG repaired | **C · fix** | `references/debugging.md` |
| a whole GitHub README as animated blocks | **D · page kit** | `references/readme-kit.md` |
| a new capability added to the skill | **learn** | `references/learning.md` |

## 2. The 38 generator types

Module in `scripts/`, example spec in `assets/specs/`, example output in `assets/examples/`.

**Diagrams** (`gen_diagram.py`, `diagram_extra.py`)

| Type | Use it for | Example spec |
|---|---|---|
| `flow` | pipelines, fan-out and fan-in, feedback loops | `flow-with-feedback` |
| `radial` | a hub with clusters around it | `radial-hub` |
| `phases` | ordered stages, each with sub-steps | `phases-method` |
| `timeline` | dated milestones | `timeline-roadmap` |
| `network` | any graph, pulses spread from start nodes | `network-services` |
| `layers` | tiers with request down and response up | `layers-stack` |
| `cycle` | a loop (CI/CD, lifecycle) | `cycle-cicd` |
| `sequence` | who calls whom, in order | `sequence-login` |
| `terminal` | a command session, typed and printed | `terminal-demo` |
| `cards` | headline numbers | `cards-stats` |
| `chart` | bar or line charts | `chart-bars`, `chart-line` |
| `banner` | a README header | `banner-readme` |
| `tree` | a hierarchy: org charts, file trees, team structures | `tree-team` |
| `gantt` | task bars on a time axis, with progress | `gantt-plan` |
| `scatter` | points on two numeric axes, with an optional trend line | `scatter-effort` |
| `heatmap` | a grid of values as colours; cells appear in a wave | `heatmap-week` |
| `funnel` | stages that shrink, with the drop between stages | `funnel-sales` |
| `venn` | two overlapping sets, sized by value | `venn-skills` |

**Things** (`things_a.py`, `things_b.py`, `things_morph.py`, `things_c.py`)

| Type | Use it for | Example spec |
|---|---|---|
| `loader` | spinners and loading states | `loader-sheet` |
| `logo` | a logo reveal | `logo-hexagon`, `logo-shield` |
| `text` | kinetic text | `text-wave`, `text-glitch`, … |
| `gauge` | dials, rings, bars, donuts | `gauge-dashboard` |
| `radar` | multi-axis comparison | `radar-skills` |
| `backdrop` | ambient backgrounds | `backdrop-waves`, … |
| `icons` | small animated icons | `icons-set` |
| `scene` | illustrated scenes | `scene-rocket`, … |
| `counter` | odometer counters | `counter-stats` |
| `art` | generative art | `art-mandala`, … |
| `morph` | a shape turning into another, without tearing | `morph-shapes` |
| `typing` | a terminal typing lines, with a word swapped in place | `typing-manifesto` |
| `table` | a data table; rows highlight in turn | `table-compare` |
| `pie` | a pie or donut chart with the shares | `pie-split` |
| `code` | a code block; highlighted lines light in order | `code-highlight` |
| `waveform` | a signal drawn as bars that grow from the centre | `waveform-signal` |
| `clock` | an analogue clock at a given time; the second hand sweeps | `clock-meeting` |
| `calendar` | one month; days in order, highlighted days stand out | `calendar-launch` |
| `marquee` | scrolling text that repeats without a visible seam | `marquee-ticker` |
| `sprite` | frame-by-frame animation from SVG frames you supply | `sprite-blink` |

Each builder's docstring is its contract (Fields, Refuses, Base state, Breaks if changed, Example). Read it before the code: it is shorter, and the test keeps it true.

**Compose** combines any of the above on one clock, in a stack, row or grid, with an optional time window per part (`compose-*` specs).

## 3. Variants inside a type

| Type | Values |
|---|---|
| `loader` | `ring dots bars orbit pulse dual wave progress` (`variant` or `variants`) |
| `text` | `wave reveal pop type shimmer glitch` (`variant`) |
| `gauge` | item `kind`: `gauge ring bar donut` |
| `backdrop` | `waves stars grid bubbles rain mesh` (`variant`) |
| `icons` | `check cross heart bell gear download star playpause sun lock wifi bolt` |
| `scene` | `rocket coffee ocean orbit` (`scene`) |
| `art` | `mandala lissajous spiral orbits flower` (`variant`) |
| `chart` | `bar line` (`kind`) |
| `typing` | any lines of text; `swap` replaces one word with another of the **same length** |

Every type takes `dur` (loop seconds), `theme` (`ember ocean forest mono paper violet sunset`) and `colors` (override any token).

## 4. Whole READMEs (the page kit)

`scripts/readme_page.py` builds a README from one spec: dark and light blocks, stacked with no gap, plus real Markdown text.
Two styles: `spine` and `blueprint` (`"style"` key). Spec reference in `references/readme-kit.md`. This repository's own README is built this way from `assets/readme/project-readme.json`.

## 5. Checks you can run

| Check | Command | Proves |
|---|---|---|
| lint | `python scripts/lint_svg_anim.py <files>` | structure, timing, rails, label overflow |
| browser frame 0 | `python scripts/verify.py <files>` | nothing is visible before its cue (needs Playwright) |
| frames | `python scripts/render_frames.py <svg> --times ...` | what it looks like at chosen moments (needs Playwright) |
| static twin | `python scripts/static_twin.py <svg> <out>` | a no-animation file for reduced motion |
| tests | `python -m unittest discover -s tests` | the generator, the examples, the coverage gate, the page kit |
| environment | `python scripts/doctor.py` | which of the above can run here |

## 6. What is NOT possible, or not verified

- **Aesthetic quality is not checked.** The linter and tests prove structure and timing. Whether a graphic looks right needs a human or a frame you have looked at.
- **Playback is not verified.** Frames are still captures at chosen times. Real-time feel in a browser is not measured.
- **GitHub's own rendering is not verified** for every type. The page kit's stacking was measured in Chromium only.
- **No interactivity inside `<img>`.** Hover and JavaScript do nothing when an SVG is embedded as an image.
- **No external fonts or images.** Text uses system font stacks; fonts differ by machine, so text width is an estimate (leave slack).
- **Raster and video output are not produced.** PNG frames exist for review only; GIF and MP4 are out of scope.
- **Reduced motion cannot be honoured inside the file.** SMIL ignores `prefers-reduced-motion`; use a static twin and a `<picture>` element.
- **Hand-built work depends on judgement.** Route B has no generator guarantees beyond the lint and the frame check.


<!-- MOTION-DNA-EXTENSION-START -->
## Optional experimental route: Motion DNA v0.2

- Input: local, self-contained SMIL or basic CSS animated SVG; websites, videos, GIF and JS-driven animations are unsupported.
- Tools: `scripts/inspect_motion.py`, `capture_motion.py`, `compare_motion.py`, `reconstruct_motion.py`, `investigate_motion.py`.
- Source analysis: SMIL/CSS keyframes, timeline, basic stagger groups, path command signatures, provenance SHA-256 and unknowns.
- Browser evidence: aligned sampled opacity, bounds and relative SVG transformation matrices, with optional screenshots; no unsupported whole-frame pixel-fidelity claim.
- Automatic original variations: 2–8 repeating opacity pulses sharing one duration, or one repeating SMIL rotation. Mixed or ambiguous source animations are refused.
- Comparison safeguards: missing observations, missing timestamps or zero coverage cannot produce PASS.
- Existing generator routes, lint, render and verification remain authoritative for the delivered SVG.

Read `references/motion-dna.md` and `docs/motion-dna/AUDIT.md` for limitations, usage and regression findings.
<!-- MOTION-DNA-EXTENSION-END -->
