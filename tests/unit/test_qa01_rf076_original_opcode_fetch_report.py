"""Original true opcode fetch and NMI marker semantic limits."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
import qa01_rf076_original_opcode_fetch_report as m


def log():
    return '\n'.join([
        'QA01RF076ORIGPC seq=1 stage=fetch f=1017 actualFetchedPC=82D4EE fetchedOpcode=CB S=01F0 v=224 h=1312',
        'QA01RF076ORIGPC seq=2 stage=nmi_before f=1017 actualFetchedPC=82D4F0 fetchedOpcode=00 S=01F0 v=225 h=0',
        'QA01RF076ORIGPC seq=3 stage=fetch f=1017 actualFetchedPC=82D4F0 fetchedOpcode=CA S=01F0 v=225 h=90',
    ])+'\n'


class TrueOriginalSource(unittest.TestCase):
    def test_real_source_markers_not_saved_context_parity(self):
        data=m.inspect(log())
        self.assertEqual(data['source_events'],3)
        self.assertEqual(data['source_observed_nmi_before_marker_count'],1)
        self.assertEqual(data['source_observed_selected_actual_opcode_fetches'],2)
        self.assertEqual(data['source_NMI_brackets'][0]['last_selected_original_opcode_fetch_before_NMI']['source_guest_PC_context'],'82D4EE')
        self.assertEqual(data['source_NMI_brackets'][0]['first_selected_original_opcode_fetch_after_NMI']['source_guest_PC_context'],'82D4F0')
        self.assertFalse(data['original_native_semantically_aligned_NMI_proven'])
        self.assertEqual(data['accepted_USA_events'],0)

    def test_mislabelled_nmi_sentinel_rejected(self):
        with self.assertRaisesRegex(ValueError,'sentinel'):
            m.inspect(log().replace('stage=nmi_before f=1017 actualFetchedPC=82D4F0 fetchedOpcode=00',
                                     'stage=nmi_before f=1017 actualFetchedPC=82D4F0 fetchedOpcode=CA'))

    def test_forged_nonselected_opcode_and_count_drift_rejected(self):
        for dirty in (log().replace('actualFetchedPC=82D4EE','actualFetchedPC=808588'),
                      log().replace('seq=2 ','seq=33 ')):
            with self.assertRaises(ValueError): m.inspect(dirty)

    def test_missing_events_or_truncation_rejected(self):
        for dirty in ('',log()+'QA01RF076ORIGPC_TRUNCATED'):
            with self.assertRaises(ValueError):m.inspect(dirty)

    def test_nmi_alone_is_no_fetch_proof(self):
        line=log().splitlines()[1].replace('seq=2 ','seq=1 ')+'\n'
        out=m.inspect(line)
        self.assertEqual(out['source_observed_selected_actual_opcode_fetches'],0)
        self.assertIsNone(out['source_NMI_brackets'][0]['last_selected_original_opcode_fetch_before_NMI'])
        self.assertFalse(out['original_opcode_fetches_unselected_sites_observed'])


if __name__ == '__main__':
    unittest.main()
