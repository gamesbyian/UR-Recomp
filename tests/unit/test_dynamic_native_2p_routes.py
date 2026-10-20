"""ROM-free unit guards for the two genuine 2P cinematic input proposals."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools/showcase/build_dynamic_2p_routes.py"
SPEC = importlib.util.spec_from_file_location("dynamic_2p_capture_routes", SCRIPT)
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)

SOURCE = (
    "turbo on\n"
    "until16 0053 == F60C\n"
    "wait 300\n"
    "press down 2\n"
    "until 0E1F != 00\n"
    + mod.EXPECTED_TAIL + "\n"
)


class DynamicTwoPlayerMediaRoutesTest(unittest.TestCase):
    def test_rom_free_route_generator_preflight(self):
        mod.self_test()

    def test_separate_racers_and_jump_stunt_inputs(self):
        one, meta1 = mod.produce(SOURCE, "p1-leads")
        two, meta2 = mod.produce(SOURCE, "p2-leads")
        prefix = SOURCE.split(mod.PREFIX)[0] + mod.PREFIX
        self.assertTrue(one.startswith(prefix))
        self.assertTrue(two.startswith(prefix))
        self.assertEqual(one.count("turbo off\n"), 1)
        self.assertEqual(two.count("turbo off\n"), 1)
        self.assertNotEqual(one, two)
        self.assertNotEqual(meta1["route_sha256"], meta2["route_sha256"])
        self.assertGreaterEqual(meta1["post_go_scripted_frames"], 1150)
        self.assertGreaterEqual(meta2["post_go_scripted_frames"], 1150)
        for route in (one, two):
            self.assertIn("press right+b 2\n", route)
            self.assertTrue("p2:b" in route)
            self.assertIn("right+p2:right", route)
            self.assertTrue("+r" in route or "+l" in route)
            self.assertTrue("p2:r" in route or "p2:l" in route)

    def test_deliberate_uneven_first_segments(self):
        first, _ = mod.produce(SOURCE, "p1-leads")
        second, _ = mod.produce(SOURCE, "p2-leads")
        early1 = first.split("turbo off\n", 1)[1].splitlines()[:2]
        early2 = second.split("turbo off\n", 1)[1].splitlines()[:2]
        self.assertEqual(early1[0], "press right 170")
        self.assertEqual(early2[0], "press p2:right 195")
        self.assertNotEqual(early1, early2)

    def test_reject_unrecognized_source_without_rewriting_gameplay(self):
        for invalid in (
            SOURCE.replace("turbo on", "turbo off"),
            SOURCE.replace("until 0E1F != 00", "wait 1"),
            SOURCE.replace("press right+p2:right 60", "press right 60"),
            SOURCE + "press right 999",
        ):
            with self.subTest(invalid=invalid[-30:]):
                with self.assertRaises(ValueError):
                    mod.produce(invalid, "p1-leads")

    def test_cannot_infer_visual_tricks_from_script(self):
        for name in mod.ROUTES:
            _, meta = mod.produce(SOURCE, name)
            self.assertTrue(meta["controls_are_attempts_not_visual_or_landing_proof"])
            self.assertTrue(meta["rendering_geometry_and_guest_unchanged"])
            self.assertEqual(meta["capture_requested"]["frame_count"], 900)


if __name__ == "__main__":
    unittest.main()
