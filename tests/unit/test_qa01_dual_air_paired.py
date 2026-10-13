"""QA-01 dual-air exact legal-input reconstruction and fail-closed paired observer."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa01_dual_air_paired as m


class DualAirPaired(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.case = self.root / "case"

    def test_exact_source_plan_is_deterministic_and_cannot_overwrite(self):
        row = m.prepare(self.case)
        self.assertEqual(row["seed"], 50036056)
        self.assertEqual((row["arm"], row["shard"]), ("rotation", 2))
        self.assertEqual(row["first_source_observed_both_air_frame"], 2580)
        self.assertEqual(row["raw_air_addresses"], {"p1": "7E:0545", "p2": "7E:0547"})
        self.assertEqual(row["release_gate_credit"], 0)
        self.assertFalse(row["exact_original_native_acceptance"])
        self.assertEqual(len(row["checkpoints"]), 16)
        self.assertEqual(row["input_sha256"], m.sha(self.case / "case.input"))
        self.assertEqual(row["script_sha256"], m.sha(self.case / "case.script"))
        with self.assertRaisesRegex(ValueError, "overwrite"):
            m.prepare(self.case)

    def _make_dump(self, p: Path, air=(0, 0), active=True, split=True):
        data = bytearray(131072)
        data[0x0313] = 1 if active else 0
        data[0x0DDB] = 1 if split else 0
        data[0x0545], data[0x0547] = air
        p.write_bytes(data)

    def _evidence(self):
        row = m.prepare(self.case)
        original, native = self.root / "original", self.root / "native"
        original.mkdir()
        native.mkdir()
        for tag in row["checkpoints"]:
            p_air = (1, 2) if tag == "endurance-2580" else (0, 0)
            self._make_dump(original / (tag + ".wram.bin"), air=p_air)
            self._make_dump(native / (tag + ".wram.bin"), air=p_air)
        rom = self.root / "rom"
        core = self.root / "core"
        executable = self.root / "exe"
        for p in (rom, core, executable):
            p.write_bytes(p.name.encode())
        return row, original, native, rom, core, executable

    def test_synthetic_samples_can_only_be_classified_as_nonadmitting(self):
        row, original, native, rom, core, executable = self._evidence()
        with mock.patch.object(m, "ROM_SHA", m.sha(rom)):
            report = m.summarize(
                self.case / "manifest.json", original, native, rom, core, executable
            )
        self.assertEqual(report["raw_both_air_at_2580"],
                         {"original": True, "native": True})
        self.assertEqual(report["active_race_at_2580"],
                         {"original": True, "native": True})
        self.assertEqual(report["read_only_paired_samples"][8]["original_menu_raw"], 0)
        self.assertEqual(report["original_wram_snapshots"], 16)
        self.assertEqual(report["native_wram_snapshots"], 16)
        self.assertFalse(report["paired_guest_relative_entry_offset_calibrated"])
        self.assertEqual(report["release_gate_credit"], 0)
        self.assertFalse(report["strict_complete_event_accepted"])
        self.assertFalse(report["same_executable_as_frontier_witness"])

    def test_corrupted_input_or_wram_does_not_yield_observation(self):
        row, original, native, rom, core, executable = self._evidence()
        kwargs = dict(
            manifest_path=self.case / "manifest.json", original_dir=original,
            native_dir=native, rom=rom, core=core, native_exe=executable,
        )
        with mock.patch.object(m, "ROM_SHA", m.sha(rom)):
            (self.case / "case.input").write_text("altered")
            with self.assertRaisesRegex(ValueError, "mutated paired"):
                m.summarize(**kwargs)
            raw, _ = m.guest.base_source()
            actions, _ = m.frontier.actions_for(m.SEED, m.ARM)
            (self.case / "case.input").write_text(
                m.guest.render_input(raw, actions, None), encoding="utf-8")
            (original / "endurance-2580.wram.bin").write_bytes(b"short")
            with self.assertRaisesRegex(ValueError, "128-KiB"):
                m.summarize(**kwargs)

    def test_original_active_2p_is_a_precondition_not_assumed(self):
        _, original, native, rom, core, executable = self._evidence()
        kwargs = dict(
            manifest_path=self.case / "manifest.json", original_dir=original,
            native_dir=native, rom=rom, core=core, native_exe=executable,
        )
        with mock.patch.object(m, "ROM_SHA", m.sha(rom)):
            self._make_dump(original / (m.BASE + ".wram.bin"), split=False)
            with self.assertRaisesRegex(ValueError, "second camera"):
                m.summarize(**kwargs)
            self._make_dump(original / (m.BASE + ".wram.bin"), active=False)
            with self.assertRaisesRegex(ValueError, "active racing"):
                m.summarize(**kwargs)

    def test_reporter_keeps_absolute_host_axis_unadjusted(self):
        row, original, native, rom, core, executable = self._evidence()
        self._make_dump(native / "endurance-2580.wram.bin", air=(1, 0))
        with mock.patch.object(m, "ROM_SHA", m.sha(rom)):
            result = m.summarize(
                self.case / "manifest.json", original, native, rom, core, executable)
        self.assertEqual(result["raw_both_air_at_2580"],
                         {"original": True, "native": False})
        self.assertFalse(result["paired_guest_relative_entry_offset_calibrated"])
        self.assertTrue(result["source_frame_labels_are_host_ticks_not_event_relative_clocks"])
        self.assertFalse(result["strict_complete_event_accepted"])
        self.assertEqual(result["active_race_at_2580"],
                         {"original": True, "native": True})
        self.assertEqual(result["read_only_paired_samples"][8]["native_course_raw"], 0)


if __name__ == "__main__":
    unittest.main()
