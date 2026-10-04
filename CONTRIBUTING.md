# Contributing to svg-animator

This file is written for **humans and AI agents alike**. An agent reading this
should be able to open a correct pull request without a single follow-up question.

The short version: this skill exists because AI-generated SVG animation is
confidently wrong. Every rule below protects the one property that makes it
worth having — *the output is verified, not assumed*. A contribution that skips
verification is worse than no contribution, because it erodes the guarantee.

---

## The bar

A PR is ready when:

```bash
python scripts/lint_svg_anim.py <every .svg you touched or added>   # 0 errors, 0 warnings
python scripts/run_pipeline.py <your spec> --out-dir ./run           # RESULT: PASS
```

…and you have **looked at the rendered frames** and can describe what you saw.

That last one is not optional and not a formality. `PASS` means the file is
structurally sound. It does not mean it looks good. Two files can both be
lint-clean and one can still be ugly, misaligned, or have its dot travelling
through a card at a moment nobody intended. You are the only one who can catch
that, and the skill's own `SKILL.md` calls it **principle 6: verify by looking**.

---

## What to contribute

Ordered by value to the project:

| Kind | Where | What good looks like |
|---|---|---|
| **Bug report** | [Issues](../../../../issues) | The SVG, what you expected, what you got, and the frame timestamp |
| **New linter check** | `scripts/lint_svg_anim.py` | A class of bug you've seen, a check that catches it, a false-positive rate you're honest about |
| **New generator type** | `scripts/things_*.py` + `gen_diagram.py` | See [Adding a generator type](#adding-a-generator-type) |
| **New spec / example** | `assets/specs/`, `assets/examples/` | A configuration that shows a capability the existing specs don't |
| **Reference improvement** | `references/*.md` | Clearer technique, a missing debugging entry, a better worked example |
| **Docs / README** | `README.md`, `docs/gallery/README.md` | Something that removes a question a first-time user would actually ask |
| **Harness support** | skill layout, `SKILL.md` routing | Make it work in an agent environment you know about |

**A bug report with a real broken SVG is worth more than most code contributions.**
It gives me a reproduction. Do not feel you need to fix it yourself.

---

## Hard rules

These are not style preferences. Each one exists because breaking it produced a
specific bug.

### 1. Frame 0 must be complete

The base state of the file is the **finished** graphic. Everything that moves
must either already be drawn, or start at `opacity="0"` and fade in.

```xml
<!-- wrong: a viewer without SMIL sees nothing -->
<circle r="6" opacity="0"><animate attributeName="opacity" values="0;1" dur="2s"/></circle>

<!-- right: the base state is the result; motion is an overlay -->
<circle r="6"/>                                     <!-- always visible -->
<circle r="13" opacity="0">                         <!-- the ripple, hidden -->
  <animate attributeName="opacity" values="0;.8;0" keyTimes="0;.3;1" dur="2s" repeatCount="indefinite"/>
</circle>
```

If the animation never runs — a PDF export, a mobile preview, a client without
SMIL — the viewer must still see the whole picture.

### 2. Compute geometry and timing; never eyeball it

Don't type `keyTimes="0.46"` because it looked about right. Derive it from the
spec, or compute it in the emitter and print the value you used. Same for rail
endpoints: they come from the card rectangles, not from a guess about where the
card is.

### 3. One master clock

The `dur` passed in by the caller is the loop. Every schedule animation is a
fraction of it. Ambient loops (spinners, particles, rotations) should be a whole
divisor — `dur/2`, `dur/4`. Never invent a new duration inside a part.

```python
# wrong
dur = 3.7

# right
dur = master_dur / 2
begin = -i * (master_dur / count)      # negative = pre-rolled, so frame 0 is alive
```

Use a **negative `begin`** to stagger a loop. It means "already partway through
when the file loads", which is the only way to get a stagger with no hidden
start state.

### 4. Motion follows drawn lines

A dot travels on a rail that exists in the file. The rail's endpoints are the
edges of the cards it connects. Nothing crosses a card or its text unless
crossing is the entire intended effect. If two cards leave no gutter, **move the
cards** — never invent a floating stub connector.

### 5. Loop seamlessly

First value equals last value. The last ~10% of the clock is at rest so the
restart isn't visible. Anything that teleports (a traveller returning to its
start) must fade out *before* the jump and fade back in after it.

### 6. Self-contained

No JavaScript. No external assets, no web fonts, no `xlink:href` unless you
declare `xmlns:xlink`. Use system font stacks. One file, under 100 KB.

### 7. Accessibility is not optional

```xml
<svg role="img" aria-labelledby="title-id desc-id" viewBox="…">
  <title id="title-id">…</title>
  <desc id="desc-id">…</desc>
```

If you use CSS animation for a loop, include the reduced-motion guard:

```css
@media (prefers-reduced-motion: reduce) { .spinning { animation: none; } }
```

---

## Adding a generator type

This is the most common substantial contribution. Six steps, in order.

**1 · Pick the file.** `scripts/things_a.py` for non-diagram types, `things_b.py`
for the rest, `diagram_extra.py` for diagram types, `diagram_common.py` for shared
helpers. Don't add a new module unless there's a real reason — the dispatch
imports these four.

