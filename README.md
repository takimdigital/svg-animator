# svg-animator

<p align="center">
  <img src="docs/hero.svg" alt="svg-animator: the brief → spec → build → lint → frames → ship pipeline, animated on one shared clock" width="100%">
</p>

<p align="center">
  <em>A skill that teaches an AI agent to make animated SVGs that are <b>correct</b>,<br>
  not just plausible — anywhere an SVG renders: READMEs, docs, sites, slides, email.</em>
</p>

---

## Why this exists

Ask a model to "make an animated architecture diagram for my README" and you get
something that *looks* right in the source. Then you open it and:

- the travelling dot cuts **straight through** a card instead of along the rail
- three glows fire at once because somebody eyeballed `keyTimes="0.46"`
- the loop has a visible **seam** — everything blinks at the restart
- frame 0 is an **empty box**, so anyone on a phone, in a PDF, or in a client that
  doesn't run SMIL sees nothing at all
- arrows stop 20px short of the thing they point at

None of these are hard. They're all just *unverified*. SVG animation fails
**silently** — a wrong `keyTime` still runs, it just runs wrong, and a model has
no way to notice by reading the XML.

So this skill doesn't ask the model to be careful. It gives it a **lint, a frame
renderer, and a rule that looking is mandatory.**

```
BRIEF → ROUTE → SPEC → BUILD → LINT → FRAMES → FIX LOOP → DELIVER
```

One command runs build → lint → frames and ends with `RESULT: PASS / PASS WITH WARNINGS / FAIL`.
It never lies about what it checked.

---

## Install

The skill is a folder of Markdown, Python and JSON. Copy it where your agent looks
for skills — the layout is deliberately conventional.

```bash
git clone https://github.com/takimdigital/svg-animator.git

# Claude Code / most agent harnesses
cp -r svg-animator ~/.claude/skills/

# or symlink it so updates land everywhere
ln -s "$PWD/svg-animator" ~/.claude/skills/svg-animator
```

Optionally install the one runtime dependency (frame rendering only — lint and
generate work without it):

```bash
pip install playwright && python -m playwright install chromium
```

**Requirements:** Python 3.9+. That's it. No Node, no build step, no npm.

---

## Use it in one command

Ask your agent for an animated SVG. It'll route itself. If you want to drive the
generator directly:

```bash
# 1. pick a spec from assets/specs/ and edit the labels to be yours
$EDITOR assets/specs/flow-with-feedback.json

# 2. build + lint + render frames, all at once
python scripts/run_pipeline.py assets/specs/flow-with-feedback.json \
        --out-dir run --name my-diagram

# 3. LOOK at run/frames/*.png before you ship anything
```

```
RESULT: PASS (0 errors, 0 warnings) - now view the frames
```

A `PASS` is not a compliment, it's a floor. It means the file is structurally
sound. Whether it looks *good* is a separate question, answered by looking.

---

## Three ways in

<p align="center">
  <img src="docs/modes.svg" alt="Three modes: generator, hand-build, and fix an existing SVG" width="100%">
</p>

### A · Generator — 22 types, one JSON spec

The fast, reliable path. You write data; it computes the geometry and the timing.

| Diagrams | Things |
|---|---|
| `flow` · `radial` · `phases` · `timeline` | `loader` · `logo` · `text` · `gauge` · `radar` |
| `network` · `layers` · `cycle` · `sequence` | `backdrop` · `icons` · `scene` · `counter` · `art` |
| `terminal` · `cards` · `chart` · `banner` | `compose` (any of the above, one canvas) |

```json
{"type": "flow", "dur": 10, "arrows": true,
 "columns": [
   [{"id": "u", "label": "User", "sub": "intent"}],
   [{"id": "c", "label": "CORE", "sub": "pool", "key": true}],
   [{"id": "x", "label": "Client"}, {"id": "y", "label": "Server"}]],
 "edges": "auto",
 "feedback": {"id": "m", "label": "Maintainer", "from": "x", "to": "c"}}
```

Every keyTime, rail endpoint and arrowhead offset is **derived** — that's the
whole point. Themes: `ember ocean forest mono paper violet sunset`, or override
any palette token.

