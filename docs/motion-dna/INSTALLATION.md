# Motion DNA integration

The Motion DNA implementation is available directly in `scripts/` and `references/motion-dna.md` on this branch. No archive installer is needed after merging.

Run `python scripts/inspect_motion.py tests/fixtures/motion-dna/staggered-pulse.svg --out /tmp/motion.json` to inspect the fixture, then `python scripts/reconstruct_motion.py /tmp/motion.json --shape diamond --out /tmp/diamond.svg` to build a variation.

Run `python -m unittest discover -s tests -v`, `python scripts/lint_svg_anim.py /tmp/diamond.svg`, and the Chromium GitHub Actions workflow to verify the result.

The original skill's generation routes remain unchanged.
