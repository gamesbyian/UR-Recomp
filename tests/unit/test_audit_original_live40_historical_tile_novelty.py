"""ROM-free controls for exact original live 40 vs historic 35 tile ancestry."""
from __future__ import annotations
import json
from pathlib import Path
import unittest

from tools.art.audit_original_live40_historical_tile_novelty import (
    SCHEMA, exact_tiles, components,
)


class Live40SourceTileLineageTests(unittest.TestCase):
    def test_8x8_original_4bpp_content_excludes_blank_only(self):
        data=bytearray(4096)
        data[0]=1
        data[7*64+7]=2
        data[8]=3
        tiles=exact_tiles(bytes(data))
        self.assertEqual(len(tiles),2)
        self.assertTrue(all(len(x)==64 and any(x) for x in tiles))
        self.assertTrue(any(1 in x and 2 in x for x in tiles))
        self.assertEqual(exact_tiles(bytes(4096)),set())
        for bad in (b"",bytes(4095),bytes([16])+bytes(4095)):
            with self.subTest(bad=bad[:1]),self.assertRaisesRegex(ValueError,"64x64"):
                exact_tiles(bad)

    def test_new_original_tiles_respect_transitive_content_connections(self):
        a,b,c,d=(bytes([v])*64 for v in (1,2,3,4))
        rows=[
            {"tick":1601,"racer":"blue","tiles":{a},
             "shares_fit":True,"shares_withheld":False},
            {"tick":1607,"racer":"red","tiles":{a,b},
             "shares_fit":False,"shares_withheld":False},
            {"tick":1618,"racer":"blue","tiles":{b,c},
             "shares_fit":False,"shares_withheld":False},
            {"tick":1700,"racer":"red","tiles":{d},
             "shares_fit":False,"shares_withheld":False},
        ]
        groups=components(rows)
        self.assertEqual(sorted(len(x["original_ticks_and_racers"]) for x in groups),[1,3])
        combined=next(x for x in groups if len(x["original_ticks_and_racers"])==3)
        self.assertTrue(combined["has_exact_nonblank_tile_shared_with_precommitted_fit"])
        self.assertFalse(combined["has_exact_nonblank_tile_shared_with_precommitted_withheld"])
        isolated=next(x for x in groups if len(x["original_ticks_and_racers"])==1)
        self.assertFalse(isolated["has_exact_nonblank_tile_shared_with_precommitted_fit"])
        for bad in ([{**rows[0],"tiles":set()}],
                    [rows[0],dict(rows[0])],
                    [{**rows[0],"shares_fit":"yes"}],
                    [{**rows[0],"tiles":{b""}}],
                    []):
            with self.subTest(case=str(bad)[:55]),self.assertRaisesRegex(
                    ValueError,"original"):
                components(bad)

    def test_frozen_sha_bound_original_source_counts_and_negative_gates(self):
        path=Path(__file__).resolve().parents[2]/(
            "analysis/data/racer-original-live40-historical-tile-content-novelty-20261103.json")
        receipt=json.loads(path.read_text())
        self.assertEqual(receipt["schema"],SCHEMA)
        self.assertEqual(receipt["original_live_Mesen_source_zip_sha256"],
                         "709fbc2a1cd94b888d8ae0d43894c42c5d455bd968f6bc11f26e710f44e2788f")
        self.assertEqual(receipt["historical_verified_representations"],59)
        self.assertEqual(receipt["historical_4bpp_planes"],35)
        self.assertEqual(receipt["historical_nonblank_unique_tiles"],250)
        self.assertEqual(receipt["historical_nonblank_shared_pair_count"],170)
        self.assertEqual(receipt["frozen_historical_role_counts"],
                         {"fit":16,"withheld":19,"strict_six":6})
        self.assertEqual(receipt["new_live_40_source_summary"],{
            "source_frames":40,"known_historical_fit":1,
            "known_historical_withheld":1,"new_unclassified":38,
            "new_sharing_at_least_one_historical_fit_tile":29,
            "new_sharing_at_least_one_historical_withheld_tile":0,
            "new_sharing_no_historical_tile":9,
            "new_union_distinct_nonblank_tiles":307,
            "new_tile_contents_absent_in_historical_corpus":247,
            "all_live_40_source_pairs_sharing_content":86,
            "new_index_plane_tile_connected_components":11,
            "new_components_with_no_fit_or_withheld_tile_connection":3,
        })
        groups=receipt["live_new_38_content_components"]
        self.assertEqual(len(groups),11)
        self.assertEqual(sum(len(g["source_ticks_and_racers"]) for g in groups),38)
        clean=[g for g in groups if not g["shares_precommitted_fit_tile"] and
               not g["shares_precommitted_withheld_tile"]]
        self.assertEqual(sorted(len(g["source_ticks_and_racers"]) for g in clean),[1,4,4])
        # Freeze the actual original emulator identities of the three
        # tile-content-independent groups, not merely their sizes. Changing
        # membership can silently contaminate future pose evaluation.
        self.assertEqual(
            {tuple(tuple(v) for v in g["source_ticks_and_racers"])
             for g in clean},
            {
                ((1648,"blue"),(1671,"blue"),(1700,"blue"),(2011,"blue")),
                ((1671,"red"),(1700,"red"),(1731,"red"),(2283,"blue")),
                ((2445,"blue"),),
            })
        identities=[tuple(v) for g in groups for v in g["source_ticks_and_racers"]]
        self.assertEqual(len(identities),len(set(identities)))
        for key in ("historical_fit_or_withheld_index_membership_modified",
                    "new_live_sources_assigned_a_fitting_or_holdout_role",
                    "original_1994_three_dimensional_pose_labels_recovered",
                    "owner_likeness_approved"):
            self.assertFalse(receipt[key])


if __name__=="__main__":
    unittest.main()
