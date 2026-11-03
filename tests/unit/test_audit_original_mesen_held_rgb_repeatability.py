"""ROM-free adversarial controls for original Mesen PPU/screen repeatability."""
import json
from pathlib import Path
import unittest

from tools.art.audit_original_mesen_held_rgb_repeatability import (
    N, RUNS, SCHEMA, changed_rgb_pixels, compare_sources, read_original_run,
)


def sample_run(run_id: int, alternate: bool = False) -> dict:
    zero = bytes(3*N)
    changed = bytes([1, 2, 3]) + bytes(3*(N-1))
    hashes = {"oam": "a"*64, "vram": "b"*64, "cgram": "c"*64}
    return {"run_id": run_id, "frames": {
        1219: {"screen_rgb": changed if alternate else zero,
               "screen_sha": "d"*64 if alternate else "e"*64,
               "source_ppu_sha": dict(hashes)},
        1220: {"screen_rgb": changed if alternate else zero,
               "screen_sha": "d"*64 if alternate else "e"*64,
               "source_ppu_sha": dict(hashes)},
    }}


class OriginalHeldRgbRepeatabilityTests(unittest.TestCase):
    def test_exact_RGB_pixel_difference_not_channel_count(self):
        first=bytes(3*N)
        changed=bytearray(first)
        changed[0],changed[1],changed[2]=255,123,72
        changed[3*N-2]=88
        self.assertEqual(changed_rgb_pixels(first,bytes(changed)),2)
        self.assertEqual(changed_rgb_pixels(first,first),0)
        with self.assertRaisesRegex(ValueError,"256x239"):
            changed_rgb_pixels(first,first[:-1])

    def test_identical_PPU_regions_do_not_imply_repeated_RGB(self):
        a=sample_run(1)
        b=sample_run(2,alternate=True)
        result=compare_sources(a,b)
        self.assertEqual(result["schema"],SCHEMA)
        self.assertEqual(result["across_executions_same_tick"]["1219"]
                         ["RGB_pixels_different_across_executions"],1)
        self.assertFalse(result["screen_RGB_repeatable_across_executions"])
        self.assertFalse(result["source_screen_to_current_PPU_scanout_phase_independently_aligned"])
        self.assertFalse(result["original_source_OAM_to_racer_pixel_ownership_verified"])

    def test_perfect_replay_is_reported_only_when_RGB_is_equal(self):
        a=sample_run(1)
        b=sample_run(2)
        result=compare_sources(a,b)
        self.assertTrue(result["screen_RGB_repeatable_across_executions"])
        self.assertFalse(result["source_screen_to_current_PPU_scanout_phase_independently_aligned"])

    def test_mismatched_original_source_memory_invalidates_comparison(self):
        a=sample_run(1)
        b=sample_run(2)
        b["frames"][1219]["source_ppu_sha"]["cgram"]="z"*64
        with self.assertRaisesRegex(ValueError,"not the same original"):
            compare_sources(a,b)

    def test_invalid_or_unpinned_historical_archive_is_rejected(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"not-original.zip"
            path.write_bytes(b"PK\\x03\\x04"*30)
            for label in RUNS:
                with self.subTest(run=label),self.assertRaisesRegex(ValueError,"ZIP SHA"):
                    read_original_run(path,label)

    def test_committed_original_source_repeatability_warning_is_exact(self):
        root=Path(__file__).resolve().parents[2]
        record=json.loads((root/"analysis/data/racer-original-mesen-screen-repeatability-discrepancy-20261103.json").read_text(encoding="utf-8"))
        self.assertEqual(record["source_original_emulator_runs"],[41565384581,41566836578])
        self.assertFalse(record["held_screen_reproducible_across_identical_original_PPU_memory_states"])
        self.assertTrue(record["same_full_OAM_VRAM_CGRAM_SHA256_per_tick_across_runs"])
        self.assertEqual(record["across_runs"]["1219"]["pixels_with_RGB_disagreement"],10258)
        self.assertEqual(record["across_runs"]["1220"]["pixels_with_RGB_disagreement"],22776)
        self.assertEqual(record["within_run_changed_RGB_pixels_between_ticks"],
                         {"41565384581":0,"41566836578":23593})
        self.assertFalse(record["reproducible_original_PPU_to_screen_scanout_phase_proved"])
        self.assertFalse(record["source_racer_pixel_ownership_verified"])
        self.assertFalse(record["owner_likeness_approved"])


if __name__ == "__main__":
    unittest.main()