**2 · Write the emitter.**

Every builder takes `(spec, th, pfx)` and returns the result of the shared
`part()` helper — a dict the compose engine knows how to place. Copy the shape of
an existing one:

```python
from diagram_common import part, esc, FONT

def build_mytype(spec, th, pfx=""):
    dur = float(spec.get("dur", 10))          # read it; never hardcode
    color = th["accent"]                      # every colour from the theme
    items = spec.get("items", [])

    body = ['<g id="%smytype">' % pfx]
    # ... compute layout from the item rectangles, then derive every keyTime ...
    body.append("</g>\n")

    return part("".join(body), W, H, sb, False, "My type: " + ", ".join(names))
```

`part(body, W, H, sb, arrows=False, desc="")` — `body` is the SVG fragment string,
`W`/`H` the fragment's size, `sb` the list of per-frame state strings the renderer
reports, `desc` a human summary. Don't return a raw tuple; `build_compose` and
the registry both expect the dict from `part()`.

Use `pfx` on every `id` you emit. In a `compose`, the same type can appear several
times, and unprefixed ids collide.

**3 · Build the base state first.** Emit the finished graphic with no animation
at all, run the linter, look at a frame. Then add motion as overlays. Building
both at once is how things get subtly wrong.

**4 · Register it.**

Builders live in dicts that `gen_diagram.py` already merges:

```python
# scripts/things_a.py
THINGS_A = {"loader": build_loader, "logo": build_logo, …}
# scripts/things_b.py
THINGS_B = {"backdrop": build_backdrop, "icons": build_icons, …}
# scripts/diagram_extra.py
EXTRA_BUILDERS = { … }
```

Add your `build_mytype` to the dict matching its category — no change to
`registry()` needed. Then document its spec fields in
`references/animated-things.md` (things) or `diagram-types.md` (diagrams).

Confirm it registered:

```bash
python -c "import sys; sys.path.insert(0,'scripts'); import gen_diagram as g; print(sorted(g.registry()))"
```

**5 · Add a spec and generate.**

```bash
cp assets/specs/loader-sheet.json assets/specs/mytype-demo.json
$EDITOR assets/specs/mytype-demo.json
python scripts/run_pipeline.py assets/specs/mytype-demo.json --out-dir ./run --name mytype
```

**6 · Look at the frames, then commit the example.**

```bash
cp run/mytype.svg assets/examples/mytype-demo.svg
```

Read the frames in `run/frames/`. Check frame 0 (complete?), an arrival moment
(is the glow on the intended element?), and ~95% (clean seam?). **Say in your PR
description what you saw.**

---

## Pull request shape

Keep it small and single-purpose. One concern per PR.

**Title:**

```
type: short imperative summary
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `perf`, `chore`.
`refactor` must not change output — if a generated SVG differs byte-for-byte,
it's not a refactor.

**Description:**

```markdown
## What
One or two sentences. What changed and why.

## Why
The bug, gap, or request this addresses. Link the issue: Fixes #12

## How it was verified
The exact commands you ran, and their real output:

    $ python scripts/lint_svg_anim.py assets/examples/mytype-demo.svg
    assets/examples/mytype-demo.svg: 0 error(s), 0 warning(s)

    $ python scripts/run_pipeline.py assets/specs/mytype-demo.json --out-dir ./run
    RESULT: PASS (0 errors, 0 warnings)

## What I saw in the frames
Describe what you actually looked at. Not "looks good" — say which frame, and
what you checked:

- t=0.0 — full graphic visible, no missing elements
- t=4.2 — dot on the rail between node 2 and 3, node 2 glowing, nothing crossing
- t=13.3 — clean rest state, no frozen dot, no half-faded card

## Not verified
Anything you couldn't check, and why. Honesty here is worth more than a clean
looking checklist.
```

If you couldn't run the pipeline (no Playwright, no Chromium), say so explicitly
and paste the lint output. A PR that admits what it didn't check gets merged
faster than one that implies everything was verified.

**Before you push:**

```bash
python -m py_compile scripts/*.py
python scripts/lint_svg_anim.py $(git diff --name-only --cached '*.svg')
git diff --stat
```

No trailing whitespace, no tabs in Python, no commented-out code left behind, no
debug `print()` statements in library code.

---

## Reporting a bug

The most useful bug report in this repo has four parts:

1. **The SVG** — paste it, or link a gist/fork. Don't describe it, paste it.
2. **What you expected** — the frame timestamp and what should be happening.
3. **What you got** — same timestamp, what actually happens.
4. **The lint output** — `python scripts/lint_svg_anim.py your.svg`

If the linter passes but the animation is still wrong, that's the **most
interesting kind of report you can file** — it means the linter has a blind spot,
and fixing it improves the skill for everyone. Say clearly that the linter passed.

Check `references/debugging.md` first; the symptom may already be documented.

---

## Code of conduct

Be decent. Assume good faith. Critique the code, never the person. A beginner
whose first PR has a rough edge is worth more than an expert who never
contributes because the bar felt high.

---

## License

By contributing you agree your work is released under the [MIT License](LICENSE).
