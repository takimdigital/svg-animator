#!/usr/bin/env python3
"""Compare aligned, element-specific motion traces without whole-frame pixel scores.

`state` compares normalized location/size and visibility/opacity on identical
SVG element IDs. `opacity` compares opacity choreography only; `transform` compares
SVG CTM linear terms (rotation/scale/skew). Both support an
explicit reference->candidate ID map for original artwork variations.
"""
from __future__ import annotations
import argparse
import json
import math
import sys
from pathlib import Path
from motion_dna_core import json_write


def _norm(frame, target, view):
    s=frame.get('elements',{}).get(target)
    if not s:return None
    box=s.get('bbox',{})
    return {'bbox':{
        'x':box.get('x',0)/view['width'],
        'y':box.get('y',0)/view['height'],
        'width':box.get('width',0)/view['width'],
        'height':box.get('height',0)/view['height']},
        'opacity':s.get('opacity',1.0),'visibility':s.get('visibility','visible'),
        'display':s.get('display','inline'), 'ctm':s.get('ctm')}


def compare(reference,candidate,targets=None,pos_tol=0.035,opacity_tol=0.1,
            ignore_missing=False, mode='state', target_map=None):
    if mode not in ('state','opacity','transform'):raise ValueError('mode must be state, opacity or transform')
    if not (math.isfinite(pos_tol) and 0 <= pos_tol <= 1 and math.isfinite(opacity_tol) and 0 <= opacity_tol <= 1):
        raise ValueError('Tolerances must be finite numbers within [0,1]')
    target_map=target_map or {}
    rf=reference['frames'];cf=candidate['frames']
    rt={round(f['time_seconds'],4):f for f in rf}
    ct={round(f['time_seconds'],4):f for f in cf}
    ts=sorted(set(rt)&set(ct))
    absent_reference_times=sorted(set(ct)-set(rt))
    absent_candidate_times=sorted(set(rt)-set(ct))
    incomplete_times=bool(absent_reference_times or absent_candidate_times)
    if not ts:
        return {'schema_version':'0.1.0','verdict':'INCONCLUSIVE',
                'reason':'No identical timestamps to compare',
                'differences':[],'missing':[],'coverage':0,
                'missing_reference_timestamps':absent_reference_times,
                'missing_candidate_timestamps':absent_candidate_times}
    if targets is None:
        if target_map:
            targets=list(target_map)
        else:
            # All reference elements are required; intersecting only shared IDs
            # can silently hide missing moving elements and yield false PASS.
            targets=sorted(set().union(*(set(frame.get('elements',{})) for frame in rt.values())))
            if not targets:
                return {'schema_version':'0.1.0','verdict':'INCONCLUSIVE',
                        'reason':'Reference contains no observable elements',
                        'differences':[],'missing':[],'coverage':0,
                        'missing_reference_timestamps':absent_reference_times,
                        'missing_candidate_timestamps':absent_candidate_times}
    if not targets:
        return {'schema_version':'0.1.0','verdict':'INCONCLUSIVE',
                'reason':'Empty target selection', 'differences':[],'missing':[],
                'coverage':0,
                'missing_reference_timestamps':absent_reference_times,
                'missing_candidate_timestamps':absent_candidate_times}
    rv=reference['sampling']['viewport'];cv=candidate['sampling']['viewport']
    delta=[];samples=0;missing=[]
    for t in ts:
        for source_id in targets:
            dest_id=target_map.get(source_id,source_id)
            a=_norm(rt[t],source_id,rv);b=_norm(ct[t],dest_id,cv)
            if not a or not b:
                missing.append({'time_seconds':t,'reference_target':source_id,'candidate_target':dest_id})
                continue
            samples+=1
            base={'time_seconds':t,'reference_target':source_id,'candidate_target':dest_id}
            if mode=='state':
                for field in ('x','y','width','height'):
                    diff=abs(a['bbox'][field]-b['bbox'][field])
                    if diff>pos_tol:
                        delta.append({**base,'property':'bbox.'+field,
                                      'reference':round(a['bbox'][field],5),'candidate':round(b['bbox'][field],5),
                                      'deviation':round(diff,5),'tolerance':pos_tol})
            if mode in ('state','transform'):
                # A symmetrical object can rotate without changing its bbox.
                # Matrix terms recover rotation/scale/skew missing from box checks.
                if a['ctm'] is not None and b['ctm'] is not None:
                    for field in ('a','b','c','d'):
                        av=a['ctm'][field];bv=b['ctm'][field]
                        if abs(av-bv)>pos_tol:
                            delta.append({**base,'property':'ctm.'+field,
                                          'reference':round(av,5),'candidate':round(bv,5),
                                          'deviation':round(abs(av-bv),5),'tolerance':pos_tol})
                elif mode=='transform' or (a['ctm'] is None)!=(b['ctm'] is None):
                    missing.append({**base,'reason':'SVG transformation matrix unavailable'})
            if mode!='transform':
                d=abs(a['opacity']-b['opacity'])
                if d>opacity_tol:
                    delta.append({**base,'property':'opacity',
                              'reference':a['opacity'],'candidate':b['opacity'],
                              'deviation':round(d,5),'tolerance':opacity_tol})
            for field in ('visibility','display'):
                if a[field]!=b[field]:
                    delta.append({**base,'property':field,'reference':a[field],
                                  'candidate':b[field]})
    # Never certify empty evidence or an incomplete aligned timeline.
    # The legacy ignore_missing flag is intentionally not a bypass for PASS.
    if not samples:
        verdict='INCONCLUSIVE'
    elif delta or missing:
        verdict='FAIL'
    elif incomplete_times:
        verdict='INCONCLUSIVE'
    else:
        verdict='PASS'
    return {'schema_version':'0.1.0','verdict':verdict,'mode':mode,'compared_timestamps':ts,
            'targets':targets,'target_map':target_map,'coverage':samples,'missing':missing,'differences':delta,
            'missing_reference_timestamps':absent_reference_times,
            'missing_candidate_timestamps':absent_candidate_times,
            'thresholds':{'position_fraction_of_viewport':pos_tol,'opacity':opacity_tol},
            'method':('element-specific computed opacity + visibility; no geometry' if mode=='opacity' else
                      'relative SVG CTM linear coefficients (rotation, scale, skew)' if mode=='transform' else
                      'element-specific boxes, opacity, and relative SVG transform matrix, normalized where appropriate'),
            'limitations':['Equal samples do not prove identical behavior between timestamps',
                           'Opacity-only verification is unsuitable for movement or morph equivalence',
                           'Matching element names and geometry does not prove equivalent design intent',
                           'CSS fill/stroke colors and path shape topology are not scored',
                           'CTM translation may be reflected in the bounding box; CTM comparisons cover its rotation/scale/skew terms']}


