"""ROM-free Ping Pong route and strict native/reference state sampler tests."""
from __future__ import annotations

import copy
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import probe_pingpong_loop_skip as pp  # noqa: E402


class PingPongScoutTests(unittest.TestCase):
    def test_menu_route_pins_walker_pingpong(self):
        self.assertIn("until 009B == 04 120", pp.MENU)
        self.assertIn("until 009B == 01 120", pp.MENU)
        self.assertIn("until 0313 == 01 1800", pp.MENU)
        self.assertEqual(pp.TRACK_ID, 21)
        script = pp.fixture_script(40, 10)
        self.assertEqual(script.count("dump s"), 5)
        self.assertTrue(script.endswith("quit\n"))
        self.assertEqual(pp.samples(42, 10), [0, 10, 20, 30, 40, 42])

    def test_jumps_are_a_single_bounded_difference(self):
        self.assertEqual(pp.route_events(100, 80), [(100, 81, 0x80)])
        self.assertEqual(pp.route_events(100, 80, 31, 12),
                         [(100, 31, 0x80), (131, 12, 0x81), (143, 38, 0x80)])
        with self.assertRaises(pp.ScoutError):
            pp.route_events(0, 80, 75, 8)
        with self.assertRaises(pp.ScoutError):
            pp.fixture_script(0, 10)

    def test_requires_full_in_race_images_and_exact_sample_set(self):
        def image(track=21, active=1, n=0x20000):
            raw = bytearray(n)
            if n > 0x313:
                raw[0x00CE] = track
                raw[0x0313] = active
            return bytes(raw)

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            for frame in pp.samples(20, 10):
                (path / f"s{frame:04d}.wram.bin").write_bytes(image())
            rows = pp.load_series(path, 20, 10)
            self.assertEqual(len(rows), 3)
            self.assertIsNone(pp.compare(rows, copy.deepcopy(rows))["first_divergence"])
            corrupted = path / "s0020.wram.bin"
            for data, match in ((image(n=0x10000), "131072"),
                                (image(track=19), "not an active Ping Pong"),
                                (image(active=0), "not an active Ping Pong")):
                corrupted.write_bytes(data)
                with self.assertRaisesRegex(pp.ScoutError, match):
                    pp.load_series(path, 20, 10)
            corrupted.unlink()
            with self.assertRaisesRegex(pp.ScoutError, "missing sampled"):
                pp.load_series(path, 20, 10)

    def test_comparison_fails_closed_and_reports_first_diff(self):
        row = {k: 0 for k in pp.FIELDS}
        a = {0: dict(row), 10: dict(row)}
        b = copy.deepcopy(a)
        b[10]["checkpoint"] = 1
        self.assertEqual(pp.compare(a, b)["first_divergence"],
                         {"relative_frame": 10, "fields": ["checkpoint"]})
        with self.assertRaisesRegex(pp.ScoutError, "nonempty"):
            pp.compare({}, {})
        with self.assertRaisesRegex(pp.ScoutError, "frame sets"):
            pp.compare(a, {0: dict(row)})


if __name__ == "__main__":
    unittest.main()
