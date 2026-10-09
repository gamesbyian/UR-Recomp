import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import probe_stunt_boundary as probe  # noqa: E402

EVIDENCE = ROOT / "analysis" / "generated" / "stunt-boundary-probe.json"


class StuntBoundaryProbeTests(unittest.TestCase):
    def test_events_hold_right_jump_then_shoulder(self):
        events = probe.stunt_events(1000, 2, 0x800)
        self.assertEqual(events[0], (1000, probe.JUMP[0], 0x080))
        masks = {}
        for start, length, mask in events:
            for f in range(start, start + length):
                masks[f - 1000] = mask
        self.assertEqual(masks[probe.JUMP[0]], 0x081)
        self.assertEqual(masks[probe.SHOULDER_START], 0x881)
        self.assertEqual(masks[probe.SHOULDER_START + 1], 0x881)
        self.assertEqual(masks[probe.SHOULDER_START + 2], 0x081)
        self.assertEqual(masks[probe.JUMP[0] + probe.JUMP[1]], 0x080)

    def test_script_writes_no_wram_and_dumps_the_window(self):
        script = probe.stunt_script(1088)
        self.assertNotIn("poke", script)
        self.assertEqual(script.count("dump w"), probe.WINDOW[1] - probe.WINDOW[0] + 1)

    def test_summary_finds_the_reward(self):
        rows = [{"pitch": 0, "roll_progress": p, "rolls": 0, "z_rotation": 0, "air_time": 9, "boost": b,
                 "queue_write": 1}
                for p, b in ((0, 0), (2, 0), (3, 0), (0, 128), (0, 124))]
        summary = probe.summarize(rows)
        self.assertEqual((summary["peak_roll_progress"], summary["reward_frame"], summary["boost_after_reward"]),
                         (3, 3, 128))
        rows = [dict(r, boost=0) for r in rows]
        self.assertFalse(probe.summarize(rows)["rewarded"])

    def test_default_boundary_cases_remain_exactly_the_admitted_six(self):
        cases = probe.planned_cases()
        self.assertEqual(len(cases), 6)
        self.assertEqual([(f, h) for f, _, h in cases], [
            ("r-shoulder-rotation", 22), ("r-shoulder-rotation", 23),
            ("r-shoulder-rotation", 24), ("r-shoulder-rotation", 25),
            ("a-twist", 4), ("a-twist", 5),
        ])
        self.assertTrue(all(mask in (0x800, 0x100) for _, mask, _ in cases))

    def test_exploration_is_opt_in_and_does_not_claim_thresholds(self):
        normal = probe.planned_cases()
        explored = probe.planned_cases(True)
        self.assertEqual(explored[:len(normal)], normal)
        self.assertGreater(len(explored), len(normal))
        self.assertEqual(len(explored), len({
            (family, hold) for family, _, hold in explored
        }))
        self.assertEqual({
            family for family, _, _ in explored[len(normal):]
        }, {"l-shoulder-flip", "a-r-simultaneous"})
        for family, mask, hold in explored[len(normal):]:
            self.assertIn(mask, (0x400, 0x900))
            events = probe.stunt_events(1088, hold, mask)
            masks = {frame - 1088: value
                     for start, count, value in events
                     for frame in range(start, start + count)}
            self.assertEqual(masks[probe.SHOULDER_START], 0x81 | mask)
            after_hold = probe.SHOULDER_START + hold
            expected = 0x080 | (0x001 if after_hold < probe.JUMP[0] + probe.JUMP[1] else 0)
            self.assertEqual(masks[after_hold], expected)

    def test_load_rows_rejects_short_or_missing_dumps(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(probe.jf.EvidenceError):
                probe.load_rows(pathlib.Path(tmp))

    def test_committed_evidence_boundaries(self):
        evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        self.assertEqual(evidence["kind"], "stunt-boundary-probe")
        self.assertIn("no WRAM writes", evidence["qualification"])
        got = {}
        for case in evidence["cases"]:
            key = (case["family"], case["hold_frames"])
            self.assertIsNone(case["first_divergence_frame"], key)
            self.assertEqual(case["reference"]["series_sha256"], case["native"]["series_sha256"], key)
            got[key] = case["reference"]
        expected = [(family, hold) for family, _, holds in probe.FAMILIES for hold in holds]
        self.assertEqual(sorted(got), sorted(expected))
        # R shoulder: the landing reward starts at the third roll-progress step.
        for hold in (22, 23):
            self.assertEqual(got[("r-shoulder-rotation", hold)]["peak_roll_progress"], 2)
            self.assertFalse(got[("r-shoulder-rotation", hold)]["rewarded"])
        for hold in (24, 25):
            self.assertEqual(got[("r-shoulder-rotation", hold)]["peak_roll_progress"], 3)
            self.assertEqual(got[("r-shoulder-rotation", hold)]["boost_after_reward"], 128)
        # A: a 5-frame press commits a full Z twist (0DFD -> 16); 4 does nothing.
        self.assertEqual(got[("a-twist", 4)]["peak_z_rotation"], 0)
        self.assertFalse(got[("a-twist", 4)]["rewarded"])
        self.assertEqual(got[("a-twist", 5)]["peak_z_rotation"], 16)
        self.assertEqual(got[("a-twist", 5)]["boost_after_reward"], 128)


if __name__ == "__main__":
    unittest.main()
