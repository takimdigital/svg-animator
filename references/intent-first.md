# Intent first — deciding what to draw before deciding how

> The catalog in `diagram-types.md` is a **floor, not a menu**. Use it when the
> request has a structure the generator already expresses. Leave it when the
> request has a *character* only you can invent. Read this before Step 0.

## The failure mode this prevents

A routing table turns a creative brief into a lookup. Given "a page for my
coffee subscription", the fastest wrong answer is `flow` with four nodes, because
`flow` is in the catalog and the request mentions steps. That diagram is
correct, lint-clean, and worthless: it says nothing about coffee, warmth, or the
act of buying someone a coffee.

**Ask what the reader should feel or do in three seconds. Then choose.** A type
chosen before the intent is a type chosen for you.

## The brief — five questions, answer before drawing

1. **What is this for?** README hero · docs explainer · PR description · slide ·
   social card. The destination sets the canvas, density and whether animation
   runs at all.
2. **Who reads it, and what do they already know?** A stranger needs the nouns
   spelled out. A colleague does not.
3. **What is the ONE thing they must take away?** One. Write it as a sentence.
   *"Requests are retried, so nothing is lost."* If you cannot, the piece is
   two pieces — split it, or let the strongest one win.
4. **What should it feel like?** Warm · clinical · playful · urgent · precise.
   This picks the palette and the motion character, and it is the question the
   catalog cannot answer for you.
5. **What does each moving thing *mean*?** See below — this is the whole job.

State the answers in one line each, in your reply, before you build. It is four
sentences and it prevents the most expensive kind of wrong.

## Motion must carry meaning

A moving thing is a claim about what matters. Before animating anything, be able
to finish this sentence for each animated element:

> "The ___ moves because ___."

| If the answer is… | Then |
|---|---|
| "it's the main thing" | it should be the most prominent thing on the canvas |
| "it shows the direction of flow" | it travels **along** a drawn line, not across empty space |
| "it draws the eye to X" | everything else must be quieter than X |
| nothing | **don't animate it** |

Worked example — the same three-second goal, two very different diagrams:

> *"Buy me a coffee"* page. One thing to take away: **this feels warm and
> personal, not like a payment form.**

| | A catalog-shaped answer | An intent-shaped answer |
|---|---|---|
| type | `flow`, 4 nodes | hand-built scene |
| what conveys it | "steps in a process" | steam rising, orbit of beans, a `THANKS` badge |
| why it's better | — | every moving thing means *warmth*, *appreciation*, or *giving* — nothing moves just because it can |
| what it costs | fast | one hand-drawn cup path, three steam strands |

Neither is "the right answer" in general. The second is right *for this brief*,
and you only get there by answering question 4.

## When to use a generator type

Reach for the catalog when the content **is** structure:

- a pipeline, architecture, hierarchy, timeline, sequence, or set of numbers
- the same shape as something the user already uses
- you need it correct and fast, and the drawing has no character to convey

Every one of the 22 types exists because that shape recurs. Using one is not the
boring choice — it is the *reliable* choice.

## When to leave the catalog

Hand-build (Mode B) when **any** of these is true:

- the subject is a **thing with personality** — a mascot, a product, a mascot's
  mug, a mascot's anything
- the brief leads with a **feeling**, not a process
- the type would need a `sub` label on every node to make sense
- you would have to write a caption explaining what the diagram is
- a **specific** shape matters (a logo, an icon set, a character)
- you want a detail that makes someone smile

That last one is not decoration. A small unexpected touch — a badge on the cup,
corner marks, a bean on an orbit — is often what makes a piece memorable, and no
generator will produce one because none of them is *for* that.

## Combining both

`compose` is the documented bridge: generator types carry the structure, custom
art carries the character. Put the art where the meaning is and let the
generator handle what must be precise.

One master clock still rules. Different durations are fine for **ambient** drift
(a halo breathing, stars twinkling) but anything that must be read as a sequence
— dots travelling, cards lighting up in order — has to be a fraction of the same
clock or the reader cannot follow it. See `references/patterns.md`.

## Anti-patterns

- **Captioning a diagram into existence.** If it needs "this diagram shows…",
  the diagram is wrong.
- **Motion as decoration.** If you cannot say what a moving thing *means*, cut
  it. Ambient only.
- **Filling the canvas.** A `compose` with three parts when one said it better is
  less effective, not more.
- **Defaulting to `flow`.** It is the most over-used type in existence. Reach for
  it when content genuinely flows, not when you don't know yet.
- **Shipping frame 0 as an afterthought.** Whatever the reader sees first is the
  real design; the animation is what happens after.

## Verify the intent, not just the file

The linter cannot tell you whether the piece says what you meant. Ask instead:

- Would someone who has never seen the project understand the one thing in 3s?
- Does the most prominent thing on the canvas match the most important idea?
- Is there any motion you could not justify in a sentence?
- Does it look like it was made *for this*, or assembled from parts?

That last question is the one that catches catalog-thinking. If it reads as
assembled, it was.

## See also

- `references/motion-vocabulary.md` — effect → technique cookbook, for the "how"
- `references/drawing-fundamentals.md` — primitives and object recipes, for the "what"
- `references/combinations.md` — generator + custom art, and light/dark pairs
- `references/static-first.md` — the rule that makes frame 0 count
- `assets/specs/` — 53 specs, all generated, all byte-reproducible