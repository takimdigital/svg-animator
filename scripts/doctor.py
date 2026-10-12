#!/usr/bin/env python3
"""doctor.py - tell an agent what works in this environment, then run the gates.

Usage:  python scripts/doctor.py

What it reports
---------------
  * Python version (3.9 or newer is required)
  * whether the optional browser tools are available (Playwright + Chromium): frames and verify.py need them
  * the gates, each run exactly as CI runs it, with PASS / FAIL and the reason

Exit code: 0 when every gate that can run here passes; 1 when any gate fails. A gate that cannot run here
(for example the browser check without Playwright) is reported as SKIP, never as a pass.
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run(cmd):
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return p.returncode, (p.stdout + p.stderr).strip()


def browser_available():
    import importlib.util
    if importlib.util.find_spec("playwright") is None:
        return False, "Playwright is not installed (pip install playwright && python -m playwright install chromium)"
    return True, "Playwright importable"


def main():
    ok_all = True
    py = sys.version_info
    print(f"python {py.major}.{py.minor}.{py.micro}", "OK" if py >= (3, 9) else "FAIL (needs 3.9+)")
    ok_all &= py >= (3, 9)
    have_browser, why = browser_available()
    print(f"browser tools: {'available' if have_browser else 'not available'} - {why}")
    print()

    gates = [
        ("tests", [sys.executable, "-m", "unittest", "discover", "-s", "tests"], True),
        ("lint (CI scope)", [sys.executable, "scripts/lint_svg_anim.py", "assets/examples/*.svg", "docs/*.svg", "docs/thumbs/*.svg"], True),
        ("gallery is current", [sys.executable, "scripts/build_gallery.py", "--check"], True),
        ("static twins current", [sys.executable, "scripts/static_twin.py", "--check", "assets/examples"], True),
        ("workflow valid", [sys.executable, "scripts/check_workflow.py", "--quiet"], True),
        ("browser frame-0 check", [sys.executable, "scripts/verify.py", "assets/examples/*.svg"], have_browser),
    ]
    for name, cmd, can_run in gates:
        if not can_run:
            print(f"SKIP  {name:24s} {why}")
            continue
        # globs are expanded by the shell in CI; expand them here so this runs the same on every platform
        expanded = []
        import glob
        for part in cmd:
            if "*" in part:
                expanded.extend(sorted(glob.glob(os.path.join(ROOT, part))) or [part])
            else:
                expanded.append(part)
        code, out = run(expanded)
        last = out.splitlines()[-1] if out else ""
        status = "PASS" if code == 0 else "FAIL"
        ok_all &= code == 0
        print(f"{status}  {name:24s} {last[:110]}")
    print()
    print("ALL GATES PASS" if ok_all else "SOME GATES FAILED - read the line above each FAIL")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
