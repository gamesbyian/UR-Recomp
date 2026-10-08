"""LoROM-verified Last Lap message queue gate, without runtime credit assumptions."""
from __future__ import annotations

import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import extract_last_lap_reward_gate as probe  # noqa: E402


def fake_report():
    return {"signed_words": [
        {"message_id": f"0x{i:02X}", "value": 152 if i == 15 else -1}
        for i in range(1, 22)
    ]}


def fixture(build: str, *, jsr: int | None = None, lap=0x17, mode=0x06):
    jsr = probe.QUEUE_JSR[build] if jsr is None else jsr
    pattern = (
        b"\xb9\xf1\x0e\xc9\x01\x00\xd0" + bytes((lap,)) +
        b"\xaf\x4b\x07\x77\x29\xff\x00\xf0" + bytes((mode,)) +
        b"\xa9\x0f\x00\x20" + jsr.to_bytes(2, "little")
    )
    block = bytes(31) + pattern + bytes(63 - 31 - len(pattern))
    start = {"usa-retail": "81:8195", "legacy-beta": "81:8195",
             "pal-prototype-1994-11-29": "81:8195", "europe-retail": "81:8187"}[build]
    isld = {"island": "Race_HandleCheckpointFinish", "regions": [
        {"name": "lap_hud", "usa_start": "81:8195", "size": 63, "builds": {
            build: {"start": start, "sha256": hashlib.sha256(block).hexdigest()}
        }}
    ]}
    buf = bytearray(0x10000)
    offset = probe.rom_offset(start)
    buf[offset:offset + len(block)] = block
    return bytes(buf), isld


class LastLapGateTests(unittest.TestCase):
    def test_synthetic_regional_queue_destinations(self):
        for build in probe.BUILDS:
            with self.subTest(build=build):
                rom, island = fixture(build)
                report = probe.extract(rom, island, fake_report(), build)
                self.assertEqual(report["signed_reward_lookup"], 152)
                self.assertEqual(report["enqueue_jsr"], f"81:{probe.QUEUE_JSR[build]:04X}")
                self.assertIn("unmeasured", report["runtime_status"])

    def test_wrong_rom_or_branch_or_helper_rejected(self):
        r, i = fixture("usa-retail")
        altered = bytearray(r)
        altered[probe.rom_offset("81:81B4")] ^= 1
        with self.assertRaisesRegex(probe.LastLapEvidenceError, "SHA-256"):
            probe.extract(bytes(altered), i, fake_report(), "usa-retail")
        for kwargs, message in (({"lap": 0x18}, "branch offsets"),
                                ({"mode": 0x07}, "branch offsets"),
                                ({"jsr": 0xC5B4}, "destination")):
            with self.subTest(kwargs=kwargs):
                r, i = fixture("usa-retail", **kwargs)
                with self.assertRaisesRegex(probe.LastLapEvidenceError, message):
                    probe.extract(r, i, fake_report(), "usa-retail")

    def test_malformed_lookup_rejected(self):
        r, i = fixture("usa-retail")
        q = fake_report()
        q["signed_words"][14]["value"] = 156
        with self.assertRaisesRegex(probe.LastLapEvidenceError, "magnitude"):
            probe.extract(r, i, q, "usa-retail")
        q = fake_report()
        q["signed_words"][14]["message_id"] = "0x0E"
        with self.assertRaisesRegex(probe.LastLapEvidenceError, "identity"):
            probe.extract(r, i, q, "usa-retail")

    def test_canonical_roms_when_available(self):
        paths = {
            "usa-retail": ROOT / "reference/roms/retail/Uniracers_USA.sfc",
            "europe-retail": ROOT / "reference/roms/retail/Unirally_Europe.sfc",
            "pal-prototype-1994-11-29":
                ROOT / "reference/roms/prototypes/Unirally_1994-11-29_PAL_prototype.sfc",
            "legacy-beta": ROOT / "reference/roms/prototypes/Uniracers_Beta_legacy.sfc",
        }
        island = json.loads(probe.ISLAND.read_text(encoding="utf-8"))
        reward = json.loads(probe.REWARDS.read_text(encoding="utf-8"))
        found = [b for b, path in paths.items() if path.exists()]
        if not found:
            self.skipTest("Original ROMs unavailable")
        for build in found:
            with self.subTest(build=build):
                result = probe.extract(paths[build].read_bytes(), island, reward, build)
                print("LAST_LAP_GATE_ROM " + json.dumps(result, sort_keys=True), flush=True)


if __name__ == "__main__":
    unittest.main()
