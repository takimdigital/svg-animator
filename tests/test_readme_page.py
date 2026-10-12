#!/usr/bin/env python3
"""Self-tests for the README page kit (scripts/readme_page.py + readme_blueprint.py).

Why these exist
---------------
The page kit assembles a whole README from generator output. Nothing in CI proves that
assembly works: the examples gates cover files under assets/examples, and a README page
is deliberately NOT stored there (a generated copy would drift, and the gallery gate
refuses any .svg there without a spec). So the kit is tested here instead, by
regenerating from its committed templates and checking the result.

What is proven, and how each test can fail:
  * both templates generate, and every block lints with 0 errors and 0 warnings
    (a block with a label overflowing its card would fail this)
  * generation is byte-reproducible (two runs, identical bytes)
  * an unknown style is refused (a positive control for the dispatch)
  * the lint really reports the overflow class a page can produce (a positive
    control: the test would fail if the lint went blind to it)

Run:
    python -m unittest discover -s tests -v

stdlib only. The lint runs as a subprocess, exactly as CI and contributors run it.
"""
import filecmp
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCRIPTS = os.path.join(ROOT, "scripts")
sys.path.insert(0, SCRIPTS)

import readme_page  # noqa: E402
from gen_diagram import registry  # noqa: E402

TEMPLATES = {
    "spine": os.path.join(ROOT, "assets", "readme", "spine-template.json"),
    "blueprint": os.path.join(ROOT, "assets", "readme", "project-readme.json"),
}
LINT = os.path.join(SCRIPTS, "lint_svg_anim.py")
COUNTS = re.compile(r"(\d+) error\(s\), (\d+) warning\(s\)")


def lint_counts(path):
    """Return (errors, warnings) as reported by lint_svg_anim.py for one file."""
    out = subprocess.run([sys.executable, LINT, path, "--quiet"], capture_output=True, text=True).stdout
    m = COUNTS.search(out)
    if not m:
        raise AssertionError(f"lint printed no summary for {path}:\n{out}")
    return int(m.group(1)), int(m.group(2))


def load(style):
    with open(TEMPLATES[style], encoding="utf-8") as fh:
        return json.load(fh)


def expected_blocks(spec):
    """hero + optional nav + one per section + footer, for each of the two modes."""
    return 2 * (1 + (1 if spec.get("nav", True) else 0) + len(spec["sections"]) + 1)


def unnamed_types(text):
    """Registered types that do not appear as a whole word in the text."""
    return sorted(n for n in registry() if not re.search(r"\b" + re.escape(n) + r"\b", text))


