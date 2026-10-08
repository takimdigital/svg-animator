#!/usr/bin/env python3
"""Self-tests for the parts of the skill that have no other safety net.

Why these exist
---------------
The CI gates prove the *output* is clean: the examples lint, verify, regenerate
byte-for-byte, have current twins and tiles. Nothing proves the machinery that
produced them is correct. A resampler bug or a theme-polarity bug produces a
file that lints clean, verifies clean, and looks plausible - exactly the class
of failure that has already happened here twice and had to be caught by eye.

So: the two pieces of logic with the most ways to be quietly wrong get tests.

Run:
    python -m unittest discover -s tests -v
    python tests/test_morph_path.py

stdlib only - `unittest`, no pytest. CI runs this with no Playwright, because a
test suite that needs a browser is a test suite people skip.
"""
import math
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import morph_path as mp  # noqa: E402
from diagram_common import DARK_THEMES, SURFACES, THEMES  # noqa: E402

GEN = os.path.join(ROOT, "scripts", "gen_diagram.py")


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


class TestParsing(unittest.TestCase):
    """The tokenizer is where a silent zero-point bug hides."""

    def test_leading_whitespace_is_consumed(self):
        # "M 50 5" has a space after the letter. A number pattern that does not
        # skip whitespace matches nothing, and every path collapses to one point
        # at the origin - which is exactly the bug this asserts against.
        self.assertEqual(mp.parse("M 50 5 L 61 38"), [("L", [50, 5]), ("L", [61, 38])])

    def test_tight_spacing_also_works(self):
        self.assertEqual(mp.parse("M50 5L61 38"), [("L", [50, 5]), ("L", [61, 38])])

    def test_relative_commands_are_absolutised(self):
        segs = mp.parse("m 10 10 l 30 0 l 0 30 z")
        self.assertEqual([s[0] for s in segs], ["L", "L", "L", "Z"])
        self.assertEqual(segs[2][1], [40, 40])

    def test_closepath_is_kept(self):
        # Z carries no numbers. A group loop drops it and the shape silently
        # stops being closed - the second bug this file exists for.
        self.assertEqual(mp.parse("M0 0 L10 0 Z")[-1][0], "Z")

    def test_horizontal_and_vertical_shorthands(self):
        pts, _ = mp.flatten("M10 10 H50 V40")
        self.assertEqual(pts[-1], (50.0, 40.0))

    def test_smooth_cubic_reflects_previous_control(self):
        pts, _ = mp.flatten("M0 0 C10 0 20 10 20 20 S30 40 40 40")
        self.assertGreater(len(pts), 20)
        self.assertLess(abs(pts[-1][0] - 40.0), 1e-6)

    def test_close_flag(self):
        self.assertTrue(mp.flatten("M0 0 L10 0 L10 10 Z")[1])
        self.assertFalse(mp.flatten("M0 0 L10 0 L10 10")[1])

    def test_subpath_count(self):
        self.assertEqual(mp.subpaths("M0 0 L1 1 Z"), 1)
        self.assertEqual(mp.subpaths("M0 0 L1 1 Z M5 5 L6 6 Z"), 2)


