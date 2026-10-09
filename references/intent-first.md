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

1. **What is this for?** A website hero · a docs explainer · a PR description ·
   a slide · a social card. The destination sets the canvas, the density, and
   whether animation runs at all. **Ask this first and do not assume.** The same
   content needs a different graphic on a landing page than in a repository, and
   a skill that only ever hears "README" will answer for both.
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

## Where will it actually live?

Destination is not a formality. It changes what is even possible, and it is the
one question whose answer you cannot guess from the content.

| where | how to embed | hover / JS | `prefers-reduced-motion` | notes |
|---|---|---|---|---|
| **Website / landing page** | `<img src>` **or** inline `<svg>` | inline only | inline: a media query can gate CSS. `<img>`: ship a twin | inline needs **unique ids** per page |
| **Docs site / blog** | `<img src>` | no | ship a static twin | same as a README |
| **README in a repo** | `![alt](docs/x.svg)` | no | ship a static twin | GitHub's light/dark is invisible inside an `<img>`; use a light/dark pair |
| **Slide / PDF / print** | none — export a still | no | n/a | render a PNG frame, or frames → GIF/MP4 |
| **Email / Notion / social** | usually stripped | no | n/a | always ship a PNG fallback |

Two rules that follow from the table and are worth knowing by heart:

- **In an `<img>`, the file is isolated.** Its ids cannot collide with the page
  and it cannot see the page — which is why light/dark pairing needs *two files*.
- **Inline SVG gets more.** Hover states, focus rings, JS libraries
  (`offset-path`, Motion, GSAP), and a real `prefers-reduced-motion` media query.
  If the user says "on my website" and wants interactivity, ask whether they can
  inline it, because that unlocks things this skill otherwise tells you to skip.

## When the request is vague

"Make me something cool." "I need a diagram for my project." "Something for the
homepage." This is the **normal** case, not a failure of the user, and
interrogating someone about it is worse than building a good default and showing
them.

The protocol:

**1 · Read for signals, not nouns.** The nouns are the least informative part.
Look for what they said about *feeling*, *audience* and *place*:

> "my homepage feels boring" → the problem is **boring**, not the content
> "something for the demo, needs to look impressive" → the goal is **impress**
> "users keep not understanding our pricing" → the goal is **clarity**
> "it's for a healthcare startup, should feel safe" → the goal is **safe**

**2 · Infer the destination from where you are.** They said "my site" → website.
They pasted a README → repository. They said "slides" → stills. This is usually
right and worth stating rather than asking.

**3 · Pick a default that is cheap to be wrong about.** Prefer the inference
that takes one word to change. A `flow` diagram in the wrong theme costs one
line to fix. A hand-built illustrated scene with the wrong feeling costs the
whole piece. When unsure between two readings, **build the smaller one.**

**4 · State the inferences, then build.** One line, three clauses, no question
mark:

> Going with: a website hero, because you said homepage. Flow diagram, because
> the content is a sequence. `flat` surface and `mono` theme, because "boring"
> reads as "too busy". 8s loop. Say the word and I'll make it warmer or busier.

**5 · Offer one axis, not a menu.** "Warmer or busier?" is a useful question.
Here are nine options in a bulleted list is not — it pushes the work back onto
the person who asked you to do it.

**6 · Ask at most one blocking question**, and only when the answers would
produce genuinely different graphics: *"is this going in the repo or on the
site?"* changes the surface and the light/dark strategy. *"should it feel
warmer or colder?"* does not — just pick and offer to change it.

The failure mode to avoid is not vagueness. It is **silently choosing** — picking
an intent and never saying so, so the user cannot tell what you decided and
therefore cannot correct it.

## Situations: what a real request usually becomes

Recognition is the skill. Keyed to what someone says, not to what exists.

| they say something like | it usually is | reach for | surface |
|---|---|---|---|
| "explain how our system works" | architecture / data flow | `flow`, `layers`, `network` | `flat` |
| "show the lifecycle / the phases" | ordered stages | `phases`, `timeline`, `cycle` | `flat` |
| "what happens when X fires" | sequence with returns | `sequence`, `terminal` | `flat` |
| "our homepage needs a hero" | one strong idea, big canvas | `banner`, `compose`, or hand-built | `glow` |
| "the site feels boring" | motion + one accent, less chrome | anything, `flat` if busy, `glow` if flat | pick by their complaint |
| "a spinner / loading state" | a loop that never resolves | `loader` | `bare` or `flat` |
| "animate our logo" | the mark reveals itself | `logo`, or hand-built | `glow` |
| "status icons for X" | small set, one behaviour each | `icons` | `bare`, or `flat` |
| "a dashboard / KPIs" | numbers that count up | `cards`, `counter`, `gauge` | `flat` |
| "compare skills / capabilities" | axes and polygons | `radar`, `chart` | `flat` |
| "we hit 10k users" | one number, made to land | `counter` | `glow` |
| "an illustration for X" | a thing with character | hand-built `scene` | `glow` |
| "background for the hero section" | slow, low contrast, non-competing | `backdrop`, `art` | `bare` |
| "a headline that types itself" | kinetic type | `text` | `glow` or `bare` |
| "morph from icon to logo" | one shape becoming another | `morph` | `glow` |
| "for the docs, show the API call" | literal, typed, reversible | `terminal`, `sequence` | `flat` |
| "for slides" | a still frame | anything → PNG via `render_frames.py` | any |
| "make me something cool" | see the protocol above; small, confident, `glow` | ask one axis | `glow` |

**None of these are about repositories.** A landing page, a docs site and a README
want the same file format and often the same graphic — the difference is the
destination rules above, not a different skill.

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
- `references/surfaces.md` - picking the visual grammar; the sixth answer to the brief
- `assets/specs/` — 53 specs, all generated, all byte-reproducible