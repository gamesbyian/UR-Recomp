"""ROM-authoritative P1/P2 collision-state handoff into course object dispatch."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from compare_europe_usa_snes2asm_homologs import cpu_to_offset

ROM = ROOT / "reference/roms/retail/Uniracers_USA.sfc"
TRACE = ROOT / "analysis/data/dragster-finish-contact-transition.json"

# Exact USA retail instruction bytes, independently recovered in Nitrodon's
# bank-81 disassembly. These brackets are deliberately not whole-routine hashes.
# The physical left side is per-player; 0F09 is the shared current-player word.
MARSHAL = {
    "P1_load_0E95_to_0F09": ("81:8D48", "ac950e8c090f"),
    "P1_store_0F09_to_0E95": ("81:8DF3", "ac090f8c950e"),
    "P2_load_0E97_to_0F09": ("81:8EA2", "ac970e8c090f"),
    "P2_store_0F09_to_0E97": ("81:8F47", "ac090f8c970e"),
}
PLAYER_CALLS = {
    "P1_contact_surface_collision": ("81:8DD6", "202a9e20958b20b88f"),
    "P2_contact_surface_collision": ("81:8F2A", "202a9e20958b20b88f"),
}
FRAME_PHASE_CALLS = {
    "main_frame_dispatch_before_sampling": ("83:CD4E", "22b58982"),
    "main_frame_contact_resampling": ("83:CD73", "22148d81"),
    "bank82_dispatch_wrapper": ("82:89B5", "20b9896b"),
}

FRAME_DISPATCH_MARSHAL = {
    "P1_frame_dispatch_load": ("82:89BB", "ac950e8c090f"),
    "P2_frame_dispatch_load": ("82:8EC3", "ac970e8c090f"),
    "P1_object_dispatch_call": ("82:8C32", "22e28281"),
    "P2_object_dispatch_call": ("82:911C", "22e28281"),
}

DISPATCH = {
    "course_checkpoint_handler_reads_shared_word": ("81:805D", "ad090f29001c"),
    "course_dispatcher_reads_shared_word": ("81:82ED", "ad090f"),
}


def rom_span(rom: bytes, cpu_address: str, hex_bytes: str) -> bytes:
    offset = cpu_to_offset(cpu_address)
    length = len(hex_bytes) // 2
    return rom[offset:offset + length]


class CourseContactMarshalContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = ROM.read_bytes()

    def test_exact_instruction_bytes_match_canonical_rom(self):
        for name, (address, expected) in {
            **MARSHAL, **PLAYER_CALLS, **DISPATCH,
            **FRAME_DISPATCH_MARSHAL, **FRAME_PHASE_CALLS,
        }.items():
            with self.subTest(name=name, address=address):
                self.assertEqual(
                    rom_span(self.rom, address, expected), bytes.fromhex(expected)
                )

    def test_legacy_beta_matches_usa_player_marshal_instructions(self):
        # The validated legacy beta is byte-identical to USA here. PAL
        # builds relocate/rewrite these sites and cannot be assigned USA
        # WRAM addresses without an independently resolved register map.
        beta = (
            ROOT / "reference/roms/prototypes/Uniracers_Beta_legacy.sfc"
        ).read_bytes()
        for name, (address, expected_hex) in MARSHAL.items():
            with self.subTest(site=name):
                self.assertEqual(
                    rom_span(beta, address, expected_hex),
                    bytes.fromhex(expected_hex),
                )

    def test_main_race_frame_calls_object_dispatch_before_new_contact_sample(self):
        # USA main race path: bank-82 per-player object dispatch first,
        # bank-81 contact/surface sample after. This establishes ordering,
        # not a universal unconditional one-frame latency.
        dispatch_addr = int(FRAME_PHASE_CALLS[
            "main_frame_dispatch_before_sampling"][0].split(":")[1], 16)
        sample_addr = int(FRAME_PHASE_CALLS[
            "main_frame_contact_resampling"][0].split(":")[1], 16)
        self.assertLess(dispatch_addr, sample_addr)
        self.assertEqual(
            FRAME_PHASE_CALLS["bank82_dispatch_wrapper"][1], "20b9896b"
        )
        self.assertIn("P1_frame_dispatch_load", FRAME_DISPATCH_MARSHAL)
        self.assertIn("P2_frame_dispatch_load", FRAME_DISPATCH_MARSHAL)

    def test_stored_player_word_enters_shared_course_dispatch(self):
        # Each bank-82 per-player dispatch loads the stored collision word
        # from its own backing address into the shared scratch before the
        # same long checkpoint/object dispatch entry, on the USA ROM.
        self.assertEqual(
            bytes.fromhex(FRAME_DISPATCH_MARSHAL["P1_frame_dispatch_load"][1]),
            bytes.fromhex("ac950e8c090f"),
        )
        self.assertEqual(
            bytes.fromhex(FRAME_DISPATCH_MARSHAL["P2_frame_dispatch_load"][1]),
            bytes.fromhex("ac970e8c090f"),
        )
        self.assertLess(0x89BB, 0x8C32)
        self.assertLess(0x8EC3, 0x911C)

    def test_marshalling_brackets_preserve_player_isolation(self):
        p1in = bytes.fromhex(MARSHAL["P1_load_0E95_to_0F09"][1])
        p1out = bytes.fromhex(MARSHAL["P1_store_0F09_to_0E95"][1])
        p2in = bytes.fromhex(MARSHAL["P2_load_0E97_to_0F09"][1])
        p2out = bytes.fromhex(MARSHAL["P2_store_0F09_to_0E97"][1])
        self.assertEqual(p1in[:3], bytes.fromhex("ac950e"))
        self.assertEqual(p2in[:3], bytes.fromhex("ac970e"))
        self.assertEqual(p1out[-3:], bytes.fromhex("8c950e"))
        self.assertEqual(p2out[-3:], bytes.fromhex("8c970e"))
        for code in (p1in, p2in, p1out, p2out):
            self.assertIn(bytes.fromhex("090f"), code)

    def test_finish_words_share_the_same_handler_control_class(self):
        # 81:805D..8063 reads 0F09 & 0x1C00. Both the pre-transition
        # 0x2024 and transition 0x2020 words produce class zero. Slot
        # difference alone cannot explain a completed lap in this handler.
        artifact = json.loads(TRACE.read_text(encoding="utf-8"))
        words = [
            r["collision_word"] for r in artifact["samples"]
            if r["object_code"] == 0x14
        ]
        self.assertEqual(words, [0x2024, 0x2020, 0x2020, 0x0022, 0x0022, 0x0022])
        self.assertEqual({w & 0x1C00 for w in words}, {0})

    def test_native_finish_trace_keeps_p1_p2_and_shared_scratch_distinct(self):
        artifact = json.loads(TRACE.read_text(encoding="utf-8"))
        self.assertEqual(artifact["provenance"]["workflow_run"], 36954104693)
        rows = artifact["samples"]
        self.assertEqual([r["frame"] for r in rows], list(range(2901, 2908)))
        self.assertTrue(all(
            r["p2_collision_word_0e97"]
            == r["settled_current_player_collision_word_0f09"]
            for r in rows
        ))
        # P1 changes over the transition; the end-of-frame shared field does not.
        self.assertEqual(
            [r["collision_word"] for r in rows],
            [0x1804, 0x2024, 0x2020, 0x2020, 0x0022, 0x0022, 0x0022],
        )
        self.assertEqual(
            {r["settled_current_player_collision_word_0f09"] for r in rows},
            {0x1804},
        )
        self.assertEqual(
            [r["object_index"] for r in rows],
            [2, 10, 8, 8, 9, 9, 9],
        )


if __name__ == "__main__":
    unittest.main()
