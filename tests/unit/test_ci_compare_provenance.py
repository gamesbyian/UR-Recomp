"""ROM-free provenance admission recovered from Agent 5 H25 engineering archive."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
from ci_compare_provenance import assess

class CompareProvenanceAdmission(unittest.TestCase):
    @staticmethod
    def sample():
        return {'base': 'a'*40, 'head': 'b'*40,
                'base_commit': {'sha':'a'*40}, 'merge_base_commit': {'sha':'c'*40},
                'status':'diverged','ahead_by':12,'behind_by':16,
                'total_commits':28,'too_large':None,
                'files':[{'filename':'tools/export_baldosa_earned_1p_run.py'}]}

    def test_source_bound_diverged_comparison_cannot_claim_merge_ready(self):
        receipt=assess(main_sha='a'*40, pr_head_sha='b'*40,
                       compare=self.sample())
        self.assertEqual(receipt['decision'], 'HOLD_MERGE_TREE_UNTESTED')
        self.assertFalse(receipt['main_merge_tree_qualified'])
        self.assertFalse(receipt['independent_windows_qa_accepted'])
        self.assertEqual(receipt['release_gate_credit'], 0)

    def test_forged_query_or_merge_base_or_status_fails_closed(self):
        for field,value in (('base','c'*40),('head','c'*40),
                            ('status','ahead'),('behind_by',0),
                            ('merge_base_commit',{'sha':'bad'})):
            with self.subTest(field=field):
                data=self.sample(); data[field]=value
                with self.assertRaises(ValueError):
                    assess(main_sha='a'*40,pr_head_sha='b'*40,compare=data)

    def test_duplicate_file_census_rejected(self):
        data=self.sample();data['files'].append(dict(data['files'][0]))
        with self.assertRaisesRegex(ValueError,'duplicate'):
            assess(main_sha='a'*40,pr_head_sha='b'*40,compare=data)

    def test_query_preimage_and_counter_types_are_not_coerced(self):
        for field,value in (('ahead_by',True),('behind_by',-1),
                            ('total_commits','28'),('too_large','false')):
            with self.subTest(field=field):
                data=self.sample();data[field]=value
                with self.assertRaises(ValueError):
                    assess(main_sha='a'*40,pr_head_sha='b'*40,compare=data)

    def test_unchanged_diff_yields_hold_without_release_credit(self):
        data=self.sample();data.update({'base':'a'*40,'head':'a'*40,
            'base_commit':{'sha':'a'*40},'merge_base_commit':{'sha':'a'*40},
            'status':'identical','ahead_by':0,'behind_by':0,'total_commits':0,
            'files':[]})
        self.assertEqual(assess(main_sha='a'*40,pr_head_sha='a'*40,
                                compare=data)['decision'],'HOLD_NO_DIFF')

if __name__=='__main__':unittest.main()
