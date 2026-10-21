import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
from qa09_qa08_ci_admission import classify

class QA09Admission(unittest.TestCase):
    def setUp(self):
        self.args=dict(source_sha='a'*40,tested_sha='a'*40,
            guest_on_off_equal=True,historic_crc_equal=False,archive_authenticated=True)
    def test_historic_mismatch_hold(self):
        x=classify(**self.args)
        self.assertEqual(x['decision'],'HOLD')
        self.assertIn('historic RF017 mismatch',x['blockers'])
        self.assertEqual(x['release_gate_credit'],0)
    def test_unbound_source_hold(self):
        self.assertIn('source epoch changed',
            classify(**{**self.args,'tested_sha':'b'*40})['blockers'])
    def test_unverified_archive_hold(self):
        self.assertIn('source archive unauthenticated',
            classify(**{**self.args,'archive_authenticated':False})['blockers'])
    def test_no_release_credit_even_all_flags_positive(self):
        x=classify(**{**self.args,'historic_crc_equal':True})
        self.assertEqual(x['decision'],'REVIEW_NEW_INDEPENDENT_EVIDENCE')
        self.assertEqual(x['release_gate_credit'],0)
        self.assertFalse(x['source_epoch_original_native_parity_proven'])
    def test_non_boolean_and_bad_sha_rejected(self):
        for changes in ({'guest_on_off_equal':1},{'historic_crc_equal':'yes'},
                        {'source_sha':'A'*40}):
            with self.subTest(changes=changes),self.assertRaises(ValueError):
                classify(**{**self.args,**changes})

if __name__=='__main__':
    unittest.main()
