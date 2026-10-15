"""Stdlib regression suite; browser-specific tests skip if Chromium unavailable."""
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from motion_dna_core import inspect_svg, safe_svg, seconds, css_keyframes, css_animation, json_write
from compare_motion import compare
from capture_motion import capture, timepoints
from reconstruct_motion import motion_to_svg
sys.path.insert(0,str(ROOT))
from install_into_svg_animator import plan
FIX=ROOT/'tests/fixtures/motion-dna'


def browser_available():
    # CI playwright install chromium supplies a browser in Playwright's cache,
    # not necessarily one named /usr/bin/chromium.
    if shutil.which('chromium') or shutil.which('chromium-browser'):
        return True
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            return Path(p.chromium.executable_path).is_file()
    except Exception:
        return False

BROWSER_AVAILABLE = browser_available()

class MotionDNATests(unittest.TestCase):
    def test_time_units(self):
        self.assertEqual(seconds('250ms'),0.25)
        self.assertEqual(seconds('-1.5s'),-1.5)
        self.assertEqual(seconds('2'),2)
        self.assertIsNone(seconds('click+2s'))

    def test_refuse_active_svg(self):
        bad=['<svg><script>alert(1)</script></svg>',
             '<svg onload="alert(1)"/>',
             '<!DOCTYPE svg [ <!ENTITY x SYSTEM "file:///etc/passwd"> ]><svg/>',
             '<svg><image href="https://example.com/secret.svg"/></svg>',
             '<svg><foreignObject/></svg>']
        for b in bad:
            with self.subTest(b=b):
                with self.assertRaises(ValueError):safe_svg(b)

    def test_stagger_detected(self):
        a=inspect_svg(FIX/'staggered-pulse.svg')
        self.assertEqual(a['summary']['animation_count'],3)
        self.assertEqual(a['summary']['target_count'],3)
        self.assertEqual(a['choreography'][0]['sequence'],'staggered')
        self.assertAlmostEqual(a['choreography'][0]['stagger_seconds'],0.15)
        self.assertEqual(a['summary']['longest_declared_duration_seconds'],1.2)

    def test_source_evidence(self):
        a=inspect_svg(FIX/'staggered-pulse.svg')
        self.assertEqual(len(a['source']['sha256']),64)
        self.assertFalse(a['evidence']['runtime_observed'])

    def test_rotation(self):
        a=inspect_svg(FIX/'rotation.svg')
        self.assertEqual(a['animations'][0]['motion_type'],'rotate')
        self.assertEqual(a['summary']['loop_seconds'],2)

    def test_morph_signature(self):
        a=inspect_svg(FIX/'morph.svg')
        self.assertTrue(a['animations'][0]['compatible_commands'])
        self.assertEqual(a['animations'][0]['motion_type'],'morph')

    def test_morph_mismatch(self):
        svg='<svg xmlns="http://www.w3.org/2000/svg"><path><animate attributeName="d" values="M0 0 L2 2 Z;M0 0 C1 2 3 4 5 6 Z" dur="1s"/></path></svg>'
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'m.svg';p.write_text(svg)
            a=inspect_svg(p)
        self.assertFalse(a['animations'][0]['compatible_commands'])
        self.assertEqual(a['issues'][0]['type'],'morph-signature-mismatch')

    def test_parked_warning(self):
        a=inspect_svg(FIX/'broken-parked.svg')
        self.assertEqual(a['issues'][0]['type'],'potential-parked-element')

    def test_css_keyframes_and_rule(self):
        a=inspect_svg(FIX/'css-bounce.svg')
        self.assertEqual(a['summary']['animation_count'],2)
        self.assertTrue(all(x['mechanism']=='CSS' for x in a['animations']))
        self.assertEqual(a['animations'][1]['begin_seconds'],0.15)
        self.assertEqual(a['animations'][0]['frames'][1]['offset'],0.5)

    def test_sample_endpoints(self):
        info=inspect_svg(FIX/'staggered-pulse.svg')
        t=timepoints(info,5,None)
        self.assertEqual(t,[0,0.375,0.75,1.125,1.5])

    def test_reconstruct_pulses(self):
        d=inspect_svg(FIX/'staggered-pulse.svg')
        output=motion_to_svg(d,shape='star')
        self.assertIn('values="0.3;1;0.3"',output)
        self.assertIn('dur="1.2s"',output)
        self.assertEqual(output.count('<animate '),3)
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'out.svg';p.write_text(output)
            re=inspect_svg(p)
            self.assertEqual(re['summary']['animation_count'],3)
            self.assertFalse(re['issues'])

    def test_reconstruct_rotate(self):
        d=inspect_svg(FIX/'rotation.svg')
        result=motion_to_svg(d)
        self.assertIn('type="rotate"',result)
        self.assertIn('dur="2s"',result)

    def test_reconstruct_unsupported(self):
        d=inspect_svg(FIX/'morph.svg')
        with self.assertRaises(ValueError):motion_to_svg(d)

    def test_compare_mocks(self):
        ref={'sampling':{'viewport':{'width':200,'height':100}},'frames':[]}
        cand={'sampling':{'viewport':{'width':200,'height':100}},'frames':[]}
        for t in [0,1]:
            el={'dot':{'bbox':{'x':40,'y':50,'width':20,'height':20},'opacity':1,'visibility':'visible','display':'inline'}}
            ref['frames'].append({'time_seconds':t,'elements':el})
            cand['frames'].append({'time_seconds':t,'elements':json.loads(json.dumps(el))})
        self.assertEqual(compare(ref,cand)['verdict'],'PASS')
        cand['frames'][1]['elements']['dot']['bbox']['x']=100
        self.assertEqual(compare(ref,cand)['verdict'],'FAIL')
        self.assertEqual(compare(ref,cand)['differences'][0]['property'],'bbox.x')
        cand['frames'][1]['elements']={}
        self.assertEqual(compare(ref,cand,targets=['dot'])['verdict'],'FAIL')

    def test_installer_idempotent_and_preserves_upstream(self):
        with tempfile.TemporaryDirectory() as td:
            dest=Path(td)/'svg-animator'
            (dest/'scripts').mkdir(parents=True)
            (dest/'references').mkdir()
            (dest/'SKILL.md').write_text('# Original skill\n')
            (dest/'references/CAPABILITIES.md').write_text('# Original capability map\n')
            (dest/'README.md').write_text('# Original README\n')
            plan(dest,dry_run=True)
            self.assertFalse((dest/'scripts/inspect_motion.py').exists())
            plan(dest)
            self.assertEqual((dest/'SKILL.md').read_text().count('MOTION-DNA-EXTENSION-START'),1)
            self.assertTrue((dest/'scripts/inspect_motion.py').exists())
            plan(dest)
            self.assertEqual((dest/'SKILL.md').read_text().count('MOTION-DNA-EXTENSION-START'),1)
            self.assertTrue((dest/'SKILL.md').read_text().startswith('# Original skill\n'))

    def test_installer_collision_refusal(self):
        with tempfile.TemporaryDirectory() as td:
            dest=Path(td)
            (dest/'scripts').mkdir()
            (dest/'references').mkdir()
            (dest/'SKILL.md').write_text('# A')
            (dest/'README.md').write_text('# B')
            (dest/'references/CAPABILITIES.md').write_text('# C')
            (dest/'scripts/inspect_motion.py').write_text('custom original')
            with self.assertRaisesRegex(ValueError,'Collision'):
                plan(dest)
            self.assertEqual((dest/'scripts/inspect_motion.py').read_text(),'custom original')

    def test_missing_is_inconclusive(self):
        ref={'sampling':{'viewport':{'width':1,'height':1}},'frames':[{'time_seconds':0,'elements':{'a':{}}}]}
        cand={'sampling':{'viewport':{'width':1,'height':1}},'frames':[{'time_seconds':0,'elements':{'b':{}}}]}
        self.assertEqual(compare(ref,cand)['verdict'],'INCONCLUSIVE')

    def test_missing_all_targets_must_never_pass(self):
        ref={'sampling':{'viewport':{'width':100,'height':100}},'frames':[{'time_seconds':0,'elements':{'dot':{}}}]}
        cand={'sampling':{'viewport':{'width':100,'height':100}},'frames':[{'time_seconds':0,'elements':{}}]}
        self.assertNotEqual(compare(ref,cand,targets=['dot'],ignore_missing=True)['verdict'],'PASS')
        self.assertEqual(compare(ref,cand,targets=['dot'],ignore_missing=True)['coverage'],0)

    def test_missing_timestamps_must_never_pass(self):
        el={'dot':{'bbox':{'x':10,'y':10,'width':5,'height':5},'opacity':1,'visibility':'visible','display':'inline'}}
        ref={'sampling':{'viewport':{'width':100,'height':100}},'frames':[{'time_seconds':t,'elements':el} for t in [0,0.5,1]]}
        cand={'sampling':{'viewport':{'width':100,'height':100}},'frames':[{'time_seconds':0,'elements':el}]}
        report=compare(ref,cand)
        self.assertEqual(report['verdict'],'INCONCLUSIVE')
        self.assertEqual(report['missing_candidate_timestamps'],[0.5,1])

    def test_missing_target_cannot_disappear_from_default_selection(self):
        elem={'bbox':{'x':10,'y':10,'width':5,'height':5},'opacity':1,'visibility':'visible','display':'inline'}
        ref={'sampling':{'viewport':{'width':100,'height':100}},'frames':[{'time_seconds':0,'elements':{'a':elem,'b':elem}}]}
        cand={'sampling':{'viewport':{'width':100,'height':100}},'frames':[{'time_seconds':0,'elements':{'a':elem}}]}
        report=compare(ref,cand)
        self.assertEqual(report['verdict'],'FAIL')
        self.assertTrue(any(m['reference_target']=='b' for m in report['missing']))

    def test_empty_requested_targets_inconclusive(self):
        ref={'sampling':{'viewport':{'width':100,'height':100}},'frames':[{'time_seconds':0,'elements':{}}]}
        self.assertEqual(compare(ref,ref,targets=[])['verdict'],'INCONCLUSIVE')

    def test_nan_tolerance_refused(self):
        ref={'sampling':{'viewport':{'width':100,'height':100}},'frames':[]}
        with self.assertRaises(ValueError):compare(ref,ref,pos_tol=float('nan'))

    def test_programmatic_single_sample_refused(self):
        d=inspect_svg(FIX/'staggered-pulse.svg')
        with self.assertRaises(ValueError):timepoints(d,1,None)

    def test_multi_animation_same_target_refused(self):
        svg='''<svg xmlns="http://www.w3.org/2000/svg"><circle id="a"><animate attributeName="opacity" values="0;1;0" dur="1s" repeatCount="indefinite"/><animate attributeName="opacity" values="0;1;0" dur="1s" repeatCount="indefinite"/></circle><circle id="b"><animate attributeName="opacity" values="0;1;0" dur="1s" repeatCount="indefinite"/></circle></svg>'''
        with tempfile.TemporaryDirectory() as td:
            file=Path(td)/'multi.svg';file.write_text(svg)
            with self.assertRaisesRegex(ValueError,'overlapping'):
                motion_to_svg(inspect_svg(file))

    def test_installer_force_preflight_does_not_partially_install(self):
        with tempfile.TemporaryDirectory() as td:
            dest=Path(td)
            (dest/'scripts').mkdir();(dest/'references').mkdir()
            for name in ('SKILL.md','README.md','references/CAPABILITIES.md'):
                (dest/name).write_text('Original')
            (dest/'scripts/compare_motion.py').write_text('custom')
            (dest/'scripts/compare_motion.py.motion-dna.bak').write_text('older backup')
            with self.assertRaisesRegex(ValueError,'Backup'):
                plan(dest,force=True)
            self.assertFalse((dest/'scripts/inspect_motion.py').exists())
            self.assertEqual((dest/'SKILL.md').read_text(),'Original')

    def test_svg_rotation_matrix_detects_equal_bbox_motion(self):
        # Transform rotation of a perfectly symmetric SVG circle has identical
        # bounding boxes. A box-only verifier falsely certifies it.
        with tempfile.TemporaryDirectory() as td:
            d=Path(td)
            header='<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200"><g id="spinner" transform="translate(100 100)"><circle r="30" fill="#34a"/>'
            animated=header+'<animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="2s" additive="sum" repeatCount="indefinite"/></g></svg>'
            static=header+'</g></svg>'
            x=d/'animated.svg';y=d/'static.svg'
            x.write_text(animated);y.write_text(static)
            a=capture(x,d/'a',samples=7,screenshots=False)
            b=capture(y,d/'b',times=','.join(str(f['time_seconds']) for f in a['frames']),screenshots=False)
            cmp=compare(a,b,targets=['spinner'])
            self.assertEqual(cmp['verdict'],'FAIL',cmp)
            self.assertTrue(any(i['property'].startswith('ctm.') for i in cmp['differences']),cmp)

    def test_external_embedded_resources_blocked(self):
        from motion_dna_core import safe_svg
        samples=[
            '<svg xmlns="http://www.w3.org/2000/svg"><style>@import url(https://evil.test/x.css)</style></svg>',
            '<svg xmlns="http://www.w3.org/2000/svg"><image href="data:image/svg+xml;base64,PHN2Zz4="/></svg>',
            '<svg xmlns="http://www.w3.org/2000/svg"><a href="javascript:alert(1)"/></svg>',
            '<svg xmlns="http://www.w3.org/2000/svg"><circle style="fill:url(https://evil.test/f.svg)"/></svg>',
        ]
        for item in samples:
            with self.subTest(sample=item):
                with self.assertRaises(ValueError):safe_svg(item)

    def test_duplicate_svg_ids_are_explicitly_reported(self):
        source='''<svg xmlns="http://www.w3.org/2000/svg"><circle id="same"><animate attributeName="opacity" dur="1s" values="0;1"/></circle><circle id="same"/></svg>'''
        with tempfile.TemporaryDirectory() as td:
            file=Path(td)/'dup.svg';file.write_text(source)
            report=inspect_svg(file)
            self.assertTrue(any('Duplicate id' in x for x in report['warnings']))

    @unittest.skipUnless(BROWSER_AVAILABLE, 'No installed Chromium')
    def test_browser_css_changes(self):
        with tempfile.TemporaryDirectory() as td:
            report=capture(FIX/'css-bounce.svg',td,samples=5,screenshots=False)
            self.assertEqual(len(report['frames']),5)
            y=[f['elements']['css-1']['bbox']['y'] for f in report['frames']]
            self.assertGreater(max(y)-min(y),4)

    @unittest.skipUnless(BROWSER_AVAILABLE, 'No installed Chromium')
    def test_browser_parked(self):
        with tempfile.TemporaryDirectory() as td:
            report=capture(FIX/'broken-parked.svg',td,samples=4,screenshots=False)
            self.assertTrue(any(a['code']=='possible-parked-element' for a in report['anomalies']))

    @unittest.skipUnless(BROWSER_AVAILABLE, 'No installed Chromium')
    def test_browser_pulse_reconstruction_matches_timing(self):
        reference=inspect_svg(FIX/'staggered-pulse.svg')
        with tempfile.TemporaryDirectory() as td:
            candidate=Path(td)/'variation.svg'
            candidate.write_text(motion_to_svg(reference),encoding='utf-8')
            a=capture(FIX/'staggered-pulse.svg',Path(td)/'a',samples=13,screenshots=False)
            b=capture(candidate,Path(td)/'b',times=','.join(map(str,a['sampling']['times_seconds'])),screenshots=False)
            match=compare(a,b,mode='opacity',target_map={f'pulse-{i}':f'motion-{i}' for i in range(1,4)})
            self.assertEqual(match['verdict'],'PASS',match['differences'])
            self.assertEqual(match['coverage'],39)

    @unittest.skipUnless(BROWSER_AVAILABLE, 'No installed Chromium')
    def test_browser_compare_detects_defect(self):
        with tempfile.TemporaryDirectory() as td:
            ref=capture(FIX/'compare-a.svg',Path(td)/'a',samples=5,screenshots=False)
            cand=capture(FIX/'compare-b.svg',Path(td)/'b',samples=5,screenshots=False)
            cmp=compare(ref,cand,targets=['dot'],pos_tol=.04)
            self.assertEqual(cmp['verdict'],'FAIL')
            self.assertGreater(len(cmp['differences']),0)

if __name__=='__main__':unittest.main()
