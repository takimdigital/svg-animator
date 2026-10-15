#!/usr/bin/env python3
"""Motion DNA: safe, evidence-based inspection of authored SVG/SMIL/CSS motion.

No dependencies beyond the stdlib and defusedxml (the latter is optional). This
module does not execute arbitrary SVG or infer intent from pixels.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path

VERSION = '0.1.0'
ANIM_TAGS = {'animate', 'animateTransform', 'animateMotion', 'set'}
_TIME = re.compile(r'^\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+))(ms|s)?\s*$', re.I)
_FLOAT = re.compile(r'^\s*[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?\s*$', re.I)
_KEYFRAMES = re.compile(r'@(?:-webkit-)?keyframes\s+([\w-]+)\s*\{', re.I)
_DECL = re.compile(r'(?:^|;)\s*([\w-]+)\s*:\s*([^;{}]+)')
_NUMS = re.compile(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?')
_PATH_CMDS = re.compile(r'[MmZzLlHhVvCcSsQqTtAa]')


def local(tag):
    return tag.rsplit('}', 1)[-1]


def seconds(value):
    """Parse literal clock durations. Event syncbases intentionally remain unknown."""
    m = _TIME.fullmatch(value or '')
    if not m:
        return None
    n = float(m.group(1))
    return round(n / 1000 if (m.group(2) or '').lower() == 'ms' else n, 6)


def split_values(s):
    return [part.strip() for part in s.split(';')] if s is not None else []


def parse_declarations(s):
    return {m.group(1).lower(): m.group(2).strip() for m in _DECL.finditer(s or '')}


def safe_svg(source):
    """Refuse active/external content before any optional browser execution."""
    issues = []
    if re.search(r'<!\s*(?:DOCTYPE|ENTITY)\b', source, re.I):
        raise ValueError('DTD / ENTITY declarations are not permitted in investigated SVG')
    try:
        root = ET.fromstring(source)
    except ET.ParseError as exc:
        raise ValueError('Invalid SVG XML: ' + str(exc)) from exc
    if local(root.tag) != 'svg':
        raise ValueError('Input root must be <svg>')
    for el in root.iter():
        tag = local(el.tag).lower()
        if tag in ('script', 'foreignobject'):
            raise ValueError(f'Active SVG <{tag}> is not accepted by Motion DNA')
        for k, v in el.attrib.items():
            attr = local(k).lower()
            if attr.startswith('on') and len(attr) > 2:
                raise ValueError(f'Event handler {attr} is not permitted')
            if attr in ('href', 'src') and v.strip() and not v.strip().startswith('#'):
                raise ValueError(f'External resource {attr}={v[:100]!r} is not permitted')
            if re.search(r'url\s*\(\s*[\'\"]?\s*(?!#)[a-z]+:', v, re.I):
                raise ValueError('External url() reference not permitted')
    if re.search(r'@import\b', source, re.I):
        raise ValueError('CSS @import is not permitted')
    # Some CSS url() syntax is outside attributes; reject only external URL forms.
    if re.search(r'url\s*\(\s*[\'\"]?\s*(?:https?:|data:|file:|//)', source, re.I):
        raise ValueError('External CSS url() reference is not permitted')
    return root, issues


def css_keyframes(css):
    """Read literal @keyframes blocks with brace-aware scanning (not a CSS engine)."""
    result = {}
    for match in _KEYFRAMES.finditer(css):
        start = match.end(); depth = 1; cursor = start
        while cursor < len(css) and depth:
            if css[cursor] == '{': depth += 1
            elif css[cursor] == '}': depth -= 1
            cursor += 1
        if depth:
            continue
        block = css[start:cursor-1]
        frames = []
        for fr in re.finditer(r'((?:from|to|(?:\d+(?:\.\d+)?%)|\s|,)+)\{([^{}]*)\}', block, re.I):
            offsets = []
            for label in fr.group(1).split(','):
                label = label.strip().lower()
                if label == 'from': offsets.append(0)
                elif label == 'to': offsets.append(1)
                elif label.endswith('%'):
                    try: offsets.append(round(float(label[:-1]) / 100, 5))
                    except ValueError: pass
            for offset in offsets:
                if 0 <= offset <= 1:
                    frames.append({'offset': offset, 'properties': parse_declarations(fr.group(2))})
        result[match.group(1)] = sorted(frames, key=lambda f: f['offset'])
    return result


def css_rules(css):
    # Remove keyframe blocks before selecting rules to avoid treating "to" as selector.
    spans = []
    for m in _KEYFRAMES.finditer(css):
        dep = 1; i = m.end()
        while i < len(css) and dep:
            dep += (css[i] == '{') - (css[i] == '}')
            i += 1
        spans.append((m.start(), i))
    for a, b in reversed(spans):
        css = css[:a] + (' ' * (b-a)) + css[b:]
    return [(s.strip(), parse_declarations(d)) for s,d in re.findall(r'([^{}]+)\{([^{}]*)\}', css)
            if 'animation' in d.lower()]


def select_simple(selector, el):
    """Only basic selectors; complex selectors are classified as unknown."""
    s = selector.strip()
    if s.startswith('#') and re.fullmatch(r'#[\w-]+', s):
        return el.get('id') == s[1:]
    if s.startswith('.') and re.fullmatch(r'\.[\w-]+', s):
        return s[1:] in (el.get('class') or '').split()
    if re.fullmatch(r'[a-zA-Z][\w-]*', s):
        return local(el.tag) == s
    return False


def css_animation(decls):
    """Parse simple CSS animation shorthand or longhands, preserving uncertainty."""
    names = (decls.get('animation-name') or '').split(',')
    durations = (decls.get('animation-duration') or '').split(',')
    delays = (decls.get('animation-delay') or '').split(',')
    repeats = (decls.get('animation-iteration-count') or '').split(',')
    timing = decls.get('animation-timing-function')
    if 'animation' in decls and not decls.get('animation-name'):
        # Supports the common `bounce 1.2s ease-in-out .15s infinite` form.
        parts = [x.strip() for x in decls['animation'].split(',')]
        result = []
        for part in parts:
            toks = part.split(); times=[]; name=None; count='1'; ease=None
            for tok in toks:
                if seconds(tok) is not None: times.append(seconds(tok))
                elif tok in ('infinite',): count = tok
                elif tok in ('linear','ease','ease-in','ease-out','ease-in-out','step-start','step-end') or tok.startswith(('steps(', 'cubic-bezier(')):
                    ease = tok
                elif tok not in ('normal', 'alternate', 'reverse', 'alternate-reverse', 'both','forwards','backwards','none', 'running', 'paused') and not re.fullmatch(r'\d+(?:\.\d+)?', tok):
                    name = tok
                elif re.fullmatch(r'\d+(?:\.\d+)?', tok): count = tok
            if name:
                result.append({'name':name, 'dur':times[0] if times else None,
                               'begin':times[1] if len(times)>1 else 0.0,
                               'repeat':count, 'easing':ease})
        return result
    results = []
    for i,name in enumerate(names):
        name=name.strip()
        if not name or name=='none':continue
        def get(arr, fallback):
            return arr[i % len(arr)].strip() if arr and arr[0].strip() else fallback
        results.append({'name':name, 'dur':seconds(get(durations,'')),
                        'begin':seconds(get(delays,'0s')),
                        'repeat':get(repeats,'1'), 'easing':timing})
    return results


def path_signature(d):
    return ''.join(_PATH_CMDS.findall(d or ''))


def motion_type(tag, attr, values):
    t = (attr or '').lower()
    if tag == 'animateMotion': return 'path-travel'
    if t == 'd': return 'morph'
    if t in ('opacity', 'fill-opacity','stroke-opacity'):return 'opacity'
    if t == 'transform':return 'transform'
    if t in ('x','y','cx','cy','dx','dy'):return 'translation'
    if t in ('r','rx','ry','width','height'):return 'geometry'
    if t in ('fill', 'stroke','color'):return 'color'
    if t == 'viewbox':return 'viewport'
    return 'property-change'


def _element_ref(el, index):
    return el.get('id') or f'@{index}'


def inspect_svg(path):
    path=Path(path)
    blob=path.read_bytes()
    if len(blob)>4_000_000:raise ValueError('SVG exceeds 4 MB investigation safety limit')
    text=blob.decode('utf-8-sig')
    root,_=safe_svg(text)
    nodes=list(root.iter()); node_ids={id(el): i-1 for i,el in enumerate(nodes)}
    parents={id(child):parent for parent in nodes for child in parent}
    css='\n'.join((e.text or '') for e in nodes if local(e.tag)=='style')
    keyframes=css_keyframes(css); rules=css_rules(css)
    warnings=[]; unknowns=[]; issues=[]; animations=[]
    durations=[]; id_counts={}
    for el in nodes:
        if el.get('id'): id_counts[el.get('id')]=id_counts.get(el.get('id'),0)+1
    for name,c in id_counts.items():
        if c>1:warnings.append(f'Duplicate id {name!r}; target identity may be ambiguous')
    for el in nodes:
        tag=local(el.tag)
        if tag not in ANIM_TAGS:continue
        owner=parents.get(id(el))
        if owner is None: owner=root
        href=(el.get('href') or el.get('{http://www.w3.org/1999/xlink}href'))
        if href and href.startswith('#'):
            owner=next((e for e in nodes if e.get('id')==href[1:]), owner)
        ownerid=_element_ref(owner,node_ids[id(owner)])
        dur=seconds(el.get('dur'))
        beginval=el.get('begin', '0s')
        begin=seconds(beginval)
        values=split_values(el.get('values'))
        attr=el.get('attributeName') or ('transform' if tag=='animateMotion' else None)
        typ=motion_type(tag,attr,values)
        if tag=='animateTransform':typ=el.get('type','transform').lower()
        data={'index':len(animations),'target':ownerid,'target_tag':local(owner.tag),
              'mechanism':'SMIL','tag':tag,'property':attr,'motion_type':typ,
              'begin_seconds':begin,'duration_seconds':dur, 'repeat':el.get('repeatCount','1'),
              'easing':{'calcMode':el.get('calcMode','linear' if tag=='animateMotion' else 'default'),
                        'keySplines':split_values(el.get('keySplines'))},
              'values':values, 'from':el.get('from'), 'to':el.get('to'), 'by':el.get('by'),
              'keyTimes':split_values(el.get('keyTimes')),
              'path':el.get('path') if tag=='animateMotion' else None,
              'source':{'element':ownerid,'animation_id':el.get('id'), 'attributeName':attr}}
        if dur is not None and dur>0:durations.append(dur)
        if begin is None:
            unknowns.append(f'{ownerid}: event/sync-based begin {beginval!r} not resolved statically')
        if dur is None and tag!='set':
            unknowns.append(f'{ownerid}: duration is unknown or event-driven')
        if tag=='animateMotion' and not (el.get('path') or any(local(x.tag)=='mpath' for x in el)):
            unknowns.append(f'{ownerid}: motion path may be supplied via values or other context')
        if typ=='morph' and len(values)>1:
            signatures=[path_signature(v) for v in values]
            data['path_signatures']=signatures
            data['compatible_commands']=all(s==signatures[0] for s in signatures)
            if not data['compatible_commands']:
                issues.append({'severity':'warning','type':'morph-signature-mismatch',
                               'target':ownerid,'message':'Morph paths have different command sequences and may snap'})
        if tag!='set' and begin is not None and begin>0:
            op=owner.get('opacity')
            try: visible=op is None or float(op)>0.02
            except ValueError:visible=True
            if visible and (attr=='opacity' or tag=='animateMotion'):
                issues.append({'severity':'warning','type':'potential-parked-element',
                               'target':ownerid,'message':'Positive begin with nonzero base opacity; confirm frame 0 in browser'})
        animations.append(data)
    for el in nodes:
        if local(el.tag) in ANIM_TAGS or local(el.tag) in ('style','defs'):continue
        declarations=parse_declarations(el.get('style'))
        for selector, attrs in rules:
            matched=False
            for part in selector.split(','):
                if select_simple(part,el):matched=True
                elif re.search(r'[>+~ :\[]', part):
                    if 'animation' in attrs or 'animation-name' in attrs:
                        msg=f'CSS selector {part.strip()!r} not resolved statically; browser observation required'
                        if msg not in unknowns:unknowns.append(msg)
            if matched:declarations={**attrs,**declarations}
        for a in css_animation(declarations):
            target=_element_ref(el,node_ids[id(el)])
            frames=keyframes.get(a['name'],[])
            props=sorted({p for kf in frames for p in kf['properties']})
            typ='transform' if 'transform' in props else 'opacity' if 'opacity' in props else 'css-keyframes'
            animations.append({'index':len(animations),'target':target,
              'target_tag':local(el.tag),'mechanism':'CSS','tag':'CSS','property':','.join(props) or None,
              'motion_type':typ,'begin_seconds':a['begin'],'duration_seconds':a['dur'],
              'repeat':a['repeat'],'easing':a['easing'],'name':a['name'],'frames':frames,
              'source':{'element':target,'keyframes_name':a['name']}})
            if a['dur'] is not None and a['dur']>0: durations.append(a['dur'])
            if not frames:unknowns.append(f'{target}: keyframes for {a["name"]!r} not resolved statically')
    # Approximate group based on shared mechanism/property/duration; zero/negative offsets included.
    groups=[]
    bykey={}
    for a in animations:
        if a.get('begin_seconds') is None or a.get('duration_seconds') is None:continue
        k=(a['mechanism'],a['motion_type'],a['duration_seconds'])
        bykey.setdefault(k,[]).append(a)
    for (mechanism,kind,dur),matches in bykey.items():
        if len({a['target'] for a in matches})<2:continue
        begins=sorted({a['begin_seconds'] for a in matches})
        group={'mechanism':mechanism,'motion_type':kind,'duration_seconds':dur,
               'targets':[a['target'] for a in matches], 'begins_seconds':[a['begin_seconds'] for a in matches],
               'sequence':'staggered' if len(begins)>1 else 'simultaneous'}
        if len(begins)>1:
            gaps=[round(b-a,5) for a,b in zip(begins,begins[1:])]
            group['stagger_seconds']=gaps[0] if max(gaps)-min(gaps)<0.00001 else None
        groups.append(group)
    view_box=root.get('viewBox')
    data={'schema_version':'0.1.0','tool_version':VERSION,
          'source':{'file':path.name,'sha256':hashlib.sha256(blob).hexdigest(),
                    'bytes':len(blob)},
          'canvas':{'viewBox':view_box,'width':root.get('width'), 'height':root.get('height')},
          'summary':{'animation_count':len(animations),'target_count':len(set(a['target'] for a in animations)),
                     'methods':sorted(set(a['mechanism'] for a in animations)),
                     'longest_declared_duration_seconds':max(durations) if durations else None,
                     'loop_seconds':'unknown',
                     'loop_reason':'Multiple animations may have different duration/repeat schedules'},
          'animations':animations,'choreography':groups,
          'issues':issues,'warnings':warnings,'unknowns':unknowns,
          'evidence':{'kind':'source-xml','hash':hashlib.sha256(blob).hexdigest(), 'runtime_observed':False}}
    if len(animations)==1 and animations[0]['duration_seconds'] and animations[0]['repeat']=='indefinite':
        data['summary']['loop_seconds']=animations[0]['duration_seconds']
        data['summary']['loop_reason']='Single indefinitely repeating animation'
    return data


def json_write(path, obj):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + '\n',encoding='utf-8')


def palette(data):
    return ' · '.join(f'{k}:{v}' for k,v in sorted(data.items()))
