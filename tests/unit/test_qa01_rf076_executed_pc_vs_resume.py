"""RF076 native-local actual opcode markers versus scheduler provenance."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
import qa01_rf076_executed_pc_vs_resume as m


def witness():
    lines = []
    def add(f, stage, fields):
        lines.append(f'QA01RF047NATIVE seq={len(lines)+1} stage={stage} f={f} {fields}')
    for fr in m.FRAMES:
        t = fr * 1000
        add(fr, 'entry', f'resume=82D4EE S=01F0 master={t}')
        add(fr, 'resume_origin', f'sourceFound=1 originMatches=1 resume=82D4EE newPC=82D4EE master={t}')
        add(fr, 'after_push', f'resume=82D4EE S=01EC master={t}')
        add(fr, 'read', f'bank=00 addr=01ED width=1 value=0026 master={t+1}')
        add(fr, 'compiled_rti', f'S=01F0 master={t+1}')
        add(fr, 'handler_return', f'resume=82D4EE S=01F0 master={t+1}')
        if fr == 1017:
            add(fr, 'opcode', f'guestPC=82D4EE tier=aot master={t+2}')
        if fr == 1018:
            add(fr, 'opcode', f'guestPC=82D4F0 tier=interp master={t+2}')
    return '\n'.join(lines)+'\n'


class Chronology(unittest.TestCase):
    def test_real_markers_are_not_scheduler_or_cross_guest_parity(self):
        v = m.inspect(witness())
        self.assertEqual(v['native_NMI_brackets'], 9)
        self.assertEqual(v['native_opcode_target_event_count'], 2)
        self.assertEqual(v['native_frames'][0]['scheduler_saved_resume_PC'], '82D4EE')
        self.assertEqual(v['native_frames'][0]['first_observed_target_opcode_after_handler_before_next_NMI']['decoded_guest_opcode_PC'], '82D4EE')
        self.assertTrue(v['native_frames'][0]['scheduler_PC_equals_first_observed_post_return_target_opcode'])
        self.assertFalse(v['actual_guest_fetch_at_saved_scheduler_NMI_PC_proven'])
        self.assertFalse(v['same_semantic_phase_original_native_proven'])
        self.assertEqual(v['accepted_USA_events'], 0)

    def test_host_fragment_prefix_is_not_an_opcode_event(self):
        raw = witness().replace('QA01RF047NATIVE seq=2', 'FRAGMENTQA01RF047NATIVE seq=2', 1)
        self.assertEqual(m.inspect(raw)['native_opcode_target_event_count'], 2)

    def test_absent_opcode_is_not_fabricated(self):
        raw = '\n'.join(l for l in witness().splitlines() if 'stage=opcode' not in l)
        raw = '\n'.join(l.replace(f'seq={int(l.split("seq=")[1].split()[0])}', f'seq={i}')
                        for i,l in enumerate(raw.splitlines(), 1))
        v = m.inspect(raw)
        self.assertEqual(v['native_opcode_target_event_count'], 0)
        self.assertIsNone(v['native_frames'][0]['first_observed_target_opcode_after_handler_before_next_NMI'])

    def test_missing_or_mutated_provenance_fails(self):
        for a,b in (('originMatches=1','originMatches=0'), ('newPC=82D4EE','newPC=82D4F0'),
                    ('S=01EC','S=01F0'), ('stage=compiled_rti','stage=interp_rti')):
            with self.subTest(a=a), self.assertRaises(ValueError):
                m.inspect(witness().replace(a,b,1))

    def test_damaged_opcode_identity_fails(self):
        for a,b in (('guestPC=82D4EE','guestPC=008588'),('tier=aot','tier=unknown')):
            with self.subTest(a=a), self.assertRaises(ValueError):
                m.inspect(witness().replace(a,b,1))

    def test_gaps_and_truncation_fail(self):
        for sample in (witness().replace('seq=4 ', 'seq=400 ',1),
                       witness()+'QA01RF047NATIVE_TRUNCATED\n'):
            with self.assertRaises(ValueError): m.inspect(sample)


if __name__ == '__main__':
    unittest.main()
