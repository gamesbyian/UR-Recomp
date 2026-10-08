import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import probe_jumpover_fallthrough_native as probe  # noqa: E402

EVIDENCE = ROOT / "analysis" / "generated" / "jumpover-fallthrough-native.json"


def _state(y, air=9):
    return {name: 0 for name in probe.FIELDS} | {"y": y, "air_time": air}


class JumpoverNativeFixtureTests(unittest.TestCase):
    def test_snes9x_word_maps_to_script_mask_bit_order(self):
        # Snes9x 1.51: B=0x8000 ... R=0x0010; script: b=1, right=0x80, a=0x100, r=0x800.
        self.assertEqual(probe.snes9x_to_mask(0x8000), 0x001)
        self.assertEqual(probe.snes9x_to_mask(0x0100), 0x080)
        self.assertEqual(probe.snes9x_to_mask(0x0080), 0x100)
        self.assertEqual(probe.snes9x_to_mask(0x0010), 0x800)
        self.assertEqual(probe.snes9x_to_mask(0x8190), 0x981)

    def test_recovered_right_movie_is_right_hold_jump_and_shoulder(self):
        masks = probe.movie_masks("right")
        self.assertEqual(len(masks), 73 + probe.EXTENSION_FRAMES)
        self.assertEqual(masks[0], 0x080)        # Right
        self.assertEqual(masks[1], 0x081)        # B + Right
        self.assertEqual(masks[2], 0x981)        # B + Right + A + R
        self.assertEqual(masks[-1], 0x881)       # held B + Right + R

    def test_events_hold_approach_then_run_length_movie(self):
        events = probe.input_events([1, 1, 2], 100, 110, 0x80)
        self.assertEqual(events, [(100, 10, 0x80), (110, 2, 1), (112, 1, 2)])
        with self.assertRaises(ValueError):
            probe.input_events([1], 100, 100, 0x80)

    def test_script_seeds_boost_once_then_dumps_every_window_frame(self):
        script = probe.fixture_script(1088, 1450, 36, 72)
        self.assertTrue(script.startswith(probe.MENU_SCRIPT.rstrip("\n")))
        self.assertEqual(script.count("poke 11CF 4800"), 1)
        self.assertEqual(script.count("dump m"), probe.WINDOW[1] - probe.WINDOW[0] + 1)
        # Seed lands at frame splice - 1 - lead = 1413, 325 frames after race entry.
        self.assertIn("dump race-entered\nwait 325\npoke 11CF 4800\n", script)
        self.assertTrue(script.endswith("quit\n"))
        with self.assertRaises(ValueError):
            probe.fixture_script(1088, 1100, 36, 72)

    def test_classify_and_divergence(self):
        ordinary = {40: _state(700), 41: _state(720, air=0), 42: _state(721, air=0)}
        falling = {40: _state(700), 41: _state(900), 42: _state(1300)}
        self.assertEqual(probe.classify(ordinary)["outcome"], "ordinary")
        self.assertEqual(probe.classify(ordinary)["contact_ranges"], [[41, 42]])
        self.assertEqual(probe.classify(falling)["outcome"], "fall_through")
        self.assertIsNone(probe.first_divergence(ordinary, dict(ordinary)))
        diverged = probe.first_divergence(ordinary, falling)
        self.assertEqual(diverged, {"frame": 41, "fields": ["air_time", "y"]})
        with self.assertRaises(ValueError):
            probe.classify({})

    def test_race_entry_frame_parses_both_cores(self):
        self.assertEqual(probe.race_entry_frame("script f=1088 dump race-entered fb=256x224"), 1088)
        self.assertEqual(probe.race_entry_frame("script f=1097 dump race-entered ok"), 1097)
        self.assertIsNone(probe.race_entry_frame("script f=12 until 009F ok"))

    def test_committed_evidence_admits_the_right_route_pair(self):
        evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        self.assertEqual(evidence["kind"], "jumpover-fallthrough-native-fixture")
        self.assertEqual(evidence["route"], "right")
        self.assertEqual(evidence["course"]["id"], "course:20")
        self.assertEqual(evidence["boost_seed"]["wram"], "7E:11CF")
        outcomes = {}
        for case in evidence["cases"]:
            self.assertIsNone(case["first_divergence"], case["seed_lead"])
            self.assertEqual(case["reference"], case["native"], case["seed_lead"])
            outcomes[case["seed_lead"]] = case["reference"]["outcome"]
        # The fall-through sits between two ordinary controls one seed frame apart.
        self.assertEqual(outcomes, {35: "ordinary", 36: "fall_through", 37: "ordinary"})
        falling = next(c for c in evidence["cases"] if c["seed_lead"] == 36)["reference"]
        self.assertEqual(falling["contact_ranges"][0], [43, 46])


if __name__ == "__main__":
    unittest.main()
