"""Fail-closed synthetic tests for one original/native Zoo +5040 WRAM discriminator.

No original game execution in this suite. The hosted, immutable movie replay
must independently establish every observed sample before any source claim.
"""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import probe_original_event_complete as qa


class ZooDirectPageBoundaryTests(unittest.TestCase):
    def test_dense_window_preserves_existing_full_mesh_and_source(self):
        normal = qa.sample_frames("zoom-zoo", 5163, zoo_race_mesh=True)
        dense = qa.sample_frames("zoom-zoo", 5163, zoo_race_mesh=True,
                                 zoo_dp_window=True)
        self.assertEqual(len(dense), len(normal) + 12)
        self.assertEqual([f for f in dense if 5034 <= f <= 5046],
                         list(range(5034, 5047)))
        self.assertEqual(dense[-1], 5120)
        self.assertTrue(set(normal).issubset(dense))
        script = qa.replay_script(2, 0xBC, dense, False)
        self.assertEqual(script.count("dump scene-05040"), 1)
        self.assertEqual(script.count("dump result-onset"), 1)
        self.assertLess(script.index("dump scene-05046"),
                        script.index("dump result-onset"))
        for case, duration, mesh in (("zoom-zoo", 5163, False),
                                     ("zoom-zoo", 5162, True),
                                     ("bowl", 5163, True)):
            with self.subTest(case=case, duration=duration), self.assertRaises(
                    qa.CompleteEventError):
                qa.sample_frames(case, duration, zoo_race_mesh=mesh,
                                 zoo_dp_window=True)

    def test_actual_bytes_and_independently_measured_clocks(self):
        frames = qa.sample_frames("zoom-zoo", 5163, zoo_race_mesh=True,
                                  zoo_dp_window=True)
        with tempfile.TemporaryDirectory() as td:
            original = Path(td) / "reference"
            native = Path(td) / "native"
            original.mkdir()
            native.mkdir()
            olines, nlines = [], []
            for f in frames:
                label = "race-entered" if f == 0 else f"scene-{f:05d}"
                o, n = bytearray(0x20000), bytearray(0x20000)
                # Synthesize the real sparse observation and a prior frame.
                if f in (5039, 5040):
                    o[0x63], n[0x63] = 115, 77
                    o[0x69], n[0x69] = 190, 151
                if f == 5034:
                    o[0x01ED], n[0x01ED] = 4, 6
                (original / f"{label}.wram.bin").write_bytes(o)
                (native / f"{label}.wram.bin").write_bytes(n)
                olines.append(f"script f={1017 + f} dump {label}\n")
                nlines.append(f"script f={1019 + f} dump {label}\n")
            old, new = "".join(olines), "".join(nlines)
            receipt = qa.observe_zoo_race_mesh(
                original, native, old, new, frames, 1017, 1019, 5163,
                zoo_dp_window=True)
            self.assertEqual(receipt["mesh_checkpoint_count"], len(frames))
            self.assertEqual(receipt["masked_or_excluded_wram_bytes"], 0)
            dp = receipt["late_direct_page_window"]
            self.assertEqual(dp["range_inclusive"], [5034, 5046])
            self.assertTrue(dp["all_guest_frames_in_range_captured"])
            self.assertEqual(len(dp["samples"]), 13)
            self.assertEqual(dp["first_sampled_direct_page_disagreement"], 5039)
            self.assertEqual(dp["last_sampled_direct_page_disagreement"], 5040)
            at = next(x for x in dp["samples"] if x["race_relative_frame"] == 5040)
            self.assertEqual((at["original_absolute_host_frame"],
                              at["native_absolute_host_frame"]), (6057, 6059))
            self.assertEqual(at["bytes"], [
                {"address": "7E:0063", "original": 115, "native": 77,
                 "differs": True},
                {"address": "7E:0069", "original": 190, "native": 151,
                 "differs": True},
            ])
            self.assertFalse(dp["executed_writer_reader_or_logic_tick_proven"])
            self.assertEqual(dp["release_complete_event_credit"], 0)
            self.assertFalse(receipt["every_gameplay_frame_compared"])
            self.assertEqual(receipt["release_complete_usa_event_credit"], 0)
            with self.assertRaisesRegex(qa.CompleteEventError, "uncalibrated"):
                qa.observe_zoo_race_mesh(
                    original, native, old.replace("script f=6057 dump",
                                                   "script f=6058 dump"),
                    new, frames, 1017, 1019, 5163, zoo_dp_window=True)
            with self.assertRaisesRegex(qa.CompleteEventError, "missing or altered"):
                qa.observe_zoo_race_mesh(
                    original, native, old, new, frames[:-1],
                    1017, 1019, 5163, zoo_dp_window=True)
            (native / "scene-05040.wram.bin").write_bytes(bytes(0x1FFFF))
            with self.assertRaisesRegex(qa.CompleteEventError, "128-KiB"):
                qa.observe_zoo_race_mesh(
                    original, native, old, new, frames,
                    1017, 1019, 5163, zoo_dp_window=True)


if __name__ == "__main__":
    unittest.main()
