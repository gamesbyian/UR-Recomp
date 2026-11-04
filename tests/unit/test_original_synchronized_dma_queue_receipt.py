"""Check original executed 65816 composer queue against unchanged ROM destination rule.

This receipt was produced by one original pinned MesenCE run, not a synthetic
queue reconstruction or prospective 1994 3D pose inference.
"""
import hashlib
import json
from pathlib import Path
import unittest
from collections import Counter

from tools.art.audit_original_rom_rider_phase_dma import nmi_effective_vram_word

ROOT=Path(__file__).resolve().parents[2]
PATH=ROOT/"analysis/data/racer-original-synchronized-composer-1218-20261103.json"
SHA="8ac053ec3c19f16abeac535e19b51a2faf4a617410378de3d71aea34fb20d825"


class ExecutedSynchronizedComposerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=PATH.read_bytes()
        cls.receipt=json.loads(cls.data)

    def test_exact_runtime_original_receipt_and_breakpoints(self):
        self.assertEqual(hashlib.sha256(self.data).hexdigest(),SHA)
        p=self.receipt
        self.assertEqual(p["schema_version"],1)
        self.assertEqual(p["breakpoints"]["pre"]["cpu"],"83:F129")
        self.assertEqual(p["breakpoints"]["post"]["cpu"],"83:F292")
        a=p["breakpoints"]["pre"]["hit"]
        b=p["breakpoints"]["post"]["hit"]
        self.assertEqual(a["pcDisplay"],"$83:F129")
        self.assertEqual(b["pcDisplay"],"$83:F292")
        self.assertEqual(a["frame"],1218)
        self.assertEqual(b["frame"],1218)
        self.assertEqual(a["pcBank"],0x83)
        self.assertEqual(b["pcBank"],0x83)
        self.assertLess(a["cpuCycleCount"],b["cpuCycleCount"])
        self.assertLess(a["masterClock"],b["masterClock"])

    def test_original_executed_frame_ids_and_composer_masks(self):
        p=self.receipt
        self.assertEqual(p["ids"],{"p1_primary":"0x0541","p2_primary":"0x0540",
                                   "p1_companion":"0x0D0D","p2_companion":"0x0000"})
        self.assertEqual(p["selectors"],{"p1":0,"p2":0})
        self.assertEqual(p["companion_enabled"],{"p1":True,"p2":False})
        self.assertTrue(p["mask_checks"]["primary_exact"])
        self.assertTrue(p["mask_checks"]["companion_raw_exact"])

    def test_all_25_executed_graphics_sources_and_queued_destinations(self):
        s=self.receipt["staging"]
        self.assertEqual(s["descriptor_count"],25)
        self.assertEqual(s["occupied_cells"],25)
        self.assertEqual(s["occupied_sources_exact"],25)
        self.assertEqual(s["occupied_destinations_present"],25)
        self.assertTrue(s["all_occupied_destinations_present"])
        self.assertTrue(s["all_occupied_sources_exact"])
        rows=s["cells"]
        self.assertEqual(len(rows),25)
        self.assertTrue(all(row["source_exact"] and row["matching_slots"] for row in rows))
        count=Counter()
        for row in rows:
            effective=nmi_effective_vram_word(int(row["vram_word"],16))
            if 0x6000<=effective<=0x6780:
                count["red_source_obj_region"]+=1
            elif 0x6880<=effective<=0x6ff0:
                count["blue_source_obj_region"]+=1
            else:
                count["outside_held_original_racer_sprite_regions"]+=1
        self.assertEqual(dict(count),{
            "red_source_obj_region":12,
            "blue_source_obj_region":13,
        })

    def test_original_queue_source_rows_keep_actual_player_attribution(self):
        rows=self.receipt["staging"]["cells"]
        self.assertEqual(set(row["player"] for row in rows),{"p1","p2"})
        self.assertEqual(set(row["choice"] for row in rows),{
            "p1_primary","p1_companion","p2_primary"})
        self.assertTrue(all(row["expected_source"].count(":")==1
                            and isinstance(row["column"],int)
                            and isinstance(row["row"],int)
                            for row in rows))


if __name__=="__main__":
    unittest.main()
