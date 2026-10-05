# Static-first, and the trap that breaks it

> The one rule that separates a diagram that works everywhere from one that looks
> broken in a README, a PDF export or a phone preview. Read this before writing a
> builder that reveals anything.

## The rule

**Frame 0 must already be a finished graphic.**

Not "mostly there". Not "the frame before the animation starts". Finished — every
node, every label, every line of the final composition, at its final position.
Motion is then added as *overlays* that start invisible.

The reason is not aesthetic. An SVG referenced by an HTML `<img>` is processed in
what the W3C SVG Integration spec calls **secure animated mode**:

| capability | in secure animated mode |
|---|---|
| script execution | no |
| external references | no |
| interactivity (hover, click, tooltips) | no |
| **declarative animation** | **yes** |

So a diagram in a README, a docs site or a slide *is* an image, and an image runs
nothing. When the surrounding document cannot animate — a PDF export, a markdown
rasteriser, a client that drops to *secure static mode* — the picture simply stops
moving. Everything still has to read.

Two corollaries the rest of this document depends on:

- No JavaScript, ever. Not "a little".
- No external font files, ever. A system font stack only. An image cannot fetch.

## The trap: the animation that sits parked in the corner

This is the single most common way the rule gets broken, and it looks fine in code.

An animation **has no effect before it begins.** No `begin`, no attribute change —
the element sits at its own base value. So if you stagger a reveal by giving
element *n* a positive `begin`, then at `t=0` every element that has not started
yet is parked at its *base* position. For most geometry that base position is
roughly sensible. For a traveller — a dot that is supposed to be somewhere along a
rail — the base value is usually its untransformed origin:

> a dot waiting its turn would sit parked at the canvas origin, in the corner, in
> full view

That is a real bug we shipped. It is invisible in the source, invisible to a
syntax check, and completely obvious the moment you scrub to `t=0` and look.

The fix is a **negative `begin`**, which pre-rolls the loop so that frame 0 lands
at a chosen point in the cycle instead of at zero:

```xml
<circle r="11" opacity="0">
  <animateMotion dur="16s" begin="-6.800s" repeatCount="indefinite" path="…"/>
</circle>
```

Pre-rolling a periodic animation does not change its period, so the loop stays
seamless. Pick the pre-roll inside the **hold window** — after the last reveal cue
has played, before the loop's fade-out — so frame 0 shows the finished state and
the animation still plays on from there.

## The subtler trap: pre-rolls inside a compose

A pre-roll is an offset in a part's own `0..1` loop. In a `compose`, a part's
`keyTimes` are **remapped into the part's `window`** before anything else runs. So
an offset chosen against the part's own loop can land *past the end of that
window*, in the region where the part's fade-out has already run — which means the
part starts **invisible**.

We shipped this twice. Both times the standalone example looked perfect and the
composed one was blank:

| part | window | frame 0 landed at | result |
|---|---|---|---|
| `terminal`, standalone | `[0, 1]` | 0.850 | correct |
| `terminal` in `compose-onboarding` | `[0, 0.5]` | 0.850 | **past 0.48 → opacity 0** |
| `logo`, standalone | `[0, 1]` | 0.850 | correct |
| `logo` in `compose-product-hero` | `[0, 0.55]` | 0.850 | **past 0.539 → opacity 0** |

So: **do not stamp a negative `begin` in a builder.** Return the fraction you want
and let the composer scale it.

```python
# build_terminal / build_logo
PRE = (fit_end + 0.90) / 2.0        # midpoint of the hold window
return part(body, W, H, sb, False, desc, preroll=PRE, dur=dur)
```

`apply_window` then converts it, scaling by whatever window the part was given:

```python
begin = f' begin="{-((a + preroll * (b - a)) * dur):.3f}s"'
```

`[0, 1]` gives `-0.85·dur` and `[0, 0.55]` gives `-0.4675·dur`. One number, every
context.

## The invariant that makes it checkable

For every type in this skill, **the base state of the file — every attribute with
all `<animate*>`, `<animateTransform>` and `<animateMotion>` elements deleted —
must still be the finished graphic.**

This is a stronger statement than "frame 0 is complete", and it is the one that
pays:

- It is a **static** property. You can check it by parsing, with no browser.
- It is what makes the reduced-motion fallback free to *generate* (below).
- It is what makes the file safe in *secure static mode*, not merely at `t=0`.

## Reduced motion: CSS inside the file cannot do this

**There is no way to stop SMIL from CSS.** This is worth stating plainly, because
the natural thing to write does not work and looks like it does:

