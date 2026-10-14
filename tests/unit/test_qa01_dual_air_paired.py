"""QA-01 dual-air exact legal-input reconstruction and fail-closed paired observer."""
from __future__ import annotations

import json
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
        self.assertEqual(len(row["checkpoints"]), 18)
        self.assertEqual(row["checkpoints"][8:11],
                         ["qa01-neighbor-2579", "endurance-2580",
                          "qa01-neighbor-2581"])
        generated = (self.case / "case.script").read_text()
        self.assertIn("wait 119\ndump qa01-neighbor-2579\nwait 1\ndump endurance-2580",generated)
        self.assertIn("wait 1\ndump qa01-neighbor-2581\nwait 119\ndump endurance-2700",generated)
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
        for side in ("original", "native"):
            lines = []
            for tag in row["checkpoints"]:
                frame = 1620 if tag == m.BASE else int(tag.rsplit("-", 1)[-1])
                lines.append(f"script f={frame} dump {tag} ok")
            (self.root / (side + ".log")).write_text(
                "guest started\n" + "\n".join(lines) + "\n",encoding="utf-8")
        # Synthetic ROM stand-in is intentionally not canonical: patch only
        # the isolated manifest and ROM identity expected by these tests.
        manifest_path = self.case / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["original_rom_sha256"] = m.sha(rom)
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        return row, original, native, rom, core, executable

    def test_synthetic_samples_can_only_be_classified_as_nonadmitting(self):
        row, original, native, rom, core, executable = self._evidence()
        with mock.patch.object(m, "ROM_SHA", m.sha(rom)):
            report = m.summarize(
                self.case / "manifest.json", original, native, rom, core, executable,
                self.root / "original.log", self.root / "native.log"
            )
        self.assertEqual(report["raw_both_air_at_2580"],
                         {"original": True, "native": True})
        self.assertEqual(report["active_race_at_2580"],
                         {"original": True, "native": True})
        self.assertEqual(report["read_only_paired_samples"][9]["original_menu_raw"], 0)
        self.assertEqual(report["original_wram_snapshots"], 18)
        self.assertEqual(report["native_wram_snapshots"], 18)
        self.assertFalse(report["paired_guest_relative_entry_offset_calibrated"])
        self.assertEqual(report["release_gate_credit"], 0)
        self.assertFalse(report["strict_complete_event_accepted"])
        self.assertFalse(report["same_executable_as_frontier_witness"])
        self.assertEqual(
            [(v["host_frame"],v["original_both_air_raw"],v["native_both_air_raw"])
             for v in report["three_frame_host_phase_window"]],
            [(2579,False,False),(2580,True,True),(2581,False,False)])
        self.assertTrue(report["neighbor_frames_are_diagnostic_not_clock_normalization"])
        self.assertTrue(report["both_engine_actual_dump_frame_receipts_verified"])
        self.assertEqual(
            report["independent_emulator_frame_receipts"]["original"][
                "observed_frame_label_pairs"][9],
            (2580, "endurance-2580"))
        self.assertEqual(
            report["independent_emulator_frame_receipts"]["native"][
                "observed_frame_label_pairs"][8],
            (2579, "qa01-neighbor-2579"))

    def test_corrupted_input_or_wram_does_not_yield_observation(self):
        row, original, native, rom, core, executable = self._evidence()
        kwargs = dict(
            manifest_path=self.case / "manifest.json", original_dir=original,
            native_dir=native, rom=rom, core=core, native_exe=executable,
            original_log=self.root / "original.log", native_log=self.root / "native.log",
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

    def test_missing_duplicate_or_wrong_clock_never_passes_as_source_air_parity(self):
        _, original, native, rom, core, executable = self._evidence()
        kwargs = dict(
            manifest_path=self.case / "manifest.json",original_dir=original,
            native_dir=native,rom=rom,core=core,native_exe=executable,
            original_log=self.root / "original.log",
            native_log=self.root / "native.log")
        original_text = (self.root / "original.log").read_text()
        native_text = (self.root / "native.log").read_text()
        with mock.patch.object(m, "ROM_SHA", m.sha(rom)):
            # File labels and complete WRAM snapshots still exist; the guest
            # itself must confirm the ACTUAL frame it wrote each one.
            for transcript in (
                native_text.replace("script f=2580 dump endurance-2580 ok",
                                    "script f=2581 dump endurance-2580 ok"),
                native_text.replace("script f=2580 dump endurance-2580 ok", ""),
                native_text + "script f=2580 dump endurance-2580 ok\n",
                native_text.replace("script f=2579 dump qa01-neighbor-2579 ok",
                                    "script f=2580 dump qa01-neighbor-2579 ok"),
            ):
                (self.root / "native.log").write_text(transcript)
                with self.subTest(transcript=transcript[-100:]),self.assertRaisesRegex(
                        ValueError,"real guest dump frame receipts"):
                    m.summarize(**kwargs)
            (self.root / "native.log").write_text(native_text)
            (self.root / "original.log").write_text(
                original_text.replace("script f=2580 dump endurance-2580 ok",
                                      "script f=2579 dump endurance-2580 ok"))
            with self.assertRaisesRegex(ValueError,"original real guest dump frame"):
                m.summarize(**kwargs)
            (self.root / "original.log").unlink()
            with self.assertRaisesRegex(ValueError,"missing or symlinked"):
                m.summarize(**kwargs)

    def test_original_active_2p_is_a_precondition_not_assumed(self):
        _, original, native, rom, core, executable = self._evidence()
        kwargs = dict(
            manifest_path=self.case / "manifest.json", original_dir=original,
            native_dir=native, rom=rom, core=core, native_exe=executable,
            original_log=self.root / "original.log", native_log=self.root / "native.log",
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
                self.case / "manifest.json", original, native, rom, core, executable,
                self.root / "original.log", self.root / "native.log")
        self.assertEqual(result["raw_both_air_at_2580"],
                         {"original": True, "native": False})
        self.assertFalse(result["paired_guest_relative_entry_offset_calibrated"])
        self.assertTrue(result["source_frame_labels_are_host_ticks_not_event_relative_clocks"])
        self.assertFalse(result["strict_complete_event_accepted"])
        self.assertEqual(result["active_race_at_2580"],
                         {"original": True, "native": True})
        self.assertEqual(result["read_only_paired_samples"][9]["native_course_raw"], 0)


if __name__ == "__main__":
    unittest.main()
