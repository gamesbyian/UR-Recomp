"""ROM-free A/B full-WRAM evidence and elapsed-time contract tests."""
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import compare_mesen_batch_replay as ab


class CompareMesenBatchTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.legacy = self.root / "legacy"
        self.batched = self.root / "batched"
        self.legacy.mkdir()
        self.batched.mkdir()
        self.rom = self.root / "rom.sfc"
        self.mesen = self.root / "Mesen"
        self.inp = self.root / "controls.input"
        self.script = self.root / "observe.script"
        self.old_log = self.root / "legacy.log"
        self.new_log = self.root / "batch.log"
        self.old_time = self.root / "old.time"
        self.new_time = self.root / "new.time"
        for file in (self.rom, self.mesen, self.inp):
            file.write_bytes(b"test-only-public-bytes")
        tags = [f"observed-{i}" for i in range(1, 7)]
        self.tags = tags
        self.script.write_text(
            "\n".join(f"wait 10\ndump {tag}" for tag in tags) + "\nquit\n"
        )
        rows = "\n".join(f"dump {tag}: frame={10 * n} bytes=131072"
                         for n, tag in enumerate(tags, 1)) + "\n"
        self.old_log.write_text(rows)
        self.new_log.write_text(rows)
        self.old_time.write_text("12.5\n")
        self.new_time.write_text("3.2\n")
        for tag in tags:
            (self.legacy / (tag + ".wram.bin")).write_bytes(bytes(131072))
            (self.batched / (tag + ".wram.bin")).write_bytes(bytes(131072))

    def measure(self):
        return ab.compare(
            source_sha="a" * 40, rom=self.rom, mesen=self.mesen,
            inp=self.inp, script=self.script, legacy=self.legacy,
            batched=self.batched, legacy_log=self.old_log,
            batched_log=self.new_log, legacy_time=self.old_time,
            batched_time=self.new_time)

    def test_every_named_full_source_snapshot_must_match(self):
        report = self.measure()
        self.assertTrue(report["exact_original_batched_parity"])
        self.assertEqual(len(report["source_observations"]), 6)
        self.assertEqual(report["release_gate_credit"], 0)
        self.assertFalse(report["independent_snes9x_hardware_or_native_parity"])
        self.assertEqual(report["replay_only_percent_time_reduction"], 74.4)

    def test_single_changed_byte_refuses_full_parity(self):
        data = bytearray(131072)
        data[0x69] = 42
        (self.batched / "observed-4.wram.bin").write_bytes(data)
        report = self.measure()
        self.assertFalse(report["exact_original_batched_parity"])
        self.assertEqual(report["first_wram_difference"],
                         {"tag": "observed-4", "offset": 0x69,
                          "legacy_byte": 0, "batched_byte": 42})

    def test_missing_or_extra_source_snapshot_fails_closed(self):
        (self.batched / "observed-4.wram.bin").unlink()
        with self.assertRaisesRegex(ValueError, "missing/excessive"):
            self.measure()

    def test_guest_frame_clock_difference_fails_closed(self):
        self.new_log.write_text(self.new_log.read_text().replace(
            "frame=40", "frame=41"))
        with self.assertRaisesRegex(ValueError, "milestones"):
            self.measure()

    def test_duplicate_or_missing_log_dump_fails_closed(self):
        self.old_log.write_text(self.old_log.read_text().replace(
            "dump observed-3: frame=30 bytes=131072", ""))
        with self.assertRaisesRegex(ValueError, "wrong/missing"):
            self.measure()

    def test_bad_time_and_nonfinite_time_fails_closed(self):
        self.new_time.write_text("nan\n")
        with self.assertRaisesRegex(ValueError, "invalid replay"):
            self.measure()

    def test_wrong_wram_size_fails_closed(self):
        (self.batched / "observed-4.wram.bin").write_bytes(bytes(32))
        with self.assertRaisesRegex(ValueError, "invalid full source WRAM"):
            self.measure()

    def test_symlinked_source_input_cannot_pass(self):
        link = self.root / "linked.script"
        try:
            link.symlink_to(self.script)
        except OSError:
            self.skipTest("symlink unavailable on this OS")
        with self.assertRaisesRegex(ValueError, "redirected immutable"):
            ab.compare(source_sha="a" * 40, rom=self.rom, mesen=self.mesen,
                       inp=self.inp, script=link, legacy=self.legacy, batched=self.batched,
                       legacy_log=self.old_log, batched_log=self.new_log,
                       legacy_time=self.old_time, batched_time=self.new_time)


if __name__ == "__main__":
    unittest.main()
