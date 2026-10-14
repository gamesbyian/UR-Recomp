"""QA-01 authentic-Zoo entry residue and byte-exact later guest-state negative gates."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa01_zoo_entry_state_crosswalk as mod


class ZooOriginalNativeEntryPair(unittest.TestCase):
    def setUp(self):
        self.entry = {"original": 1604, "native": 1606}
        self.receipts = {
            side: {f: host + f for f in range(5156, 5164)}
            for side, host in self.entry.items()
        }

    @staticmethod
    def frame(*, entry=False):
        wram = bytearray(mod.SIZES["wram"])
        wram[0x0313] = 1
        if entry:
            wram[0x00CE] = 1
        else:
            wram[0x009F] = 0x84
            wram[0x1199] = 1
            wram[0x119D] = 1
        return {"wram": bytes(wram), "vram": bytes(mod.SIZES["vram"]),
                "cgram": bytes(mod.SIZES["cgram"])}

    def snapshots(self):
        states = {
            side: {"entry": self.frame(entry=True),
                   **{f: self.frame() for f in range(5156, 5164)}}
            for side in ("original", "native")
        }
        for index, (expected_original, expected_native) in mod.ENTRY_BYTES.items():
            for side, val in (("original", expected_original), ("native", expected_native)):
                memory = bytearray(states[side]["entry"]["wram"])
                memory[index] = val
                states[side]["entry"]["wram"] = bytes(memory)
        for oframe, (wc, vc, cc) in mod.EXPECTED_RESIDUES.items():
            self.assertEqual(vc, 0)
            nframe = oframe - 1
            mem = bytearray(states["native"][nframe]["wram"])
            for at in range(wc):
                mem[0x01DB + at] = 1
            states["native"][nframe]["wram"] = bytes(mem)
            cg = bytearray(states["native"][nframe]["cgram"])
            for at in range(cc):
                cg[0xD8 + at] = 1
            states["native"][nframe]["cgram"] = bytes(cg)
        return states

    def evaluate(self, states=None, entries=None, receipts=None):
        return mod.evaluate(
            self.snapshots() if states is None else states,
            entries=self.entry if entries is None else entries,
            frame_receipts=self.receipts if receipts is None else receipts)

    def test_first_identical_guest_state_and_later_narrow_residues_are_not_acceptance(self):
        report = self.evaluate()
        self.assertEqual(
            [(x["offset"], x["original"], x["native"]) for x in
             report["entry_source_original_native_wram_differences"]],
            [(i, *ab) for i, ab in sorted(mod.ENTRY_BYTES.items())])
        self.assertEqual(report["exact_matched_pair"]["total_identical_bytes"], 197120)
        self.assertEqual(
            (report["exact_matched_pair"]["original_host"],
             report["exact_matched_pair"]["native_host"]), (6761, 6762))
        self.assertTrue(report["entry_vram_and_cgram_identical"])
        self.assertEqual(
            [list(x["difference_count_by_memory"].values()) for x in
             report["adjacent_aligned_residuals"]],
            [[4, 0, 8], [4, 0, 8], [5, 0, 8], [5, 0, 8], [13, 0, 0],
             [13, 0, 0]])
        self.assertFalse(report["scene_entry_predicate_source_cpu_authority_proven"])
        self.assertFalse(report["source_original_native_cpu_nmi_scanline_synchronized"])
        self.assertFalse(report["entry_candidate_7e2000_and_7e2004_owner_verified"])
        self.assertFalse(report["original_native_event_terminal_phase_equivalent"])
        self.assertEqual(report["release_complete_event_credit"], 0)

    def test_mutated_entrance_field_requires_new_source_evidence(self):
        states = self.snapshots()
        wram = bytearray(states["original"]["entry"]["wram"])
        wram[0x2008] = 1
        states["original"]["entry"]["wram"] = bytes(wram)
        with self.assertRaisesRegex(ValueError, "difference surface drifted"):
            self.evaluate(states)
        states = self.snapshots()
        wram = bytearray(states["native"]["entry"]["wram"])
        wram[0x0313] = 0
        states["native"]["entry"]["wram"] = bytes(wram)
        with self.assertRaisesRegex(ValueError, "difference surface drifted"):
            self.evaluate(states)

    def test_earlier_exact_full_memory_pair_cannot_silently_degrade(self):
        states = self.snapshots()
        cg = bytearray(states["native"][5156]["cgram"])
        cg[0xD8] = 1
        states["native"][5156]["cgram"] = bytes(cg)
        with self.assertRaisesRegex(ValueError, "197120-byte sample diverged"):
            self.evaluate(states)

    def test_other_equal_length_residue_outside_source_window_is_rejected(self):
        states = self.snapshots()
        raw = bytearray(states["native"][5157]["wram"])
        raw[0x01DB] = 0
        raw[0x2000] = 1
        states["native"][5157]["wram"] = bytes(raw)
        with self.assertRaisesRegex(ValueError, "outside observed scratch window"):
            self.evaluate(states)

    def test_missing_or_counterfeit_original_native_guest_receipts_fail(self):
        receipts = {s: dict(t) for s, t in self.receipts.items()}
        receipts["native"][5156] += 1
        with self.assertRaisesRegex(ValueError, "frame receipts drifted"):
            self.evaluate(receipts=receipts)
        with self.assertRaisesRegex(ValueError, "entry drifted"):
            self.evaluate(entries={"original": 1604, "native": 1605})

    def test_completely_unknown_zip_is_not_executed_original(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "unknown.zip"
            p.write_bytes(b"NOT the exact executed original/native guest ZIP")
            with self.assertRaisesRegex(ValueError, "exact executed"):
                mod.analyze(p)


if __name__ == "__main__":
    unittest.main()
