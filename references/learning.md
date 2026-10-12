# Learning: how an AI adds a new capability to this skill

This is the procedure for turning a request the skill cannot yet serve into a capability it can. Follow it in
order. Each step ends in something checkable, so you cannot quietly skip one. Read `references/CAPABILITIES.md`
first, so you do not build what already exists.

## Contents
1. Decide the route
2. Break the request down
3. Build a new type (when the request will recur)
4. Prove it (tests, examples, checks)
5. Record it (CAPABILITIES, SKILL routing, the learned log)
6. Rules that do not bend

---

## 1. Decide the route

| The request is… | Do |
|---|---|
| already a type, or a variant of one | use the spec. Stop here. |
| a one-off piece (a mascot, a bespoke logo) | route B, hand-build. Optionally record it (step 5). |
| a repeatable effect that a spec could describe | **new type** (steps 2–5). |
| a fix to an existing SVG | route C. |

Ask: *would a second request for something like this come soon?* If yes, make it a type. A type is a
contract: data in, a finished graphic out, checkable forever.

## 2. Break the request down

Write these down before writing any code. They become the spec fields and the tests.

- **Nouns** → the shapes. What is on the screen?
- **Verbs** → the motion. What does each shape do, and when?
- **Clock** → the loop length (`dur`) and the fraction of the loop each event occupies.
- **Rest pose** → the finished graphic. This is the still frame and the static fallback.
- **Invariants** → what must always be true. Examples: "the swapped word has the same length", "the dot stays on the rail", "no label is wider than its card". Each invariant is a check you can write.
- **Inputs that must be refused** → the cases where the type cannot draw the request well. Refuse them with a message that says what to change.

## 3. Build a new type

1. **Builder.** Add `scripts/things_<name>.py` with `build_<name>(spec, th, idp="") -> part(...)`. Use the helpers in `diagram_common.py` (`F`, `T`, `esc`, `part`, `FONT`). Keep every keyTime computed, never typed by feel. Put the storyboard in the `sb` list.
2. **Static-first.** Every element's *base* attributes are its finished state. Animations only change them. A renderer that ignores SMIL then shows the finished graphic, not a mess. (`things_c.py` shows this for swapped letters: the removed letter's base opacity is 0, the new one's is 1.)
3. **Contract.** Write the builder's docstring first: Fields, Refuses, Base state, Breaks if changed, Example. `tests/test_contracts.py` fails if a section is missing, if the code reads a key the Fields do not list, or if the example does not exist.
3. **Validate.** Reject bad specs with `sys.exit("<type>: <what is wrong and how to fix it>")`.
4. **Register.** Add the import and `b.update(...)` in `gen_diagram.registry()`.
5. **Example.** Add `assets/specs/<name>-<variant>.json`, then generate, in this order:
   ```
   python scripts/gen_diagram.py assets/specs/<spec>.json assets/examples/<spec>.svg
   python scripts/static_twin.py assets/examples/<spec>.svg assets/examples/<spec>-static.svg
   python scripts/build_gallery.py
   ```
   Thumbnails are a curated list in `build_thumbs.py`; add one only if the README should show it.

## 4. Prove it

Run each, and read the output:

```
python scripts/lint_svg_anim.py assets/examples/<spec>.svg          # must be 0 errors, 0 warnings
python scripts/verify.py assets/examples/<spec>.svg                  # browser frame-0 check (needs Playwright)
python scripts/render_frames.py assets/examples/<spec>.svg --times 0.1,0.4,0.6,0.9
python -m unittest discover -s tests                                 # must pass
```

Then **look at the frames**. Lint cannot tell you whether it looks right. Write a test for each invariant from step 2,
and for each refusal from step 2, make sure it can fail: break the code on purpose, confirm the test fails, then
restore. A test that cannot fail proves nothing (`tests/test_type_coverage.py` shows both controls).

## 5. Record it

- **`references/CAPABILITIES.md`**: add the type to its table, with its example spec.
- **`SKILL.md`**: add a routing row if the type answers a new kind of request.
- **`references/learned/<name>.md`**: the learned log. One short file per capability: the request in the user's own words, the decisions and why, what was verified, and what was not. This is how the next AI learns from this one. Start from `references/learned/TEMPLATE.md`.

## 6. Rules that do not bend

- Frame 0 is complete. The static fallback is the finished graphic.
- No JavaScript, no external fonts or images, no scripts in the output.
- Lint is 0 errors and 0 warnings on every example.
- Every registered type has an example. The coverage test enforces it.
- Refuse what you cannot do well. A clear refusal beats a broken graphic.
- Report what you did not verify. "Looks right" is a claim that needs a frame you looked at.
