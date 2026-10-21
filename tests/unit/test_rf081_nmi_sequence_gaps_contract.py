"""Archive-free negative controls for source-local RF081 NMI evidence."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
from rf081_nmi_sequence_gaps import analyze_records, analyze_archive


def witnesses():
    original = {'source_NMI_brackets': []}
    native = {'native_frames': []}
    for i, frame in enumerate(range(1017, 1026)):
        s, n = 10 * i, 20 * i
        original['source_NMI_brackets'].append({
            'original_NMI_wake_pending_event': {
                'source_local_seq': s + 1, 'original_host_frame': frame,
                'stage': 'nmi_pending', 'decoded_original_guest_fetch_executed': False},
            'original_NMI_before_push_event': {
                'source_local_seq': s + 2, 'original_host_frame': frame,
                'stage': 'nmi_before', 'decoded_original_guest_fetch_executed': False},
            'first_selected_original_opcode_fetch_after_NMI': {
                'source_local_seq': s + 5, 'original_host_frame': frame,
                'stage': 'fetch', 'source_guest_PC_context': '82D4F0',
                'decoded_original_guest_fetch_executed': True},
            'all_intervening_unselected_opcode_fetches_observed': False})
        native['native_frames'].append({
            'native_entry_seq': n + 1, 'native_compiled_handler_return_seq': n + 4,
            'first_observed_target_opcode_after_handler_before_next_NMI': {
                'seq': n + 6, 'frame': frame, 'decoded_guest_opcode_PC': '82D4F0',
                'actual_guest_emitter_tier': 'aot'},
            'native_NMI_frame_label': frame,
            'original_native_interrupt_instruction_phase_qualified': False,
            'scheduler_PC_is_independently_proven_fetched_interrupt_target': False})
    return original, native


class RF081NMIGapContract(unittest.TestCase):
    def test_nine_frame_sequence_census_is_not_instruction_parity(self):
        result = analyze_records(*witnesses())
        self.assertEqual(len(result['rows']), 9)
        self.assertEqual([x['host_frame_label'] for x in result['rows']],
                         list(range(1017, 1026)))
        self.assertEqual(result['release_gate_credit'], 0)
        self.assertFalse(result['first_causal_divergence_proven'])
        self.assertFalse(result['actual_rts_operand_consumption_observed'])

    def test_original_pending_frame_swap_refused(self):
        a, b = witnesses()
        a['source_NMI_brackets'][1]['original_NMI_wake_pending_event']['original_host_frame'] = 1017
        with self.assertRaises(ValueError): analyze_records(a, b)

    def test_original_before_frame_swap_refused(self):
        a, b = witnesses()
        a['source_NMI_brackets'][1]['original_NMI_before_push_event']['original_host_frame'] = 1017
        with self.assertRaises(ValueError): analyze_records(a, b)

    def test_malformed_pc_lexemes_refused(self):
        for side, field, value in [('original', 'source_guest_PC_context', '82d4f0'),
                                   ('original', 'source_guest_PC_context', '0x82D4F0'),
                                   ('native', 'decoded_guest_opcode_PC', '82D4F')]:
            a, b = witnesses()
            target = (a['source_NMI_brackets'][0]['first_selected_original_opcode_fetch_after_NMI']
                      if side == 'original' else
                      b['native_frames'][0]['first_observed_target_opcode_after_handler_before_next_NMI'])
            target[field] = value
            with self.subTest(side=side, value=value), self.assertRaises(ValueError):
                analyze_records(a, b)

    def test_reused_sequences_and_fake_phase_refused(self):
        for mutation in ('sequence', 'phase'):
            a, b = witnesses()
            if mutation == 'sequence':
                b['native_frames'][1]['native_entry_seq'] = 2
            else:
                b['native_frames'][0]['original_native_interrupt_instruction_phase_qualified'] = True
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                analyze_records(a, b)

    def test_wrong_archive_refused_before_untrusted_content(self):
        with self.assertRaises(ValueError): analyze_archive(b'not the genuine RF081 archive')


if __name__ == '__main__':
    unittest.main()
