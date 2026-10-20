"""Fail-closed promotional track-topology route source tests, no ROM required."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "tools/showcase/build_topology_2p_routes.py"
S = importlib.util.spec_from_file_location("topology_2p_capture", MODULE_PATH)
m = importlib.util.module_from_spec(S)
S.loader.exec_module(m)

D = m.dynamic_module()
SOURCE = (
    "turbo on\n"
    "until16 0053 == F60C\n"
    "wait 300\n"
    "press down 2\n"
    + m.SOURCE_ANCHOR
    + "until 0E1F != 00\ndump go\n"
    + D.EXPECTED_TAIL + "\n"
)

class TopologyTwoPlayerCaptureTest(unittest.TestCase):
    def test_exact_pinned_upstream_two_player_route(self):
        """The actual immutable upstream menu script must pass every route gate.

        Synthetic fixtures alone are insufficient: a different prefix, dump,
        GO marker or menu grammar would otherwise fail only after native build.
        """
        source = (ROOT / "tests/fixtures/pinned-baldosa-race-2p-split.txt").read_text()
        self.assertIn(m.SOURCE_ANCHOR, source)
        self.assertTrue(source.rstrip().endswith(D.EXPECTED_TAIL))
        for course in m.TARGETS:
            for profile in D.ROUTES:
                with self.subTest(course=course, profile=profile):
                    out, evidence = m.produce(source, course, profile)
                    self.assertIn("dump cinematic-go\\n", out)
                    self.assertIn("dump cinematic-lead\\n", out)
                    self.assertIn("dump cinematic-middle\\n", out)
                    self.assertIn("dump cinematic-late\\n", out)
                    self.assertEqual(out.count("until 0E1F != 00\\n"), 1)
                    self.assertEqual(out.count("until 00CE =="), 1)
                    self.assertEqual(out.count("quit\\n"), 1)
                    self.assertFalse(evidence["topology_visually_verified"])
                    self.assertFalse(evidence["2p_tour_track_navigation_executed"])


    def test_catalog_and_both_profiles_rom_free(self):
        m.self_test()

    def test_original_state_gates_instead_of_forced_memory_writes(self):
        for target in m.TARGETS:
            with self.subTest(target=target):
                script = m.menu_route(SOURCE, target)
                self.assertIn("until 009F == 6D 1200", script)
                self.assertIn("until 009F == 92 1200", script)
                self.assertIn("until 0313 == 01 1800", script)
                self.assertIn("until 0E1F != 00", script)
                self.assertEqual(script.count("dump verified-course-"), 2)
                self.assertEqual(script.count("until 00CE =="), 1)
                self.assertNotIn("poke", script)
                self.assertNotIn("write ", script)
                self.assertEqual(script.split("press p2:start 2")[0],
                                 SOURCE.split("press p2:start 2")[0])

    def test_loop_and_ramp_candidates_still_unverified(self):
        for case in ("looper", "megajump", "jumps"):
            a, receipt = m.produce(SOURCE, case, "p1-leads")
            b, other = m.produce(SOURCE, case, "p2-leads")
            self.assertNotEqual(a,b)
            self.assertNotEqual(receipt["route_sha256"],other["route_sha256"])
            for r in (receipt,other):
                self.assertFalse(r["topology_visually_verified"])
                self.assertFalse(r["2p_tour_track_navigation_executed"])
                self.assertFalse(r["successful_tricks_executed"])
                self.assertFalse(r["course_result_or_parity_claim"])
                self.assertGreater(r["post_go_scripted_frames"], 1100)
                self.assertEqual(r["runtime_expected_track_byte_7E00CE"],
                                 f"{r['stream_index']-1:02X}")

    def test_refuses_unqualified_tour_or_changed_menu(self):
        bad = SOURCE.replace("press p2:start 2","press p2:a 2")
        with self.assertRaises(ValueError):
            m.produce(bad,"jumps","p1-leads")
        with self.assertRaises(ValueError):
            m.menu_route(SOURCE,"two-loops")

if __name__ == "__main__":
    unittest.main()
