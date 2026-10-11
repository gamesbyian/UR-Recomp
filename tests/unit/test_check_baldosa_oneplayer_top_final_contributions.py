"""One-player source 98/99 final PPU visibility: actual removal, never RGB guess."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from tools.check_baldosa_oneplayer_top_final_contributions import inspect, FRAME
from tools.check_baldosa_wide_slot_final_visibility import HEADER, WIDTH, HEIGHT


class OnePlayerCounterfactualTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.stock = root / "stock" / f"ur-baldosa-ws342-{FRAME:06d}.pam"
        self.sources = {
            slot: root / f"source{slot}" /
            f"ur-baldosa-ws342-obj-slot{slot}-frame{FRAME:06d}.pam"
            for slot in (98, 99)
        }
        self.removed = {
            slot: root / f"removed{slot}" /
            f"ur-baldosa-ws342-{FRAME:06d}.pam" for slot in (98, 99)
        }
        self.logs = {slot: root / f"removed{slot}.log" for slot in (98, 99)}
        self.crcs = {key: root / f"{key}.crc" for key in
                     ("stock", "probe98", "probe99", "removed98", "removed99")}
        for crc in self.crcs.values():
            crc.write_bytes(b"a9ff1a00\n" * 5447)
        for slot in (98, 99):
            self.logs[slot].write_text(
                f"UR_RACER_HD_WIDE_REMOVE_SLOT frame={FRAME} slot={slot} "
                "status=armed guest_unchanged=1\n", encoding="utf-8")
        self.original = bytearray(bytes((20, 20, 20, 255)) * (WIDTH * HEIGHT))
        self.alpha = {slot: bytearray(WIDTH * HEIGHT * 4) for slot in (98, 99)}
        self.counter = {slot: bytearray(self.original) for slot in (98, 99)}
        # The first racer has a final contribution; the second emitted pixel
        # can be hidden behind a same-RGB background without a visible delta.
        self.pixel98 = 122 * WIDTH + 101
        self.pixel99 = 123 * WIDTH + 44
        self.set_rgba(self.alpha[98], self.pixel98, (7, 8, 9, 255))
        self.set_rgba(self.original, self.pixel98, (7, 8, 9, 255))
        self.set_rgba(self.counter[99], self.pixel98, (7, 8, 9, 255))
        self.set_rgba(self.alpha[99], self.pixel99, (20, 20, 20, 255))
        self.set_rgba(self.counter[98], self.pixel98, (20, 20, 20, 255))
        self.report = root / "source-report.json"
        self.write_sources()

    @staticmethod
    def set_rgba(data, pos, rgba):
        data[pos * 4:pos * 4 + 4] = bytes(rgba)

    @staticmethod
    def write_pam(path, rgba):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(HEADER + bytes(rgba))

    def write_sources(self):
        # Keep counterfactual at other slot's source pixel synchronized
        # with the final stock (only slot98 removal changes pixel98).
        self.write_pam(self.stock, self.original)
        for slot in (98, 99):
            self.write_pam(self.sources[slot], self.alpha[slot])
            self.write_pam(self.removed[slot], self.counter[slot])
        records = []
        for slot in (98, 99):
            source = bytes(self.alpha[slot])
            records.append({
                "original_oam_slot": slot,
                "rgba_sha256": hashlib.sha256(source).hexdigest(),
                "native_source": {"top_opaque_source_pixels": 1,
                                  "bottom_opaque_source_pixels": 0},
                "rgb_vs_final_observation": {"isolated_source_opaque": 1},
            })
        self.report.write_text(json.dumps({
            "status": "native-1p-paired-top-oam-source-truth",
            "native_guest_frame": FRAME,
            "native_original_guest_crc_identical": 5447,
            "native_1x_and_4x_source_frames_identical": 7,
            "independent_original_guest_processes": 5,
            "no_sprite_removal_or_guest_mutation": True,
            "source_slot_emission_accepted": True,
            "individual_final_bg_or_obj_priority_accepted": False,
            "authored_hd_or_wide_replacement_accepted": False,
            "original_top_slot98_and_slot99_sources": records,
        }), encoding="utf-8")

    def assess(self):
        return inspect(self.stock, self.sources, self.removed, self.crcs,
                       self.logs, self.report)

    def test_real_ppu_delta_proves_single_slot_not_rgb_only(self):
        result = self.assess()
        self.assertEqual(result["status"],
                         "native-oneplayer-paired-single-slot-final-counterfactual")
        self.assertEqual(result["slots"]["98"]["source_emitted_alpha_pixels"], 1)
        self.assertEqual(result["slots"]["98"]["changed_final_ppu_pixels_after_native_slot_removal"], 1)
        self.assertEqual(result["slots"]["99"]["changed_final_ppu_pixels_after_native_slot_removal"], 0)
        self.assertEqual(result["slots"]["99"]["source_emitted_but_no_final_delta"], 1)
        self.assertEqual(result["slots"]["98"]["changed_raster_112_223"], 1)
        self.assertEqual(result["slots"]["98"]["bounded_changed_original_xy_examples"],
                         [[101, 122]])
        self.assertEqual(result["emitted_source_coordinate_overlap"], 0)
        self.assertEqual(result["distinct_changed_final_ppu_coordinates"], 1)
        self.assertTrue(result["any_native_final_contribution_proven"])
        self.assertFalse(result["authored_hd_replacement_or_sprite_removal_admitted"])

    def test_an_entirely_hidden_source_is_a_valid_proven_negative(self):
        self.counter[98][:] = self.original
        self.counter[99][:] = self.original
        self.write_sources()
        result = self.assess()
        self.assertFalse(result["any_native_final_contribution_proven"])
        self.assertEqual(result["distinct_changed_final_ppu_coordinates"], 0)
        self.assertTrue(result["complete_per_slot_final_visibility_proven"])

    def test_changes_outside_emitted_alpha_fail_closed(self):
        self.set_rgba(self.counter[98], 200 * WIDTH + 220, (5, 5, 5, 255))
        self.write_sources()
        with self.assertRaisesRegex(ValueError, "outside OBJ alpha"):
            self.assess()

    def test_wrong_guest_crc_provenance_rejected(self):
        self.crcs["removed98"].write_bytes(b"ffffffff\n" * 5447)
        with self.assertRaisesRegex(ValueError, "5447-frame guest CRC"):
            self.assess()

    def test_missing_native_remove_marker_and_duplicate_rejected(self):
        self.logs[98].write_text("read-only capture\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "missing/duplicate"):
            self.assess()
        self.logs[98].write_text(
            (f"UR_RACER_HD_WIDE_REMOVE_SLOT frame={FRAME} slot=98 "
             "status=armed guest_unchanged=1\n") * 2, encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "missing/duplicate"):
            self.assess()

    def test_swapped_source_hash_rejected(self):
        self.sources[99].write_bytes(self.sources[98].read_bytes())
        with self.assertRaisesRegex(ValueError, "SHA mismatch"):
            self.assess()

    def test_identical_removed_file_and_stock_rejected(self):
        self.removed[98] = self.stock
        with self.assertRaisesRegex(ValueError, "alias Original"):
            self.assess()

    def test_losing_native_source_report_review_rejects(self):
        data = json.loads(self.report.read_text())
        data["source_slot_emission_accepted"] = False
        self.report.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "missing accepted"):
            self.assess()

    def test_workflow_reuses_one_native_AOT_for_readonly_oneplayer_deltas(self):
        workflow = (Path(__file__).resolve().parents[2] /
                    ".github/workflows/baldosa-core-spike.yml").read_text()
        self.assertIn("tools/check_baldosa_oneplayer_top_final_contributions.py", workflow)
        self.assertIn("race_1p_ur_ws342_counterfactual_slot", workflow)
        self.assertIn("for slot in 98 99; do", workflow)
        self.assertIn("UR_RACER_HD_WIDE_REMOVE_FRAME=2208", workflow)
        self.assertIn("UR_RACER_HD_WIDE_REMOVE_DIAGNOSTIC=counterfactual", workflow)
        self.assertIn("UR_RACER_HD_WIDE_SOURCE_SLOT", workflow)


if __name__ == "__main__":
    unittest.main()
