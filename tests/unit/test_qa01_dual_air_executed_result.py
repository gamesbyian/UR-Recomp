"""Synthetic corruption controls for the pinned real original/native dual-air report."""
from __future__ import annotations
import io
import json
import sys
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa01_dual_air_executed_result as m


class PairedExecutedDualAir(unittest.TestCase):
    def setUp(self):
        tags = ["two-player-both-post-1620"] + [f"endurance-{i}"
              for i in range(1740, 3421, 120)]
        tags.extend(["qa01-neighbor-2579", "qa01-neighbor-2581"])
        tags.sort(key=lambda tag: int(tag.rsplit("-", 1)[-1]))
        self.manifest = {"seed": 50036056, "checkpoints": tags}
        self.original = "\n".join(
            f"script f={int(tag.rsplit('-',1)[-1])} dump {tag} "
            "fb=256x224 RGB565 sram=8192 ppuw=1063" for tag in tags) + "\n"
        self.native = "\n".join(
            f"script f={int(tag.rsplit('-',1)[-1])} dump {tag} ok"
            for tag in tags) + "\n"
        sample = []
        for tag in tags:
            frame = int(tag.rsplit("-", 1)[-1])
            air = m.EXPECTED_AIR.get(frame, {"original": [0, 0], "native": [0, 0]})
            row = {"host_frame_label": tag}
            for side in ("original", "native"):
                row.update({
                    side + "_air_raw": air[side],
                    side + "_active_race_raw": 1,
                    side + "_progress": {"player1": {"laps_remaining": 1}},
                    side + "_velocity": [[0, (19 if frame == 2580 and
                                             side == "native" else 0)], [0, 0]],
                    side + "_xy": [[858 if frame >= 2580 and side == "native"
                                    else 857, 0], [0, 0]],
                })
            sample.append(row)
        import hashlib
        self.report = {
            "release_gate_credit": 0, "strict_complete_event_accepted": False,
            "paired_guest_relative_entry_offset_calibrated": False,
            "both_engine_actual_dump_frame_receipts_verified": True,
            "same_executable_as_frontier_witness": True,
            "original_wram_snapshots": 18, "native_wram_snapshots": 18,
            "raw_both_air_at_2580": {"original": False, "native": True},
            "active_race_at_2580": {"original": True, "native": True},
            "read_only_paired_samples": sample,
            "independent_emulator_frame_receipts": {
                side: {
                    "transcript_sha256": hashlib.sha256(log.encode()).hexdigest(),
                    "observed_frame_label_pairs": [
                        [int(tag.rsplit("-", 1)[-1]), tag] for tag in tags],
                }
                for side, log in (("original", self.original), ("native", self.native))
            },
        }

    def blob(self, *, report=None, original=None, native=None, manifest=None):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as z:
            z.writestr("paired-report.json", json.dumps(
                self.report if report is None else report))
            z.writestr("original.log", self.original if original is None else original)
            z.writestr("native.log", self.native if native is None else native)
            z.writestr("manifest.json", json.dumps(
                self.manifest if manifest is None else manifest))
        return buffer.getvalue()

    def test_synthetic_positive_still_has_no_release_credit(self):
        result = m.classify(self.blob(), verify_zip_hash=False)
        self.assertTrue(result["original_native_raw_air_discrepancy_at_2580"])
        self.assertFalse(result["source_native_same_host_frame_2580_raw_both_air_parity"])
        self.assertEqual(result["complete_event_credit"], 0)
        self.assertEqual(
            [x["original_raw_air"] for x in result["neighbor_three_frame_samples"]],
            [[0, 1], [0, 2], [0, 0]])
        self.assertEqual(
            [x["native_raw_air"] for x in result["neighbor_three_frame_samples"]],
            [[0, 1], [1, 2], [0, 0]])

    def test_synthetic_report_cannot_impersonate_real_executed_zip(self):
        with self.assertRaisesRegex(ValueError, "not the exact"):
            m.classify(self.blob())

    def test_raw_air_mutation_or_fake_release_gate_is_rejected(self):
        report = json.loads(json.dumps(self.report))
        next(row for row in report["read_only_paired_samples"]
             if row["host_frame_label"] == "endurance-2580")["original_air_raw"] = [1, 2]
        with self.assertRaisesRegex(ValueError, "raw air bytes differ"):
            m.classify(self.blob(report=report), verify_zip_hash=False)
        report = json.loads(json.dumps(self.report))
        report["release_gate_credit"] = 1
        with self.assertRaisesRegex(ValueError, "provenance or admission"):
            m.classify(self.blob(report=report), verify_zip_hash=False)

    def test_real_guest_log_clock_and_grammar_fail_closed(self):
        for mutated in (
            self.original.replace("script f=2580 dump", "script f=2581 dump"),
            self.original.replace("fb=256x224 RGB565", "ok"),
            self.original + "script f=2580 dump endurance-2580 "
                            "fb=256x224 RGB565 sram=8192 ppuw=1063\n",
        ):
            with self.subTest(mutated=mutated[-45:]), self.assertRaises(ValueError):
                m.classify(self.blob(original=mutated), verify_zip_hash=False)
        report = json.loads(json.dumps(self.report))
        import hashlib
        mutated = self.native.replace("dump endurance-2580 ok",
                                      "dump endurance-2580 partial")
        report["independent_emulator_frame_receipts"]["native"][
            "transcript_sha256"] = hashlib.sha256(mutated.encode()).hexdigest()
        with self.assertRaisesRegex(ValueError, "invalid actual native"):
            m.classify(self.blob(report=report, native=mutated), verify_zip_hash=False)

    def test_missing_sample_and_wrong_manifest_seed_fail(self):
        report = json.loads(json.dumps(self.report))
        report["read_only_paired_samples"] = report["read_only_paired_samples"][:-1]
        with self.assertRaisesRegex(ValueError, "18"):
            m.classify(self.blob(report=report), verify_zip_hash=False)
        manifest = dict(self.manifest, seed=50036057)
        with self.assertRaisesRegex(ValueError, "provenance"):
            m.classify(self.blob(manifest=manifest), verify_zip_hash=False)


if __name__ == "__main__":
    unittest.main()
