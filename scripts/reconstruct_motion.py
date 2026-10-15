#!/usr/bin/env python3
"""Generate an original SVG variation from supported Motion DNA patterns.

MVP recipes: staggered opacity pulse, single indefinite rotation. Unsupported
patterns are refused rather than being hallucinated. This is not a general SVG
replicator and intentionally does not copy geometry from references.
"""
from __future__ import annotations
import argparse
import html
import json
import math
import sys
from pathlib import Path

SHAPES={'circle':'<circle cx="0" cy="0" r="20"/>',
        'diamond':'<path d="M0 -23 L23 0 L0 23 L-23 0 Z"/>',
        'square':'<rect x="-18" y="-18" width="36" height="36" rx="5"/>',
        'star':'<path d="M0 -24 L7 -7 L25 -7 L11 4 L16 22 L0 12 L-16 22 L-11 4 L-25 -7 L-7 -7 Z"/>'}


def svg_color(s):
    import re
    if not re.fullmatch(r'#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?',s):
        raise ValueError('Color must be #RGB or #RRGGBB')
    return s


def motion_to_svg(data, shape='diamond', color='#4263EB', title='Motion study'):
    if shape not in SHAPES:raise ValueError('Unsupported shape')
    svg_color(color)
    anims=data.get('animations',[])
    # Supported pattern: one indefinite opacity animation per distinct target
    pulses=[a for a in anims if a['motion_type']=='opacity' and a['mechanism']=='SMIL'
            and a.get('duration_seconds') and a.get('repeat')=='indefinite']
    unique={a['target']:a for a in pulses}
    if len(unique)>=2 and len(unique)<=8:
        if any(a.get('easing',{}).get('calcMode') not in ('linear','default',None) or a.get('easing',{}).get('keySplines') for a in pulses):
            raise ValueError('Spline/discrete/paced opacity timing is not faithfully supported')
        if len(unique)!=len(pulses) or len(anims)!=len(pulses):
            raise ValueError('Source contains overlapping or unsupported additional animations; cannot transfer faithfully')
        pulses=sorted(unique.values(),key=lambda a:(a.get('begin_seconds') or 0,a['target']))
        if len({a['duration_seconds'] for a in pulses})!=1:
            raise ValueError('Staggered pulses must share one duration for v0.1 reconstruction')
        dur=pulses[0]['duration_seconds']
        if any(a.get('begin_seconds') is None for a in pulses):
            raise ValueError('Event-driven begin is not supported')
        width=max(260,len(pulses)*74+48);height=150
        shapes=[]
        for i,a in enumerate(pulses):
            x=width*(i+1)/(len(pulses)+1)
            delay=a['begin_seconds']
            # Delayed elements have base opacity 0; no parked-visible frame.
            offset=delay
            vals=a.get('values') or []
            if not vals or any(not _is_number(v) for v in vals):vals=['0.4','1','0.4']
            values=';'.join(vals)
            kt=a.get('keyTimes') or []
            if len(kt)!=len(vals) or any(not _is_number(k) for k in kt):
                kt=[_fmt(j/(len(vals)-1)) for j in range(len(vals))]
            key_times=';'.join(kt)
            shapes.append('''  <g id="motion-%s" transform="translate(%s 75)" fill="%s" opacity="0">\n    %s\n    <animate attributeName="opacity" values="%s" keyTimes="%s" dur="%ss" begin="%ss" repeatCount="indefinite"/>\n  </g>'''%(i+1,_fmt(x),color,SHAPES[shape],values,key_times,_fmt(dur),_fmt(offset)))
        return _wrap(width,height,title,shapes,'staggered-opacity-pulse',{'source_motion':'extracted per-element timing and values','new_geometry':shape})
    rotations=[a for a in anims if a['mechanism']=='SMIL' and a['motion_type']=='rotate'
               and a.get('duration_seconds') and a.get('repeat')=='indefinite']
    if len(rotations)==1:
        if len(anims)!=1:
            raise ValueError('Rotation recipe requires exactly one source animation')
        a=rotations[0];dur=a['duration_seconds']
        if a.get('from') != '0' or a.get('to') != '360' or a.get('values') or a.get('by'):
            raise ValueError('Rotation recipe only supports an explicit 0-to-360 degree full turn')
        if a.get('easing',{}).get('calcMode') not in ('linear','default',None) or a.get('easing',{}).get('keySplines'):
            raise ValueError('Nonlinear rotation easing is not supported in this variation recipe')
        shape_code=SHAPES[shape]
        rotation=('''  <g transform="translate(150 90)">\n    <g fill="%s">%s\n      <animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="%ss" repeatCount="indefinite"/>\n    </g>\n  </g>'''%(color,shape_code,_fmt(dur)))
        return _wrap(300,180,title,[rotation],'single-rotation',{'source_motion':'extracted rotation period','new_geometry':shape})
    raise ValueError('No supported pattern: MVP handles 2-8 SMIL indefinite opacity pulses or one SMIL indefinite rotation')


def _is_number(v):
    try:
        return math.isfinite(float(v)) and 0<=float(v)<=1
    except (ValueError,TypeError):return False


def _fmt(n):return ('%.5f'%n).rstrip('0').rstrip('.') if float(n)!=0 else '0'


def _wrap(w,h,title,parts,recipe,provenance):
    return '''<svg xmlns="http://www.w3.org/2000/svg" width="%s" height="%s" viewBox="0 0 %s %s" role="img" aria-label="%s">
  <title>%s</title>
  <desc>Original %s variation from a Motion DNA timing specification; geometry independently drawn.</desc>
  <rect x="0" y="0" width="%s" height="%s" fill="#101828" rx="15"/>
%s
</svg>
'''%(w,h,w,h,html.escape(title,quote=True),html.escape(title),recipe,w,h,'\n'.join(parts))


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('motion_json')
    ap.add_argument('--out',required=True)
    ap.add_argument('--shape',choices=sorted(SHAPES),default='diamond')
    ap.add_argument('--color',default='#4263EB')
    ap.add_argument('--title',default='Motion DNA original variation')
    a=ap.parse_args(argv)
    try:
        data=json.loads(Path(a.motion_json).read_text(encoding='utf-8'))
        svg=motion_to_svg(data,a.shape,a.color,a.title)
        Path(a.out).parent.mkdir(parents=True,exist_ok=True)
        Path(a.out).write_text(svg,encoding='utf-8')
        print('Generated:',a.out)
    except (OSError, ValueError, KeyError) as exc:
        print('RECONSTRUCTION UNSUPPORTED:',exc,file=sys.stderr)
        return 2
    return 0

if __name__=='__main__':sys.exit(main())
