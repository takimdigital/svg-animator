# README page kit ("Spine" style)

A whole GitHub README that reads as **one designed page** but is really a stack of animated SVG blocks. `scripts/readme_page.py` turns one JSON spec into the blocks, a dark and a light variant of each, and the `README.md` that stacks them.

```
python scripts/readme_page.py assets/readme/spine-template.json ./out --check --seams-selftest
```
Output: `out/README.md`, `out/docs/readme/NN-<block>-{dark,light}.svg`. Add `--preview` for stitched PNGs of the page at four moments.

The generated output is **not committed**. `assets/examples/` is reserved for spec-backed examples (CI refuses an `.svg` there without a spec), and a second copy of generated output drifts. The spec in `assets/readme/` is the source; regenerate the page from it. `python -m unittest discover -s tests` regenerates both templates, checks every block, and checks the output is byte-reproducible.

## Contents
1. Why it feels like one page
2. The stacking markup (measured)
3. Spec reference
4. Verification
5. Limits
6. Troubleshooting

---

## 1. Why it feels like one page

| Device | What it does | Why it matters |
|---|---|---|
| **One spine** | A vertical line at the same x in every block, with a numbered station node per section and a diamond end cap | The eye reads continuity before it reads blocks |
| **One pulse, one clock** | A dot crosses the *whole page* (0.03 → 0.88 of the loop, constant speed); each station lights as it arrives | Blocks are separate images, but they share a timeline, so the motion reads as one |
| **Page-coordinate glow** | Background glows are positioned in page y, and each block draws only its slice | A glow that crosses a block border continues instead of restarting |
| **Page-aligned ruler** | Tick marks on the right edge land on page-y multiples of 24 (long every 120) | Ticks line up across blocks with no per-block tuning |
| **Transparent blocks, dark + light pairs** | No background rectangle; `<picture>` picks the variant | The GitHub page is the background, so a hairline between blocks has nothing to contrast with |
| **Ghost numerals + crop marks** | Outlined `01`…`06` behind each section, corner marks around the content | Gives each station a printed-sheet structure |

## 2. The stacking markup (measured)

Plain Markdown cannot do this on its own. Measured in Chromium, standards mode, 888 px column:

| Markup | Gap between consecutive images |
|---|---|
| `<img>` per line | **7 px** (the text baseline gap) |
| one image per paragraph (what Markdown generates) | **16 px** |
| one `<div>`, `<picture><img … align="top">` per block, no blank lines | **0 px** |

The generator emits the third form. **Do not put blank lines inside the `<div>`** (Markdown would start a new paragraph) and do not remove `align="top"`.

## 3. Spec reference

```json
{ "style":"spine", "name":"…", "tagline":"…", "description":"…", "badges":["MIT","v1.4.0"],
  "dur":24, "themes":{"dark":"ember","light":"paper"}, "brand":{"accent":"#D97757"},
  "hero":{"eyebrow":"open source","href":"https://github.com/you/repo","cta":[{"label":"Get started"}],"visual":{"type":"art","variant":"orbits"}},
  "nav":true,
  "sections":[{"id":"install","nav":"Install","title":"…","lede":"…","copy":["npm i -g …"],"part":{"type":"terminal", … }}],
  "footer":{"closing":"…","text":"MIT © …","links":[{"label":"Docs","href":"…"}]} }
```
- `part` accepts **any generator type** (see `diagram-types.md`, `animated-things.md`). Its `title` is ignored (the section supplies the heading).
- **Fitting**: content width is 820 px. A wider part is rebuilt narrower (flow `gap_x`, cards `tile_w`, timeline spacing, `width`/`size`/`radius` knobs). Only if that fails is it scaled, with a `WARNING`; **geometry lint is skipped for a scaled part**, so prefer a spec that fits.
- **Windows**: overlay-type parts (cards, flow, radial, timeline, layers, …) play in a window that opens when the pulse reaches their station. *Reveal-type* parts (`terminal counter gauge chart logo text radar`) hide their own content outside their cue, so they keep the **whole loop**; otherwise they would sit blank for most of it.
- `copy` lines also appear as a real, copyable code block under the page (`<details>`).
- `prose` is an optional list of Markdown strings emitted **after the page** in `README.md`. The page's words live inside images, so search engines, GitHub search and screen readers cannot read them; put the real explanation here. A spec without `prose` produces the same output as before.
- `footer.rev` sets the revision label in the blueprint title block (default `1.0 · <sheet>`). `footer.links` entries may be relative paths (`CONTRIBUTING.md`) or URLs.
- `hero.href` wraps the hero block in a link; other blocks are not clickable (images), so real links belong in the closing `<p>`.
- `themes` must name one dark and one light theme from `diagram-types.md` §2; `brand` overrides tokens in both.

