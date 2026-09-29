from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import analyze_audio_port_events as ape


def event(kind: str, port: int, value: int, sample: int, frame: int) -> dict:
    return {
        "t": kind,
        "adr": f"0x{port:02x}",
        "val": f"0x{value:02x}",
        "s": sample,
        "aux": frame,
    }


class AudioPortEventTests(unittest.TestCase):
    def test_applied_command_seen_by_spc(self) -> None:
        report = ape.analyze(
            [
                event("cpu_wr", 2, 0x31, 100, 10),
                event("cpu_ap", 2, 0x31, 104, 10),
                event("spc_rd", 2, 0x31, 111, 10),
            ]
        )
        self.assertTrue(report["has_apply_events"])
        self.assertEqual(report["candidate_command_count"], 1)
        cmd = report["commands"][0]
        self.assertEqual(cmd["fate"], "SEEN")
        self.assertEqual(cmd["apply_latency_samples"], 4)
        self.assertEqual(cmd["seen_latency_samples"], 7)

    def test_applied_command_replaced_before_spc_read_is_lost(self) -> None:
        report = ape.analyze(
            [
                event("cpu_wr", 0, 0x22, 100, 10),
                event("cpu_ap", 0, 0x22, 103, 10),
                event("cpu_wr", 0, 0x00, 120, 11),
                event("cpu_ap", 0, 0x00, 122, 11),
            ]
        )
        self.assertEqual(report["commands"][0]["fate"], "LOST")
        self.assertEqual(report["commands"][0]["replaced_by"]["value"], 0)

    def test_falls_back_to_cpu_write_without_apply_events(self) -> None:
        report = ape.analyze(
            [
                event("cpu_wr", 1, 0x44, 100, 20),
                event("spc_rd", 1, 0x44, 105, 20),
            ]
        )
        self.assertFalse(report["has_apply_events"])
        self.assertEqual(report["mutation_type"], "cpu_wr")
        self.assertEqual(report["commands"][0]["fate"], "SEEN")

    def test_zero_mutations_are_not_candidate_commands(self) -> None:
        report = ape.analyze(
            [
                event("cpu_ap", 3, 0x00, 1, 1),
                event("spc_rd", 3, 0x00, 2, 1),
            ]
        )
        self.assertEqual(report["candidate_command_count"], 0)


if __name__ == "__main__":
    unittest.main()
