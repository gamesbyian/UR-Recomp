import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import probe_boost_speed as probe  # noqa: E402

EVIDENCE = ROOT / "analysis" / "generated" / "boost-speed-probe.json"


def _rows(pairs):
    return [{"x_speed": s, "boost": b, "y": 539, "air_time": 0} for s, b in pairs]


class BoostSpeedProbeTests(unittest.TestCase):
    def test_law_is_base_plus_half_boost_capped(self):
        self.assertEqual(probe.law_speed(0), 448)
        self.assertEqual(probe.law_speed(64), 480)
        self.assertEqual(probe.law_speed(255), 575)
        self.assertEqual(probe.law_speed(0x400), 640)

    def test_script_seeds_once_then_dumps_each_frame(self):
        script = probe.boost_script(1088, 0x180)
        self.assertEqual(script.count("poke 11CF 8001"), 1)
        self.assertIn(f"wait {probe.SEED_OFFSET}\npoke 11CF 8001\ndump s000\n", script)
        self.assertEqual(script.count("dump s"), probe.FRAMES + 1)
        self.assertTrue(script.endswith("quit\n"))

    def test_summary_separates_ramp_from_the_law(self):
        pairs = [(448, 256), (472, 252), (496, 248), (520, 244), (544, 240), (566, 236)]
        pairs += [(566, 236)] * (probe.FLAT_FRAMES + 2 - len(pairs))
        summary = probe.summarize(_rows(pairs))
        self.assertEqual(summary["max_ramp_step"], 24)
        self.assertEqual(summary["ramp_frames"], 4)
        self.assertEqual(summary["max_law_deviation_after_ramp"], 2)
        self.assertEqual(summary["boost_spent_on_flat"], 20)
        self.assertTrue(summary["series"].startswith("448/256/0 472/252/0"))
        with self.assertRaises(ValueError):
            probe.summarize(_rows(pairs[:3]))

    def test_air_summary_uses_the_longest_airborne_run(self):
        rows = [{"x_speed": 512, "boost": 128 - 2 * i, "y": 500, "air_time": 1 if 3 <= i <= 9 else 0}
                for i in range(12)]
        summary = probe.summarize_air(rows)
        self.assertEqual(summary["airborne_run"], [3, 9])
        self.assertEqual(summary["boost_spent_airborne"], 12)
        with self.assertRaises(ValueError):
            probe.summarize_air([{"x_speed": 448, "boost": 0, "y": 539, "air_time": 0}])

    def test_offscreen_summary_ignores_bounces_and_law_limited_frames(self):
        def row(xs, boost, air, off, sx=112):
            return {"x_speed": xs, "boost": boost, "y": 400, "air_time": air, "offscreen": off,
                    "screen_x": sx}
        rows = [row(640, 900, 0, 0, 170), row(640, 896, 0, 0, 176), row(640, 876, 0, 0, 180),
                row(584, 400, 9, 1), row(581, 380, 9, 1), row(578, 360, 9, 1),
                row(470, 340, 0, 1), row(491, 320, 1, 1),           # bounce
                row(488, 80, 9, 1), row(480, 64, 9, 1)]            # law-limited
        summary = probe.summarize_offscreen(rows)
        self.assertEqual(summary["offscreen_airborne_x_speed_deltas"], [-3])
        self.assertEqual(summary["meter_drain_otherwise"], [4])
        self.assertEqual(summary["meter_drain_at_edge_or_offscreen"], [16, 20, 240, 476])

    def test_load_rows_requires_every_full_in_race_dump(self):
        def image(track=19, race=1, size=0x20000):
            wram = bytearray(size)
            if size > 0x313:
                wram[0x00CE], wram[0x0313] = track, race
            return bytes(wram)

        with tempfile.TemporaryDirectory() as tmp:
            d = pathlib.Path(tmp)
            for i in range(probe.FRAMES + 1):
                (d / f"s{i:03d}.wram.bin").write_bytes(image())
            self.assertEqual(len(probe.load_rows(d)), probe.FRAMES + 1)
            last = d / f"s{probe.FRAMES:03d}.wram.bin"
            for bad in (image(size=100), image(track=0), image(race=0)):
                last.write_bytes(bad)
                with self.assertRaises(probe.jf.EvidenceError):
                    probe.load_rows(d)
            last.unlink()
            with self.assertRaises(probe.jf.EvidenceError):
                probe.load_rows(d)

    def test_committed_evidence_native_matches_and_the_law_holds(self):
        evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        self.assertEqual(evidence["kind"], "boost-speed-probe")
        self.assertIn("controlled-state", evidence["qualification"])
        self.assertEqual([c["seed"] for c in evidence["cases"]], list(probe.SEEDS))
        for case in evidence["cases"]:
            ref, nat = case["reference"], case["native"]
            self.assertIsNone(case["first_divergence_frame"], case["seed"])
            self.assertEqual(ref["series_sha256"], nat["series_sha256"], case["seed"])
            self.assertLessEqual(ref["max_law_deviation_after_ramp"], 1, case["seed"])
            self.assertLessEqual(ref["max_ramp_step"], 24, case["seed"])
            # Frame 0 follows the seed frame and its idle frame: at most two
            # depletion steps (4 each) have run, and nothing clamps the meter.
            first_boost = int(ref["series"].split()[0].split("/")[1])
            self.assertLessEqual(case["seed"] - first_boost, 8, case["seed"])
        by_seed = {c["seed"]: c["reference"] for c in evidence["cases"]}
        self.assertEqual(by_seed[0x400]["max_flat_x_speed"], probe.SPEED_CAP)
        self.assertGreater(int(by_seed[0x400]["series"].split()[0].split("/")[1]), 0x180)
        self.assertEqual(by_seed[0]["boost_spent_on_flat"], 0)
        # Airborne: the meter keeps draining at the ground rate and air speed
        # follows the same law; nothing is stored for landing.
        self.assertEqual([c["seed"] for c in evidence["air_cases"]], list(probe.AIR_SEEDS))
        for case in evidence["air_cases"]:
            ref = case["reference"]
            self.assertIsNone(case["first_divergence_frame"], case["seed"])
            self.assertEqual(ref["series_sha256"], case["native"]["series_sha256"])
            a, b = ref["airborne_run"]
            self.assertGreaterEqual(b - a, 20, case["seed"])
            self.assertLessEqual(ref["max_law_deviation_airborne"], 1, case["seed"])
        air = {c["seed"]: c["reference"] for c in evidence["air_cases"]}
        self.assertGreater(air[256]["boost_spent_airborne"], 3 * (air[256]["airborne_run"][1] - air[256]["airborne_run"][0]))
        # Offscreen: the stock -3/frame X-speed decay (82:A6FE) while above the
        # viewport, native-identical.
        off = evidence["offscreen_case"]
        self.assertIsNone(off["first_divergence_frame"])
        self.assertEqual(off["reference"]["series_sha256"], off["native"]["series_sha256"])
        self.assertGreaterEqual(off["reference"]["offscreen_frames"], 10)
        self.assertEqual(off["reference"]["offscreen_airborne_x_speed_deltas"], [-3])
        # At the viewport edge or offscreen the stock path takes 16 more per frame
        # (82:A75F) on top of the periodic decrement (0 or 4 in this run).
        self.assertEqual(off["reference"]["meter_drain_at_edge_or_offscreen"], [16, 20])
        self.assertEqual(off["reference"]["meter_drain_otherwise"], [0, 4])
        # Depletion saturates at 4 per frame from 256 up.
        self.assertEqual(by_seed[256]["boost_spent_on_flat"], 4 * probe.FLAT_FRAMES)
        self.assertEqual(by_seed[0x400]["boost_spent_on_flat"], 4 * probe.FLAT_FRAMES)


if __name__ == "__main__":
    unittest.main()
