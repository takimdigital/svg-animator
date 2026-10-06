#!/usr/bin/env python3
"""Check that .github/workflows/*.yml is structurally valid.

Why this exists
---------------
PR #16 shipped a workflow step containing only `with:` and no `uses` or `run`.
GitHub rejects the *entire file* for that, so no job started and the run failed
with zero jobs and no message. The pre-push check used `yaml.safe_load()`, which
parsed the broken file without complaint.

Parsing valid is not the same as being valid. These two conditions are what
GitHub enforces on the file and neither is catchable by parsing:

  * every step must have a `uses` or a `run`
  * `jobs.<name>.runs-on` must be present, or the job never gets a runner

A workflow that is syntactically perfect but structurally rejected is worse than
one that fails to parse, because there is nothing to read.

Usage
-----
    python scripts/check_workflow.py            # every workflow, exits 1 on failure
    python scripts/check_workflow.py --quiet

Requires PyYAML. In CI: pip install pyyaml.
"""
import glob
import os
import sys

try:
    import yaml
except ImportError:
    sys.exit("PyYAML is not installed.  pip install pyyaml")


def check(path, quiet):
    """Return a list of complaints about one workflow file. Empty means valid."""
    with open(path, encoding="utf-8") as fh:
        try:
            doc = yaml.safe_load(fh)
        except yaml.YAMLError as exc:
            return ["does not parse: %s" % str(exc).replace("\n", " ")]

    if not isinstance(doc, dict):
        return ["top level is %s, expected a mapping" % type(doc).__name__]

    jobs = doc.get("jobs")
    if not isinstance(jobs, dict) or not jobs:
        return ["no jobs defined"]

    bad = []
    for name, spec in jobs.items():
        if not isinstance(spec, dict):
            bad.append("job %s is %s, expected a mapping" % (name, type(spec).__name__))
            continue
        if "runs-on" not in spec:
            # skip: reusable workflow calls use `uses:` instead, legitimately
            if "uses" not in spec:
                bad.append("job %s has neither runs-on nor uses" % name)
        for i, step in enumerate(spec.get("steps") or []):
            if not isinstance(step, dict):
                bad.append("job %s step %d is %s, expected a mapping"
                           % (name, i, type(step).__name__))
            elif not ("uses" in step or "run" in step):
                # This exact condition is what broke #16 and why this file exists.
                bad.append("job %s step %d has neither uses nor run (keys=%s)"
                           % (name, i, sorted(step)))
    if not quiet:
        n = sum(len(j.get("steps") or []) for j in jobs.values() if isinstance(j, dict))
        print("  %-46s %d job(s), %d step(s)" % (path, len(jobs), n))
    return bad


def main(argv):
    quiet = "--quiet" in argv[1:]
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    paths = sorted(glob.glob(os.path.join(root, ".github", "workflows", "*.yml")))
    if not paths:
        sys.exit("no workflow files found")

    failures = 0
    for p in paths:
        bad = check(os.path.relpath(p, root).replace("\\", "/"), quiet)
        for b in bad:
            print("ERROR: %s: %s" % (os.path.basename(p), b), file=sys.stderr)
        failures += len(bad)

    if failures:
        print("", file=sys.stderr)
        print("GitHub rejects the whole file for any of the above, so no job runs "
              "and the failure looks unrelated to the real problem.", file=sys.stderr)
        return 1
    print("%d workflow file(s) structurally valid" % len(paths))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))