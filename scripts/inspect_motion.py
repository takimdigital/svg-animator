#!/usr/bin/env python3
"""Inspect authored SMIL/CSS motion in an SVG without running it."""
import argparse
import json
import sys
from motion_dna_core import inspect_svg, json_write

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('svg')
    p.add_argument('--out',help='Write Motion DNA JSON (stdout when omitted)')
    args=p.parse_args(argv)
    try:
        report=inspect_svg(args.svg)
        if args.out:
            json_write(args.out,report)
            print('Motion DNA: %d animation(s), %d unknown(s), %d issue(s) => %s' %
                  (report['summary']['animation_count'],len(report['unknowns']),len(report['issues']),args.out))
        else:print(json.dumps(report,indent=2))
    except (OSError, ValueError) as exc:
        print('ERROR:',exc,file=sys.stderr)
        return 2
    return 0

if __name__=='__main__':sys.exit(main())
