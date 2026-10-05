# Combinations: how to mix types, effects, themes and timing

Four levels of combining. Use the lowest level that does the job.

## Contents
1. Level 1 — effects inside one graphic (named recipes)
2. Level 2 — diagrams together (`compose` recipes)
3. Level 3 — choreography patterns across parts
4. Level 4 — generator + hand-made artwork
5. Theme pairing
6. What not to combine

---

## 1. Effects inside one graphic (named recipes)

| Recipe | Ingredients | When |
|---|---|---|
| **Signal flow** | rails + relay dots + node glow on arrival | any pipeline (`flow`, `network`, `timeline`) |
| **Sonar broadcast** | hub + 3 phased rings under cards + clockwise glow sweep | one-to-many (`radial`) |
| **Request/response** | down dot + up dot (different colours) + layer glow | tiers (`layers`), sequence |
| **Orbit loop** | arcs + one dot + step glow + slow dashed deco ring | lifecycles (`cycle`) |
| **Reveal then hold** | grow/draw from the finished base, hold, fade at 90–100 % | charts, terminal |
| **Shimmer title** | repeating gradient translated one period | banners, logos (ambient, 8–16 s) |
| **Aurora bed** | 3 gradient blobs, 24/27/30 s drift | background for all dark themes |
| **Draw-on → fill → shimmer** | stroke draw-on (`pathLength`), fill-opacity in, one gradient pass | logo reveal |
| **Pulse + ripple** | core breathing (`dur/2`) + expanding rings (negative begins) | "alive" hub, status |
| **Parallax + particles** | 2–3 layers drifting at 60/40/25 s + seeded particles | hero backgrounds |
| **Typewriter + cursor** | cover rect (discrete steps) + blinking/following cursor | terminal, quotes |
| **Counter swap** | stacked texts, discrete opacity, one visible at a time | stats |
| **Flow + dash march** | static dashed rail with `stroke-dashoffset` animation under relay dots | data streams, busy links |
| **Odometer roll** | stacked digits `0-9,0-9` in a clip, translate to the final digit (spline ease, staggered) | `counter` |
| **Count-up** | stacked texts with discrete opacity, final value is the base state | `gauge` |
| **Highlight + dim** | glow on the active element + opacity 0.55 on others during its window | focus tours |

Rules: one hero motion at a time; ambient motion (aurora, particles, rings) must be slow (≥ 12 s) and low contrast; synced pulses use `dur`, `dur/2`, `dur/4`.

## 2. Diagrams together (`compose`)

| Goal | Layout | Parts (windows) |
|---|---|---|
| **README hero** | stack | `banner` (always) + `cards` `[0,0.5]` + `flow` `[0.15,1]` |
| **Story / walkthrough** | stack | `flow` `[0,0.48]` then `sequence` `[0.52,1]` (disjoint = one after the other) |
| **Dashboard** | grid `cols:2` | `chart` bar + `chart` line + `terminal` + `timeline`, all `[0,1]` |
| **Before / after** | row | two `flow` specs, second with `window:[0.5,1]` |
| **Architecture + proof** | stack | `layers` + `chart` (latency) |
| **Roadmap page** | stack | `banner` + `timeline` + `cards` |
| **Onboarding** | stack | `terminal` (install) `[0,0.5]` → `cycle` (daily loop) `[0.5,1]` |
| **System tour** | stack | `radial` (what exists) → `sequence` (how it talks) → `layers` (where it runs) with three thirds as windows |
| **Product hero** | stack | `logo` `[0,.55]` + `counter` `[.2,.75]` + `icons` (always) |
| **Status board** | grid `cols:2` | `gauge` + `radar` + `loader` + `layers`, all `[0,1]` |
| **Launch story** | stack | `text` reveal `[0,.3]` → `scene` rocket `[.28,.72]` → `counter` `[.7,1]` |
| **Cover** | stack | `backdrop` (waves/stars) + `text` shimmer + `art` mandala |
| **Loading page** | row | `loader` (single variant) + `text` type |

Practical limits: ≤ 4 parts per compose; total height ≤ ~1100 px; keep parts' widths within ~15 % of each other (they are centred), or use `row`/`grid`. Give each part a short `title` so viewers know what they are looking at. Disjoint windows mean each part is only animated ~⅓–½ of the loop: raise `dur` (12–18 s) accordingly.

