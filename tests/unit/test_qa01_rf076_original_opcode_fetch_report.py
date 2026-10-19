"""Original Snes9x genuine fetched opcode, pending wake and actual NMI boundary."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
import qa01_rf076_original_opcode_fetch_report as m


def log():
    return '\n'.join([
        'QA01RF076ORIGPC seq=1 stage=fetch f=1017 actualFetchedPC=82D4EE fetchedOpcode=CB S=01F0 v=224 h=1312 wai=0',
        'QA01RF076ORIGPC seq=2 stage=nmi_pending f=1017 actualFetchedPC=82D4EE fetchedOpcode=00 S=01F0 v=225 h=0 wai=1',
        'QA01RF076ORIGPC seq=3 stage=nmi_before f=1017 actualFetchedPC=82D4EF fetchedOpcode=00 S=01F0 v=225 h=12 wai=0',
        'QA01RF076ORIGPC seq=4 stage=fetch f=1017 actualFetchedPC=82D4F0 fetchedOpcode=CA S=01F0 v=225 h=90 wai=0',
    ])+'\n'


class TrueOriginalSource(unittest.TestCase):
    def test_real_source_markers_and_wai_but_no_cross_guest_parity(self):
        d=m.inspect(log())
        self.assertEqual(d['source_events'],4)
        self.assertEqual(d['source_observed_nmi_before_marker_count'],1)
        self.assertFalse(d['complete_nine_original_NMI_frames_observed'])
        self.assertEqual(d['missing_original_NMI_frames'],list(range(1018,1026)))
        self.assertEqual(d['source_observed_selected_actual_opcode_fetches'],2)
        b=d['source_NMI_brackets'][0]
        self.assertTrue(b['original_source_wake_incremented_PC'])
        self.assertEqual(b['original_source_wake_pc_before'],'82D4EE')
        self.assertEqual(b['original_source_wake_pc_after'],'82D4EF')
        self.assertEqual(b['last_selected_original_opcode_fetch_before_NMI']['source_guest_PC_context'],'82D4EE')
        self.assertEqual(b['first_selected_original_opcode_fetch_after_NMI']['source_guest_PC_context'],'82D4F0')
        self.assertFalse(d['original_native_semantically_aligned_NMI_proven'])
        self.assertEqual(d['accepted_USA_events'],0)

    def test_all_nine_source_NMI_frames_explicitly_qualified(self):
        row=[]
        for f in range(1017,1026):
            for sample in log().splitlines():
                sample=sample.replace('f=1017',f'f={f}')
                sample=sample.replace('seq='+sample.split('seq=')[1].split()[0],
                                      'seq='+str(len(row)+1),1)
                row.append(sample)
        v=m.inspect('\n'.join(row)+'\n')
        self.assertTrue(v['complete_nine_original_NMI_frames_observed'])
        self.assertEqual(v['missing_original_NMI_frames'],[])
        self.assertEqual(v['source_observed_nmi_before_marker_count'],9)
        self.assertFalse(v['original_native_semantically_aligned_NMI_proven'])

    def test_duplicate_frame_nmi_is_scientific_hold(self):
        lines=log().splitlines()
        extra=[line.replace('seq=2 ','seq=5 ').replace('seq=3 ','seq=5 ')
                    for line in lines[1:3]]
        extra[1]=extra[1].replace('seq=5 ','seq=6 ')
        with self.assertRaisesRegex(ValueError,'duplicated or reordered'):
            m.inspect('\n'.join(lines+extra)+'\n')

    def test_no_wai_no_pre_nmi_pc_advance(self):
        sample=log().replace('82D4EE fetchedOpcode=00 S=01F0 v=225 h=0 wai=1',
                             '82D4EE fetchedOpcode=00 S=01F0 v=225 h=0 wai=0').replace(
                             '82D4EF fetchedOpcode=00','82D4EE fetchedOpcode=00')
        b=m.inspect(sample)['source_NMI_brackets'][0]
        self.assertFalse(b['original_source_wake_incremented_PC'])
        self.assertEqual(b['original_source_wake_pc_before'],b['original_source_wake_pc_after'])

    def test_bad_wai_flag_or_wrong_original_wake_pc_fails(self):
        for src in (log().replace('wai=1','wai=2'),
                    log().replace('82D4EF fetchedOpcode=00','82D4EE fetchedOpcode=00'),
                    log().replace('82D4EF fetchedOpcode=00','82D4F0 fetchedOpcode=00'),
                    log().replace('v=225 h=12 wai=0','v=225 h=12 wai=1')):
            with self.subTest(src=src[:100]), self.assertRaises(ValueError):
                m.inspect(src)

    def test_mislabelled_nmi_sentinel_rejected(self):
        with self.assertRaisesRegex(ValueError,'sentinel'):
            m.inspect(log().replace('stage=nmi_before f=1017 actualFetchedPC=82D4EF fetchedOpcode=00',
                                     'stage=nmi_before f=1017 actualFetchedPC=82D4EF fetchedOpcode=CA'))

    def test_forged_nonselected_opcode_and_count_drift_rejected(self):
        for dirty in (log().replace('actualFetchedPC=82D4EE fetchedOpcode=CB','actualFetchedPC=808588 fetchedOpcode=CB'),
                      log().replace('seq=2 ','seq=33 ')):
            with self.assertRaises(ValueError): m.inspect(dirty)

    def test_missing_prewake_event_rejected(self):
        lines=[x for x in log().splitlines() if 'stage=nmi_pending' not in x]
        v='\n'.join(x.replace('seq=3 ','seq=2 ').replace('seq=4 ','seq=3 ') for x in lines)
        with self.assertRaisesRegex(ValueError,'wake-pending'):m.inspect(v)

    def test_missing_events_or_truncation_rejected(self):
        for dirty in ('',log()+'QA01RF076ORIGPC_TRUNCATED'):
            with self.assertRaises(ValueError):m.inspect(dirty)

    def test_wake_alone_is_no_fetch_proof(self):
        line1=log().splitlines()[1].replace('seq=2 ','seq=1 ')
        line2=log().splitlines()[2].replace('seq=3 ','seq=2 ')
        out=m.inspect(line1+'\n'+line2+'\n')
        self.assertEqual(out['source_observed_selected_actual_opcode_fetches'],0)
        self.assertIsNone(out['source_NMI_brackets'][0]['last_selected_original_opcode_fetch_before_NMI'])
        self.assertFalse(out['original_opcode_fetches_unselected_sites_observed'])


if __name__ == '__main__':
    unittest.main()
