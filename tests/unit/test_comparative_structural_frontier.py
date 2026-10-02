import sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import rank_comparative_structural_frontier as mod

class TestComparativeFrontierRanker(unittest.TestCase):
    def test_direct_jsr_same_bank(self):
        blob = bytearray(0x10000)
        off = mod.cpu_to_offset("81:9000")
        blob[off:off+3] = bytes([0x20, 0x34, 0x92])
        kind, target = mod.direct_target(bytes(blob), off)
        self.assertEqual(kind, "JSR")
        self.assertEqual(mod.offset_to_cpu(target), "81:9234")

    def test_direct_jsl_long(self):
        blob = bytearray(0x18000)
        off = mod.cpu_to_offset("81:9000")
        blob[off:off+4] = bytes([0x22, 0x78, 0xA5, 0x82])
        kind, target = mod.direct_target(bytes(blob), off)
        self.assertEqual(kind, "JSL")
        self.assertEqual(mod.offset_to_cpu(target), "82:A578")

    def test_in_census(self):
        self.assertTrue(mod.in_census(15, [(10,20)]))
        self.assertFalse(mod.in_census(21, [(10,20)]))

    def test_forwarding_wrapper_into_census(self):
        blob = bytearray(0x18000)
        wrapper = mod.cpu_to_offset("82:9000")
        callee = mod.cpu_to_offset("82:A000")
        blob[wrapper:wrapper+4] = bytes([0x20, 0x00, 0xA0, 0x6B])
        self.assertEqual(
            mod.forwarding_census_target(bytes(blob), wrapper, [(callee, callee + 10)]),
            "82:A000",
        )
        blob[wrapper+3] = 0x60
        self.assertIsNone(
            mod.forwarding_census_target(bytes(blob), wrapper, [(callee, callee + 10)])
        )

    def test_known_support_plumbing_is_deprioritized(self):
        self.assertGreater(mod.DEPRIORITIZED["82:8000"][0], 0)
        self.assertIn("APU", mod.DEPRIORITIZED["82:8000"][1])
        self.assertGreater(mod.DEPRIORITIZED["81:B68B"][0], 0)

    def test_rom_backed_build(self):
        if not all(p.exists() for p in mod.ROMS.values()) or not mod.CENSUS.exists():
            self.skipTest("ROM corpus/census absent")
        result = mod.build()
        self.assertGreater(result["candidate_count"], 0)
        self.assertEqual(result["candidates"], sorted(
            result["candidates"],
            key=lambda x:(-x["score"], -x["incoming_calls"], x["usa_target"])
        ))
        print("FRONTIER_RANKING_JSON=" + __import__("json").dumps(result, sort_keys=True))

if __name__ == "__main__":
    unittest.main()