<p align="center">
  <img src="docs/gallery/flow-with-feedback.svg" alt="Flow diagram with a feedback loop" width="88%">
</p>

### B · Hand-build — anything the generator can't

A mascot. A bespoke logo. A scene with an opinion. Decompose it: **nouns → shapes,
verbs → motion**, then draw the still first and animate second.

<p align="center">
  <img src="docs/mark.svg" alt="The svg-animator mark: an S-curve rail with a dot riding it between two nodes" width="180">
</p>

The mark above is Mode B — hand-written, geometry computed rather than eyeballed.
Note the S-curve's control points share their `y` with their endpoints, so the
traveller arrives moving horizontally and the arrowhead sits flat; and note the dot
fades out at 90% before teleporting back, so the loop restart is invisible.

### C · Fix — an SVG that already exists

Paste in something broken. The skill cleans paste artifacts (`\<svg`,
`xlink\:href`, smart quotes), inventories every animation before touching it,
maps symptom → cause → fix, and changes as little as possible.

---

## The gallery

Everything below is a real generator output from `assets/examples/`, lint-clean.
These are not mockups pasted into a README — they're the artifacts.

### Diagrams

<p align="center">
  <img src="docs/gallery/network-services.svg" alt="Service network with pulses spreading from a gateway" width="100%">
</p>

<p align="center">
  <img src="docs/gallery/timeline-roadmap.svg" alt="Roadmap timeline with alternating milestone cards" width="100%">
</p>

<p align="center">
  <img src="docs/gallery/terminal-demo.svg" alt="Terminal window typing a command and its output" width="88%">
</p>

<p align="center">
  <img src="docs/gallery/chart-line.svg" alt="Line chart that draws on and reveals its area" width="88%">
</p>

### Things

<p align="center">
  <img src="docs/gallery/loader-sheet.svg" alt="Sheet of eight loading spinner variants" width="100%">
</p>

<p align="center">
  <img src="docs/gallery/gauge-dashboard.svg" alt="Dashboard of gauges, rings, bars and a donut" width="100%">
</p>

<p align="center">
  <img src="docs/gallery/radar-skills.svg" alt="Radar chart comparing skills across axes" width="70%">
</p>

<p align="center">
  <img src="docs/gallery/logo-shield.svg" alt="Shield logo reveal animation" width="55%">
</p>

<p align="center">
  <img src="docs/gallery/text-shimmer.svg" alt="Shimmer text effect" width="80%">
</p>

<p align="center">
  <img src="docs/gallery/counter-stats.svg" alt="Odometer counters rolling up to their values" width="100%">
</p>

<p align="center">
  <img src="docs/gallery/icons-set.svg" alt="Twelve micro-animated icons on a grid" width="100%">
</p>

<p align="center">
  <img src="docs/gallery/scene-rocket.svg" alt="Rocket launch scene with shake and smoke" width="55%">
</p>

<p align="center">
  <img src="docs/gallery/art-mandala.svg" alt="Generative mandala art" width="45%">
</p>

<p align="center">
  <img src="docs/gallery/backdrop-mesh.svg" alt="Animated mesh-gradient backdrop" width="100%">
</p>

---

## The seven principles

Every graphic this skill produces obeys these. They're the difference between
"animation" and "a moving thing that's wrong."

**1 · Static-first.** Frame 0 is already a complete, good-looking graphic. Base
shapes are always visible; motion is an *overlay* that starts at `opacity="0"`.
If the animation never runs — mobile preview, PDF export, a client without SMIL —
the viewer still sees the whole picture. This is why the terminal type isn't typed
into existence: all the text is in the DOM, and cover rectangles slide away.

**2 · Compute, don't guess.** Layout, rail endpoints and every `keyTime` come out
of a spec or the linter. Nobody types `0.46` because it feels right.

**3 · Motion follows drawn lines.** Dots travel on rails that exist, each rail
touches its cards, and nothing crosses a card or its text unless crossing is the
entire point.

**4 · One master clock.** One loop length; every phase is a fraction of it;
secondary pulses are `dur/2` or `dur/4`. Leave ~10% of the loop at rest so the
seam is invisible.