class PageKitTests(unittest.TestCase):

    def generate(self, style, outdir):
        spec = load(style)
        readme_page.write_all(spec, outdir, registry(), False, False)
        return os.path.join(outdir, "docs", "readme")

    def test_templates_generate_and_every_block_lints_clean(self):
        for style in TEMPLATES:
            with self.subTest(style=style), tempfile.TemporaryDirectory() as td:
                adir = self.generate(style, td)
                blocks = sorted(f for f in os.listdir(adir) if f.endswith(".svg"))
                self.assertEqual(len(blocks), expected_blocks(load(style)), f"{style}: wrong block count")
                for name in blocks:
                    errors, warnings = lint_counts(os.path.join(adir, name))
                    self.assertEqual((errors, warnings), (0, 0),
                                     f"{style}/{name}: {errors} error(s), {warnings} warning(s)")

    def test_generation_is_byte_reproducible(self):
        for style in TEMPLATES:
            with self.subTest(style=style), tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
                da = self.generate(style, a)
                db = self.generate(style, b)
                names = sorted(os.listdir(da))
                self.assertEqual(names, sorted(os.listdir(db)))
                for n in names:
                    self.assertTrue(filecmp.cmp(os.path.join(da, n), os.path.join(db, n), shallow=False),
                                    f"{style}/{n} differs between two runs")

    def test_committed_readme_matches_its_spec(self):
        # Drift gate: the README and its page graphics in the repo must be exactly what the spec
        # generates today. Edit assets/readme/project-readme.json and regenerate; never hand-edit the output.
        spec_path = TEMPLATES["blueprint"]
        with tempfile.TemporaryDirectory() as td:
            readme_page.write_all(load("blueprint"), td, registry(), False, False)
            fresh_readme = os.path.join(td, "README.md")
            committed_readme = os.path.join(ROOT, "README.md")
            self.assertTrue(filecmp.cmp(fresh_readme, committed_readme, shallow=False),
                            "README.md is out of date with assets/readme/project-readme.json - regenerate it")
            fresh_dir = os.path.join(td, "docs", "readme")
            committed_dir = os.path.join(ROOT, "docs", "readme")
            self.assertEqual(sorted(os.listdir(fresh_dir)), sorted(os.listdir(committed_dir)),
                             "docs/readme/ has a different set of blocks than the spec generates")
            for n in sorted(os.listdir(fresh_dir)):
                self.assertTrue(filecmp.cmp(os.path.join(fresh_dir, n), os.path.join(committed_dir, n), shallow=False),
                                f"docs/readme/{n} is out of date with {os.path.relpath(spec_path, ROOT)}")

    def test_readme_text_names_every_registered_type(self):
        # The page's words are inside images; search and screen readers only see the Markdown. A type that the
        # README text never names is invisible to them, so every registered type must appear in the committed README.
        with open(os.path.join(ROOT, "README.md"), encoding="utf-8") as fh:
            text = fh.read()
        self.assertEqual(unnamed_types(text), [], "README.md text does not name these registered types")

    def test_unnamed_type_is_reported(self):
        # Negative control: a README that names only some types must be reported, not pass.
        partial = "flow radial tree gantt"
        self.assertIn("pie", unnamed_types(partial))

    def test_unknown_style_is_refused(self):
        # Positive control for the dispatch: a typo must stop the build, not silently fall back.
        spec = load("spine")
        spec["style"] = "bogus"
        with tempfile.TemporaryDirectory() as td, self.assertRaises(SystemExit):
            readme_page.write_all(spec, td, registry(), False, False)

    def test_lint_still_reports_label_overflow(self):
        # Positive and negative control for the lint's label-overflow check. A page block can ship a
        # label wider than its card. The known-bad file must produce THAT warning (matching its
        # exact wording, not just any WARN), and the clean twin must produce none at all. Both files
        # carry one animation so the unrelated "no animation" warning cannot satisfy the test.
        def card(label_w, text):
            return (
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 120" role="img" aria-label="t">'
                '<title>t</title><rect width="400" height="120" fill="#111"/>'
                f'<rect x="20" y="30" width="{label_w}" height="40" rx="6" fill="#222"/>'
                f'<text x="{20 + label_w / 2}" y="58" text-anchor="middle" font-size="16" fill="#fff">{text}'
                '<animate attributeName="opacity" values="1;0.6;1" dur="2s" repeatCount="indefinite"/></text>'
                "</svg>"
            )
        with tempfile.TemporaryDirectory() as td:
            bad, good = os.path.join(td, "bad.svg"), os.path.join(td, "good.svg")
            with open(bad, "w", encoding="utf-8") as fh:
                fh.write(card(60, "this label is far too wide"))
            with open(good, "w", encoding="utf-8") as fh:
                fh.write(card(300, "fits"))
            bad_out = subprocess.run([sys.executable, LINT, bad], capture_output=True, text=True).stdout
            good_out = subprocess.run([sys.executable, LINT, good], capture_output=True, text=True).stdout
        self.assertIn("will draw through the shape", bad_out,
                      "lint no longer reports text wider than its card")
        self.assertNotIn("WARN", good_out, "clean fixture should produce no warnings")

if __name__ == "__main__":
    unittest.main()
