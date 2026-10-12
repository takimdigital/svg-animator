# AGENT HANDOFF — publish this skill as `animated-svg-skill`

**Read this whole file before changing anything. Delete this file before the final commit.**

This repository is the `svg-animator` skill for AI agents: it builds animated SVG diagrams, charts, loaders, logos,
typing effects and GitHub README headers, and verifies them. It is being published as a **new** GitHub repository.
Make it publish-ready: no references to any other repository or project, complete GitHub metadata (name, description,
topics, social preview, funding), SEO-friendly README text, and the Buy me a coffee link kept.

---

## 0. Acceptance: the work is done when all of these hold

1. The removal check in section 6 prints **nothing**.
2. `python -m unittest discover -s tests` passes (114 tests today; the count may grow, but no test may fail).
3. `python scripts/doctor.py` ends with `ALL GATES PASS`.
4. `python scripts/readme_page.py assets/readme/project-readme.json . --check` prints `lint: all blocks clean`.
5. The README's first line is an H1 that names the skill, and the README text names all 38 generator types.
6. `.github/FUNDING.yml` and `docs/social-preview.png` exist; `HANDOVER.md` does not exist.
7. The Support section of the README is unchanged, and it still links to `https://www.buymeacoffee.com/takimdigital`.
8. `AGENT_HANDOFF.md` is deleted.

**Starting point (measured before your work):** 59 source lines in 22 files must change (Appendix A), and 28 generated
files change when you regenerate (Appendix B). Do not edit Appendix B files by hand.

## 1. Decisions already made (do not change them)

- **New repository name:** `animated-svg-skill`. Chosen for search: "animated SVG" is the phrase people search for, and "skill" matches how AI-agent skills are found.
- **Repository URL used everywhere:** `https://github.com/takimdigital/animated-svg-skill`. The owner is assumed to be `takimdigital`. If the owner differs, replace only the owner part of this URL, everywhere it appears.
- **The skill's internal name stays `svg-animator`** (the `name:` in `SKILL.md` and the folder name agents install). The README says that this repository is the `svg-animator` skill. Do not rename the skill.
- **Keep:** `LICENSE` (MIT), the Support section text verbatim, `.github/FUNDING.yml`, `docs/social-preview.png`, and the footer line `MIT © takimdigital`.
- **Delete:** `HANDOVER.md`. It is an internal document about the previous repository, and it contains a personal email address and a local path.

## 2. GitHub metadata (Settings, or the `gh` CLI)

Replace `OWNER` with the owner name.

- **Name:** `animated-svg-skill`
- **Description** (221 characters):
  > An AI agent skill for animated SVG: build animated diagrams, charts, loaders, logos, typing effects and README headers that are lint-verified and browser-checked. 38 generator types, a whole-README page kit, MIT licensed.
- **Website:** leave empty.
- **Topics** (20, lowercase, hyphens only):
  `svg, animated-svg, svg-animation, animation, smil, css-animation, claude-skill, ai-agents, llm, github-readme, readme-generator, diagrams, data-visualization, charts, generative-art, motion-design, svg-generator, developer-tools, python, documentation`
- **Social preview:** upload `docs/social-preview.png` (1280 × 640) under Settings → General → Social preview. GitHub cannot read it from the repository; it must be uploaded on the settings page.
- **Sponsor button:** appears automatically from `.github/FUNDING.yml`.
- **CLI equivalent:**
  ```
  gh repo edit OWNER/animated-svg-skill --description "An AI agent skill for animated SVG: build animated diagrams, charts, loaders, logos, typing effects and README headers that are lint-verified and browser-checked. 38 generator types, a whole-README page kit, MIT licensed."
  gh repo edit OWNER/animated-svg-skill --add-topic svg,animated-svg,svg-animation,animation,smil,css-animation,claude-skill,ai-agents,llm,github-readme,readme-generator,diagrams,data-visualization,charts,generative-art,motion-design,svg-generator,developer-tools,python,documentation
  ```
- **After the repository is public (optional):** create a release `v1.0.0` with the repository zip attached. Releases are indexed and help people find the project.

## 3. Remove every reference to other repositories and projects

Every item below comes from another project or repository. Replace each one with the neutral text in the right column.
Check the context: a name may sit inside a sentence, a command, a label, a stat or a comment.