**5 · Self-contained.** System font stacks, everything inlined, no scripts, no
external assets. One `.svg` file that works offline, forever.

**6 · Verify by looking.** Lint, render frames at meaningful timestamps, *view
them*, and say what you actually saw.

**7 · Report honestly.** State what was verified and what wasn't. Comments in the
SVG restate lint and frame results — never intentions.

---

## What the linter catches

`scripts/lint_svg_anim.py` — 31 KB of the "don't ship this broken" department:

- `keyTimes`/`values`/`keySplines` count mismatches, non-monotonic or unterminated keyTimes
- glow and opacity windows that never return to `0` — the classic half-faded ghost
- **whether each dot's path is geometrically identical to the rail it rides**
- **whether a rail actually touches the cards it claims to connect**
- **when each dot enters and leaves each card**, and whether it crosses one it shouldn't
- unresolvable `url(#id)` / `href="#id"` references
- duplicate IDs
- invisible elements that are supposed to be hidden, and visible ones that aren't
- files over 100 KB or with a runaway SMIL node count
- CSS transforms missing `transform-box: fill-box` (they silently rotate around
  the wrong origin)
- arrowheads that don't land on their target's edge

And it tells you the *diagnostic*, not just the verdict — it prints each dot's
enter/leave times per card so you can fix the cause instead of nudging a number.

---

## Layout

```
svg-animator/
├── SKILL.md                     the pipeline, the rules, the routing
├── references/                  read on demand, not upfront
│   ├── diagram-types.md           12 diagram types + compose: every spec field
│   ├── animated-things.md         10 non-diagram types
│   ├── combinations.md            effect recipes, compose recipes, choreography
│   ├── readme-diagrams.md         the 12 techniques behind README-grade diagrams
│   ├── diagrams.md                diagram rules + failure modes
│   ├── motion-vocabulary.md       40+ verbs → techniques
│   ├── drawing-fundamentals.md     primitives, paths, composition, colour
│   ├── patterns.md                copy-ready animated snippets
│   ├── smil-cheatsheet.md         syntax and the 10 gotchas
│   ├── css-animation.md           transforms, staggering, reduced-motion
│   ├── design-principles.md       timing, easing, loops, palette
│   └── debugging.md               symptom → cause → fix
├── scripts/
│   ├── run_pipeline.py            the whole thing, one entry point
│   ├── gen_diagram.py             22 types + compose
│   ├── diagram_common.py · diagram_extra.py · things_a.py · things_b.py
│   ├── lint_svg_anim.py           the linter
│   └── render_frames.py           PNG frames at chosen timestamps
└── assets/
    ├── template.svg
    ├── specs/*.json               49 worked specs, one per type
    └── examples/*.svg             49 generated, lint-clean references
```

Progressive disclosure: `SKILL.md` is the whole method in one page. The twelve
reference files load only when the task touches them, so the skill stays cheap.

---

## Embedding in your README

```markdown
![architecture](docs/hero.svg)
```

or, to control width:

```html
<img src="docs/hero.svg" alt="architecture" width="100%">
```

Three caveats worth knowing:

- Inside `<img>`, hover and JavaScript do nothing. Design for the loop alone.
- Give dark graphics their **own** background rect — don't inherit GitHub's page
  colour. Every generated file ships with a rounded one.
- The static fallback is **frame 0**, which is why frame 0 must be complete.

Full discussion in `references/readme-diagrams.md` §4.

---

## Adding a generator type

1. Write the emitter in `scripts/things_a.py` (or `things_b.py` / `diagram_extra.py`),
   returning `(svg_fragment, height, info)`.
2. Take `dur`, `theme` and `colors` from the common helper — never hardcode a colour
   or a duration; the master clock belongs to the caller.
3. Build every base shape as the **finished** state, then add animation as overlays.
4. Register it in `gen_diagram.py`'s dispatch table.
5. Add a spec to `assets/specs/`, run the pipeline, and **view the frames**.
6. Add the generated `.svg` to `assets/examples/`.

---

## License

MIT. See [LICENSE](LICENSE).

Built because AI-generated SVG animation is confidently wrong, and the fix isn't
a better prompt — it's a linter and a habit of looking at the output.
