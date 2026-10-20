"""RF079 real source-local BIT operand and BPL decision report tests."""
import sys
import unittest
import tempfile
import zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
import qa01_rf079_real_bit_bpl_report as r

def sample():
    original=[]
    native=[]
    def n(frame,stage,more):
        native.append(f'QA01RF047NATIVE seq={len(native)+1} stage={stage} f={frame} master={len(native)+100} {more}')
    def o(frame,before,opcode,after,value):
        original.append(
            f'QA01RF079ORIG seq={1+sum("QA01RF079ORIG" in x for x in original)} '
            f'f={frame} before={before} opcode={opcode} after={after} D=0000 '
            f'M=1 Nbyte={value:02X} N={int(bool(value&128))} V=226 H=944 '
            'phase=after_real_guest_opcode')
    for frame in r.FRAMES:
        original.append(f'QA01RF044ORIGNMI f={frame} f1={frame} pc=82D4EE '
                        'S0=01F0 S1=01EC old=00000000 new=26EED482')
        if frame==1017:
            o(frame,'82D4F0','10','82D4EE',0)
        else:
            o(frame,'82D4EE','24','82D4F0',0)
            o(frame,'82D4F0','10','82D4EE',0)
        for stage,other in (
            ('entry','resume=82D4EE'),
            ('resume_origin','resume=82D4EE sourceFound=1 originMatches=1'),
            ('after_push','resume=82D4EE'),
            ('compiled_rti','returnPC=82D4EE'),
            ('handler_return','resume=82D4EE'),
            ('opcode','guestPC=82D4EE tier=aot'),
            ('bit_real_return','guestPC=82D4EE D=0000 addr=0057 value=00'),
            ('opcode','guestPC=82D4F0 tier=aot'),
            ('bpl_actual_input','guestPC=82D4F0 D=0000 N=0 bitReadSeen=1'),
        ):
            n(frame,stage,other)
    return '\n'.join(original)+'\n','\n'.join(native)+'\n'

class RealBitBranch(unittest.TestCase):
    def test_real_returned_value_and_control(self):
        o,n=sample()
        result=r.inspect(o,n)
        self.assertEqual(result['source_two_frame_brackets_compared'],2)
        self.assertEqual(result['real_BPL_N_input_disagreement_count'],0)
        self.assertEqual(result['frames'][0]['original_first_selected_post_NMI_opcode_PC'],'82D4F0')
        self.assertEqual(result['frames'][1]['original_first_selected_post_NMI_opcode_PC'],'82D4EE')
        self.assertEqual(result['frames'][0]['native_first_actual_post_NMI_BIT_returned_byte'],'00')
        self.assertFalse(result['first_causally_significant_gameplay_divergence_proven'])
        self.assertFalse(result['semantic_original_native_clock_alignment_proven'])
        self.assertEqual(result['accepted_USA_events'],0)

    def test_native_paced_read_is_not_an_inferred_value(self):
        o,n=sample()
        for modified in (
            n.replace('addr=0057','addr=0058',1),
            n.replace('value=00','value=80',1),
            n.replace('bitReadSeen=1','bitReadSeen=0',1),
            n.replace('tier=aot','tier=interp',1),
            n.replace('guestPC=82D4F0 tier=aot','guestPC=82D4EE tier=aot',1),
            n.replace('seq=7 ','seq=777 ',1),
            n+'QA01RF047NATIVE_TRUNCATED\n',
        ):
            with self.subTest(modified=modified[:100]),self.assertRaises(ValueError):
                r.inspect(o,modified)

    def test_original_postbranch_true_operand_checks(self):
        o,n=sample()
        for modified in (
            o.replace('after=82D4EE','after=82D4F2',1),
            o.replace('opcode=10','opcode=24',1),
            o.replace('M=1','M=0',1),
            o.replace('Nbyte=00 N=0','Nbyte=80 N=0',1),
            o.replace('seq=1 ','seq=3 ',1),
            o.replace('f=1018 f1=1018','f=1017 f1=1018',1),
            o+'QA01RF079ORIG_TRUNCATED\n',
        ):
            with self.subTest(modified=modified[:100]),self.assertRaises(ValueError):
                r.inspect(modified,n)

    def test_zip_requires_explicit_strict_sidecar_even_with_good_raw_stderr(self):
        o,n=sample()
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'same-case.zip'
            with zipfile.ZipFile(path,'w') as z:
                z.writestr(r.ORIG,o)
                z.writestr(r.NATIVE,n)
            with self.assertRaisesRegex(ValueError,'strict native event sidecar absent'):
                r.case_archive(path)

    def test_strict_sidecar_runs_and_preserves_original_raw_stderr_bytes(self):
        o,n=sample()
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'same-case.zip'
            raw_stderr='LEGACY_FRAGMENT '+n
            with zipfile.ZipFile(path,'w') as z:
                z.writestr(r.ORIG,o)
                z.writestr(r.NATIVE,raw_stderr)
                z.writestr(r.STRICT_SIDECAR,n)
            report=r.case_archive(path)
            self.assertTrue(report['native_RF047_dedicated_source_ordinals_verified'])
            self.assertTrue(report['native_raw_stderr_separately_preserved_unchanged'])
            self.assertFalse(report['native_stderr_full_RF047_source_continuity_claimed'])
            self.assertEqual(report['native_raw_stderr_missing_complete_RF047_source_events'],1)
            self.assertEqual(report['native_raw_stderr_malformed_or_mismatched_RF047_prefix_rows'],0)
            self.assertEqual(report['source_two_frame_brackets_compared'],2)

    def test_non_source_or_mixed_line_inside_sidecar_is_strict_failure(self):
        o,n=sample()
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'bad-case.zip'
            with zipfile.ZipFile(path,'w') as z:
                z.writestr(r.ORIG,o)
                z.writestr(r.NATIVE,n)
                z.writestr(r.STRICT_SIDECAR,
                           n.replace('QA01RF047NATIVE seq=7 ',
                                     'LEGACY_INTERLEAVED QA01RF047NATIVE seq=7 ',1))
            with self.assertRaisesRegex(ValueError,'non-source line'):
                r.case_archive(path)

    def test_missing_nmi_and_missing_postopcode_fail(self):
        o,n=sample()
        with self.assertRaises(ValueError):
            r.inspect('\n'.join(x for x in o.splitlines()
                                if 'QA01RF044ORIGNMI f=1017' not in x),n)
        with self.assertRaises(ValueError):
            r.inspect(o.replace('before=82D4F0 opcode=10','before=82D4F1 opcode=10',1),n)

if __name__=='__main__':
    unittest.main()
