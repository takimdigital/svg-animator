# Motion DNA: investigate motion before building an original variation

Motion DNA is an **optional Route E** for the existing `svg-animator` agent skill. Use it if the user supplies an existing animated **SVG file** and wants to understand, diagnose or reinterpret its motion. This route does **not** replace the existing build/lint/verify/render pipeline; its reports are evidence, not a PASS certificate.

## Agent investigation protocol

1. **Scope.** Confirm that the input is a locally supplied/self-contained SVG and that inspection is authorized. Never run untrusted SVG code or fetch external assets. Video, websites, GIFs, Lottie and screen captures are NOT supported in v0.1.
2. **Inspect.** `python scripts/inspect_motion.py reference.svg --out run/motion-dna.json`. Read `animations`, `choreography`, `issues`, `unknowns` and evidence hash; don't reinterpret an unknown as a fact.
3. **Observe.** `python scripts/capture_motion.py reference.svg --out-dir run/reference --samples 13`. Inspect `trace.json` and frame PNGs. Browser observations resolve sampled computed opacity, position and size; they do not prove behavior between samples.
4. **Hypothesize.** Identify a specific motion property and a testable claim, e.g. “the 3 pulses are staggered by 0.15s, with a 1.2s cycle.” Retain original source/evidence hash.
5. **Create.** If the input fits the narrow supported recipes, `python scripts/reconstruct_motion.py run/motion-dna.json --shape diamond --out run/variation.svg`. Otherwise route to generator A or hand-build B, reusing the measured motion facts and describing what cannot be transferred automatically.
6. **Validate.** Run the existing `scripts/run_pipeline.py` (or lint, `verify.py`, `render_frames.py`) on the variation. Inspect actual screenshots manually; do not declare aesthetic quality based on comparison scores.
7. **Compare.** For the same geometry and element IDs use `compare_motion.py ... --mode state`; for opacity-only choreography applied to different artwork use `--mode opacity --target-map reference-id:new-id,...`. For differing geometry, state comparisons are inappropriate. Always use aligned timestamps.
8. **Report.** Distinguish directly parsed source facts, actual browser observations, inferred choreography and unresolved unknowns. Include the verification surface and limitations.

## Quick run

```bash
python scripts/investigate_motion.py reference.svg --out-dir run/reference-analysis --samples 13
python scripts/reconstruct_motion.py run/reference-analysis/motion-dna.json --shape star --out run/star-pulse.svg
python scripts/investigate_motion.py reference.svg --candidate run/star-pulse.svg --out-dir run/comparison --samples 13 --mode opacity --target-map pulse-1:motion-1,pulse-2:motion-2,pulse-3:motion-3
```

The target map above is specific to the bundled demo fixture and will differ for other inputs.

## Capabilities (v0.1)

| Input | Static extraction | Browser observation | Automatic original variation |
|---|---|---|---|
| Basic SMIL `<animate>` | Targets, values, keyTimes, begin/duration/repeat | Opacity and computed geometry snapshots | 2–8 indefinite opacity pulses with shared duration |
| Basic SMIL `<animateTransform>` | Transform type, timing | Computed geometry | One indefinite rotation; rotation angle is not fidelity-verified |
| SMIL `<animateMotion>` | Literal motion path/timing | Computed geometry | Not yet |
| SMIL `<animate attributeName="d">` | Command signatures / mismatch candidates | Bounds snapshots | Not yet |
| Simple CSS `@keyframes` | Literal frames; `#id`, `.class`, tag selectors | Computed geometry / opacity | Not yet |
| Advanced selectors, event/sync begins, scripts, external URLs | Record unknown or refuse | Refuse active content | Not supported |

### Evidence integrity

- Every static JSON report retains SHA-256 of the inspected bytes and identifies the operation as *source inspection*.
- Browser traces contain exact sampled timestamps, viewport, source hash, computed per-element properties and screenshot paths. These are *browser observations*, not source-of-truth intent.
- In comparisons, missing aligned timestamps or no matching targets is **INCONCLUSIVE**, never PASS. Missing individual elements are FAIL unless every element is missing, which is INCONCLUSIVE.
- Every comparison result retains deviations, coverage, missing reference/candidate timestamps and explicit limitations.
- `state` comparison checks relative SVG transform matrix rotation/scale/skew coefficients when present, including rotations of elements whose bounding box is unchanged.
- The old `ignore_missing` programmatic option cannot make missing evidence pass; use an explicit target selection and justify the exclusions.
- A similarity PASS is prohibited on missing targets, zero observed comparisons, or missing aligned timestamps. It validates only the **declared sampled properties**. It does not prove aesthetic equivalence, actual runtime performance, full path topology, colors or behavior at unsampled instants.

### Known limits

- Simple CSS parser: no selector engine for descendant/combinator selectors, nested media queries, CSS variables, compound transforms or interpolated cubic-bezier analysis. For such inputs browser inspection can still produce sampled evidence; the source report records unknowns.
- SMIL begins such as `foo.end+0.3s` aren't converted into numeric offsets. Complex multi-clock loop duration is left unknown; the longest single duration is reported separately.
- `--mode opacity` measures opacity choreography, *not position*, morph similarity or rotation. For those use `state` with identical geometry, or add a purpose-built verified metric.
- The browser is a restricted local testing environment, not a hardened sandbox for adversarial SVG. Treat unfamiliar inputs cautiously; it refuses scripts, event handlers, external URLs and DTD/entity declarations, and blocks requests during the page run.
- Animations inside embedded `<img>` and PDF environments may have different support. Keep the skill's original compatibility guidance.

## Extension design / principles adopted from REA

- **Evidence before synthesis:** tool output has source identity and coverage; avoid an unsupported causal story.
- **Unknowns are real:** preserve limits and questions instead of concealing them.
- **Target-specific observations:** use aligned element-by-element measurements, not global pixel difference that confounds ambient motion.
- **Bounded, repeatable investigations:** explicit local target, fixed sample times, no external navigation, verifiable exit criteria.
- **Small tool interfaces:** inspectors do measurements; the LLM is the investigator that decides which questions matter.

The extension is not itself a copy of REA, and does not require REA as a dependency.