## 3b. Styles

The `"style"` key selects the page skeleton. Both styles take the same spec, so content moves between them without edits.

| Style | Look | Template |
|---|---|---|
| `spine` (default) | one vertical spine through every block, numbered station nodes, ghost numerals, crop marks, page-aligned ruler | `assets/readme/spine-template.json` |
| `blueprint` | drafting sheet: millimetre grid behind every block, dimension line down the margin, numbered section circles, a dimension line under each part labelled with its real width, title block in the footer | `assets/readme/project-readme.json` (this repository's own README) |

An unknown style is refused with an error, not silently replaced. Blueprint drops the feedback arrow from its flow (the four-column flow has no room for it at that width); the spine version keeps it.

## 4. Verification

| Command | Proves | Does not prove |
|---|---|---|
| `--check` | every block passes `lint_svg_anim.py` (0 errors, 0 warnings) | that it looks right |
| `--preview` | stitched page PNGs (inline SVG, seekable in time) — **look at them** | exact GitHub rendering (inline SVG can show a 1 px hairline that `<img>` does not) |
| `--seams` | renders the README markup as real `<img>` at 888/760/640/480/390 px, dark and light; fails on layout gap > 0.5 px or spine dip > 40/765 | GitHub's own CSS, dimmed/high-contrast themes |
| `python -m unittest discover -s tests` | both templates generate; every block lints 0 errors and 0 warnings; output is byte-identical across two runs; an unknown style is refused; the lint still reports label overflow (matched by its exact message, with a clean twin that must produce no warnings) | exact GitHub rendering |
| `python scripts/verify.py <blocks>` | in a real browser at frame 0: no animated element is visible before its cue (the parked-element trap). Spine and blueprint: 18/18 blocks pass | motion quality — look at the previews |
| `--seams-selftest` | the gate can fail: correct markup passes **and** plain `<img>` (no `align`) fails | — |

Template result: gap 0.00 px at every width in both themes, worst spine dip 12/765; the no-`align` markup fails (7.00 px gap, dip up to 135 in dark). The dip measure alone does **not** catch light mode; the gap measure does. `--seams` needs Playwright and Pillow (optional extras, as for `render_frames.py`).

## 5. Limits
- Each block is an independent image: SMIL timelines start when each image loads, so pulse hand-off across a block border is approximate if one loads late.
- Text inside images is not selectable or searchable. Alt text carries the meaning; `copy` carries anything a reader must copy.
- Not tested on GitHub's dimmed / high-contrast themes (`<picture>` serves the light or dark file).
- Page blocks ship **no reduced-motion twins**. CONTRIBUTING requires a `-static.svg` twin for every *example*; these blocks are page output, not examples, so that gate does not reach them. A `prefers-reduced-motion` source in the `<picture>` would be the way to add it. That is not built, and it has not been checked on GitHub.
- Page height is fixed by the spec (~3.9 k px for the template); very long pages are better split into a short README plus docs pages.

## 6. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Thin stripes between blocks | blank line inside the `<div>`, or `align="top"` missing | restore the generated markup |
| A section is blank for seconds | a reveal-type part given a short window | leave `window` alone (the kit assigns the full loop) |
| `WARNING … scaled to 0.9` | part wider than 820 px and no knob could shrink it | shorten labels, drop a column, or pick another type |
| Hero title overflows | very long `name` | the title auto-shrinks to a floor of 34 px; shorten the name |
