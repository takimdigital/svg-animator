# Animated "things" catalog (non-diagram types)

Ten generator types that are **not diagrams**: loaders, logos, text, gauges, charts, backgrounds, icons, scenes, counters and generative art. Same engine, same guarantees: computed layout/timing, static-first (frame 0 is the finished graphic), lint-clean, no JS/external assets, and each one works standalone **and** inside `compose` next to diagrams.

`python scripts/run_pipeline.py spec.json --out-dir ./run --name <name>` (or `gen_diagram.py`). Example specs: `assets/specs/<type>-*.json`. Common keys (`title`, `aria`, `dur`, `theme`, `colors`, `aurora`) are in `diagram-types.md` §2. Themes: `ember ocean forest mono paper violet sunset`.

## Contents
1. Which type for which request
2. loader · logo · text · gauge · radar
3. backdrop · icons · scene · counter · art
4. Clock behaviour (what follows `dur`, what loops on its own)
5. When none of these fits

---

## 1. Which type for which request

| The user asks for… | Use |
|---|---|
| a spinner / loading indicator / "loading…" animation | `loader` |
| a logo animation / brand intro / wordmark reveal | `logo` |
| animated heading, tagline, typing effect, glitch text | `text` |
| progress, KPI, dial, health meter, split (donut) | `gauge` |
| compare things across several dimensions (skills, versions, products) | `radar` |
| an animated background / hero backdrop / ambience | `backdrop` |
| small animated icons for a feature list | `icons` |
| a little illustration (rocket, coffee, sea, space) | `scene` |
| big rolling numbers (stars, users, uptime) | `counter` |
| abstract / decorative / generative art | `art` |
| a bar or line chart | `chart` (see `diagram-types.md`) |
| several of these together | `compose` |

## 2. loader · logo · text · gauge · radar

### loader
`variant` (one) or `variants:[…]` (default: all eight, as a sheet), `period` (s, default 1.2), `cols`, `cell`.
Variants: `ring dots bars orbit pulse dual wave progress`. Loops run on their own `period` (they are not tied to `dur`). Use a single `variant` for a README spinner (`cols:1`).

### logo
```json
{"type":"logo","mark":"hexagon","initials":"DA","wordmark":"design-atlas","tagline":"concept pool","dur":8}
```
`mark`: `hexagon diamond triangle pentagon circle shield square`. Sequence: outline draws on → fill + initials → wordmark slides in → tagline → one shine pass → lockup fades before the loop restarts. Base state = finished logo. Text is a system sans stack (convert to paths in a design tool if exact brand lettering matters). Knobs: `width height wordmark_size`.

### text
```json
{"type":"text","variant":"wave","text":"Ship faster","size":64,"subtitle":"…"}
```
`variant`: `wave` (letters bob), `reveal` (letters rise in, then reset), `pop` (scale pop sweep), `type` (typewriter with cursor, per-letter discrete reveal — works on any background), `shimmer` (gradient pass), `glitch` (RGB-split bursts). Letter variants use a monospace grid (0.6 em per char); `shimmer`/`glitch` use sans unless `font:"mono"`. Keep text ≤ ~24 characters.

### gauge
```json
{"type":"gauge","cols":3,"items":[
 {"kind":"gauge","label":"CPU","value":72},
 {"kind":"ring","label":"UPTIME","value":99,"unit":"%"},
 {"kind":"bar","label":"REQUESTS","value":1840,"max":2400,"unit":""},
 {"kind":"donut","label":"TRAFFIC","center":"3 regions","segments":[{"value":52},{"value":31},{"value":17}]}]}
```
`kind`: `gauge` (semicircle + needle), `ring`, `bar`, `donut`. Per item: `max` (100), `unit` (`%` when max is 100), `color`. Values count up (discrete steps) while the arc/needle sweeps, hold, then reset at the end of the loop. Base state = finished values.

### radar
`axes:[labels]` (3–10), `series:[{name,values:[…],max?,color?}]` (1–4), `radius`. Polygons grow from the centre (SMIL `points` animation), vertex dots pop, legend appears when there are several series.

## 3. backdrop · icons · scene · counter · art

### backdrop
`variant`: `waves` (layered, seamless drift) · `stars` (twinkle + 2 shooting stars) · `grid` (dot grid with an outward ripple) · `bubbles` (rise + sway) · `rain` · `mesh` (colour blobs). Optional `heading`, `subtitle`, `width` (1200), `height` (400), `count`, `layers`, `seed`. All ambient and slow; the still is already a finished backdrop. Use inside `compose` as the first part, or as a README header image.

### icons
`items:[{name,label}]` (default: all 12), `size` (56), `cols`, `cell`, `period` (2.4 s, each icon rests between actions).
Names: `check cross heart bell gear download star playpause sun lock wifi bolt`. Icons are drawn on a 24-unit grid and scaled.

### scene
`scene`: `rocket` (shake → lift-off → smoke → returns) · `coffee` (steam, warm glow) · `ocean` (waves, bobbing boat, sun) · `orbit` (sun, planets on ellipses, a moon). Optional `caption`, `width`, `height`, `seed`. Shapes use theme colours, so the same scene re-skins with `theme`.

### counter
`items:[{value,label,prefix,suffix}]`, `size`. Odometer: each digit column rolls up to its value (staggered), thousands separators are added automatically; hold, then reset. Base state = final number.

### art
`variant`: `mandala` (`petals`) · `lissajous` (`a`,`b`) · `spiral` (`turns`) · `orbits` · `flower` (`k`). `size` (520), `seed`. Decorative; combine with `text` or `logo` in a `compose` for covers.

## 4. Clock behaviour
- **Follow `dur`** (and a compose `window`): `logo`, `text` (reveal/pop/type/glitch), `gauge`, `radar`, `counter`, `scene` rocket's launch, `art` draw-on.
- **Loop on their own period** (ambient, independent of the master clock): `loader` (`period`), `icons` (`period`), `backdrop`, `art` rotations, `scene` ambient parts. Inside a compose they keep their own rhythm; the lint prints an INFO listing durations that are not whole divisors of the master clock — expected for these.
- Windows (`window:[a,b]`) only shift schedule animations; ambient motion keeps running.

## 5. When none of these fits
Build it by hand (Mode B): `drawing-fundamentals.md` for the artwork, `motion-vocabulary.md` / `patterns.md` for the motion, then run the pipeline on the `.svg`. To mix a hand-built piece with generator output, see `combinations.md` §4.