class TestGeometry(unittest.TestCase):
    """Resampling must preserve the shape, not merely produce the right count."""

    CIRCLE = "M 50 6 A 44 44 0 1 1 49.9 6 Z"
    SQUARE = "M 6 6 L 94 6 L 94 94 L 6 94 Z"
    STAR = "M50 4 L61 37 L96 37 L68 58 L79 93 L50 72 L21 93 L32 58 L4 37 L39 37 Z"

    def test_resample_returns_requested_count(self):
        for d in (self.CIRCLE, self.SQUARE, self.STAR):
            pts, _ = mp.resample(d, 40)
            self.assertEqual(len(pts), 40, d[:16])

    def test_resample_is_arc_length_even(self):
        # For a circle, equal arc-length steps must be roughly equidistant.
        # A naive "every nth control point" would fail this badly.
        pts, _ = mp.resample(self.CIRCLE, 16)
        gaps = [dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
        self.assertLess(max(gaps) - min(gaps), max(gaps) * 0.25,
                        "arc-length spacing is uneven: %s" % [round(g, 2) for g in gaps])

    def test_resample_endpoints_survive(self):
        # A closed shape resampled must start and end at the same place.
        pts, closed = mp.resample(self.CIRCLE, 32)
        self.assertTrue(closed)
        self.assertLess(dist(pts[0], pts[-1]), 1e-6)

    def test_square_extent_is_preserved(self):
        # The real property is that resampling keeps the shape's extent, not
        # that every corner lands on a sample. With 8 points on a 4-sided
        # square, arc length cannot hit all four corners, and asserting that it
        # does would be asserting something false.
        pts, _ = mp.resample(self.SQUARE, 8)
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        self.assertAlmostEqual(min(xs), 6.0, places=1)
        self.assertAlmostEqual(max(xs), 94.0, places=1)
        self.assertAlmostEqual(min(ys), 6.0, places=1)
        self.assertAlmostEqual(max(ys), 94.0, places=1)

    def test_square_keeps_its_start_corner_exact(self):
        # n samples span n-1 intervals, so equal arc-length steps generally
        # cannot land on every corner of a 4-sided shape. The start corner must
        # still be exact, and the extent test above covers the rest.
        pts, _ = mp.resample(self.SQUARE, 8)
        self.assertLess(dist(pts[0], (6, 6)), 0.01)

    def test_flattens_a_real_cubic(self):
        pts, _ = mp.flatten("M 10 90 C 40 0 60 40 90 10")
        self.assertGreater(len(pts), 10)
        self.assertLess(abs(pts[0][0] - 10.0), 1e-6)
        self.assertLess(abs(pts[-1][0] - 90.0), 1e-6)


class TestMorphing(unittest.TestCase):
    """The whole point: mismatched structures must end up with one signature."""

    FORMS = {
        "star": "M50 4 L61 37 L96 37 L68 58 L79 93 L50 72 L21 93 L32 58 L4 37 L39 37 Z",
        "circle": "M50 6 A44 44 0 1 1 49.9 6 Z",
        "heart": ("M50 90 C20 68 4 48 4 31 C4 15 16 5 30 5 C40 5 46 11 50 19 "
                  "C54 11 60 5 70 5 C84 5 96 15 96 31 C96 48 80 68 50 90 Z"),
        "square": "M6 6 L94 6 L94 94 L6 94 Z",
        "bolt": "M56 4 L22 54 L44 54 L38 96 L78 42 L54 42 Z",
        "drop": "M50 6 C72 34 88 52 88 66 A38 38 0 0 1 12 66 C12 52 28 34 50 6 Z",
        "cross": "M38 6 L62 6 L62 38 L94 38 L94 62 L62 62 L62 94 L38 94 L38 62 L6 62 L6 38 L38 38 Z",
        "leaf": "M50 6 C82 26 88 58 50 94 C12 58 18 26 50 6 Z",
        "wave": "M4 60 C18 30 32 30 50 60 C68 90 82 90 96 60",
        "arrow": "M6 50 L70 50 L70 26 L96 50 L70 74 L70 50 Z",
        "hexagon": "M50 4 L90 27 L90 73 L50 96 L10 73 L10 27 Z",
        "ring": "M50 8 A42 42 0 1 1 49.9 8 Z M50 26 A24 24 0 1 0 50.1 26 Z",
    }

    def test_all_forms_parse_to_something_real(self):
        for name, d in self.FORMS.items():
            pts, closed = mp.flatten(d)
            self.assertGreater(len(pts), 1, name)
        # `wave` is deliberately open - an open stroke is a legitimate shape.
        self.assertFalse(mp.flatten(self.FORMS["wave"])[1])
        self.assertTrue(mp.flatten(self.FORMS["star"])[1])

    def test_every_pair_gets_one_signature(self):
        # The core contract. If this fails, SMIL snaps and nothing says so.
        # `ring` and `wave` are excluded by design, not by luck: see the two
        # refusal tests below, which are the reason they are excluded.
        closed = [n for n, d in self.FORMS.items()
                  if n != "ring" and mp.flatten(d)[1]]
        for a in closed:
            for b in closed:
                if a == b:
                    continue
                x, y = mp.morph_pair(self.FORMS[a], self.FORMS[b], n=12)
                self.assertEqual(mp.signature(x), mp.signature(y), "%s -> %s" % (a, b))

    def test_open_shape_pairs_with_another_open_shape(self):
        open_a = "M4 60 C18 30 32 30 50 60"
        open_b = "M4 20 C18 80 32 80 50 20"
        x, y = mp.morph_pair(open_a, open_b, n=12)
        self.assertEqual(mp.signature(x), mp.signature(y))
        self.assertNotIn("Z", mp.signature(x))

    def test_closed_and_open_are_refused(self):
        # Found by this suite: star (closed) against wave (open) produced
        # "MCCCZ" and "MCCC", which cannot interpolate, and it snapped silently.
        with self.assertRaises(ValueError) as ctx:
            mp.morph_pair(self.FORMS["star"], self.FORMS["wave"], n=12)
        self.assertIn("closed", str(ctx.exception))

    def test_signature_is_one_move_then_cubics_then_z(self):
        x, _ = mp.morph_pair(self.FORMS["star"], self.FORMS["circle"], n=20)
        sig = mp.signature(x)
        self.assertEqual(sig[0], "M")
        self.assertEqual(sig[-1], "Z")           # both shapes are closed
        self.assertEqual(set(sig[1:-1]), {"C"})
        self.assertEqual(len(sig), 22)   # M + 20 C + Z for n=20

    def test_shapes_with_holes_are_refused(self):
        # A ring flattens both contours into one polyline and is wrong at
        # every frame, so it must raise rather than return nonsense.
        with self.assertRaises(ValueError) as ctx:
            mp.morph_pair(self.FORMS["ring"], self.FORMS["star"], n=12)
        self.assertIn("subpath", str(ctx.exception))

    def test_alignment_reduces_travel(self):
        # Unaligned pairing collapses circle -> heart through the middle.
        a, _ = mp.resample(self.FORMS["circle"], 32)
        b, _ = mp.resample(self.FORMS["heart"], 32)

        def cost(pb):
            return sum(dist(a[i], pb[i]) ** 2 for i in range(len(a))) / len(a)

        raw = cost(b)
        k, _best = mp._best_offset(a, b)
        shifted = b[k:] + b[:k]
        self.assertLessEqual(cost(shifted), raw + 1e-9)
        self.assertLess(cost(shifted), raw * 0.5,
                        "alignment barely helped: %.0f -> %.0f" % (raw, cost(shifted)))

    def test_align_false_is_the_raw_correspondence(self):
        pa, _ = mp.resample(self.FORMS["circle"], 16)
        raw = mp.to_uniform(pa, True)
        a, _ = mp.morph_pair(self.FORMS["circle"], self.FORMS["heart"], n=16, align=False)
        self.assertTrue(a.startswith(raw[:12]))

    def test_size_grows_linearly(self):
        small, _ = mp.morph_pair(self.FORMS["star"], self.FORMS["circle"], n=10)
        big, _ = mp.morph_pair(self.FORMS["star"], self.FORMS["circle"], n=20)
        self.assertGreater(len(big), len(small) * 1.5)

    def test_coordinates_are_rounded_not_truncated(self):
        # "%.2f" then rstrip would turn 0.50 into "0.5" (fine) but must never
        # produce a bare "." or a trailing "." on an integer.
        d = mp.to_uniform([(0.0, 0.0), (10.5, 20.0), (0.0, 10.0)], closed=True)
        self.assertNotIn(" .", d)
        self.assertNotIn("C .", d)


class TestThemePairs(unittest.TestCase):
    """`--pair` is documented and polarity-guarded but was never run end to end.

    Light/dark pairing is a shipped feature with zero shipped pairs, so nothing
    had ever exercised the code path. These run the real generator.
    """

    SPEC = {
        "type": "radial", "theme": "ocean", "dur": 6,
        "center": {"label": "core/", "sub": "hub"},
        "items": [{"title": "A", "count": "01", "lines": ["one"]},
                  {"title": "B", "count": "02", "lines": ["two"]},
                  {"title": "C", "count": "03", "lines": ["three"]}],
    }

    def _run(self, extra, out_stem):
        import json
        with tempfile.TemporaryDirectory() as td:
            spec = os.path.join(td, "s.json")
            with open(spec, "w", encoding="utf-8") as fh:
                json.dump(self.SPEC, fh)
            r = subprocess.run(
                [sys.executable, GEN, spec, out_stem] + extra,
                capture_output=True, text=True, cwd=ROOT)
            return r

    def test_pair_writes_both_halves(self):
        with tempfile.TemporaryDirectory() as td:
            r = self._run(["--pair", "paper", "ocean"],
                          os.path.join(td, "hero.svg"))
            self.assertEqual(r.returncode, 0, r.stderr[-400:])
            self.assertTrue(os.path.exists(os.path.join(td, "hero-light.svg")))
            self.assertTrue(os.path.exists(os.path.join(td, "hero-dark.svg")))

    def test_pair_halves_really_differ(self):
        # If both halves came out identical the pair would be worthless, and a
        # theme lookup that ignored its argument would produce exactly that.
        with tempfile.TemporaryDirectory() as td:
            self._run(["--pair", "paper", "ocean"], os.path.join(td, "hero.svg"))
            with open(os.path.join(td, "hero-light.svg"), encoding="utf-8") as fh:
                light = fh.read()
            with open(os.path.join(td, "hero-dark.svg"), encoding="utf-8") as fh:
                dark = fh.read()
            self.assertNotEqual(light, dark)
            self.assertIn(THEMES["paper"]["bg"], light)
            self.assertIn(THEMES["ocean"]["bg"], dark)

    def test_pair_prints_the_picture_snippet(self):
        with tempfile.TemporaryDirectory() as td:
            r = self._run(["--pair", "paper", "ocean"], os.path.join(td, "hero.svg"))
            self.assertIn("<picture>", r.stdout)
            self.assertIn("media", r.stdout)

    def test_pair_refuses_two_dark_themes(self):
        # An <img> SVG cannot see the page theme, so a "light" half that is
        # actually dark is a silent lie. The guard must hold.
        r = self._run(["--pair", "ember", "ocean"], os.path.join(tempfile.gettempdir(), "x.svg"))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("dark theme", (r.stderr + r.stdout).lower())

    def test_pair_refuses_two_light_themes(self):
        r = self._run(["--pair", "paper", "paper"], os.path.join(tempfile.gettempdir(), "x.svg"))
        self.assertNotEqual(r.returncode, 0)

    def test_pair_refuses_unknown_theme(self):
        r = self._run(["--pair", "paper", "chartreuse"], os.path.join(tempfile.gettempdir(), "x.svg"))
        self.assertNotEqual(r.returncode, 0)

    def test_every_theme_has_a_polarity(self):
        # A new theme added to THEMES without a DARK_THEMES entry would make
        # --pair guess. Fail here instead of shipping an ambiguous pair.
        self.assertEqual(DARK_THEMES | {"paper"}, set(THEMES))


class TestMorphTypeEndToEnd(unittest.TestCase):
    """The builder asserts its own contract; prove the assertion is reachable."""

    def test_spec_generates_and_lints(self):
        import json
        spec = os.path.join(ROOT, "assets", "specs", "morph-shapes.json")
        with tempfile.TemporaryDirectory() as td:
            out = os.path.join(td, "m.svg")
            r = subprocess.run([sys.executable, GEN, spec, out],
                               capture_output=True, text=True, cwd=ROOT)
            self.assertEqual(r.returncode, 0, r.stderr[-400:])
            with open(out, encoding="utf-8") as fh:
                svg = fh.read()
            self.assertIn('<animate attributeName="d"', svg)
            r2 = subprocess.run(
                [sys.executable, os.path.join(ROOT, "scripts", "lint_svg_anim.py"), out],
                capture_output=True, text=True, cwd=ROOT)
            self.assertEqual(r2.returncode, 0, r2.stdout[-400:])

    def test_builder_refuses_a_shape_with_a_hole(self):
        # If someone adds `ring` to a spec, the build must stop with a message
        # rather than emitting a file whose shapes quietly do not morph.
        import json
        spec = dict(forms=["ring", "star"])
        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, "s.json")
            with open(p, "w", encoding="utf-8") as fh:
                json.dump({"type": "morph", "forms": spec["forms"], "dur": 6}, fh)
            r = subprocess.run([sys.executable, GEN, p, os.path.join(td, "o.svg")],
                               capture_output=True, text=True, cwd=ROOT)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("subpath", (r.stderr + r.stdout).lower())


