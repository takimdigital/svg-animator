#!/usr/bin/env python3
"""run_pipeline.py - one command for the whole SVG animation pipeline.

  python scripts/run_pipeline.py INPUT [--out-dir run] [--deliver ./out] [--name my-diagram]
                                       [--theme ember|ocean|forest|mono|paper] [--times 0,2,4] [--no-frames]

INPUT is either
  * a JSON diagram spec (any gen_diagram.py type, incl. compose) -> stage BUILD runs gen_diagram.py first, or
  * an .svg file you wrote / fixed by hand          -> stage BUILD is skipped.

Stages:  1 BUILD (spec -> svg)   2 LINT   3 FRAMES (PNG at computed moments)   4 REPORT   5 DELIVER (optional)
Exit code: 0 = lint clean of ERRORs (warnings are printed, read them); 1 = ERRORs or a failed stage.

Frame times are chosen automatically: 0 (the still must look complete), the middle of every travel slot /
phase window found in the generated schedule, and 95 % of the loop (loop seam). Override with --times.
After it finishes, VIEW the PNGs (and the contact sheet) and look for: dot on a rail, only the intended card
glowing, arrows reaching targets, no text overlap. Then report honestly what was and was not verified.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def auto_times(svg_text):
    """Frame times: 0, the middle of every scheduled window ("at a..b label" lines, also legacy slot/phase lines),
    and 95 % of the loop. Long schedules are subsampled to at most 9 moments."""
    m = re.search(r"loop=([\d.]+)s", svg_text)
    if m:
        dur = float(m.group(1))
    else:
        ds = [float(x) * (0.001 if u == "ms" else 1) for x, u in re.findall(r'dur="([\d.]+)(ms|s)"', svg_text)]
        ds = [d for d in ds if d <= 15] or [6.0]
        dur = max(ds)
    mids = []
    for a, b in re.findall(r"^\s*at ([\d.]+)\.\.([\d.]+)", svg_text, re.M):
        mids.append((float(a) + float(b)) / 2)
    for a, b in re.findall(r"(?:slot \d+|phase \d+ \([^)]*\)): (?:on )?([\d.]+)(?:\s*->\s*|\.\.)([\d.]+)", svg_text):
        mids.append((float(a) + float(b)) / 2)
    mids = sorted(set(round(x, 3) for x in mids if 0 < x < 0.95))
    if len(mids) > 7:
        step = (len(mids) - 1) / 6
        mids = [mids[round(i * step)] for i in range(7)]
    if not mids:
        mids = [0.25, 0.5, 0.75]
    times = [0.0] + [m_ * dur for m_ in mids] + [dur * 0.95]
    out = []
    for t in times:
        t = round(t, 2)
        if t not in out:
            out.append(t)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("--out-dir", default="/tmp/svg-run")
    ap.add_argument("--deliver", default=None, help="directory to copy the final .svg into")
    ap.add_argument("--name", default=None, help="output file stem (default: input stem)")
    ap.add_argument("--theme", default=None)
    ap.add_argument("--times", default=None)
    ap.add_argument("--width", type=int, default=1200)
    ap.add_argument("--no-frames", action="store_true")
    a = ap.parse_args()

    os.makedirs(a.out_dir, exist_ok=True)
    stem = a.name or os.path.splitext(os.path.basename(a.input))[0]
    svg = os.path.join(a.out_dir, stem + ".svg")
    ok = True
    report = []

    # 1 BUILD
    if a.input.lower().endswith(".json"):
        cmd = [sys.executable, os.path.join(HERE, "gen_diagram.py"), a.input, svg]
        if a.theme:
            cmd += ["--theme", a.theme]
        rc, out = run(cmd)
        print("== 1 BUILD (gen_diagram.py)\n" + out.strip() + "\n")
        if rc != 0:
            print("BUILD FAILED")
            return 1
        report.append("build: generated from spec")
    else:
        if os.path.abspath(a.input) != os.path.abspath(svg):
            shutil.copyfile(a.input, svg)
        print("== 1 BUILD skipped (input is an .svg)\n")
        report.append("build: hand-written svg")

    # 2 LINT
    rc, out = run([sys.executable, os.path.join(HERE, "lint_svg_anim.py"), svg])
    print("== 2 LINT (lint_svg_anim.py)\n" + out.strip() + "\n")
    errs = len(re.findall(r"^ERROR:", out, re.M))
    warns = len(re.findall(r"^WARN:", out, re.M))
    if rc != 0:
        ok = False
    report.append(f"lint: {errs} error(s), {warns} warning(s)")

    # 3 FRAMES
    frames = []
    if not a.no_frames:
        text = open(svg, encoding="utf-8").read()
        times = a.times or ",".join(str(t) for t in auto_times(text))
        fdir = os.path.join(a.out_dir, "frames")
        rc, out = run([sys.executable, os.path.join(HERE, "render_frames.py"), svg, "--times", times, "--out", fdir, "--width", str(a.width), "--sheet"])
        print("== 3 FRAMES (render_frames.py)  times: " + times + "\n" + out.strip() + "\n")
        frames = [ln for ln in out.splitlines() if ln.endswith(".png") and "contact_sheet" not in ln]
        if rc != 0:
            report.append("frames: NOT captured (Playwright/Chromium unavailable) - say so in the final message")
        else:
            report.append(f"frames: {len(frames)} PNG(s) captured at t = {times}")

    # 4 REPORT / 5 DELIVER
    print("== 4 REPORT")
    for r in report:
        print("  - " + r)
    print("  - NEXT: view the PNGs yourself and check: dot on a rail, only the intended card glowing, arrows reaching targets,")
    print("          frame 0 looks complete, no text overlap, loop seam (last frame) clean. Then summarise what was verified.")
    if a.deliver and ok:
        os.makedirs(a.deliver, exist_ok=True)
        dst = os.path.join(a.deliver, stem + ".svg")
        shutil.copyfile(svg, dst)
        print(f"== 5 DELIVER: {dst}  (now show/attach that file to the user)")
    elif a.deliver and not ok:
        print("== 5 DELIVER skipped: fix the lint ERRORs first")
    if not ok:
        print("\nRESULT: FAIL (lint errors) - fix them and re-run")
    elif warns:
        print(f"\nRESULT: PASS WITH {warns} WARNING(S) - fix each at its root cause or justify it; re-run")
    else:
        print("\nRESULT: PASS (0 errors, 0 warnings) - now view the frames")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