```xml
<!-- WRONG. Does absolutely nothing. -->
<style>
  @media (prefers-reduced-motion: reduce){
    svg * { animation: none !important }        /* CSS animation, not SMIL */
    animate, animateTransform, animateMotion { display: none }   /* still animates */
  }
</style>
```

SMIL is a separate animation system from CSS animations. `animation:` and
`display:` are CSS properties; an `<animate>` element's clock is not driven by
either. Measured, by emulating `prefers-reduced-motion: reduce` and watching a
traveller in real time:

```
reduce + svg * { animation: none !important }   bean x: 718 → 792 → 870 → 944   STILL MOVING
reduce + display:none on animate*               bean x: 721 → 800 → 878 → 952   STILL MOVING
reduce + animation-name:none                    bean x: 713 → 787 → 860 → 936   STILL MOVING
no-preference (baseline)                        bean x: 718 → 792 → 870 → 944   STILL MOVING
```

Identical. A file that ships the block looks accessible and is not.

### What actually works: ship a static twin

Because the base state is already the finished graphic, the static twin is just
**the same file with every animation element removed** — no second drawing to
maintain, and the two cannot drift:

```bash
# one spec, two files
python scripts/gen_diagram.py spec.json docs/hero.svg
python scripts/static_twin.py docs/hero.svg docs/hero-static.svg
```

```html
<picture>
  <source media="(prefers-reduced-motion: reduce)" srcset="hero-static.svg">
  <img src="hero.svg" alt="…" width="100%">
</picture>
```

Verified: with `prefers-reduced-motion: no-preference` the browser served
`flow.svg`; with `reduce` it served `flow-static.svg`, and the static one is the
complete diagram. `<picture>` and `<source>` are on GitHub's sanitiser allowlist
and `<picture>` in Markdown is GA since Aug 2022.

This is the same mechanism as the light/dark pair, and the two compose:

```html
<picture>
  <source media="(prefers-reduced-motion: reduce)" srcset="hero-dark-static.svg">
  <source media="(prefers-color-scheme: dark)"     srcset="hero-dark.svg">
  <img src="hero-light.svg" alt="…">
</picture>
```

Order matters: the first `<source>` whose `media` matches wins, so put the
reduced-motion one first.

If you ship only one file, frame 0 is what a reduced-motion user gets anyway —
which is the whole reason for the static-first rule. The twin is an upgrade, not
a substitute.

## Verifying it

Static analysis cannot see occlusion, so measure the rendered frame:

```python
# frame 0 must show the finished graphic
effective = 1
for node in text.ancestors():                       # ancestors matter!
    effective *= opacity_of(node)
```

The ancestor chain is the part people get wrong. A `compose` wraps each part in a
group that is itself at `opacity 0` outside the part's window, so a check that
only reads each text node's own `opacity` reports a blank terminal as complete.
Multiply down the chain, and compare `t=0` against `t=0.5·dur`.

### There is no lint check for this, and that is deliberate

`scripts/measure_frame0.py` reports the numbers. It does not gate, because four
attempts to make it gate all failed against the real pre-fix files:

| attempt | why it fails |
|---|---|
| no `<text>` invisible at frame 0 | `gauge-dashboard` legitimately hides 45 count-up labels and renders a complete graphic |
| visible characters, frame 0 vs mid-loop | reads 1.00 even on broken files — opacity cannot see **occlusion**, and the pre-fix terminal hid its text under a cover *rect* |
| absolute painted pixels | every example paints a full-canvas background rect, so ink saturates at ~100% either way |
| pixels *differing* frame 0 vs mid-loop | works mechanically, useless as a gate: broken terminal **2.1%**, fixed terminal **1.9%** — ambient aurora motion swamps the signal |

Separating "hidden until its cue" from "genuinely blank" needs per-type knowledge
of intent. Use the measurement as a trend across your diff: a file whose numbers
move when you did not touch it is the interesting signal. That is how the composed
logo bug was found.

If you want to add a real check, prove it on a known-bad file first:

```bash
git show <ref-before-the-fix>:assets/examples/<name>.svg > /tmp/bad.svg
```

## Checklist

- [ ] Frame 0 is the finished graphic, not an intro pose
- [ ] Nothing meaningful is hidden behind a positive `begin`
- [ ] Pre-rolls come from `preroll=`, never a hardcoded `begin` in a builder
- [ ] The pre-roll fraction sits inside the hold window, after the last cue
- [ ] Deleting all animation elements still leaves a complete graphic
- [ ] A `prefers-reduced-motion` block is present
- [ ] Verified by rendering `t=0` and *looking*, with ancestor-aware opacity

## See also

- `CONTRIBUTING.md` — the `part()` signature and when to return `preroll`
- `references/diagram-types.md` — every type, and its spec fields