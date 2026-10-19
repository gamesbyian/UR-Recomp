"""ROM-free checks for source-true noncausal temporal deltas and missing images."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa01_frame_delta_atlas as delta
import qa01_frame_fingerprint as frames


class FrameDeltaAtlasTests(unittest.TestCase):
    def make(self, root: Path, *, all_raw: bool = False):
        a = root / "original"
        b = root / "native"
        a.mkdir()
        b.mkdir()
        for rel in range(5):
            for guest, parent, origin in (("original", a, 1000),
                                          ("native", b, 2000)):
                wram = bytearray(frames.WRAM)
                sram = bytearray(frames.SRAM)
                wram[0x01ee] = 0xF0
                if guest == "native" and rel in (0, 2):
                    wram[0x01ee] = 0xEE
                if guest == "native" and rel == 2:
                    wram[0x0069] = 0xC1
                frames.snapshot_path(parent, origin+rel, "wram").write_bytes(wram)
                frames.snapshot_path(parent, origin+rel, "sram").write_bytes(sram)
        identity = {
            "source_sha": "a" * 40,
            "rom_sha256": "b" * 64,
            "movie_sha256": "c" * 64,
            "input_sha256": "d" * 64,
            "observation_phase": "post-script-dump",
            "original_frame_origin": 1000,
            "native_frame_origin": 2000,
            "masked_wram_bytes": 0,
            "masked_sram_bytes": 0,
        }
        retained = root / "retained"
        report = frames.audit(identity, a, b, 0, 4, retained=retained,
                              max_retained=5, retain_all_raw=all_raw)
        return report, retained

    def test_sparse_raw_scope_preserves_unknown_equal_interior_without_guessing(self):
        with tempfile.TemporaryDirectory() as tmp:
            report, retained = self.make(Path(tmp))
            census = delta.atlas(report, retained)
            self.assertEqual(census["equal_digest_only_frame_pairs_not_independently_reopened"],
                             [1, 3])
            self.assertEqual(census["full_original_native_raw_frame_pairs_independently_reopened"],
                             3)
            self.assertEqual(census["unmasked_original_native_byte_occurrences"],
                             {"wram": 3, "sram": 0})
            self.assertEqual(census["per_address_occurrences"]["7E:01EE"]["frames"],
                             [0, 2])
            self.assertEqual(census["per_address_occurrences"]["7E:0069"]["frames"],
                             [2])
            self.assertEqual(census["timeline"][1]["original_native_observed_deltas"],
                             None)
            self.assertIsNone(census["timeline"][2]["intra_guest_changes_since_previous"])
            self.assertFalse(census["first_genuinely_consumed_CPU_or_SPC_divergence_proven"])
            self.assertEqual(census["accepted_USA_events"], 0)

    def test_all_raw_retention_reopens_equal_frames_and_guest_transitions(self):
        with tempfile.TemporaryDirectory() as tmp:
            report, retained = self.make(Path(tmp), all_raw=True)
            census = delta.atlas(report, retained)
            self.assertEqual(census["equal_digest_only_frame_pairs_not_independently_reopened"],
                             [])
            self.assertEqual(census["full_original_native_raw_frame_pairs_independently_reopened"],
                             5)
            self.assertEqual(len(census["timeline"][1]["original_native_observed_deltas"]),0)
            self.assertEqual(census["timeline"][1]["intra_guest_changes_since_previous"]
                             ["native"]["wram"], 1)
            self.assertEqual(census["timeline"][2]["intra_guest_changes_since_previous"]
                             ["native"]["wram"], 2)
            self.assertEqual(census["timeline"][3]["intra_guest_changes_since_previous"]
                             ["native"]["wram"], 2)

    def test_actual_byte_tampering_missing_manifest_and_budget_fail_closed(self):
        for fault in ("tamper", "missing", "manifest", "budget"):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as tmp:
                report, retained = self.make(Path(tmp), all_raw=True)
                if fault == "budget":
                    with self.assertRaisesRegex(ValueError, "budget"):
                        delta.atlas(report, retained, max_deltas=1)
                    continue
                member = retained / "native-relative-000002-wram.bin"
                if fault == "tamper":
                    changed = bytearray(member.read_bytes())
                    changed[0x0069] ^= 3
                    member.write_bytes(changed)
                elif fault == "missing":
                    member.unlink()
                else:
                    report["raw_retained_members"].pop()
                with self.assertRaises(ValueError):
                    delta.atlas(report, retained)


if __name__ == "__main__":
    unittest.main()
