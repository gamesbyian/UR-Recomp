"""ROM-free exact source-asset holdout selection and negative provenance gates."""
import unittest

from tools.art.freeze_original_racer_tile_disjoint_holdout import freeze, FIRST


A="a"*64
B="b"*64
C="c"*64
D="d"*64
E="e"*64


def edge(a,b,n):
    return {"left_source_index_sha256":a,
            "right_source_index_sha256":b,
            "shared_nonblank_exact_tile_contents":n}


class OriginalTileDisjointHoldoutTests(unittest.TestCase):
    def test_transitive_registry_windows_and_stricter_asset_control(self):
        windows={FIRST:{A}, "connected":{A,B}, "withheld-a":{C},
                 "withheld-b":{D,E}}
        report=freeze(windows,[edge(B,C,2),edge(C,E,3)])
        self.assertEqual(report["fit_connected_original_registry_windows"],
                         ["connected",FIRST])
        self.assertEqual(report["original_fitting_index_plane_shas"],[A,B])
        self.assertEqual(report["original_withheld_index_plane_shas"],[C,D,E])
        self.assertEqual(report["potential_fitting_to_withheld_pairs"],6)
        self.assertEqual(report["fitting_to_withheld_pairs_with_any_shared_exact_nonblank_tile"],1)
        self.assertEqual(report["fully_tile_disjoint_original_withheld_index_plane_shas"],[D,E])
        self.assertEqual(report["fitting_to_withheld_tile_overlap_histogram"],
                         {"0":5,"2":1})
        self.assertTrue(report["selection_uses_no_GLb_model_results"])
        self.assertFalse(report["source_original_3d_viewpoint_independence_verified"])

    def test_window_order_does_not_change_selection(self):
        windows={FIRST:{B,A}, "linked":{B}, "other":{C,D}}
        edges=[edge(D,B,1),edge(A,C,3)]
        a=freeze(windows,edges)
        b=freeze(dict(reversed(list(windows.items()))),list(reversed(edges)))
        self.assertEqual(a,b)
        self.assertEqual(a["fitting_to_withheld_pairs_with_any_shared_exact_nonblank_tile"],2)
        self.assertEqual(a["fully_tile_disjoint_original_withheld_index_plane_shas"],[])

    def test_reject_duplicate_tile_edges_in_reverse(self):
        windows={FIRST:{A}, "other":{B}}
        with self.assertRaisesRegex(ValueError,"duplicate"):
            freeze(windows,[edge(A,B,1),edge(B,A,1)])

    def test_reject_unregistered_planes_and_bad_counts(self):
        windows={FIRST:{A},"other":{B}}
        with self.assertRaisesRegex(ValueError,"unknown"):
            freeze(windows,[edge(A,C,1)])
        for invalid in (0,31,1.3,True):
            with self.subTest(invalid=invalid):
                with self.assertRaisesRegex(ValueError,"invalid source"):
                    freeze(windows,[edge(A,B,invalid)])

    def test_reject_synthetic_provenance_violations(self):
        with self.assertRaisesRegex(ValueError,"windows"):
            freeze({FIRST:{A}},[])
        with self.assertRaisesRegex(ValueError,"windows"):
            freeze({FIRST:{A},"other":{"not-a-sha"}},[])
        with self.assertRaisesRegex(ValueError,"no genuinely withheld"):
            freeze({FIRST:{A},"other":{A}},[])
        with self.assertRaisesRegex(ValueError,"windows"):
            freeze({FIRST:{A},"other":set()},[])

    def test_tile_disjoint_is_stricter_than_sha_disjoint_and_not_3d(self):
        windows={FIRST:{A},"other":{B}}
        matching=freeze(windows,[edge(A,B,7)])
        self.assertEqual(matching["original_withheld_planes"],1)
        self.assertFalse(matching["per_original_withheld_plane"][0]
                         ["tile_disjoint_from_every_fitted_original_plane"])
        no_match=freeze(windows,[])
        self.assertEqual(no_match["fully_tile_disjoint_original_withheld_index_plane_shas"],[B])
        self.assertFalse(no_match["source_live_ppu_sequence_verified"])
        self.assertFalse(no_match["original_source_to_model_pose_correspondence_verified"])

    def test_frozen_real_source_holdout_sha_identity_and_scope(self):
        import json
        from pathlib import Path
        path=(Path(__file__).resolve().parents[2] /
              "analysis/data/racer-original-strict-tile-disjoint-holdout-20261103.json")
        data=json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["actual_SHA_bound_source_workflow_run"],41556181251)
        self.assertEqual(data["original_source_manifest_sha256"],
                         "e26193f767d22280ab65b0549e707fa05ef246a903a4cebd47411f75726dc66e")
        self.assertEqual(data["source_4bpp_planes_in_fit"],16)
        self.assertEqual(data["source_4bpp_planes_in_withheld"],19)
        self.assertEqual(data["fit_to_withheld_exact_nonblank_tile_pair_histogram"],
                         {"0":291,"1":12,"7":1})
        fit=data["fit_original_index_plane_sha256"]
        held=data["withheld_original_index_plane_sha256"]
        strict=data["strictly_tile_disjoint_withheld_index_plane_sha256"]
        self.assertEqual(len(fit),16)
        self.assertEqual(len(held),19)
        self.assertEqual(len(strict),6)
        self.assertFalse(set(fit) & set(held))
        self.assertTrue(set(strict).issubset(held))
        self.assertEqual(len(set(fit+held)),35)
        for digest in fit+held:
            self.assertRegex(digest,r"\A[0-9a-f]{64}\Z")
        self.assertEqual(set(strict),
                         set(data["strictly_tile_disjoint_withheld_original_registry_representation_ids"]))
        self.assertFalse(data["source_original_live_PPU_timing_verified"])
        self.assertFalse(data["experimental_GLb_pose_correspondence_verified"])


if __name__=="__main__":
    unittest.main()
