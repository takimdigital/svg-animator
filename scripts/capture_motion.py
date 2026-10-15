#!/usr/bin/env python3
"""Collect browser-observed SVG motion states and optional PNG evidence frames.

Requires Playwright and an installed Chromium browser. Does not fetch remote assets,
execute SVG scripts or allow the SVG to navigate. Deterministic timestamps use
SVG setCurrentTime and the Web Animations API, not wall-clock frame sampling.
"""
from __future__ import annotations
import argparse
import json
import math
import shutil
import sys
from pathlib import Path
from motion_dna_core import inspect_svg, json_write, safe_svg

PROBE = r"""() => {
  const svg = document.querySelector('svg');
  const all = Array.from(svg.querySelectorAll('*'));
  all.unshift(svg);
  function ref(el) { return el.id || '@' + (all.indexOf(el)-1); }
  const result = {};
  for (const el of all) {
    if (['animate','animateMotion','animateTransform','set','style','defs','clipPath','mask','filter','linearGradient','radialGradient','stop','marker','pattern','title','desc'].includes(el.localName)) continue;
    const cs = getComputedStyle(el);
    let rect; try { rect = el.getBoundingClientRect(); } catch(e) { continue; }
    const bb = {x: rect.x, y:rect.y, width:rect.width, height:rect.height};
    const matrix = cs.transform === 'none' ? null : cs.transform;
    // SVG CTM records SMIL animateTransform and SVG-specific transforms even
    // when computed CSS transform is `none`. Express it in root SVG units.
    let ctm = null;
    try {
      const rootMatrix = svg.getScreenCTM();
      const targetMatrix = el.getScreenCTM();
      if (rootMatrix && targetMatrix) {
        const m = rootMatrix.inverse().multiply(targetMatrix);
        ctm = {a:m.a,b:m.b,c:m.c,d:m.d,e:m.e,f:m.f};
      }
    } catch (_) {}
    result[ref(el)] = {tag:el.localName, opacity:Number(cs.opacity),
      transform:matrix, ctm:ctm, fill:cs.fill, stroke:cs.stroke,
      bbox:Object.fromEntries(Object.entries(bb).map(([k,v])=>[k,Math.round(v*10000)/10000])),
      visibility:cs.visibility, display:cs.display};
  }
  return result;
}"""

SEEK = r"""(t) => {
  const s = document.querySelector('svg');
  s.pauseAnimations();
  s.setCurrentTime(t);
  for (const a of document.getAnimations({subtree:true})) {
    try { a.pause(); a.currentTime = t*1000; } catch(e) {}
  }
}"""


def timepoints(info, samples, times):
    if not 2 <= samples <= 80: raise ValueError('samples must be between 2 and 80')
    if times:
        seq = [float(x) for x in times.split(',') if x.strip()]
    else:
        ends = []
        for a in info['animations']:
            d = a['duration_seconds']; b = a['begin_seconds']
            if d is not None and d > 0 and b is not None:
                ends.append(min(max(0,b) + d,60.0))
        horizon = min(max(ends or [4.0]),60.0)
        seq = [horizon * i / (samples-1) for i in range(samples)]
    if not seq or any(not math.isfinite(t) or t<0 or t>60 for t in seq):
        raise ValueError('Times must be finite and within 0 to 60 seconds')
    return sorted(set(round(t,5) for t in seq))


def _browser(p,browser_path=None):
    launch={'headless':True}
    executable=browser_path or (shutil.which('chromium') or shutil.which('chromium-browser'))
    if executable:launch['executable_path']=executable
    return p.chromium.launch(**launch)


