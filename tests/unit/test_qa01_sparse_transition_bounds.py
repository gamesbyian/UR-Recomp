"""Archive-free RF081 sparse-transition bounds and source-epoch admission tests."""
import itertools
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from tools.qa01_sparse_transition_bounds import transition_bounds, audit


class QA01SparseTransitionBounds(unittest.TestCase):
    def test_same_endpoints_can_hide_multiple_flips(self):
        r = transition_bounds([(1, False), (5, False)], 5)
        self.assertEqual(r['minimum_transitions_between_observed_samples'], 0)
        self.assertEqual(r['maximum_transitions_in_observed_span_and_suffix'], 4)
        self.assertFalse(r['monotonic_first_transition_inference_justified'])
        self.assertEqual(r['independently_accepted_USA_events'], 0)

    def test_opposite_endpoints_can_hide_three_flips(self):
        r = transition_bounds([(1, False), (4, True)], 4)
        self.assertEqual(r['minimum_transitions_between_observed_samples'], 1)
        self.assertEqual(r['maximum_transitions_in_observed_span_and_suffix'], 3)

    def test_unobserved_suffix_is_not_claimed_exact(self):
        r = transition_bounds([(1, False), (2, False)], 10)
        self.assertEqual(r['unconstrained_suffix_frame_count'], 8)
        self.assertEqual(r['maximum_transitions_in_observed_span_and_suffix'], 8)
        self.assertEqual(r['minimum_transitions_between_observed_samples'], 0)

    def test_observed_endpoint_bounds_match_exhaustive_boolean_paths(self):
        for distance in range(1, 7):
            for left, right in itertools.product((False, True), repeat=2):
                possible = []
                for mid in itertools.product((False, True), repeat=distance-1):
                    states = (left,) + mid + (right,)
                    possible.append(sum(a != b for a, b in zip(states, states[1:])))
                r = transition_bounds([(1, left), (distance+1, right)], distance+1)
                with self.subTest(distance=distance, left=left, right=right):
                    self.assertEqual(r['minimum_transitions_between_observed_samples'], min(possible))
                    self.assertEqual(r['maximum_transitions_in_observed_span_and_suffix'], max(possible))

    def test_invalid_order_and_types_fail_closed(self):
        invalid = ([(2,False),(2,True)], [(2,False),(1,True)], [(1,0)],
                   [(1,False),(20,True)], [(True,False)], [],
                   [[1,False,False]], [(1,'False')])
        for samples in invalid:
            with self.subTest(samples=samples), self.assertRaises(ValueError):
                transition_bounds(samples, 10)
        for horizon in (True, 0, 1.0, -1):
            with self.subTest(horizon=horizon), self.assertRaises(ValueError):
                transition_bounds([(1,False)], horizon)

    def test_unauthenticated_archive_epoch_refused(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'untrusted.zip'
            with ZipFile(path, 'w') as z:
                z.writestr('work/zoom-zoo/replay/ref/scene-00001.wram.bin', b'x')
            with self.assertRaisesRegex(ValueError, 'wrong RF081 evidence epoch'):
                audit(path)

    def test_missing_cli_archive_argument_is_hard_failure(self):
        script = Path(__file__).resolve().parents[2] / 'tools' / 'qa01_sparse_transition_bounds.py'
        r = subprocess.run([sys.executable, str(script)], capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('usage:', r.stderr)


if __name__ == '__main__':
    unittest.main()
