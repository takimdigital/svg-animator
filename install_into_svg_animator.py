#!/usr/bin/env python3
"""Install Motion DNA as an optional, additive SVG Animator route.

Usage: python install_into_svg_animator.py /path/to/svg-animator [--dry-run] [--force]
"""
from __future__ import annotations
import argparse
import shutil
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
COPY=[
    'install_into_svg_animator.py',
    'scripts/motion_dna_core.py', 'scripts/inspect_motion.py',
    'scripts/capture_motion.py','scripts/compare_motion.py',
    'scripts/reconstruct_motion.py','scripts/investigate_motion.py',
    'references/motion-dna.md','tests/test_motion_dna.py',
    'schemas/motion-dna.schema.json','schemas/motion-trace.schema.json','schemas/motion-comparison.schema.json',
]
COPY += [str(p.relative_to(HERE)) for p in sorted((HERE/'tests/fixtures/motion-dna').glob('*.svg'))]

INSERTIONS={
'SKILL.md': '''\n## Optional Route E — Motion DNA: Investigate a reference animation\n\nIf the user supplies a **self-contained animated SVG** and asks to understand its motion, derive a motion recipe, or create an original variation, read `references/motion-dna.md` first.\n\n1. `python scripts/inspect_motion.py reference.svg --out run/motion-dna.json` — structural evidence and unknowns.\n2. `python scripts/capture_motion.py reference.svg --out-dir run/motion-evidence` — observe sampled browser motion, if Playwright is installed.\n3. Reconstruct only a **supported** pattern with `scripts/reconstruct_motion.py`, otherwise use the existing generator/hand-build route to interpret the evidence.\n4. Run the **existing** lint, browser `verify.py`, frame rendering and visual review on the output. `compare_motion.py` checks only declared, aligned properties; an opacity PASS is not proof of motion/shape/visual equivalence.\n\nThis route is optional. Never replace the original BRIEF → ROUTE → SPEC → BUILD → LINT → FRAMES → FIX → DELIVER path for normal generation.\n''',
'references/CAPABILITIES.md': '''\n## Optional experimental route: Motion DNA (v0.1)\n\n- Input: local self-contained SVG animation using simple SMIL/CSS (not video, GIF, website URLs or arbitrary scripting).\n- Tools: `scripts/inspect_motion.py`, `capture_motion.py`, `compare_motion.py`, `reconstruct_motion.py`, `investigate_motion.py`.\n- Detects: authored keyframes, timing, path signatures, initial visibility candidates, simple stagger groups.\n- Browser: captures explicit timestamp evidence of computed opacity/geometry and frame PNGs.\n- Variation support: 2–8 repeating staggered opacity targets with shared duration, or one repeating SMIL rotation. Other transformations remain hand-build tasks.\n- Limits: no proof of exact design intent, continuous behavior or visual equivalence; no automatic reconstruction for motion paths, path morphs, complex CSS or videos.\n- Protocol, CLI commands, security posture: `references/motion-dna.md`.\n''',
'README.md': '''\n## Optional Motion DNA investigation extension\n\nSVG Animator can optionally **inspect, observe, compare and reinterpret** an existing self-contained animated SVG. `scripts/inspect_motion.py` generates an evidence-backed motion JSON report; `scripts/capture_motion.py` records browser states and screenshots at explicit timestamps; `scripts/reconstruct_motion.py` produces an original variation for limited pulse/rotation recipes. It does not replace any of the 38 existing generators or their lint/verify pipeline.\n\n```bash\npython scripts/investigate_motion.py reference.svg --out-dir ./motion-investigation --samples 13\n```\n\nRead `references/motion-dna.md` for the agent workflow, supported patterns and honest verification limits.\n'''
}
START='<!-- MOTION-DNA-EXTENSION-START -->'
END='<!-- MOTION-DNA-EXTENSION-END -->'


def plan(destination,force=False,dry_run=False):
    dest=Path(destination)
    if not (dest/'SKILL.md').is_file() or not (dest/'scripts').is_dir() or not (dest/'references').is_dir():
        raise ValueError('Destination does not look like an svg-animator clone (missing SKILL.md/scripts/references)')
    actions=[]
    for filename in COPY:
        source=HERE/filename;target=dest/filename
        if target.exists():
            if target.read_bytes()==source.read_bytes():actions.append(('unchanged',filename))
            elif force:actions.append(('replace-with-backup',filename))
            else:raise ValueError(f'Collision at {filename}. Use --force after reviewing diff.')
        else:actions.append(('copy',filename))
    for filename, content in INSERTIONS.items():
        file=dest/filename
        if not file.exists():raise ValueError(f'Documentation target {filename} missing')
        orig=file.read_text(encoding='utf-8')
        block=START+'\n'+content.strip()+'\n'+END
        if START in orig:
            if END not in orig:raise ValueError(f'Unterminated Motion DNA documentation marker in {filename}')
            existing=orig.split(START,1)[1].split(END,1)[0]
            if existing.strip()==content.strip():actions.append(('unchanged',filename))
            elif force:actions.append(('update-doc-with-backup',filename))
            else:raise ValueError(f'Existing Motion DNA block in {filename} differs. Use --force.')
        else:actions.append(('append-doc',filename))
    # Refuse all foreseeable backup collisions before mutating any file.
    # This prevents half-installed results when --force is used.
    if not dry_run:
        for action, filename in actions:
            if action in ('replace-with-backup','update-doc-with-backup'):
                target=dest/filename
                backup=target.with_name(target.name+'.motion-dna.bak')
                if backup.exists():
                    raise ValueError(f'Backup {backup} already exists; remove or preserve it before retrying')
    for action, filename in actions:
        print(('%s: '%('WOULD' if dry_run else 'DO'))+action+' '+filename)
        if dry_run or action=='unchanged':continue
        target=dest/filename
        if action in ('replace-with-backup','update-doc-with-backup'):
            backup=target.with_name(target.name+'.motion-dna.bak')
            if backup.exists():raise ValueError(f'Backup {backup} exists; preserve it before continuing')
            shutil.copy2(target,backup)
        if action in ('copy','replace-with-backup'):
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(HERE/filename,target)
        elif action=='append-doc':
            with target.open('a',encoding='utf-8') as f:f.write('\n'+START+'\n'+INSERTIONS[filename].strip()+'\n'+END+'\n')
        elif action=='update-doc-with-backup':
            original=target.read_text(encoding='utf-8')
            beginning, tail=original.split(START,1)
            _,ending=tail.split(END,1)
            target.write_text(beginning+START+'\n'+INSERTIONS[filename].strip()+'\n'+END+ending,encoding='utf-8')
    return actions


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('repo',help='Existing svg-animator clone')
    ap.add_argument('--dry-run',action='store_true')
    ap.add_argument('--force',action='store_true',help='Replace collisions, keeping backup copies')
    a=ap.parse_args()
    try:
        actions=plan(a.repo,force=a.force,dry_run=a.dry_run)
        print('\n%s: %d extension file/document actions' % ('DRY RUN' if a.dry_run else 'INSTALLED',len(actions)))
    except (ValueError,OSError) as exc:
        print('ERROR:',exc,file=sys.stderr);return 2
    return 0

if __name__=='__main__':sys.exit(main())