def capture(svg, out_dir, samples=9, times=None, width=900, screenshots=True, browser_path=None):
    from playwright.sync_api import sync_playwright
    src=Path(svg).read_text(encoding='utf-8-sig')
    safe_svg(src)  # refuse scripts, remote media, external links and entities
    info=inspect_svg(svg)
    stamps=timepoints(info,samples,times)
    out=Path(out_dir);out.mkdir(parents=True,exist_ok=True)
    # Use inline document so Playwright can seek SVG/SMIL and CSS keyframes.
    src=__import__('re').sub(r'<\?xml[^>]*\?>','',src)
    html=("<!doctype html><html><head><meta charset='utf-8'></head>"
          "<body style='margin:0;padding:0;overflow:hidden;background:transparent'>"+src+"</body></html>")
    vb=info['canvas']['viewBox']
    aspect=0.6
    if vb:
        try:
            nums=[float(x) for x in __import__('re').split(r'[\s,]+',vb.strip())]
            if len(nums)==4 and nums[2]>0 and nums[3]>0:aspect=nums[3]/nums[2]
        except ValueError:pass
    h=max(100,min(3000,round(width*aspect)))
    evidence=[];notes=[]
    with sync_playwright() as p:
        browser=_browser(p,browser_path)
        try:
            context=browser.new_context(viewport={'width':width,'height':h}, device_scale_factor=1, service_workers='block')
            context.route('**/*',lambda route: route.abort())  # page.set_content has no document request
            page=context.new_page()
            page.set_content(html,wait_until='domcontentloaded')
            page.evaluate('''() => {const s=document.querySelector('svg');s.setAttribute('width','100%');s.setAttribute('height','100%');s.pauseAnimations();s.setCurrentTime(0);}''')
            for frame,t in enumerate(stamps):
                page.evaluate(SEEK,t)
                page.wait_for_timeout(45)
                state=page.evaluate(PROBE)
                if not state:notes.append('No observable drawable elements at '+str(t)+'s')
                shot=None
                if screenshots:
                    shot='frame_%03d_t%.3fs.png'%(frame,t)
                    page.screenshot(path=str(out/shot))
                evidence.append({'time_seconds':t,'elements':state,'screenshot':shot})
            context.close()
        finally:browser.close()
    # A trace is evidence of *observed computed geometry*, not of designer intent.
    report={'schema_version':'0.1.0','source':info['source'],'canvas':info['canvas'],
            'sampling':{'times_seconds':stamps,'viewport':{'width':width,'height':h},
                        'seek':'SMIL setCurrentTime + Web Animations currentTime',
                        'network':'blocked','scripted_svg':'refused'},
            'frames':evidence,'notes':notes,'anomalies':[]}
    # Scoped initial-state check: only if explicit delayed SMIL animation targets an element.
    initial=evidence[0]['elements'] if evidence and stamps[0]==0 else {}
    for a in info['animations']:
        if a['mechanism']=='SMIL' and (a['begin_seconds'] or 0)>0 and a['target'] in initial:
            state=initial[a['target']]
            if state['opacity'] >0.02 and state['display']!='none' and state['visibility']!='hidden' and a['motion_type'] in ('path-travel','opacity'):
                report['anomalies'].append({'code':'possible-parked-element','target':a['target'],
                  'time_seconds':0,'observed_opacity':state['opacity'],
                  'note':'Delayed SMIL effect has visible target at 0s; inspect design intent before treating as defect'})
    json_write(out/'trace.json',report)
    return report


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('svg')
    ap.add_argument('--out-dir',default='motion-dna-evidence')
    ap.add_argument('--samples',type=int,default=9)
    ap.add_argument('--times',help='Comma-separated timestamps in seconds (0..60)')
    ap.add_argument('--width',type=int,default=900)
    ap.add_argument('--no-images',action='store_true')
    ap.add_argument('--browser-path',help='Custom Chromium executable')
    a=ap.parse_args(argv)
    if a.samples<2 or a.samples>80:ap.error('--samples must be between 2 and 80')
    if a.width<200 or a.width>2400:ap.error('--width must be between 200 and 2400')
    try:
        result=capture(a.svg,a.out_dir,a.samples,a.times,a.width,not a.no_images,a.browser_path)
        print('Captured %d states, %d possible anomalies -> %s/trace.json' % (
              len(result['frames']),len(result['anomalies']),a.out_dir))
        return 0
    except ImportError:
        print('Install Playwright: pip install playwright && python -m playwright install chromium',file=sys.stderr)
        return 2
    except Exception as e:
        print('Motion capture failed:',e,file=sys.stderr)
        return 2

if __name__=='__main__':sys.exit(main())
