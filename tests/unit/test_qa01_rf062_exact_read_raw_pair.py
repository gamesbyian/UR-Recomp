"""No-ROM tests for authentic native-PC / original opcode / raw host-frame crosswalk."""
from __future__ import annotations

import copy
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa01_frame_fingerprint as frames
import qa01_verify_frame_capture as raw
import qa01_rf062_exact_read_raw_pair as pair


class SoundFrameJoin(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        original, native, retained = (root / n for n in ("original", "native", "retained"))
        original.mkdir()
        native.mkdir()
        for guest, directory, origin in (("original", original, 6120),
                                         ("native", native, 6122)):
            for f in range(2, 5):
                wram = bytearray(131072)
                wram[0x63] = (0x30 + f + (0 if guest == "original" else 3))
                wram[0x69] = (0x70 + f + (0 if guest == "original" else 3))
                frames.snapshot_path(directory, origin + f, "wram").write_bytes(wram)
                frames.snapshot_path(directory, origin + f, "sram").write_bytes(bytes(8192))
        info = {
            "source_sha": "a"*40,
            "rom_sha256": "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478",
            "movie_sha256": "06dce29e9d36997fc2a1fac4bab72180ab6c8096366cfcf05780c1b2dea4b442",
            "input_sha256": "b"*64,
            "observation_phase": "post-script-dump",
            "original_frame_origin": 6120,
            "native_frame_origin": 6122,
            "masked_wram_bytes": 0,
            "masked_sram_bytes": 0,
        }
        self.fp = frames.audit(info, original, native, 2, 4, retained=retained)
        self.independent = raw.verify(self.fp, retained)
        self.retained = retained
        self.sound = {
            "schema": "ur-qa01-rf062-source-opcode-direct-native-bus/1",
            "actual_native_decoder_bound_read_count": 10,
            "actual_source_and_native_11C774_consumed_byte_same": True,
            "actual_native_opcode_pc": "8282F0",
            "original_native_clock_epochs_equivalent": False,
            "complete_USA_events_accepted": 0,
            "native_reads": [
                {"native_physical_operand": "11"+f"{0xC770+i:04X}",
                 "source_opcode_guest_PC": "8282F0",
                 "native_real_returned_byte": "D0" if i == 4 else "00",
                 "independent_rf054_real_helper_ordinal": 492 if i == 4 else i,
                 "native_independent_CPU_master": 1000 + i}
                for i in range(10)
            ],
        }

    def test_distinct_relative_frames_both_reopen_same_named_host_6124(self):
        # Actual test files and their saved manifest already use true distinct
        # original/native frame origins. No retrospective report relabeling.
        result = pair.correlate(self.sound, self.fp, self.independent, self.retained)
        self.assertEqual(result["reopened_raw_images_each_guest_at_its_own_host_frame"]
                         ["original"]["guest_relative_frame"], 4)
        self.assertEqual(result["reopened_raw_images_each_guest_at_its_own_host_frame"]
                         ["native"]["guest_relative_frame"], 2)
        self.assertFalse(result["original_native_relative_frame_offsets_same"])
        self.assertFalse(result["raw_sample_at_exact_CPU_bus_instruction_instant_proven"])
        self.assertFalse(result["original_native_instruction_clock_alignment_proven"])
        self.assertEqual(result["accepted_USA_events"], 0)

    def valid_rebased(self):
        # No synthetic relabeling: actual source files were created at the
        # claimed host frames, and audit() created the immutable manifest.
        pass

    def test_missing_original_at_true_host_fails(self):
        self.valid_rebased()
        (self.retained / "original-relative-000004-wram.bin").unlink()
        with self.assertRaises(ValueError):
            pair.correlate(self.sound, self.fp, self.independent, self.retained)

    def test_corrupt_native_actual_host_raw_rejected(self):
        self.valid_rebased()
        path = self.retained / "native-relative-000002-wram.bin"
        image = bytearray(path.read_bytes())
        image[0x63] ^= 1
        path.write_bytes(image)
        with self.assertRaises(ValueError):
            pair.correlate(self.sound, self.fp, self.independent, self.retained)

    def test_false_native_guest_PC_or_ROM_byte_rejected(self):
        self.valid_rebased()
        for field, changed in (("source_opcode_guest_PC", "8282F1"),
                               ("native_real_returned_byte", "D1")):
            forged = copy.deepcopy(self.sound)
            forged["native_reads"][4][field] = changed
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "native actual read"):
                pair.correlate(forged, self.fp, self.independent, self.retained)

    def test_wrong_original_guest_frame_origin_rejected(self):
        self.valid_rebased()
        self.fp["source_identity"]["original_frame_origin"] = 6121
        with self.assertRaises(ValueError):
            pair.correlate(self.sound, self.fp, self.independent, self.retained)

    def test_opcode_semantic_or_release_claim_rejected(self):
        self.valid_rebased()
        report = copy.deepcopy(self.fp)
        report["coverage"]["between_frame_opcode_semantics_proven"] = True
        with self.assertRaisesRegex(ValueError, "continuity"):
            pair.correlate(self.sound, report, self.independent, self.retained)
        sound = copy.deepcopy(self.sound)
        sound["original_native_clock_epochs_equivalent"] = True
        with self.assertRaisesRegex(ValueError, "opcode/source proof"):
            pair.correlate(sound, self.fp, self.independent, self.retained)


if __name__ == "__main__":
    unittest.main()
