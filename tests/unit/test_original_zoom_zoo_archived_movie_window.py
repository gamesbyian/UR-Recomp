"""Exercise the actual preserved original 2014 Zoom Zoo controller window.

This is L1 archived input evidence, NOT a native/reference guest simulation
comparison or proof of checkpoint/lap results.
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import extract_historical_smv_scene_window as movie


class OriginalZoomZooMovieInputWitnessTests(unittest.TestCase):
    def test_archived_first_1810_zoom_zoo_candidate_frames_are_extractable(self):
        self.assertTrue(movie.ARCHIVE.is_file(), "preserved 2014 archived SMV must exist")
        meta = json.loads(movie.METADATA.read_text(encoding="utf-8"))
        source, member = movie.read_movie(movie.ARCHIVE)
        self.assertEqual(member, "100% run.smv")
        self.assertEqual(len(source), meta["smv_size_bytes"])
        # 3190 is an ORIGINAL core inRace=0->1 transition, checked separately
        # by historical_2014_first_race_reference and the Zoom Zoo anchor.
        # The input/frame off-by-one convention still requires live parity.
        report = movie.window(source, meta, 3190, 1810)
        self.assertEqual(report["movie_frame_range"], [3190, 4999])
        self.assertEqual(report["frames"], 1810)
        self.assertEqual(report["movie_uid"], 1396370047)
        self.assertEqual(report["movie_original_rom_crc32"], "383858c7")
        self.assertEqual(len(report["raw_controller_window_sha256"]), 64)
        segments = report["relative_input_segments"]
        self.assertGreater(len(segments), 10)
        self.assertTrue(all(0 <= x["start"] < 1810 for x in segments))
        self.assertTrue(all(x["start"] + x["duration"] <= 1810 for x in segments))
        self.assertTrue(all(
            a["start"] + a["duration"] <= b["start"]
            for a, b in zip(segments, segments[1:])
        ))
        self.assertGreater(len({x["mask"] for x in segments}), 2)
        self.assertIn("NOT a known race entry", report["source_limit"])
        # Printed so the exact real archive window fingerprint and controller
        # diversity are available in retained unit job logs for future pinning.
        print(
            "ORIGINAL-ZOOM-ZOO-ARCHIVE-WINDOW "
            + json.dumps({
                "range": report["movie_frame_range"],
                "sha256": report["raw_controller_window_sha256"],
                "runs": len(segments),
                "distinct_masks": sorted({x["mask"] for x in segments}),
            }, sort_keys=True),
            flush=True,
        )


if __name__ == "__main__":
    unittest.main()