class TestSurfaces(unittest.TestCase):
    """The visual grammar, which used to be hardcoded to one value.

    Every one of the 53 shipped examples had the same surface - rounded opaque
    background, three blurred radial blobs, generous glow blur - because
    assemble() and common_defs() emitted them unconditionally. Not a theme
    choice; a constant.
    """

    SPEC = {
        "type": "radial", "theme": "ocean", "dur": 6,
        "center": {"label": "core/", "sub": "hub"},
        "items": [{"title": "A", "count": "01", "lines": ["one"]},
                  {"title": "B", "count": "02", "lines": ["two"]},
                  {"title": "C", "count": "03", "lines": ["three"]}],
    }

    def _gen(self, surface=None, extra=()):
        import json
        with tempfile.TemporaryDirectory() as td:
            spec = dict(self.SPEC)
            if surface:
                spec["surface"] = surface
            p = os.path.join(td, "s.json")
            with open(p, "w", encoding="utf-8") as fh:
                json.dump(spec, fh)
            out = os.path.join(td, "o.svg")
            r = subprocess.run([sys.executable, GEN, p, out] + list(extra),
                               capture_output=True, text=True, cwd=ROOT)
            body = ""
            if r.returncode == 0 and os.path.exists(out):
                with open(out, encoding="utf-8") as fh:
                    body = fh.read()
            return r, body

    def test_glow_is_the_default(self):
        r, implicit = self._gen(None)
        r2, explicit = self._gen("glow")
        self.assertEqual(r.returncode, 0, r.stderr[-300:])
        self.assertEqual(implicit, explicit,
                         "omitting `surface` must be identical to surface=glow")

    def test_default_keeps_the_rounded_background_and_aurora(self):
        _, svg = self._gen()
        self.assertIn('rx="16"', svg)
        self.assertIn("<ellipse", svg)          # the drifting gradient bed
        self.assertIn('stdDeviation="3.6"', svg)

    def test_flat_drops_the_aurora_and_the_rounding(self):
        _, svg = self._gen("flat")
        self.assertNotIn("<ellipse", svg, "flat must not emit the aurora bed")
        self.assertNotIn('rx="16"', svg, "flat must not round the background")
        self.assertIn("<rect width=", svg)

    def test_bare_draws_no_background_at_all(self):
        _, svg = self._gen("bare")
        head = svg.split("</defs>")[-1]
        first_rect = head.find("<rect")
        # no full-bleed background rect before the content
        self.assertNotRegex(head[:400], r'<rect width="\d+(\.\d+)?" height="\d+(\.\d+)?"\s+fill=')

    def test_every_surface_still_defines_the_glow_filter(self):
        # Builders reference url(#glow) from 11 inline sites. A surface that
        # omitted the definition produced 9 dangling references and the linter
        # correctly rejected the file - which is why there is no "line" surface.
        for s in ("glow", "flat", "bare"):
            r, svg = self._gen(s)
            self.assertEqual(r.returncode, 0, "%s: %s" % (s, r.stderr[-300:]))
            self.assertIn('id="glow"', svg, s)
            self.assertIn("url(#glow)", svg, s)

    def test_unknown_surface_is_refused(self):
        r, _ = self._gen("chrome")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("surface", (r.stderr + r.stdout).lower())

    def test_every_shipped_example_lints_under_its_own_surface(self):
        for stem in ("flow-flat", "gauge-dashboard-flat"):
            f = os.path.join(ROOT, "assets", "examples", stem + ".svg")
            if not os.path.exists(f):
                self.skipTest("%s not generated yet" % stem)
            r = subprocess.run(
                [sys.executable, os.path.join(ROOT, "scripts", "lint_svg_anim.py"), f],
                capture_output=True, text=True, cwd=ROOT)
            self.assertEqual(r.returncode, 0, "%s: %s" % (stem, r.stdout[-300:]))

    def test_surfaces_table_is_small_and_documented(self):
        # A surface that differs only by a blur amount is indistinguishable from
        # its neighbour, so the set is kept short on purpose.
        self.assertEqual(set(SURFACES), {"glow", "flat", "bare"})
        for name, cfg in SURFACES.items():
            self.assertEqual(set(cfg), {"bg", "aurora", "blur", "grad"}, name)
            self.assertIn(cfg["bg"], ("rounded", "square", "none"), name)
        self.assertTrue(SURFACES["glow"]["aurora"])
        self.assertFalse(SURFACES["flat"]["aurora"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
