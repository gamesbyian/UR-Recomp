"""Dependency-free near-duplicate original-source holdout grouping tests."""
import hashlib
import importlib.util
from pathlib import Path
import unittest

SCRIPT=Path(__file__).resolve().parents[2]/"tools/art/audit_original_racer_holdout_near_duplicates.py"
spec=importlib.util.spec_from_file_location("holdout_cluster",SCRIPT)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def make_mask(x0,y0,width=10,height=10,missing=()):
    mask=bytearray(4096)
    for y in range(y0,y0+height):
        for x in range(x0,x0+width):
            if (x,y) not in missing: mask[y*64+x]=1
    return bytes(mask)


def record(a,b):
    return {"unpaired_candidate_scores":
            {"1.0":{"mask_iou":a},"1.1":{"mask_iou":b}}}


class NearDuplicateTests(unittest.TestCase):
    def test_correlated_masks_receive_one_cluster_vote(self):
        a=make_mask(1,1)
        b=make_mask(1,1,missing=((1,1),))
        c=make_mask(40,40)
        masks={hashlib.sha256(x).hexdigest():x for x in (a,b,c)}
        groups,pairs=module.cluster_masks(masks,0.90)
        self.assertEqual(sorted(map(len,groups)),[1,2])
        self.assertEqual(len(pairs),3)
        self.assertGreater(max(pairs),0.95)
        scores={k:record(0.2,0.4) for k in masks}
        clusters=module.score_clusters(groups,scores)
        self.assertEqual(clusters["cluster_count"],2)
        self.assertEqual(clusters["cluster_sizes"],[2,1])
        self.assertEqual(clusters["equal_cluster_mean_baseline_iou"],0.2)
        self.assertEqual(clusters["equal_cluster_mean_wider_iou"],0.4)
        self.assertEqual(clusters["equal_cluster_wider_wins"],2)

    def test_threshold_monotonicity_and_source_hash(self):
        a=make_mask(1,1)
        b=make_mask(1,1,missing=((1,1),))
        c=make_mask(2,1)
        masks={hashlib.sha256(x).hexdigest():x for x in (a,b,c)}
        prior=0
        for threshold in module.THRESHOLDS:
            clusters,_=module.cluster_masks(masks,float(threshold))
            self.assertGreaterEqual(len(clusters),prior)
            prior=len(clusters)
        corrupted=dict(masks)
        corrupted[next(iter(masks))]=b"\x00"*4096
        with self.assertRaises(ValueError):
            module.cluster_masks(corrupted,0.90)

    def test_empty_or_nonbinary_source_and_duplicate_score_rejected(self):
        a=make_mask(3,4)
        b=make_mask(50,50)
        with self.assertRaisesRegex(ValueError,"binary"):
            module.mask_iou(a,b"\x02"*4096)
        with self.assertRaisesRegex(ValueError,"empty"):
            module.mask_iou(b"\x00"*4096,b"\x00"*4096)
        sha=hashlib.sha256(a).hexdigest()
        with self.assertRaises(ValueError):
            module.score_clusters([[sha],[sha]],{sha:record(0.2,0.3)})
        with self.assertRaises(ValueError):
            module.cluster_masks({sha:a},0.90)


if __name__=="__main__":
    unittest.main()
