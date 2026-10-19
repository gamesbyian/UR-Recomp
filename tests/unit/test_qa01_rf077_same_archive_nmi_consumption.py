"""RF077 same-source original/native RTI getter proof, without source clock rebase."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
import qa01_rf077_same_archive_nmi_consumption as r

def fixture():
    original, native = [], []
    def native_event(frame, stage, extra):
        native.append(f'QA01RF047NATIVE seq={len(native)+1} stage={stage} f={frame} {extra}')
    for f in r.FRAMES:
        pc=0xD4F0 if f%2 else 0xD4EE
        original.append(
            f'QA01RF044ORIGNMI f={f} f1={f} pc=82{pc:04X}'
            f' S0=01F0 S1=01EC old=0011223344 new=26{pc&255:02X}D48226')
        for i,(kind,base,width,value) in enumerate((
            ('pullB','01ED',1,0x26),('pullW','01EE',2,pc),
            ('pullB','01F0',1,0x82))):
            original.append(f'QA01RF066ORIGCONSUMED seq={f*10+i} f={f}'
                            f' phase=post_real_stack_getter_return'
                            f' kind={kind} base={base} width={width} returned={value:04X}')
        native_event(f,'entry','S=01F0 resume=82D4EE')
        native_event(f,'resume_origin',
                     'phase=before_real_interrupt_push sourceFound=1'
                     ' originMatches=1 kind=set resume=82D4EE')
        native_event(f,'after_push','S=01EC resume=82D4EE stack=26EED482')
        native_event(f,'read','addr=01ED width=1 value=0026')
        native_event(f,'compiled_rti','S=01F0')
        native_event(f,'handler_return','S=01F0 resume=82D4EE')
    return '\n'.join(original)+'\n','\n'.join(native)+'\n'

class SameArchiveConsumption(unittest.TestCase):
    def test_real_getters_and_compiled_status_only(self):
        o,n=fixture()
        result=r.parse(o,n)
        self.assertEqual(result['original_nmi_stack_getter_brackets'],9)
        self.assertEqual(result['native_compiled_status_only_brackets'],9)
        self.assertEqual(result['actual_stack_saved_PC_value_differs_on_same_host_label_count'],5)
        self.assertTrue(result['different_original_and_native_RTI_memory_consumption_proven_within_own_guest_phase'])
        self.assertFalse(result['first_causally_significant_gameplay_divergence_proven'])
        self.assertFalse(result['same_original_native_interrupt_instruction_phase_proven'])
        self.assertEqual(result['accepted_USA_events'],0)

    def test_original_consumed_operand_missing_or_modified_fails(self):
        o,n=fixture()
        for changed in (
            o.replace('base=01EE','base=01EF',1),
            o.replace('returned=D4F0','returned=D4EE',1),
            o.replace('kind=pullW','kind=pullB',1),
            o.replace(' S0=01F0',' S0=01ED',1),
        ):
            with self.subTest(changed=changed[:100]), self.assertRaises(ValueError):
                r.parse(changed,n)

    def test_native_actual_status_or_scheduler_origin_mutation_fails(self):
        o,n=fixture()
        for changed in (
            n.replace('addr=01ED width=1 value=0026',
                      'addr=01EE width=1 value=00EE',1),
            n.replace('addr=01ED width=1 value=0026',
                      'addr=01ED width=1 value=0000',1),
            n.replace('seq=4 ','seq=70 ',1),
            n.replace('stage=compiled_rti','stage=interp_rti',1),
            n.replace('originMatches=1','originMatches=0',1),
        ):
            with self.subTest(changed=changed[:100]), self.assertRaises(ValueError):
                r.parse(o,changed)

    def test_missing_frame_or_truncation_is_a_real_failure(self):
        o,n=fixture()
        for orig,nat in (
            (o.replace('f=1025 f1=1025','f=1024 f1=1025'),n),
            (o+'QA01RF066ORIGCONSUMED_TRUNCATED\n',n),
            (o,n+'QA01RF047NATIVE_TRUNCATED\n'),
            (o,n.replace('stage=after_push','stage=entry',1)),
        ):
            with self.assertRaises(ValueError):
                r.parse(orig,nat)

if __name__=='__main__':
    unittest.main()
