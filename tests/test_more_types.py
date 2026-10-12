#!/usr/bin/env python3
"""Refusals and validity for the nine types in scripts/things_e.py.

Each refusal is checked against the exact message fragment its contract promises, so a removed or
weakened refusal fails the test. Each type also has one valid spec that must build.

Run: python -m unittest discover -s tests -v   (stdlib only)
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

from diagram_common import THEMES  # noqa: E402
from things_e import (build_calendar, build_clock, build_funnel, build_heatmap, build_marquee,  # noqa: E402
                      build_scatter, build_sprite, build_venn, build_waveform)

TH = dict(THEMES["ember"])


def refuses(builder, spec, fragment):
    with unittest.TestCase().assertRaises(SystemExit) as cm:
        builder(spec, TH)
    if fragment not in str(cm.exception):
        raise AssertionError(f"expected '{fragment}' in refusal, got: {cm.exception}")


class ScatterTests(unittest.TestCase):

    def test_valid(self):
        self.assertGreater(build_scatter({"points": [{"x": 1, "y": 2}, {"x": 3, "y": 5}]}, TH)["W"], 0)

    def test_needs_points(self):
        refuses(build_scatter, {"points": []}, "scatter: needs at least one point")

    def test_numeric_coordinates(self):
        refuses(build_scatter, {"points": [{"x": "a", "y": 1}]}, "point 1 needs numeric x and y")


class HeatmapTests(unittest.TestCase):

    def test_valid(self):
        self.assertGreater(build_heatmap({"rows": ["a"], "cols": ["x", "y"], "values": [[1, 2]]}, TH)["W"], 0)

    def test_needs_rows_and_cols(self):
        refuses(build_heatmap, {"rows": [], "cols": ["x"], "values": []}, "heatmap: needs rows and cols")

    def test_row_count_matches(self):
        refuses(build_heatmap, {"rows": ["a", "b"], "cols": ["x"], "values": [[1]]}, "values has 1 rows, expected 2")

    def test_row_length_matches(self):
        refuses(build_heatmap, {"rows": ["a"], "cols": ["x", "y"], "values": [[1]]}, "row 1 has 1 values, expected 2")


class FunnelTests(unittest.TestCase):

    def test_valid(self):
        self.assertGreater(build_funnel({"stages": [{"label": "a", "value": 10}, {"label": "b", "value": 4}]}, TH)["W"], 0)

    def test_needs_a_stage(self):
        refuses(build_funnel, {"stages": []}, "funnel: needs at least one stage")

    def test_value_must_be_positive(self):
        refuses(build_funnel, {"stages": [{"label": "zero", "value": 0}]}, "stage zero must have a positive value")

    def test_funnels_only_shrink(self):
        refuses(build_funnel, {"stages": [{"label": "a", "value": 5}, {"label": "b", "value": 9}]},
                "stage b is larger than the stage before it")


class VennTests(unittest.TestCase):

    def test_valid(self):
        self.assertGreater(build_venn({"sets": [{"label": "a", "size": 3}, {"label": "b", "size": 5}]}, TH)["W"], 0)

    def test_exactly_two_sets(self):
        refuses(build_venn, {"sets": [{"label": "a", "size": 1}]}, "venn: supports exactly 2 sets")

    def test_positive_size(self):
        refuses(build_venn, {"sets": [{"label": "a", "size": 0}, {"label": "b", "size": 1}]},
                "set a needs a positive size")

    def test_overlap_range(self):
        refuses(build_venn, {"sets": [{"label": "a", "size": 1}, {"label": "b", "size": 1}], "overlap": 1.5},
                "overlap must be between 0 and 1")


class WaveformTests(unittest.TestCase):

    def test_valid(self):
        self.assertGreater(build_waveform({"samples": [0.1, -0.4, 0.9]}, TH)["W"], 0)

    def test_needs_samples_or_generate(self):
        refuses(build_waveform, {}, "waveform: needs samples or generate")

    def test_sample_must_be_a_number(self):
        refuses(build_waveform, {"samples": [1, "loud"]}, "sample 2 is not a number")

    def test_generate_kind_is_limited(self):
        refuses(build_waveform, {"generate": {"kind": "square"}}, "generate.kind must be sine or noise")


class ClockTests(unittest.TestCase):

    def test_valid(self):
        self.assertGreater(build_clock({"time": "10:10"}, TH)["W"], 0)

    def test_time_format(self):
        refuses(build_clock, {"time": "9am"}, "time must look like HH:MM (24-hour)")

    def test_time_range(self):
        refuses(build_clock, {"time": "25:00"}, "time must look like HH:MM (24-hour)")


class CalendarTests(unittest.TestCase):

    def test_valid(self):
        self.assertGreater(build_calendar({"year": 2026, "month": 10}, TH)["W"], 0)

    def test_month_range(self):
        refuses(build_calendar, {"year": 2026, "month": 13}, "month must be 1 to 12")

    def test_highlight_must_be_in_month(self):
        refuses(build_calendar, {"year": 2026, "month": 2, "highlight": [31]}, "day 31 is not in this month")


class MarqueeTests(unittest.TestCase):

    def test_valid(self):
        self.assertGreater(build_marquee({"items": ["hello"]}, TH)["W"], 0)

    def test_needs_items(self):
        refuses(build_marquee, {"items": []}, "marquee: needs at least one item")

    def test_items_not_empty(self):
        refuses(build_marquee, {"items": ["ok", "   "]}, "items must not be empty")


class SpriteTests(unittest.TestCase):

    def test_valid(self):
        self.assertGreater(build_sprite({"frames": ['<circle cx="5" cy="5" r="3"/>']}, TH)["W"], 0)

    def test_needs_frames(self):
        refuses(build_sprite, {"frames": []}, "sprite: needs at least one frame")

    def test_frame_must_be_valid_markup(self):
        refuses(build_sprite, {"frames": ['<circle cx="5"']}, "frame 1 is not valid SVG markup")


if __name__ == "__main__":
    unittest.main()
