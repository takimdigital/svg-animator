#!/usr/bin/env python3
"""Self-tests that keep the generator honest as it grows.

Why these exist
---------------
The skill is meant to be extended by any AI. An extension that registers a new type but ships no example is
invisible: nothing shows it works, and the next person cannot see what it looks like. So:

  * every registered type must have at least one spec in assets/specs, and that spec must build clean
    (a type with no example fails here, not in review)
  * every example in assets/examples must regenerate byte-for-byte from its spec (drift fails here)
  * the typing type refuses swaps it cannot draw in place (positive controls: a bad spec must fail)

Run:  python -m unittest discover -s tests -v          (stdlib only)
"""
import filecmp
import glob
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCRIPTS = os.path.join(ROOT, "scripts")
sys.path.insert(0, SCRIPTS)

import gen_diagram  # noqa: E402
from things_c import build_typing  # noqa: E402
from diagram_common import THEMES  # noqa: E402

LINT = os.path.join(SCRIPTS, "lint_svg_anim.py")


def specs():
    out = {}
    for path in sorted(glob.glob(os.path.join(ROOT, "assets", "specs", "*.json"))):
        with open(path, encoding="utf-8") as fh:
            out[os.path.basename(path)[:-5]] = json.load(fh)
    return out


def types_used(spec):
    used = {spec.get("type")}
    used |= {p.get("type") for p in spec.get("parts", [])}
    used |= {sec["part"].get("type") for sec in spec.get("sections", []) if "part" in sec}
    return used


class TypeCoverage(unittest.TestCase):

    def test_every_registered_type_has_an_example(self):
        registered = set(gen_diagram.registry()) | {"compose"}
        covered = set()
        for spec in specs().values():
            covered |= types_used(spec)
        missing = sorted(registered - covered)
        self.assertEqual(missing, [], f"registered types with no example spec: {missing}. "
                                      "Add assets/specs/<type>-*.json, build it, and commit the example.")

    def test_every_example_regenerates_byte_for_byte(self):
        drift = []
        with tempfile.TemporaryDirectory() as td:
            for name, spec in specs().items():
                example = os.path.join(ROOT, "assets", "examples", f"{name}.svg")
                if not os.path.exists(example):
                    drift.append(f"{name}: no example file")
                    continue
                theme = gen_diagram.theme_for(spec)
                built = gen_diagram.build(spec, theme, None)
                out = os.path.join(td, f"{name}.svg")
                with open(out, "w", encoding="utf-8") as fh:
                    fh.write(gen_diagram.assemble(spec, theme, built))
                if not filecmp.cmp(out, example, shallow=False):
                    drift.append(name)
        self.assertEqual(drift, [], f"examples out of date with their specs: {drift}")

    def test_typing_example_lints_clean(self):
        path = os.path.join(ROOT, "assets", "examples", "typing-manifesto.svg")
        out = subprocess.run([sys.executable, LINT, path, "--quiet"], capture_output=True, text=True).stdout
        self.assertIn("0 error(s), 0 warning(s)", out)


class TypingValidation(unittest.TestCase):
    """Positive controls: the typing type must refuse what it cannot draw in place."""

    def theme(self):
        return dict(THEMES["ember"])

    def test_refuses_swap_of_different_length(self):
        spec = {"type": "typing", "lines": [{"text": "Hardware", "swap": {"from": "ware", "to": "reps!"}}]}
        with self.assertRaises(SystemExit) as cm:
            build_typing(spec, self.theme())
        self.assertIn("same length", str(cm.exception))

    def test_refuses_swap_source_that_is_not_unique(self):
        spec = {"type": "typing", "lines": [{"text": "ware and ware", "swap": {"from": "ware", "to": "work"}}]}
        with self.assertRaises(SystemExit) as cm:
            build_typing(spec, self.theme())
        self.assertIn("exactly once", str(cm.exception))

    def test_accepts_a_valid_swap(self):
        spec = {"type": "typing", "lines": [{"text": "Hard" + "ware...", "swap": {"from": "ware", "to": "work"}}]}
        body = build_typing(spec, self.theme())["body"]
        # the new letters are drawn (base opacity 1), and the removed letter starts hidden (base opacity 0)
        self.assertIn('opacity="1">k<animate', body)
        self.assertIn('opacity="0">e<animate', body)


if __name__ == "__main__":
    unittest.main()
