"""Source-derived H25 exact PR-head and workflow-base admission negatives.

Read-only research classifier. A green workflow cannot qualify a merge tree.
"""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
from ci_exact_epoch import classify, NAMES

MAIN = 'a' * 40
HEAD = 'b' * 40
OLD_BASE = 'c' * 40


class ExactWorkflowEpochTests(unittest.TestCase):
    def runs(self, *, base=OLD_BASE):
        return [dict(id=100+i, name=name, event='pull_request',
                     status='completed', conclusion='success', head_sha=HEAD,
                     pr_number=2060, run_attempt=1, base_sha=base)
                for i, name in enumerate(sorted(NAMES))]

    def test_stale_main_still_holds_despite_three_green_runs(self):
        result = classify(MAIN, OLD_BASE, HEAD, 2060, 12, 14, self.runs())
        self.assertTrue(result['workflow_head_success'])
        self.assertFalse(result['merge_base_current'])
        self.assertFalse(result['current_merge_tree_qualified'])
        self.assertEqual(result['disposition'], 'HOLD_CURRENT_MAIN_MERGE_TREE_UNTESTED')
        self.assertEqual(result['release_gate_credit'], 0)

    def test_same_run_id_cannot_prove_two_workflows(self):
        runs = self.runs()
        runs[1]['id'] = runs[0]['id']
        with self.assertRaisesRegex(ValueError, 'uniquely'):
            classify(MAIN, OLD_BASE, HEAD, 2060, 12, 14, runs)

    def test_strict_pr_head_event_attempt_and_base_binding(self):
        for key, wrong in (
            ('pr_number', 2061),
            ('head_sha', MAIN),
            ('base_sha', MAIN),
            ('run_attempt', False),
            ('event', 'push'),
            ('conclusion', 'failure'),
            ('status', 'queued'),
        ):
            with self.subTest(field=key):
                runs = self.runs()
                runs[0][key] = wrong
                with self.assertRaises(ValueError):
                    classify(MAIN, OLD_BASE, HEAD, 2060, 12, 14, runs)

    def test_fresh_base_still_requires_merge_tree_proof(self):
        result = classify(MAIN, MAIN, HEAD, 2060, 1, 0,
                          self.runs(base=MAIN))
        self.assertTrue(result['merge_base_current'])
        self.assertFalse(result['current_merge_tree_qualified'])
        self.assertEqual(result['windows_release_accepted'], False)

    def test_missing_extra_and_duplicate_workflows_refused(self):
        runs = self.runs()
        for bad in (runs[:-1], runs + [runs[0]], [runs[0], runs[0], runs[2]]):
            with self.subTest(size=len(bad)):
                with self.assertRaises(ValueError):
                    classify(MAIN, OLD_BASE, HEAD, 2060, 12, 14, bad)

    def test_bool_commit_counts_and_invalid_hashes_refused(self):
        with self.assertRaises(ValueError):
            classify(MAIN, OLD_BASE, HEAD, 2060, True, 14, self.runs())
        with self.assertRaises(ValueError):
            classify('not-a-sha', OLD_BASE, HEAD, 2060, 12, 14, self.runs())
        with self.assertRaises(ValueError):
            classify(MAIN, OLD_BASE, HEAD, True, 12, 14, self.runs())


if __name__ == '__main__':
    unittest.main()