## 3. Choreography patterns across parts

- **Sequential**: windows `[0,.5]`, `[.5,1]`. Clear story, slower loop.
- **Cascade**: overlapping windows `[0,.6]`, `[.2,.8]`, `[.4,1]`. Feels like one wave rolling down the page.
- **Concurrent**: all `[0,1]`. Dashboards; use only if each part has a different rhythm.
- **Call and response**: part A animates `[0,.5]` (cause), part B `[.5,1]` (effect), e.g. `terminal` then `chart`.
- **Wave**: inside one type, `cards`/`radial` already sweep; use `compose` row with staggered windows to sweep across diagrams.
- **Rest**: leave the last ~8 % of the master loop without activity; `window` ends ≤ 0.95 for the last part if a clean seam matters.

## 4. Generator + hand-made artwork
When a spec nearly fits but the user wants custom art:
1. Generate the diagram (`gen_diagram.py`).
2. Insert hand-built elements (mascot, icon, logo, illustration from `drawing-fundamentals.md`) as `<g>` blocks **before** the labels/travellers; give them ids and their own animations from `motion-vocabulary.md`.
3. Keep the clock: use the same `dur` (or divisors), negative begins for staggering.
4. Run the pipeline on the edited `.svg`; the lint still checks rails/cards/dots.
Typical combos: banner + custom mascot; flow node replaced by an icon; chart + annotation arrows; radial with a logo in the hub.

## 5. Theme pairing

Two different questions use the word "pairing". Both matter.

### Light + dark for the reader's theme (use this for anything public)

A single SVG **cannot** adapt to the reader's light/dark setting, and this is not a
limitation we can code around. An SVG referenced by an `<img>` runs in the W3C's
*secure animated mode*: it cannot see the page it is embedded in, so
`prefers-color-scheme` inside the file has nothing to match against. Its own
`@media` block evaluates against the *renderer's* preferences, not GitHub's.

So light and dark must be **two files**, swapped by the host page:

```bash
python scripts/gen_diagram.py spec.json docs/hero --pair paper ocean
```

writes `docs/hero-light.svg` and `docs/hero-dark.svg` and prints the embed:

```html
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="hero-dark.svg">
  <img src="hero-light.svg" alt="…">
</picture>
```

GitHub supports `<picture>` in Markdown (GA since Aug 2022) and `source` is on the
sanitiser allowlist, so this works in a README, in an issue or a PR comment.

Rules the generator enforces for you:

- **The two files must differ in polarity.** `paper` is the only light theme;
  `ember`, `ocean`, `forest`, `mono`, `violet`, `sunset` are dark. The tool rejects
  `--pair ember violet` rather than shipping two dark files behind a light/dark
  switch, which would look like a bug.
- **The light file goes in the `<img>`,** the dark one in the `<source>`. Reversed,
  you get a white flash on a dark page.
- **Loop lengths are identical** across the pair, so switching theme mid-read is not
  a visual jump.
- **Ship both, or neither.** A lone dark diagram on a light page is the single most
  common complaint about generated README graphics.

### Two themes in one README (visual variety)

- Same theme for everything in one README (consistency beats variety); use a second theme only to signal a *different domain* (e.g. forest charts inside an ember page) and only on whole parts.
- Dark README images need their own background (the generator's rounded rect); don't rely on GitHub's page colour.
- Pair accent + warm/cool text: `ember`+warm text, `ocean`/`violet` + cool text; `paper` only on light pages.
- Override tokens via `colors` to match a brand: `accent`, `accent2`, `accent3`, `bg`. Note `colors` applies to both halves of a `--pair` run, so override once and it holds in both.

## 6. What not to combine
- Two heavy blur sources animating (aurora_blur + glow on many nodes).
- More than one particle field, or particles over text.
- Overlapping windows on parts that both show travelling dots in the same screen region.
- Mixed loop lengths: every part follows the compose `dur`; do not hand-set different `dur` values inside parts (the compose overrides them).
- Hover/JS interactions inside a README image (they don't run).
