"""Last Lap's consumer eligibility after original-ROM message queue admission."""
from __future__ import annotations

import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests/unit"))  # reuse only the synthetic regional fixture

import check_last_lap_consumer_eligibility as c  # noqa: E402
from test_extract_last_lap_reward_gate import fixture as lap_fixture, fake_report  # noqa: E402


class ConsumerEligibilityTests(unittest.TestCase):
    def fake(self, build="usa-retail", mapping=3):
        raw, lap = lap_fixture(build)
        data = bytearray(c.BLOCK_SIZE)
        data[c.TABLE_ORIGINAL - c.BLOCK_ORIGINAL + 0x0F - 1] = mapping
        info = {
            "island": "StuntMessageRewardDisplayPipeline",
            "regions": [{
                "name": c.DATA_NAME, "kind": "data", "usa_start": "81:C458",
                "size": c.BLOCK_SIZE,
                "builds": {build: {
                    "start": {
                        "usa-retail": "81:C458",
                        "legacy-beta": "81:C458",
                        "pal-prototype-1994-11-29": "81:C435",
                        "europe-retail": "81:C441"
                    }[build],
                    "sha256": hashlib.sha256(data).hexdigest(),
                }}
            }],
        }
        wram = bytearray(raw)
        start = c.rom_offset(info["regions"][0]["builds"][build]["start"])
        wram[start:start + len(data)] = data
        return bytes(wram), lap, info

    def test_regional_reachable_and_unreachable_mapping(self):
        for build in c.BUILDS:
            for value, status in ((0x03, "conditional_on_runtime_per_message_enable"),
                                  (0xFF, "blocked_by_0xFF_mapping")):
                with self.subTest(build=build, mapping=value):
                    rom, lap, data = self.fake(build, mapping=value)
                    got = c.check(rom, lap, fake_report(), data, build)
                    self.assertEqual(got["static_reachability"], status)
                    self.assertEqual(got["per_message_enable_gate"][:7], "7E:20F6")
                    self.assertEqual(got["signed_reward_if_gates_allow"], 152)

    def test_wrong_block_or_wrong_sha_fail_closed(self):
        rom, lap, data = self.fake()
        b = bytearray(rom)
        b[c.rom_offset("81:C458")] ^= 1
        with self.assertRaisesRegex(c.ConsumerEvidenceError, "SHA-256"):
            c.check(bytes(b), lap, fake_report(), data, "usa-retail")
        x = copy.deepcopy(data)
        x["regions"][0]["size"] = 281
        with self.assertRaisesRegex(c.ConsumerEvidenceError, "definition drifted"):
            c.check(rom, lap, fake_report(), x, "usa-retail")

    def test_original_roms_print_actual_consumer_eligibility(self):
        paths = {
            "usa-retail": ROOT / "reference/roms/retail/Uniracers_USA.sfc",
            "europe-retail": ROOT / "reference/roms/retail/Unirally_Europe.sfc",
            "pal-prototype-1994-11-29":
                ROOT / "reference/roms/prototypes/Unirally_1994-11-29_PAL_prototype.sfc",
            "legacy-beta": ROOT / "reference/roms/prototypes/Uniracers_Beta_legacy.sfc",
        }
        available = [name for name, p in paths.items() if p.is_file()]
        if not available:
            self.skipTest("preserved original ROMs absent")
        lap = json.loads(c.ISLAND.read_text(encoding="utf-8"))
        stunt = json.loads(c.STUNT_ISLAND.read_text(encoding="utf-8"))
        rewards = json.loads(c.REWARDS.read_text(encoding="utf-8"))
        retained = json.loads(
            (ROOT / "analysis/generated/last-lap-consumer-gate-verification.json")
            .read_text(encoding="utf-8")
        )
        self.assertEqual(retained["expected_message_mapping_byte"], "0xFF")
        for build in available:
            with self.subTest(build=build):
                result = c.check(paths[build].read_bytes(), lap, rewards, stunt, build)
                expected = retained["original_builds"][build]
                self.assertEqual(result["consumer_data_sha256"], expected["data_sha256"])
                self.assertEqual(
                    c.rom_offset(expected["map_address"]),
                    c.rom_offset(expected["data_block_start"]) +
                    retained["consumer_map_offset_from_verified_data_block"]
                )
                self.assertEqual(result["message_mapping_byte"], "0xFF")
                self.assertEqual(result["static_reachability"], "blocked_by_0xFF_mapping")
                self.assertIn("unreachable_through_this_consumer", result["runtime_award_status"])
                print("LAST_LAP_CONSUMER_ROM " + json.dumps(result, sort_keys=True), flush=True)


if __name__ == "__main__":
    unittest.main()