def parse_mapping(s):
    result={}
    if not s:return result
    for pair in s.split(','):
        bits=pair.strip().split(':')
        if len(bits)!=2 or not all(bits):raise ValueError('--target-map must be ref-id:candidate-id,...')
        result[bits[0]]=bits[1]
    return result


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('reference',help='trace.json from reference')
    ap.add_argument('candidate',help='trace.json from candidate')
    ap.add_argument('--targets',help='Comma-separated SVG element IDs (same in both traces)')
    ap.add_argument('--target-map',help='Mapping ref-id:candidate-id,... for renamed targets')
    ap.add_argument('--mode',choices=['state','opacity','transform'],default='state')
    ap.add_argument('--position-tolerance',type=float,default=.035)
    ap.add_argument('--opacity-tolerance',type=float,default=.1)
    ap.add_argument('--out',help='Write comparison JSON')
    a=ap.parse_args(argv)
    if not (math.isfinite(a.position_tolerance) and 0<=a.position_tolerance<=1 and math.isfinite(a.opacity_tolerance) and 0<=a.opacity_tolerance<=1):ap.error('tolerances must be finite and within [0,1]')
    try:
        ref=json.loads(Path(a.reference).read_text(encoding='utf-8'))
        cand=json.loads(Path(a.candidate).read_text(encoding='utf-8'))
        result=compare(ref,cand,a.targets.split(',') if a.targets else None,a.position_tolerance,a.opacity_tolerance,
                       mode=a.mode,target_map=parse_mapping(a.target_map))
        if a.out:json_write(a.out,result)
        print('RESULT:',result['verdict'],'| compared:',result['coverage'],'| deviations:',len(result['differences']),
              '| missing:',len(result['missing']))
        if a.out:print('Report:',a.out)
        return 0 if result['verdict']=='PASS' else 1 if result['verdict']=='FAIL' else 2
    except (OSError,ValueError,KeyError) as exc:
        print('ERROR:',exc,file=sys.stderr);return 2

if __name__=='__main__':sys.exit(main())
