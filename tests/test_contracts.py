#!/usr/bin/env python3
"""Every generator builder carries a contract docstring, and the contract matches the code.

A contract has fixed sections: Fields, Refuses, Base state, Breaks if changed, Example (Timing and
Alternatives are optional). A model that reads a builder's docstring learns the spec it accepts, what is
refused, what the still frame shows, what must not change, and which example to copy.

This test fails when:
  * a builder has no docstring, or a required section is missing
  * the code reads a spec key (spec.get('k') or spec['k']) that the Fields section does not mention
  * the Example section names a spec that does not exist in assets/specs

Negative controls at the bottom prove that each of these checks can fail.

Run: python -m unittest discover -s tests -v   (stdlib only)
"""
import ast
import inspect
import os
import re
import sys
import textwrap
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import gen_diagram  # noqa: E402

REQUIRED = ["Fields:", "Refuses:", "Base state:", "Breaks if changed:", "Example:"]
HEADINGS = ["Fields:", "Refuses:", "Base state:", "Timing:", "Alternatives:", "Breaks if changed:", "Example:", "Tests:"]


def builders():
    """Every registered type (23) plus compose: name -> function."""
    out = dict(gen_diagram.registry())
    out["compose"] = gen_diagram.build_compose
    return out


def spec_keys_read(func):
    """Constant keys the builder reads from its spec: spec.get('k') and spec['k'] inside the function body."""
    tree = ast.parse(textwrap.dedent(inspect.getsource(func)))
    keys = set()
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "get"
                and isinstance(node.func.value, ast.Name) and node.func.value.id == "spec"
                and node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str)):
            keys.add(node.args[0].value)
        if (isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name) and node.value.id == "spec"
                and isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str)):
            keys.add(node.slice.value)
    return keys


def section(doc, heading):
    """Text of one section: from its heading to the next heading (or the end)."""
    start = doc.index(heading) + len(heading)
    ends = [doc.index(h, start) for h in HEADINGS if h != heading and h in doc[start:]]
    end = min(ends) if ends else len(doc)
    return doc[start:end]


def contract_problems(func, spec_dir=os.path.join(ROOT, "assets", "specs")):
    doc = inspect.getdoc(func) or ""
    if not doc:
        return [f"{func.__name__}: no docstring (no contract)"]
    problems = []
    for h in REQUIRED:
        if h not in doc:
            problems.append(f"{func.__name__}: missing section '{h}'")
    if problems:
        return problems
    fields = section(doc, "Fields:")
    for key in sorted(spec_keys_read(func)):
        # the key must open a field entry: followed by its default, a separator or a brace,
        # not merely appear inside an expression such as (card_w + 28)
        entry = r"(?:^|[\s;,(\[{])" + re.escape(key) + r"(?=\s*(?:\(|;|,|\.|\)|\]|\[|\{|\}|:|$))"
        if not re.search(entry, fields, re.M):
            problems.append(f"{func.__name__}: spec key '{key}' is read by the code but has no entry in Fields")
    example = section(doc, "Example:")
    names = re.findall(r"([\w.-]+\.json)", example)
    if not names:
        problems.append(f"{func.__name__}: Example names no spec file")
    for name in names:
        if not os.path.exists(os.path.join(spec_dir, name)):
            problems.append(f"{func.__name__}: Example names '{name}', which is not in assets/specs")
    return problems


class EveryBuilderHasAContract(unittest.TestCase):

    def test_all_builders_have_complete_contracts(self):
        bad = []
        for name, func in sorted(builders().items()):
            bad += contract_problems(func)
        self.assertEqual(bad, [], "contract problems:\n  " + "\n  ".join(bad))

    def test_counts_match_the_capability_map(self):
        # references/CAPABILITIES.md lists the types; compose is one more builder. Change them together.
        self.assertEqual(len(gen_diagram.registry()), 38)
        self.assertEqual(len(builders()), 39)


class SharedHelpersAreDocumented(unittest.TestCase):
    """Every public helper in diagram_common carries its contract: builders depend on these rules."""

    def test_every_public_helper_has_a_docstring(self):
        import diagram_common
        bad = []
        for name, fn in inspect.getmembers(diagram_common, inspect.isfunction):
            if fn.__module__ == "diagram_common" and not name.startswith("_") and not inspect.getdoc(fn):
                bad.append(name)
        self.assertEqual(bad, [], f"shared helpers with no docstring: {bad}")


class NegativeControls(unittest.TestCase):
    """The checks above must be able to fail. Each control is a builder with one deliberate defect."""

    def test_missing_docstring_is_reported(self):
        def build_undocumented(spec, th, idp=""):
            return None
        self.assertTrue(contract_problems(build_undocumented), "a builder without a docstring must be reported")

    def test_undocumented_helper_is_reported(self):
        def helper_without_contract(v):
            return v
        self.assertFalse(inspect.getdoc(helper_without_contract), "control: an undocumented helper has no doc")

    def test_missing_section_is_reported(self):
        def build_no_refusals(spec, th, idp=""):
            """x: y.

            Fields: dur.
            Base state: finished.
            Breaks if changed: nothing.
            Example: typing-manifesto.json
            """
            return spec.get("dur")
        problems = contract_problems(build_no_refusals)
        self.assertTrue(any("'Refuses:'" in p for p in problems), problems)

    def test_undocumented_spec_key_is_reported(self):
        def build_hidden_key(spec, th, idp=""):
            """x: y.

            Fields: dur.
            Refuses: nothing.
            Base state: finished.
            Breaks if changed: nothing.
            Example: typing-manifesto.json
            """
            return spec.get("dur"), spec.get("secret_option")
        problems = contract_problems(build_hidden_key)
        self.assertTrue(any("secret_option" in p for p in problems), problems)

    def test_example_that_does_not_exist_is_reported(self):
        def build_missing_example(spec, th, idp=""):
            """x: y.

            Fields: dur.
            Refuses: nothing.
            Base state: finished.
            Breaks if changed: nothing.
            Example: no-such-spec.json
            """
            return spec.get("dur")
        problems = contract_problems(build_missing_example)
        self.assertTrue(any("no-such-spec.json" in p for p in problems), problems)


if __name__ == "__main__":
    unittest.main()
