"""Independent hosted Windows candidate pin-classification tests; no gate credit."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from qa04_external_candidate_verdict import classify


class ExternalCandidateVerdict(unittest.TestCase):
    def setUp(self):
        self.k = {
            'tested_source':'a'*40, 'current_main':'b'*40,
            'nominated_source':'c'*40, 'tested_inner_zip':'d'*64,
            'nominated_inner_zip':'e'*64, 'hosted_package_verified':True,
            'physical_journey_verified':False,
        }

    def test_stale_main_and_unmatched_nomination_hold(self):
        r = classify(**self.k)
        self.assertEqual(r['decision'],'HOLD')
        self.assertEqual(r['release_gate_credit'],0)
        self.assertEqual(len(r['blockers']),4)

    def test_match_still_requires_physical_journey(self):
        r = classify(**{**self.k,'current_main':'a'*40,
                        'nominated_source':'a'*40,'nominated_inner_zip':'d'*64})
        self.assertEqual(r['blockers'],['physical_journey_not_verified'])

    def test_physical_flag_never_grants_gate_credit(self):
        r = classify(**{**self.k,'current_main':'a'*40,
                        'nominated_source':'a'*40,'nominated_inner_zip':'d'*64,
                        'physical_journey_verified':True})
        self.assertEqual(r['decision'],'READY_FOR_SEPARATE_GATE_REVIEW')
        self.assertEqual(r['release_gate_credit'],0)

    def test_malformed_or_noncanonical_hashes_refused(self):
        for field,bad in [('tested_source','A'*40),('current_main','G'*40),
                          ('nominated_source','f'*39),('tested_inner_zip','F'*64),
                          ('nominated_inner_zip','g'*64),('tested_source',True)]:
            with self.subTest(field=field),self.assertRaises(ValueError):
                classify(**{**self.k,field:bad})

    def test_hosted_and_physical_flags_must_be_booleans(self):
        for field,bad in [('hosted_package_verified',1),
                          ('physical_journey_verified',0),
                          ('hosted_package_verified','yes')]:
            with self.subTest(field=field),self.assertRaises(ValueError):
                classify(**{**self.k,field:bad})


if __name__ == '__main__':
    unittest.main()