| Find | Replace with | Typical places |
|---|---|---|
| `design-atlas`, `DESIGN-ATLAS` | `demo-kit`, `DEMO-KIT` | specs, the spine template, `references/animated-things.md` (logo example), `docs/gallery/README.md` |
| `ATLAS CORE` and `ATLAS` (as a label) | `CORE` | `flow-flat.json`, `flow-with-feedback.json`, `spine-template.json` |
| `Atlas` / `atlas` in commands (`atlas init`, `atlas build`, `atlas release`, `npx atlas build`) | `demo-kit init`, `demo-kit build`, `demo-kit release`, `npx demo-kit build` | `terminal-demo.json`, `compose-dashboard.json`, `compose-onboarding.json`, `spine-template.json` |
| `npm install design-atlas`, `npm i -g design-atlas` | `npm install demo-kit`, `npm i -g demo-kit` | `terminal-demo.json`, `compose-onboarding.json`, `spine-template.json` |
| `Deckhand` (a product label) | `Runner` | `flow-flat.json`, `flow-with-feedback.json`, `compose-readme-hero.json`, `references/diagrams.md`, `docs/thumbs` (regenerated) |
| `502 concepts`, `354 terms`, `354 craft terms`, `craft terms`, `in the pool`, `greppable` (statistics of the other project) | neutral figures, e.g. `24 modules`, `120 terms`, `ready` (choose one set and use it everywhere) | `cards-stats.json`, `counter-stats.json`, `banner-readme.json`, `compose-readme-hero.json`, `flow-with-feedback.json`, `terminal-demo.json`, `spine-template.json`, `references/readme-diagrams.md` |
| `concept pool`, `CONCEPT POOL` (tagline of the other project) | a neutral tagline, e.g. `a shared catalogue` | `logo-hexagon.json`, `compose-product-hero.json`, `compose-readme-hero.json`, `banner-readme.json`, `text-shimmer.json` |
| `12840`, `12,840 stars` (the other project's star count) | `1,200 stars` (or any neutral figure) | `counter-stats.json`, `spine-template.json` |
| `v1.4.0` (the other project's version) | `v1.0.0` | `readme-kit.md` (badges example), `compose-dashboard.json`, `spine-template.json` |
| `214 packages`, `tests passed (214)` (the other project's numbers) | `42 packages`, `tests passed (42)` | `terminal-demo.json`, `compose-dashboard.json` |
| `DA` (logo initials of the other project) | `DK` | `compose-product-hero.json`, `references/animated-things.md` |
| `your-name/design-atlas` (placeholder links) | `your-name/demo-kit` | `spine-template.json` |

Also replace these:
- `CONTRIBUTING.md`: the relative link `../../../../issues` becomes `https://github.com/takimdigital/animated-svg-skill/issues`.
- `docs/PROPOSAL-expression-layer.md`: delete the first line, which cites pull request `#4` of the old repository. Keep the rest of the document as design history.
- `scripts/check_workflow.py` line 6: the comment cites `PR #16`. Rewrite it as a neutral sentence, for example: "A past workflow step contained only `with:`, so the check rejects steps with neither `uses` nor `run`." Do not change the code.
- `scripts/build_gallery.py` line 296: remove the sentence that mentions `HANDOVER.md`. Then regenerate the gallery.
- `README.md` and `docs/gallery/README.md` are generated: change the sources, then regenerate them (section 5).

**Generated files change when their sources change.** Appendix B lists them. Regenerate them (section 5); never edit them by hand.

## 4. README: SEO and correctness

The README is generated from `assets/readme/project-readme.json`. Edit the spec and the generator, never `README.md` or `docs/readme/*`.

1. **Add an `intro` key to the page generator.** In `scripts/readme_page.py`, when the spec has an `intro` string, write it to `README.md` **before** the first `<div>`, so the H1 is the first thing in the file. Add a unit test in `tests/test_readme_page.py`: the generated README starts with the intro text, and a spec without `intro` produces the same output as before (compare with the committed output).
2. **Set `"name": "animated-svg-skill"`** in the spec. This changes the hero title and the page alt texts.
3. **Set `intro`** to this text (keep the wording; it is written for search):
   ```
   # Animated SVG skill for AI agents

   This repository is the **svg-animator** skill. It lets an AI agent build animated SVG diagrams, charts, loaders, logos, typing effects and GitHub README headers. Every graphic is computed from a small JSON spec, then linted and checked in a real browser at frame 0, so it is correct before anyone looks at it.

   38 generator types · whole-README page kit · lint-verified · MIT licensed
   ```
4. **Update the repository URLs** in the spec: the hero `href`, the footer `links`, and the Quick start `git clone` line (`https://github.com/takimdigital/animated-svg-skill.git`). In the Quick start, the install line becomes:
   `cp -r animated-svg-skill ~/.claude/skills/svg-animator` (the skill is installed under its own name).
5. **Remove** any remaining mention of the old repository from the spec.
6. **Keep the Support section verbatim.** Its link must still point to `https://www.buymeacoffee.com/takimdigital`.
7. **Keep the 38-type list** in the page and in the text. `tests/test_readme_page.py` fails if a registered type is not named in `README.md`.

## 5. Regeneration, in this order

Run these after you finish the source changes in sections 3 and 4.

```
# 1. every example whose spec you changed (repeat for each name listed in Appendix B)
python scripts/gen_diagram.py assets/specs/<name>.json assets/examples/<name>.svg
python scripts/static_twin.py assets/examples/<name>.svg assets/examples/<name>-static.svg

# 2. the thumbnails built from changed examples (the curated list is in scripts/build_thumbs.py)
python scripts/build_thumbs.py --only flow-with-feedback
python scripts/build_thumbs.py --only terminal-demo

# 3. the gallery, then the README and its page blocks
python scripts/build_gallery.py
python scripts/readme_page.py assets/readme/project-readme.json .
```

After step 3, `docs/readme/` must hold the 10 blocks per theme (20 files), and `python scripts/build_gallery.py --check` must pass.

## 6. Verification

Run the removal check **after** regeneration. It searches every tracked file except this handoff.

```
# the removal check: must print nothing
git grep -n -E "design-atlas|DESIGN-ATLAS|[Dd]eckhand|\bATLAS\b|\bAtlas\b|\batlas\b|502 concepts|354 terms|354 craft terms|craft terms|concept pool|CONCEPT POOL|12840|12,840|v1\.4\.0|214 packages|tests passed \(214\)|HANDOVER|PROPOSAL-expression|PR #|pull/|takimdigital/svg-animator|svg-animator\.git|D:/|takimdigital@gmail" -- ':!AGENT_HANDOFF.md'

# the coffee link must still exist (README, funding file and spec)
git grep -n "buymeacoffee.com/takimdigital"

python -m unittest discover -s tests
python scripts/doctor.py
python scripts/readme_page.py assets/readme/project-readme.json . --check
test -f .github/FUNDING.yml && test -f docs/social-preview.png && ! test -f HANDOVER.md && echo files-ok
```

Expected: the removal check prints nothing. The coffee grep prints lines in the README, the spec and `FUNDING.yml`.
The tests pass. The doctor prints `ALL GATES PASS`. The README check prints `lint: all blocks clean`. The last line prints `files-ok`.

If the removal check finds a word that is not a reference to another project (for example the English word "atlas" in a
sentence about maps), keep it and say so in your report. Do not weaken the check to make it pass.

## 7. Rules that apply to every change

- **Never hand-edit generated files:** `README.md`, `docs/readme/*`, `docs/gallery/README.md`, `assets/examples/*.svg`, `docs/thumbs/*.svg`. Change the source, then regenerate.
- **Never weaken or delete a test or gate** to make it pass. If one fails, find out why, fix the source (spec or code), and regenerate.
- **Keep every example at 0 errors and 0 warnings** (`python scripts/lint_svg_anim.py assets/examples/*.svg --quiet`). Static twins are exempt from the warnings check.
- **Commit in logical commits**, one concern per commit, with clear messages. Use the repository owner's identity.
- **Delete `AGENT_HANDOFF.md`** and check that `git status` is clean before you report.

## 8. Report back

Tell the owner, in a short list: the final repository name and URL, what was removed and replaced (file count), what was
added (intro key, funding file, social preview), the verification results from section 6, and anything you could not
decide or verify (for example, how the page looks on github.com, which needs a first push).

---

## Appendix A — source lines that must change (59 lines, 22 files)

Each line below comes from the removal check. Change it, or delete the file (`HANDOVER.md`).

```
HANDOVER.md:3  **Repo:** `https://github.com/takimdigital/svg-animator` (public, MIT)
HANDOVER.md:5  **Owner:** Takim — `takimdigital@gmail.com`, GitHub `takimdigital`
HANDOVER.md:37  proposal — kept on `main` as `docs/PROPOSAL-expression-layer.md` with a
HANDOVER.md:43  cd "D:/TakimDigital/svg-animator"          # adjust to your checkout path
HANDOVER.md:45  git status --porcelain                     # expect empty (or only HANDOVER.md)
HANDOVER.md:120  ### B · Document the visual grammar — accepted from PR #4
HANDOVER.md:122  PR #4 identified that the generator's node shape, emphasis and traveller are
HANDOVER.md:141  Then add a one-line cross-reference from `docs/PROPOSAL-expression-layer.md`'s
HANDOVER.md:394  - Anything from the declined parts of PR #4: `shape` variants, `traveller`
HANDOVER.md:402  `docs/PROPOSAL-expression-layer.md` (with its status banner) and in the PR
assets/readme/project-readme.json:20  "href": "https://github.com/takimdigital/svg-animator",
assets/readme/project-readme.json:294  "href": "https://github.com/takimdigital/svg-animator"
assets/readme/project-readme.json:313  "```bash\ngit clone https://github.com/takimdigital/svg-animator.git\ncp -r svg-animator ~/.claude/skills/        # or symlink it so updates land ever
assets/readme/spine-template.json:3  "name": "design-atlas",
assets/readme/spine-template.json:5  "description": "A concept pool and a craft vocabulary that an LLM can grep, plus a deterministic workflow that ends in a standalone Next.js site.",
assets/readme/spine-template.json:6  "badges": ["MIT", "v1.4.0", "502 concepts", "zero deps"],
assets/readme/spine-template.json:11  "href": "https://github.com/your-name/design-atlas",
assets/readme/spine-template.json:17  {"id": "why", "nav": "Why", "title": "Why design-atlas",
assets/readme/spine-template.json:21  {"value": "354", "label": "craft terms", "sub": "greppable"},
assets/readme/spine-template.json:26  "copy": ["npm i -g design-atlas", "atlas init my-site", "atlas build"],
assets/readme/spine-template.json:28  {"kind": "cmd", "text": "npm i -g design-atlas"}, {"kind": "out", "text": "added 1 package in 2.1s"},
assets/readme/spine-template.json:29  {"kind": "cmd", "text": "atlas init my-site && atlas build"}, {"kind": "ok", "text": "✔ site ready in ./out (3.2s)"}]}},
assets/readme/spine-template.json:34  [{"id": "c", "label": "ATLAS", "sub": "concepts", "key": true}],
assets/readme/spine-template.json:46  "part": {"type": "counter", "items": [{"value": 12840, "label": "stars", "suffix": "+"}, {"value": 502, "label": "concepts"}, {"value": 99, "label": "
assets/readme/spine-template.json:56  "links": [{"label": "Docs", "href": "https://github.com/your-name/design-atlas#readme"}, {"label": "Issues", "href": "https://github.com/your-name/des
assets/specs/banner-readme.json:1  {"type":"banner","heading":"design-atlas","subtitle":"concept pool → design DNA → standalone sites","dur":12,"theme":"ember","title":"open source · MI
assets/specs/banner-readme.json:2  "aria":"design-atlas README banner with the tagline and three tags.",
assets/specs/banner-readme.json:3  "tags":["502 concepts","354 craft terms","zero-shot"]}
assets/specs/cards-stats.json:2  "aria":"Four stat tiles: 502 concepts, 354 craft terms, 26 skills and 0 dependencies.",
assets/specs/cards-stats.json:3  "items":[{"value":"502","label":"concepts","sub":"in the pool","key":true},{"value":"354","label":"craft terms","sub":"greppable"},
assets/specs/compose-dashboard.json:6  {"type":"terminal","title":"ship it","width":620,"window_title":"zsh","lines":[{"kind":"cmd","text":"atlas release"},{"kind":"out","text":"tests passe
assets/specs/compose-onboarding.json:5  "lines":[{"kind":"cmd","text":"npm i -g design-atlas"},{"kind":"out","text":"added 1 package"},{"kind":"cmd","text":"atlas init && atlas build"},{"kin
assets/specs/compose-product-hero.json:4  {"type":"logo","mark":"hexagon","initials":"DA","wordmark":"design-atlas","tagline":"concept pool → sites","width":900,"height":240,"window":[0,0.55]}
assets/specs/compose-product-hero.json:5  {"type":"counter","items":[{"value":12840,"label":"stars","suffix":"+"},{"value":502,"label":"concepts"},{"value":99,"label":"uptime","suffix":"%"}],"
assets/specs/compose-readme-hero.json:4  {"type":"banner","heading":"design-atlas","subtitle":"concept pool → design DNA → standalone sites","tags":["502 concepts","354 craft terms","zero-sho
assets/specs/compose-readme-hero.json:5  {"type":"cards","cols":4,"items":[{"value":"502","label":"concepts","sub":"in the pool","key":true},{"value":"354","label":"craft terms","sub":"greppa
assets/specs/compose-readme-hero.json:7  "columns":[[{"id":"u","label":"User","sub":"intent"}],[{"id":"c","label":"CORE","sub":"pool","key":true}],[{"id":"w","label":"Workflow","sub":"config 
assets/specs/counter-stats.json:6  "aria": "Odometer counters rolling to 12,840 stars, 502 concepts and 99 percent.",
assets/specs/counter-stats.json:9  "value": 12840,
assets/specs/flow-flat.json:19  "label": "ATLAS CORE",
assets/specs/flow-flat.json:20  "sub": "502 concepts \u00b7 354 terms",
assets/specs/flow-flat.json:47  "label": "Deckhand",
assets/specs/flow-with-feedback.json:3  "title": "design-atlas · system architecture",
assets/specs/flow-with-feedback.json:4  "aria": "design-atlas system architecture: user intent flows into the atlas core, through a deterministic workflow into outputs, then to any LLM or De
assets/specs/flow-with-feedback.json:10  [{"id": "core", "label": "ATLAS CORE", "sub": "502 concepts · 354 terms", "key": true}],
assets/specs/flow-with-feedback.json:14  {"id": "dh", "label": "Deckhand", "sub": "optional production"}]
assets/specs/logo-hexagon.json:6  "wordmark": "design-atlas",
assets/specs/logo-hexagon.json:7  "tagline": "concept pool",
assets/specs/logo-hexagon.json:9  "aria": "Logo reveal of design-atlas: a hexagon mark draws on, the wordmark slides in and a shine passes."
assets/specs/terminal-demo.json:3  "lines":[{"kind":"cmd","text":"npm install design-atlas"},{"kind":"out","text":"added 214 packages in 3.1s"},
assets/specs/terminal-demo.json:4  {"kind":"cmd","text":"npx atlas build --theme ember"},{"kind":"out","text":"compiling 502 concepts..."},{"kind":"ok","text":"✔ site ready in ./out (3.
assets/specs/text-shimmer.json:4  "text": "design-atlas",
docs/PROPOSAL-expression-layer.md:3  > Kept on `main` as the decision record for [#4](https://github.com/takimdigital/svg-animator/pull/4).
references/animated-things.md:41  {"type":"logo","mark":"hexagon","initials":"DA","wordmark":"design-atlas","tagline":"concept pool","dur":8}
references/diagrams.md:71  1. **Invented "gap rails" instead of fixing the layout.** Two tiny arrows at x=1075 sat between the Outputs card and the LLM/Deckhand cards but touche
references/readme-diagrams.md:65  [{"id":"b","label":"CORE","sub":"502 concepts","key":true}],
references/readme-kit.md:48  { "style":"spine", "name":"…", "tagline":"…", "description":"…", "badges":["MIT","v1.4.0"],
scripts/build_gallery.py:296  L.append("not six looks. It is the open visual-range item in `HANDOVER.md`.")
scripts/check_workflow.py:6  PR #16 shipped a workflow step containing only `with:` and no `uses` or `run`.
```

## Appendix B — generated files that change when you regenerate (28 files)

Do not edit these by hand. Regenerate them with section 5 after you change their sources.

```
README.md
assets/examples/banner-readme-static.svg
assets/examples/banner-readme.svg
assets/examples/cards-stats-static.svg
assets/examples/cards-stats.svg
assets/examples/compose-dashboard-static.svg
assets/examples/compose-dashboard.svg
assets/examples/compose-onboarding-static.svg
assets/examples/compose-onboarding.svg
assets/examples/compose-product-hero-static.svg
assets/examples/compose-product-hero.svg
assets/examples/compose-readme-hero-static.svg
assets/examples/compose-readme-hero.svg
assets/examples/counter-stats-static.svg
assets/examples/counter-stats.svg
assets/examples/flow-flat-static.svg
assets/examples/flow-flat.svg
assets/examples/flow-with-feedback-static.svg
assets/examples/flow-with-feedback.svg
assets/examples/logo-hexagon-static.svg
assets/examples/logo-hexagon.svg
assets/examples/terminal-demo-static.svg
assets/examples/terminal-demo.svg
assets/examples/text-shimmer-static.svg
assets/examples/text-shimmer.svg
docs/gallery/README.md
docs/thumbs/flow-with-feedback.svg
docs/thumbs/terminal-demo.svg
```
