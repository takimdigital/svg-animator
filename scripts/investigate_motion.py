#!/usr/bin/env python3
"""End-to-end Motion DNA: inspect + optionally capture + compare a candidate."""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
from motion_dna_core import inspect_svg,json_write

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('reference',help='Reference SVG with self-contained SMIL/CSS')
    ap.add_argument('--out-dir',default='motion-dna-run')
    ap.add_argument('--candidate',help='Optional SVG to compare using aligned timestamps and element ids')
    ap.add_argument('--targets',help='Comma-separated IDs for comparison')
    ap.add_argument('--target-map',help='Explicit ref:candidate element mapping')
    ap.add_argument('--mode',choices=['state','opacity','transform'],default='state')
    ap.add_argument('--samples',type=int,default=9)
    ap.add_argument('--no-browser',action='store_true',help='Static inspection only')
    ap.add_argument('--no-images',action='store_true',help='Capture state but not screenshots')
    ap.add_argument('--browser-path',help='Chromium executable')
    a=ap.parse_args(argv)
    if not 2<=a.samples<=80:ap.error('samples must be within [2,80]')
    if a.candidate and a.no_browser:ap.error('--candidate requires browser capture')
    out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)
    try:
        spec=inspect_svg(a.reference)
        json_write(out/'motion-dna.json',spec)
        print('SOURCE:',spec['summary']['animation_count'],'animation(s);',len(spec['unknowns']),'unknown(s)')
        if a.no_browser:return 0
        from capture_motion import capture
        ref=capture(a.reference,out/'reference',samples=a.samples,screenshots=not a.no_images,browser_path=a.browser_path)
        print('OBSERVED:',len(ref['frames']),'reference frames; possible anomalies:',len(ref['anomalies']))
        if a.candidate:
            cand=capture(a.candidate,out/'candidate',times=','.join(map(str,ref['sampling']['times_seconds'])),
                         screenshots=not a.no_images,browser_path=a.browser_path)
            from compare_motion import compare, parse_mapping
            result=compare(ref,cand,a.targets.split(',') if a.targets else None,
                           mode=a.mode,target_map=parse_mapping(a.target_map))
            json_write(out/'comparison.json',result)
            print('COMPARISON:',result['verdict'],len(result['differences']),'deviations;',
                  len(result['missing']),'missing states')
            return 0 if result['verdict']=='PASS' else 1 if result['verdict']=='FAIL' else 2
        return 0
    except Exception as e:
        print('INVESTIGATION ERROR:',e,file=sys.stderr)
        return 2

if __name__=='__main__':sys.exit(main())
