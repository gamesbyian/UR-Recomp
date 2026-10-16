"""QA-01 source-authentic 2014 Zoo whole-Circuit mesh, synthetic negatives only.

A fixed-movie original/native sparse 128-KiB checkpoint census has zero
admission authority. Never infer unobserved frames or CPU/AOT instruction time.
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import probe_original_event_complete as qa


class ZooFullRaceMeshTests(unittest.TestCase):
    def test_source_mesh_is_bounded_and_default_is_unchanged(self):
        regular = qa.sample_frames("zoom-zoo", 5163)
        dense = qa.sample_frames("zoom-zoo", 5163, zoo_race_mesh=True)
        self.assertEqual(regular[-1], 2400)
        self.assertEqual(len(dense), len(regular) + 24)
        self.assertTrue(set(regular).issubset(dense))
        self.assertEqual([f for f in dense if f > 2400],
                         [*range(2520, 5041, 120), 5100, 5120])
        self.assertEqual(dense[-1], 5120)
        self.assertEqual(qa.sample_frames("bowl", 3365),
                         qa.sample_frames("bowl", 3365, zoo_race_mesh=False))
        for case, duration in (("bowl", 5163), ("dragster", 5163),
                               ("zoom-zoo", 5162), ("zoom-zoo", 6000)):
            with self.subTest(case=case,duration=duration), self.assertRaisesRegex(
                    qa.CompleteEventError, "exact archived 2014 Zoo"):
                qa.sample_frames(case, duration, zoo_race_mesh=True)

    def test_executed_original_native_mesh_receipt_preserves_all_fail_gates(self):
        report = json.loads((ROOT / "analysis/data" /
            "qa01-zoo-fullrace-mesh-executed-20261015.json").read_text())
        self.assertEqual(report["source"]["run_id"], 38830671735)
        self.assertEqual(report["source"]["exact_workflow_head_sha"],
                         "2224b2414675c8191999510a9f6e6fcf40bf9a9c")
        self.assertEqual(report["source"]["case_artifact_zip_sha256"],
                         "886e533cf029f398af754699c6b7ba3c6a728623b6b7e4243469823bdcdb91f6")
        self.assertEqual(report["source"]["producer_report_sha256"],
                         "d377ba95dbf5e77bae141980a6d5962bda1b34e300372db8ac075fdc00018a6e")
        self.assertEqual(report["source"]["case_disposition"], "strict_candidate")
        data = report["observed"]
        self.assertEqual(data["fresh_native_entry_host_frame"] -
                         data["fresh_original_entry_host_frame"], 2)
        self.assertEqual(data["guest_result_relative_frame_original"], 5163)
        self.assertEqual(data["guest_result_relative_frame_native"], 5163)
        frames = qa.sample_frames("zoom-zoo", 5163, zoo_race_mesh=True)
        samples = data["full_wram_pairs"]
        self.assertEqual([s["relative_guest_frame"] for s in samples], frames)
        self.assertEqual(len(samples), 66)
        self.assertEqual(data["total_byte_exact_pairs"], 44)
        self.assertEqual(sum(not s["differing_full_wram_bytes"] for s in samples), 44)
        self.assertEqual(sum(s["differing_full_wram_bytes"] for s in samples), 86)
        self.assertEqual(len([s for s in samples if s["relative_guest_frame"] > 2400]), 24)
        self.assertEqual(data["excluded_wram_byte_count"], 0)
        self.assertEqual(data["full_wram_bytes_compared_per_guest_per_pair"], 131072)
        self.assertIsNone(data["original_native_sampled_named_state_first_disagreement"])
        self.assertEqual(data["distinct_differing_snes_addresses"], [
            "7E:0063","7E:0069","7E:01ED","7E:01EE",
            "7E:01EF","7E:01F0","7E:2000","7E:2004"])
        late = data["new_late_nonstack_difference"]
        self.assertEqual(late["guest_relative"], 5040)
        self.assertEqual(late["original_absolute_host_frame"], 6057)
        self.assertEqual(late["native_absolute_host_frame"], 6059)
        self.assertEqual(late["bytes"], [
            {"address":"7E:0063","original":115,"native":77},
            {"address":"7E:0069","original":190,"native":151}])
        self.assertTrue(late["subsequent_guest_relative_5100_all_wram_bytes_exact"])
        self.assertTrue(data["all_eleven_zoo_to_bowl_full_sram_pairs_equal"])
        self.assertEqual(data["bowl_active_entry_relative_to_zoo_result"], 267)
        self.assertEqual(data["zoo_earned_record_centiseconds"], 2510)
        limit = report["cautions"]
        self.assertTrue(limit["sample_interval_is_not_continuous_every_guest_frame"])
        self.assertFalse(limit["cpu_pc_nmi_apu_logic_tick_parity_proven"])
        self.assertFalse(limit["meaning_of_7e0063_and_7e0069_at_5040_proven"])
        self.assertFalse(limit["windows_shipping_binary_bound"])
        self.assertFalse(limit["host_filesystem_record_hard_kill_proven"])
        self.assertEqual(limit["complete_event_usa_credit"], 0)
        self.assertEqual(limit["usa_event_denominator"], 45)

    def test_script_keeps_all_original_input_and_samples_strictly_in_order(self):
        frames = qa.sample_frames("zoom-zoo", 5163, zoo_race_mesh=True)
        standard = qa.replay_script(2, 0xBC,
                                    qa.sample_frames("zoom-zoo", 5163), False)
        expanded = qa.replay_script(2, 0xBC, frames, False)
        self.assertTrue(expanded.startswith(qa.stock_crawler_script(2)))
        self.assertTrue(standard.startswith(qa.stock_crawler_script(2)))
        for frame in frames[1:]:
            self.assertEqual(expanded.count(f"dump scene-{frame:05d}\n"), 1)
        self.assertLess(expanded.index("dump scene-05120"),
                        expanded.index("until 009F == BC 9000"))
        self.assertEqual(expanded.count("until 009F == BC 9000"), 1)
        self.assertEqual(expanded.count("dump result-onset"), 1)

    def test_full_wram_and_host_receipts_not_sampled_field_substitution(self):
        frames = qa.sample_frames("zoom-zoo", 5163, zoo_race_mesh=True)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            a, b = root / "original", root / "native"
            a.mkdir()
            b.mkdir()
            reference_entry, native_entry = 1017, 1019
            original_log, native_log = [], []
            for frame in frames:
                name = "race-entered" if frame == 0 else f"scene-{frame:05d}"
                ref_raw = bytearray(0x20000)
                nat_raw = bytearray(0x20000)
                if frame == 2520:
                    ref_raw[0x2000] = 4
                    nat_raw[0x2000] = 3
                if frame == 5120:
                    ref_raw[0x1F2] = 37
                    nat_raw[0x1F2] = 39
                (a / f"{name}.wram.bin").write_bytes(ref_raw)
                (b / f"{name}.wram.bin").write_bytes(nat_raw)
                original_log.append(f"script f={reference_entry+frame} dump {name}\n")
                native_log.append(f"script f={native_entry+frame} dump {name}\n")
            olog, nlog = "".join(original_log), "".join(native_log)
            out = qa.observe_zoo_race_mesh(
                a, b, olog, nlog, frames, reference_entry, native_entry, 5163)
            self.assertEqual(out["mesh_checkpoint_count"], len(frames))
            self.assertEqual(out["new_post_2400_checkpoint_count"], 24)
            self.assertEqual(out["last_race_relative_checkpoint"], 5120)
            self.assertEqual(out["raw_byte_exact_sample_count"], len(frames)-2)
            self.assertEqual(out["masked_or_excluded_wram_bytes"], 0)
            self.assertFalse(out["cpu_instruction_or_logic_tick_parity_proven"])
            self.assertFalse(out["every_gameplay_frame_compared"])
            self.assertEqual(out["release_complete_usa_event_credit"], 0)
            first = out["first_nonidentical_raw_wram_pair"]
            self.assertEqual(first["race_relative_frame"], 2520)
            self.assertEqual(first["original_absolute_host_frame"], 3537)
            self.assertEqual(first["native_absolute_host_frame"], 3539)
            self.assertEqual(first["first_differing_address"], "7E:2000")
            self.assertEqual(first["differing_byte_count"], 1)
            late = out["samples"][-1][
                "original_native_full_wram_byte_difference"]
            self.assertEqual(late["differing_byte_count"], 1)
            self.assertEqual(late["first_differing_address"], "7E:01F2")
            with self.assertRaisesRegex(qa.CompleteEventError, "uncalibrated"):
                qa.observe_zoo_race_mesh(
                    a, b, olog.replace("script f=3537 dump", "script f=3538 dump"),
                    nlog, frames, reference_entry, native_entry, 5163)
            (b / "scene-02520.wram.bin").write_bytes(bytes(0x20000-1))
            with self.assertRaisesRegex(qa.CompleteEventError, "128-KiB"):
                qa.observe_zoo_race_mesh(
                    a, b, olog, nlog, frames, reference_entry, native_entry, 5163)
            (b / "scene-02520.wram.bin").unlink()
            with self.assertRaisesRegex(qa.CompleteEventError, "missing Zoo"):
                qa.observe_zoo_race_mesh(
                    a, b, olog, nlog, frames, reference_entry, native_entry, 5163)
            with self.assertRaisesRegex(qa.CompleteEventError, "missing or altered"):
                qa.observe_zoo_race_mesh(
                    a, b, olog, nlog, frames[:-1], reference_entry,
                    native_entry, 5163)


if __name__ == "__main__":
    unittest.main()
