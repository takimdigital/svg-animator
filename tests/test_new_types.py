#!/usr/bin/env python3
"""Refusals and validity for the five types in scripts/things_d.py: tree, table, pie, gantt, code.

Each refusal is checked against its exact message fragment, so a refusal that is removed, or that stops naming
the fix, fails the test. Each type also has one valid spec that must build with a positive size.

Run: python -m unittest discover -s tests -v   (stdlib only)
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))

from diagram_common import THEMES  # noqa: E402
from things_d import build_code, build_gantt, build_pie, build_table, build_tree  # noqa: E402

TH = dict(THEMES["ember"])


def refuses(builder, spec, fragment):
    """Assert the builder exits with a message containing the fragment."""
    with unittest.TestCase().assertRaises(SystemExit) as cm:
        builder(spec, TH)
    msg = str(cm.exception)
    if fragment not in msg:
        raise AssertionError(f"expected '{fragment}' in refusal, got: {msg}")


class TreeTests(unittest.TestCase):

    def test_valid_tree_builds(self):
        p = build_tree({"root": {"label": "A", "children": [{"label": "B"}, {"label": "C"}]}}, TH)
        self.assertGreater(p["W"], 0)
        self.assertGreater(p["H"], 0)

    def test_root_must_be_an_object(self):
        refuses(build_tree, {"root": ["not", "an", "object"]}, "tree: root must be an object")

    def test_every_node_needs_a_label(self):
        refuses(build_tree, {"root": {"label": "A", "children": [{"sub": "no label"}]}}, "every node needs a label")

    def test_children_must_be_objects(self):
        refuses(build_tree, {"root": {"label": "A", "children": ["B"]}}, "children must be objects")


class TableTests(unittest.TestCase):

    def test_valid_table_builds(self):
        p = build_table({"columns": ["a", "b"], "rows": [["1", "2"]]}, TH)
        self.assertGreater(p["W"], 0)

    def test_needs_a_column(self):
        refuses(build_table, {"columns": [], "rows": []}, "table: needs at least one column")

    def test_ragged_row_is_refused_with_counts(self):
        refuses(build_table, {"columns": ["a", "b", "c"], "rows": [["1", "2"]]},
                "row 1 has 2 cells, expected 3")

    def test_align_length_must_match(self):
        refuses(build_table, {"columns": ["a", "b"], "rows": [], "align": ["l"]},
                "align must have one entry per column")

    def test_align_values_are_limited(self):
        refuses(build_table, {"columns": ["a"], "rows": [], "align": ["justify"]},
                "align entries must be l, c or r")


class PieTests(unittest.TestCase):

    def test_valid_pie_builds(self):
        p = build_pie({"slices": [{"label": "x", "value": 1}, {"label": "y", "value": 3}]}, TH)
        self.assertGreater(p["W"], 0)

    def test_needs_a_slice(self):
        refuses(build_pie, {"slices": []}, "pie: needs at least one slice")

    def test_zero_value_is_refused_by_label(self):
        refuses(build_pie, {"slices": [{"label": "empty", "value": 0}]},
                "slice empty must have a positive value")


class GanttTests(unittest.TestCase):

    def test_valid_gantt_builds(self):
        p = build_gantt({"tasks": [{"name": "t", "start": 0, "end": 3, "progress": 50}]}, TH)
        self.assertGreater(p["W"], 0)

    def test_needs_a_task(self):
        refuses(build_gantt, {"tasks": []}, "gantt: needs at least one task")

    def test_end_must_follow_start(self):
        refuses(build_gantt, {"tasks": [{"name": "bad", "start": 4, "end": 4}]},
                "task bad must end after it starts")

    def test_start_cannot_be_negative(self):
        refuses(build_gantt, {"tasks": [{"name": "early", "start": -1, "end": 2}]},
                "task early starts before 0")

    def test_progress_is_a_percentage(self):
        refuses(build_gantt, {"tasks": [{"name": "over", "start": 0, "end": 2, "progress": 150}]},
                "progress must be between 0 and 100")

    def test_axis_cannot_cut_a_bar(self):
        refuses(build_gantt, {"tasks": [{"name": "long", "start": 0, "end": 9}], "axis_max": 5},
                "axis_max is smaller than the latest end")


class CodeTests(unittest.TestCase):

    def test_valid_code_builds(self):
        p = build_code({"lines": ["a", "b"], "highlight": [2]}, TH)
        self.assertGreater(p["H"], 0)

    def test_needs_a_line(self):
        refuses(build_code, {"lines": []}, "code: needs at least one line")

    def test_highlight_must_point_inside_the_block(self):
        refuses(build_code, {"lines": ["a", "b"], "highlight": [3]}, "highlight line 3 is outside 1..2")


if __name__ == "__main__":
    unittest.main()
