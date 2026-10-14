"""Fail-closed original/native Zoo restore-anchored phase witness tests.

Synthetic memory fixtures are intentionally NOT genuine game evidence; only the
source-hash-pinned executed ZIP can establish the real three-stage result.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa01_zoo_restore_anchored_phase as probe


class RestoreAnchoredZooTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "executed-synthetic.zip"

    def fixtures(self, *, mutation=None):
        memory = {}
        logs = {}
        for side in ("original", "native"):
            entry = 1604 if side == "original" else 1606
            stage = probe.EVENTS[side]
            log = [f"script f={entry} dump scene-entered "
                   + ("fb=256x224 RGB565 sram=8192 ppuw=4"
                      if side == "original" else "ok")]
            for f in range(5156, 5164):
                b = bytearray(131072)
                b[0x009F] = (0x84 if f < stage["restore"] else
                             0xBC if f >= stage["result_text"] else 0x16)
                b[0x00CE] = 0 if f < stage["restore"] else 1
                b[0x0313] = (1 if f < stage["clear"] else
                             0x3D if f >= stage["result_text"] else 0)
                b[0x1199] = 1
                b[0x119D] = 1
                memory[f"{probe.DIRS[side]}/boundary-{f:05d}.wram.bin"] = bytes(b)
                log.append(f"script f={entry+f} dump boundary-{f:05d} "
                           + ("fb=256x224 RGB565 sram=8192 ppuw=4"
                              if side == "original" else "ok"))
            logs[probe.HOST_LOGS[side]] = "\n".join(log) + "\n"
        logs[probe.TRACE_LOGS["original"]] = "\n".join(
            probe.SOURCE_OPCODES.values()) + "\n"
        logs[probe.TRACE_LOGS["native"]] = "\n".join(
            probe.NATIVE_STORES.values()) + "\n"
        if mutation is not None:
            mutation(memory, logs)
        with ZipFile(self.path, "w") as z:
            for p, content in memory.items():
                z.writestr(p, content)
            for p, content in logs.items():
                z.writestr(p, content)
        return self.path

    def run_probe(self, mutation=None):
        return probe.analyze(self.fixtures(mutation=mutation),
                             expected_sha256=None)

    def test_equal_restoration_to_text_cadence_is_not_complete_event(self):
        d = self.run_probe()
        self.assertTrue(d["restoration_to_result_presentation_cadence_equal"])
        self.assertEqual(d["independently_reported_scene_entry_host_frames"],
                         {"original": 1604, "native": 1606})
        self.assertEqual(d["native_minus_original_entry_host_frames"], 2)
        self.assertEqual(d["native_minus_original_absolute_stage_host_frames"],
                         {"restore": 1, "clear": 1, "result_text": 1})
        self.assertEqual(d["elapsed_host_frames_since_observed_restore"],
                         {"restore": {"original": 0, "native": 0},
                          "clear": {"original": 4, "native": 4},
                          "result_text": {"original": 5, "native": 5}})
        self.assertTrue(d["source_and_native_genuine_result_both_observed"])
        self.assertFalse(d["artifact_identity_pinned"])
        self.assertFalse(d["source_native_course_finish_decision_instant_proven"])
        self.assertEqual(d["complete_event_release_credit"], 0)

    def test_unpinned_artifact_cannot_impersonate_original_execution(self):
        p = self.fixtures()
        with self.assertRaisesRegex(ValueError, "identity mismatch"):
            probe.analyze(p)  # the SHA is pinned by default

    def test_missing_or_duplicate_source_opcode_provenance_fails(self):
        def absent(mem, logs):
            logs["original-pc.log"] = logs["original-pc.log"].replace(
                probe.SOURCE_OPCODES["restore"] + "\n", "")
        with self.assertRaisesRegex(ValueError, "missing or duplicated"):
            self.run_probe(absent)

        def duplicate(mem, logs):
            logs["native-menu-writes.log"] += (
                probe.NATIVE_STORES["text_buffer"] + "\n")
        with self.assertRaisesRegex(ValueError, "missing or duplicated"):
            self.run_probe(duplicate)

    def test_changed_state_cannot_be_rephased_to_match(self):
        def changed(mem, logs):
            p = "native-boundary/dump/boundary-05161.wram.bin"
            raw = bytearray(mem[p])
            raw[0x0313] = 1
            mem[p] = bytes(raw)
        with self.assertRaisesRegex(ValueError, "clear-buffer"):
            self.run_probe(changed)

        def false_course(mem, logs):
            p = "original-boundary/boundary-05163.wram.bin"
            raw = bytearray(mem[p])
            raw[0x00CE] = 2
            mem[p] = bytes(raw)
        with self.assertRaisesRegex(ValueError, "genuine result-text"):
            self.run_probe(false_course)

        def false_laps(mem, logs):
            p = "original-boundary/boundary-05163.wram.bin"
            raw = bytearray(mem[p])
            raw[0x0EF1] = 1
            mem[p] = bytes(raw)
        with self.assertRaisesRegex(ValueError, "course progress changed"):
            self.run_probe(false_laps)

    def test_frame_receipts_must_match_independent_guest_ticks(self):
        def wrong_host(mem, logs):
            logs["original-boundary.log"] = logs["original-boundary.log"].replace(
                "script f=6767 dump boundary-05163",
                "script f=6766 dump boundary-05163")
        with self.assertRaisesRegex(ValueError, "mistimed"):
            self.run_probe(wrong_host)

        def missing(mem, logs):
            logs["native-boundary/log.txt"] = logs["native-boundary/log.txt"].replace(
                "script f=6768 dump boundary-05162 ok\n", "")
        with self.assertRaisesRegex(ValueError, "missing, duplicate or mistimed"):
            self.run_probe(missing)

    def test_corrupt_or_duplicate_full_wram_artifact_rejected(self):
        def shortened(mem, logs):
            p = "original-boundary/boundary-05158.wram.bin"
            mem[p] = mem[p][:-1]
        with self.assertRaisesRegex(ValueError, "incomplete"):
            self.run_probe(shortened)

        self.fixtures()
        with ZipFile(self.path, "a") as z:
            z.writestr("original-boundary/boundary-05158.wram.bin", b"duplicate")
        with self.assertRaisesRegex(ValueError, "duplicate"):
            probe.analyze(self.path, expected_sha256=None)


if __name__ == "__main__":
    unittest.main()
