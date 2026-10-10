"""Exact adjacent-frame identity is evidence, never guest-fidelity credit."""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import baldosa_2014_zoo_phase_equivalence as phase


REPORT = {
    "schema": "UR-QA01-ORIGINAL-BALDOSA-ZOO-FIXED-BOUNDARY/1",
    "complete_event_qa_credit": 0,
    "first_fixed_frame_result_menu": {"original": 5163, "native": 5162},
}


class AdjacentGuestMemoryTest(unittest.TestCase):
    def samples(self, root: Path):
        for name in ("original", "native"):
            folder = root / name
            folder.mkdir()
            for frame in range(5154, 5165):
                for suffix, size in phase.MEMORY.items():
                    value = frame % 251
                    if name == "native" and frame == 5156:
                        value = 5157 % 251  # Exact original next-frame copy.
                    (folder / f"boundary-{frame:05d}.{suffix}").write_bytes(
                        bytes([value]) * size)
        return root / "original", root / "native"

    def test_true_5155_anchor_and_5156_native_matches_5157_reference(self):
        with tempfile.TemporaryDirectory() as td:
            original, native = self.samples(Path(td))
            report = phase.analyze(original, native, REPORT, (5155, 5156))
            self.assertTrue(report["exact_source_wram_at_5155"])
            self.assertTrue(report["exact_full_guest_memory_native_5156_original_5157"])
            self.assertEqual(report["first_exact_next_reference_frame"], 5156)
            self.assertEqual(report["comparisons"]["5156"]["same_fixed_frame"]
                             ["groups"]["wram"]["differing_bytes"], 131072)
            self.assertEqual(report["comparisons"]["5156"]["reference_next_frame"]
                             ["groups"]["cgram"]["differing_bytes"], 0)
            self.assertEqual(report["complete_event_qa_credit"], 0)

    def test_rejects_absent_or_malformed_raw_and_false_provenance(self):
        with tempfile.TemporaryDirectory() as td:
            original, native = self.samples(Path(td))
            (original / "boundary-05157.vram.bin").write_bytes(b"short")
            with self.assertRaisesRegex(ValueError, "expected 65536 bytes"):
                phase.analyze(original, native, REPORT, (5155, 5156))
            with self.assertRaisesRegex(ValueError, "independent fixed-boundary"):
                phase.analyze(original, native, {**REPORT, "schema": "wrong"},
                              (5155,))
            with self.assertRaisesRegex(ValueError, "must not consume"):
                phase.analyze(original, native,
                              {**REPORT, "complete_event_qa_credit": 1}, (5155,))

    def test_same_frame_only_is_not_sufficient(self):
        with tempfile.TemporaryDirectory() as td:
            original, native = self.samples(Path(td))
            for suffix, size in phase.MEMORY.items():
                # Explicitly falsify the cross-frame copy while keeping
                # original/native at +5155 identical.
                (native / f"boundary-05156.{suffix}").write_bytes(b"Z" * size)
            report = phase.analyze(original, native, REPORT, (5155, 5156))
            self.assertTrue(report["exact_source_wram_at_5155"])
            self.assertFalse(report["exact_full_guest_memory_native_5156_original_5157"])


if __name__ == "__main__":
    unittest.main()
