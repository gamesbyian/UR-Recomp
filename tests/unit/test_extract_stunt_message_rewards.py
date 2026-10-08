"""Synthetic-ROM acceptance for the original message-to-boost lookup."""
from __future__ import annotations

import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from extract_stunt_message_rewards import (  # noqa: E402
    RewardEvidenceError, extract, rom_offset, BUILDS,
)


class RewardTableTests(unittest.TestCase):
    def setUp(self):
        self.aliases = {"schema_version": 1, "mapping": [
            {"message_id": "0x01", "name": "Roll", "boost": 128},
            {"message_id": "0x11", "name": "Tabletop", "boost": 152},
            {"message_id": "0x15", "name": "Z Flip City", "boost": 200},
        ]}
        self.block = bytearray(282)
        for i in range(1, 22):
            v = -1
            if i == 1:
                v = 128
            if i == 0x11:
                v = 152
            if i == 0x15:
                v = 200
            pos = (0xC4AA - 0xC458) + 2 * (i - 1)
            self.block[pos:pos + 2] = v.to_bytes(2, "little", signed=True)
        digest = hashlib.sha256(self.block).hexdigest()
        self.structure = {
            "island": "StuntMessageRewardDisplayPipeline",
            "regions": [{"name": "message_reward_lookup_block", "kind": "data",
                         "usa_start": "81:C458", "size": 282, "builds": {
                build: {"start": f"81:{0xC458 + shift:04X}", "sha256": digest}
                for build, shift in [
                    ("usa-retail", 0), ("legacy-beta", 0),
                    ("pal-prototype-1994-11-29", -35), ("europe-retail", -23)
                ]
            }}],
        }
    def build_rom(self, build):
        rom = bytearray(0x10000)
        start = rom_offset(self.structure["regions"][0]["builds"][build]["start"])
        rom[start:start + len(self.block)] = self.block
        return bytes(rom)

    def test_build_specific_relocation_and_signed_words(self):
        for build in BUILDS:
            with self.subTest(build=build):
                report = extract(self.build_rom(build), self.structure, self.aliases, build)
                self.assertEqual(report["historical_disagreements"], [])
                self.assertEqual(len(report["raw_signed_words"]), 21)
                self.assertEqual(report["raw_signed_words"][0]["value"], 128)
                self.assertEqual(report["raw_signed_words"][1]["value"], -1)
                self.assertEqual(report["raw_signed_words"][0x10]["value"], 152)
                self.assertEqual(report["raw_signed_words"][0x14]["value"], 200)

    def test_actual_preserved_roms_when_available(self):
        paths = {
            "usa-retail": ROOT / "reference/roms/retail/Uniracers_USA.sfc",
            "europe-retail": ROOT / "reference/roms/retail/Unirally_Europe.sfc",
            "pal-prototype-1994-11-29":
                ROOT / "reference/roms/prototypes/Unirally_1994-11-29_PAL_prototype.sfc",
            "legacy-beta": ROOT / "reference/roms/prototypes/Uniracers_Beta_legacy.sfc",
        }
        structure = json.loads(
            (ROOT / "analysis/generated/stunt-message-pipeline-structure-island.json")
            .read_text(encoding="utf-8")
        )
        aliases = json.loads(
            (ROOT / "analysis/generated/dessyreqt-named-boost-messages.json")
            .read_text(encoding="utf-8")
        )
        retained = json.loads(
            (ROOT / "analysis/generated/stunt-message-reward-rom-verification.json")
            .read_text(encoding="utf-8")
        )
        self.assertEqual(
            retained["validated_region_sha256"],
            structure["regions"][[r["name"] for r in structure["regions"]].index(
                "message_reward_lookup_block"
            )]["builds"]["usa-retail"]["sha256"]
        )
        available = [name for name, path in paths.items() if path.is_file()]
        if not available:
            self.skipTest("canonical ROMs unavailable on this runner")
        for build in available:
            with self.subTest(build=build):
                report = extract(paths[build].read_bytes(), structure, aliases, build)
                self.assertEqual(report["raw_signed_words"], retained["signed_words"])
                self.assertEqual(report["historical_disagreements"], retained["historical_named_mapping_disagreements"])
                self.assertEqual(len(report["historical_comparison"]), len(aliases["mapping"]))
                print("STUNT_REWARD_ROM_EVIDENCE " + json.dumps({
                    "build": build, "words": report["raw_signed_words"],
                    "historical_disagreements": report["historical_disagreements"],
                }, sort_keys=True), flush=True)

    def test_historical_mismatch_is_reported_not_normalized(self):
        aliases = copy.deepcopy(self.aliases)
        aliases["mapping"][1]["boost"] = 156
        report = extract(self.build_rom("usa-retail"), self.structure, aliases, "usa-retail")
        self.assertEqual(report["historical_disagreements"], ["0x11"])
        self.assertEqual(report["historical_comparison"][1]["rom_signed_word"], 152)

    def test_changed_rom_block_rejected(self):
        rom = bytearray(self.build_rom("usa-retail"))
        rom[rom_offset("81:C4AA")] ^= 1
        with self.assertRaisesRegex(RewardEvidenceError, "SHA-256 differs"):
            extract(bytes(rom), self.structure, self.aliases, "usa-retail")

    def test_truncated_rom_rejected(self):
        with self.assertRaisesRegex(RewardEvidenceError, "truncated"):
            extract(bytes(0xC458), self.structure, self.aliases, "usa-retail")

    def test_invalid_histories_and_structure_rejected(self):
        rom = self.build_rom("usa-retail")
        aliases = copy.deepcopy(self.aliases)
        aliases["mapping"].append(copy.deepcopy(aliases["mapping"][0]))
        with self.assertRaisesRegex(RewardEvidenceError, "duplicate"):
            extract(rom, self.structure, aliases, "usa-retail")
        aliases["mapping"][-1]["message_id"] = "0x16"
        with self.assertRaisesRegex(RewardEvidenceError, "out-of-range"):
            extract(rom, self.structure, aliases, "usa-retail")
        structure = copy.deepcopy(self.structure)
        structure["regions"][0]["size"] = 281
        with self.assertRaisesRegex(RewardEvidenceError, "definition changed"):
            extract(rom, structure, self.aliases, "usa-retail")
        with self.assertRaisesRegex(RewardEvidenceError, "non-ROM"):
            rom_offset("01:7000")


if __name__ == "__main__":
    unittest.main()
