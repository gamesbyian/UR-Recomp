"""Synthetic original/native 2508 full-byte cold snapshot artifact protections."""
from __future__ import annotations
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa01_dragster_cold_raw_archive as target


class DragsterColdRawTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.seed = bytearray(8192)
        self.seed[0x422:0x424] = (2508).to_bytes(2, "little")
        self.seed[0x54E:0x550] = (2508).to_bytes(2, "little")
        self.producer = {
            "name": "dragster", "course_id": "course:01",
            "original_source_event": {"original_result_frame": 2874},
            "comparison": {"paired_event_candidate": False},
            "dragster_next_zoo_handoff": {
                "release_complete_usa_event_credit": 0,
                "samples": [
                    {"offset_from_respective_dragster_result": k}
                    for k in (304, 308, 312, 314, 315, 316, 317, 318,
                              319, 320, 321, 324, 328)
                ] + [{"offset_from_respective_dragster_result": 336,
                      "fresh_guests": {
                          side: {"full_sram_sha256": target.sha(self.seed)}
                          for side in ("original", "native")}}],
            },
        }
        for name in ("rom_sha256", "original_movie_sha256",
                     "original_movie_window_sha256", "input_sha256",
                     "reference_core_sha256", "native_executable_sha256"):
            self.producer[name] = "a" * 64
        self.observations = [
            {"host_frame_since_fresh_boot": frame, "fresh_guests": {}}
            for frame in (300, 420)]
        self.cold = {
            "schema": target.COLD_SCHEMA,
            "source_earned_dragster_rank0_centiseconds": 2508,
            "two_independent_original_native_new_guest_processes": True,
            "source_seeds_from_actual_completed_race_plus_336": True,
            "release_complete_usa_event_credit": 0,
            "actual_windows_host_disk_autosave_power_cut_proven": False,
            "complete_original_native_dragster_event_parity_proven": False,
            "source_bound_identities": {
                k: self.producer[k] for k in (
                    "rom_sha256", "original_movie_sha256",
                    "original_movie_window_sha256", "input_sha256",
                    "reference_core_sha256", "native_executable_sha256")},
            "source_sram_digest_per_guest": {
                "original": target.sha(self.seed), "native": target.sha(self.seed)},
            "boot_observations": self.observations,
        }
        for side, folder in (("original", "ref"), ("native", "native")):
            seed_path = self.root / "dragster/replay" / folder / "dragster-next-zoo-336.sram.bin"
            seed_path.parent.mkdir(parents=True)
            seed_path.write_bytes(self.seed)
            lines = []
            for i, frame in enumerate((300, 420)):
                path = self.root / "cold-boot" / side / folder / f"cold-{frame}.sram.bin"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(self.seed)
                self.observations[i]["fresh_guests"][side] = {
                    "entire_battery_bytes": 8192,
                    "sram_sha256": target.sha(self.seed),
                    "ranked": target.ranked(self.seed)}
                lines.append(f"script f={frame} dump cold-{frame} ok")
            (self.root / "cold-boot" / f"{side}.log").write_text(
                "\n".join(lines)+"\n")
        self.write()

    def write(self):
        producer_path = self.root / "dragster-report.json"
        producer_path.write_text(json.dumps(self.producer))
        self.cold["producer_report_sha256"] = target.sha(producer_path.read_bytes())
        (self.root / "dragster-cold.json").write_text(json.dumps(self.cold))

    def test_actual_guest_full_byte_and_checksum_positive(self):
        result = target.audit(self.root)
        self.assertEqual(result["independently_rehashed_full_8k_sram_snapshots"], 4)
        self.assertTrue(result["source_earned_dragster_2508_preserved"])
        self.assertEqual(result["actual_cold_guest_host_frames"], [300, 420])
        self.assertFalse(result["actual_windows_host_disk_durability_proven"])
        self.assertEqual(result["accepted_usa_event_credit"], 0)

    def test_missing_corrupt_or_forged_cold_guest_is_not_success(self):
        path = self.root / "cold-boot/native/native/cold-420.sram.bin"
        image = bytearray(path.read_bytes())
        image[0x550] = 12
        path.write_bytes(image)
        with self.assertRaisesRegex(ValueError, "actual new guest cold record differs"):
            target.audit(self.root)
        path.unlink()
        with self.assertRaisesRegex(ValueError, "missing|short"):
            target.audit(self.root)
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(self.seed)
        log = self.root / "cold-boot/native.log"
        log.write_text(log.read_text().replace(
            "script f=300 dump cold-300", "script f=301 dump cold-300"))
        with self.assertRaisesRegex(ValueError, "incorrect host clock"):
            target.audit(self.root)

    def test_source_negative_ledger_and_checksum_guards(self):
        self.cold["release_complete_usa_event_credit"] = 1
        self.write()
        with self.assertRaisesRegex(ValueError, "cold result not"):
            target.audit(self.root)
        self.cold["release_complete_usa_event_credit"] = 0
        self.cold["source_bound_identities"]["rom_sha256"] = "0" * 64
        self.write()
        with self.assertRaisesRegex(ValueError, "IDs differ"):
            target.audit(self.root)


if __name__ == "__main__":
    unittest.main()
