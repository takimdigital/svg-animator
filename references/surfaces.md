# Visual surfaces: choosing a grammar, not just a palette

> `theme` is colour. `surface` is everything else about how the graphic is drawn.

## The problem this fixes

For its first 53 examples, this skill had six palettes and exactly **one** look.
Measured across all 53:

| always present | never present |
|---|---|
| a rounded opaque background rect | `textPath` |
| three blurred radial blobs drifting behind it | animated `feTurbulence` |
| a generous blur on every glow | `stroke-dash` draw-on |
| | a CSS `<style>` animation |

Six themes over one surface is not visual range. And it was not a prompt
problem — the surface was hardcoded:

```
assemble()    →  <rect ... rx="16" fill="bg"/>     unconditional
common_defs() →  <filter id="glow"><feGaussianBlur/> unconditional
aurora()      →  three blobs, unless "aurora": false
```

A model told "be more visual" would still hand back the same glowing rounded
box, because the generator had no other option to give it.

## The three surfaces

Set `"surface"` in the spec. Everything else about the graphic is unchanged.

| `surface` | background | aurora bed | glow blur | reads as |
|---|---|---|---|---|
| `glow` *(default)* | rounded, opaque | yes | 3.6 | ambient, product-y, the house style |
| `flat` | square, opaque | no | 1.0 | technical, instrument, diagram |
| `bare` | **none** | no | 1.0 | for embedding into a page you control |

```json
{ "type": "flow", "theme": "mono", "surface": "flat", "dur": 10 }
```

Verified by rendering the same spec in each:

- **`glow` → `flat`** is unmistakable: the drifting colour bed disappears, the
  corners square off, and a flow diagram stops looking like a marketing hero and
  starts looking like a terminal. Same theme, so the surface is doing the work.
  See `assets/examples/flow-flat.svg` beside `flow-with-feedback.svg`.
- It is not diagram-only: `gauge-dashboard-flat.svg` is the same instruments
  with the glow bed gone, and they read as gauges rather than as ambience.

## Choosing one

This is the intent question that was previously unanswerable, because there was
nothing to choose between.

| the brief says | use |
|---|---|
| a hero, a cover, something for the top of a README | `glow` |
| a diagram, a pipeline, anything that has to be *read* | `flat` |
| it goes inside a page you control and you know that page's colour | `bare` |

If the brief says none of those, it is `glow`, because it is the default and
because it is the one that survives being embedded anywhere.

### `bare` has one hard constraint

**`bare` draws no background, so it inherits whatever is behind it.** Rendered on
a light page, a dark-themed `bare` graphic is nearly illegible — the dark strokes
disappear into a cream background. That is not a defect to work around, it is
the trade: you get transparency and you take responsibility for what is behind it.

So `bare` is for controlled embedding, **not** for a public README. This matches
the rule the skill already states — *"give dark graphics their own background
rect, don't inherit GitHub's page colour"* — and there is deliberately **no
`bare` example in the gallery**, because half of GitHub's readers would see it
unreadable.

## Why there is no fourth surface

A `line` variant with the glow filter removed was built and cut. Every builder
references `url(#glow)` from 11 inline sites across four modules, so omitting
the definition left **9 dangling references** and the linter correctly rejected
the output.

The surface is applied by redefining the shared defs in one place rather than
by editing every call site — which is why it stays cheap, and also why it can
only vary the *defs*. A surface that differs in the bodies (hairline strokes
instead of filled cards, rules instead of blobs) needs every builder changed, and
would be worth doing properly on its own rather than as a flag.

`tests/test_morph_path.py` asserts every surface still defines `#glow`, so this
cannot regress silently.

## Why `glow` must never change

It is the default, and all 53 pre-existing examples were generated with it.
Any change to its output stops every committed example from regenerating
byte-for-byte, which the `reproducible` CI job enforces.

This is not theoretical: adding a surface initially rewrote `stop-opacity="0.34"`
as `stop-opacity="0.340"` and broke all 53 at once. The byte-identity gate caught
it immediately, which is the only reason it was a five-minute fix rather than a
silent regression.

## See also

- `references/intent-first.md` — the 5-question brief; `surface` is one of its answers
- `references/combinations.md` §5 — light/dark pairs, the other half of "fitting the page"
- `assets/examples/flow-flat.svg`, `gauge-dashboard-flat.svg` — the shipped proof
- `scripts/diagram_common.py` — `SURFACES`, the whole table
