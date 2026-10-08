import tempfile
import unittest
from pathlib import Path

from tools.analyze_snesrecomp_audio_stats import (
    FIELDS,
    parse_audio_stats,
    summarize_audio_stats,
)


class ProductionAudioStatsTests(unittest.TestCase):
    def fixture(self, root, rows, *, header=True):
        path = root / "audio-stats.txt"
        lines = (["# " + " ".join(FIELDS)] if header else [])
        lines.extend(" ".join(str(row.get(field, 0)) for field in FIELDS) for row in rows)
        path.write_text("\n".join(lines) + "\n")
        return path

    def test_computes_interval_deltas_not_process_totals(self):
        with tempfile.TemporaryDirectory() as td:
            path = self.fixture(Path(td), [
                dict(ms=1000, produced=5000, consumed=3000, dropped=4,
                     dropped_audible=0, underflows=3, missing_frames=1600,
                     occupancy=200, hiwater=500, prod_cpu=2000, prod_audio=3000),
                dict(ms=2000, produced=15000, consumed=13000, dropped=6,
                     dropped_audible=1, underflows=5, missing_frames=2400,
                     occupancy=100, hiwater=600, prod_cpu=7000, prod_audio=8000),
                dict(ms=3000, produced=22000, consumed=20000, dropped=8,
                     dropped_audible=1, underflows=5, missing_frames=2400,
                     occupancy=300, hiwater=600, prod_cpu=9000, prod_audio=13000),
            ])
            report = summarize_audio_stats(
                path, max_new_audible_drops=1, max_new_underflows=2,
                max_new_missing_frames=800
            )
            self.assertEqual(report["observed_ms"], 2000)
            self.assertEqual(report["snapshots"], 3)
            self.assertEqual(report["deltas"]["dropped_audible"], 1)
            self.assertEqual(report["deltas"]["underflows"], 2)
            self.assertEqual(report["deltas"]["missing_frames"], 800)
            self.assertEqual(report["occupancy_min"], 100)
            self.assertEqual(report["occupancy_max"], 300)

    def test_strict_limits_reject_new_audible_losses(self):
        with tempfile.TemporaryDirectory() as td:
            path = self.fixture(Path(td), [
                dict(ms=1000, dropped=2, dropped_audible=1),
                dict(ms=2000, dropped=5, dropped_audible=2),
            ])
            with self.assertRaisesRegex(ValueError, "dropped_audible delta 1"):
                summarize_audio_stats(path, max_new_audible_drops=0)

    def test_strict_limits_reject_new_underflows(self):
        with tempfile.TemporaryDirectory() as td:
            path = self.fixture(Path(td), [
                dict(ms=1000, underflows=4, missing_frames=100),
                dict(ms=2000, underflows=5, missing_frames=500),
            ])
            with self.assertRaisesRegex(ValueError, "underflows delta 1"):
                summarize_audio_stats(path, max_new_underflows=0)
            with self.assertRaisesRegex(ValueError, "missing_frames delta 400"):
                summarize_audio_stats(path, max_new_missing_frames=399)

    def test_rejected_malformed_and_missing_headers(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = self.fixture(root, [dict(ms=1000), dict(ms=2000)], header=False)
            with self.assertRaisesRegex(ValueError, "missing audio stats header"):
                parse_audio_stats(path)
            path.write_text("# unexpected header\n" + "0 " * len(FIELDS))
            with self.assertRaisesRegex(ValueError, "invalid or repeated"):
                parse_audio_stats(path)
            path = self.fixture(root, [dict(ms=1000), dict(ms=2000)])
            path.write_text(path.read_text() + "# " + " ".join(FIELDS) + "\n")
            with self.assertRaisesRegex(ValueError, "repeated audio stats header"):
                parse_audio_stats(path)

    def test_rejected_counter_regression_and_impossible_production(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = self.fixture(root, [
                dict(ms=1000, produced=500, consumed=300),
                dict(ms=2000, produced=499, consumed=400),
            ])
            with self.assertRaisesRegex(ValueError, "produced regressed"):
                parse_audio_stats(path)
            path = self.fixture(root, [
                dict(ms=1000, produced=100, prod_cpu=90, prod_audio=90),
                dict(ms=2000, produced=200),
            ])
            with self.assertRaisesRegex(ValueError, "attribution exceeds"):
                parse_audio_stats(path)
            path = self.fixture(root, [
                dict(ms=1000, dropped=1, dropped_audible=2),
                dict(ms=2000),
            ])
            with self.assertRaisesRegex(ValueError, "audible drops exceed"):
                parse_audio_stats(path)

    def test_requires_sufficient_snapshots(self):
        with tempfile.TemporaryDirectory() as td:
            path = self.fixture(Path(td), [dict(ms=1000)])
            with self.assertRaisesRegex(ValueError, "need 2"):
                parse_audio_stats(path)
            self.assertEqual(len(parse_audio_stats(path, min_records=1)), 1)


if __name__ == "__main__":
    unittest.main()
