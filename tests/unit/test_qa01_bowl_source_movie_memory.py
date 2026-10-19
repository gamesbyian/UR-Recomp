"""Synthetic-only independent source-movie/fresh-guest Bowl WRAM + SRAM bounds."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa01_bowl_source_movie_memory as witness
import probe_original_event_complete as producer


class MovieBowlMemoryTests(unittest.TestCase):
    def setUp(self):
        ctx = tempfile.TemporaryDirectory()
        self.addCleanup(ctx.cleanup)
        root = Path(ctx.name)
        self.movie, self.ref, self.native = (
            root / "movie", root / "original", root / "native")
        for p in (self.movie, self.ref, self.native):
            p.mkdir()
        self.reference_entry, self.native_entry = 984, 985
        self.reference_result, self.native_result = 3365, 3364
        self.trace = {}
        self.logs = {"movie": [], "original": [], "native": []}
        for offset in witness.OFFSETS:
            frame = witness.SOURCE_RESULT + offset
            source = self._capture(self.movie,
                                   f"source-bowl-switcher-{offset:03d}",
                                   offset >= 342)
            self.trace[frame] = source
            self.logs["movie"].append(
                f"script f={frame} dump source-bowl-switcher-{offset:03d} ok")
            for side, directory, entry, result, becomes_active in (
                    ("original", self.ref, 984, 3365, offset >= 341),
                    ("native", self.native, 985, 3364, offset >= 344)):
                self._capture(directory, f"bowl-next-switcher-{offset:03d}",
                              becomes_active)
                self.logs[side].append(
                    f"script f={entry + result + offset} dump "
                    f"bowl-next-switcher-{offset:03d} ok")
        self.log = {k: "\n".join(lines) + "\n"
                    for k, lines in self.logs.items()}
        self.source = {
            "source_result_host_frame": 11985,
            "source_next_switcher_entry_host_frame": 12327,
            "source_result_to_next_active_entry_frames": 342,
            "source_active_eight_consecutive_frames": True,
            "source_controller_masks_modified": False,
        }

    def _capture(self, directory, tag, active):
        raw = bytearray(witness.WRAM_SIZE)
        raw[0x009F] = 0
        raw[0x00CE] = 3
        raw[0x0313] = 1 if active else 0
        (directory / f"{tag}.wram.bin").write_bytes(raw)
        sram = bytearray(witness.SRAM_SIZE)
        sram[0x0426:0x0428] = (764).to_bytes(2, "little")
        sram[0x054E:0x0550] = (764).to_bytes(2, "little")
        (directory / f"{tag}.sram.bin").write_bytes(sram)
        return {"menu": 0, "track": 3, "in_race": 1 if active else 0}

    def observe(self, *, source=None, movie_log=None, native_log=None):
        return witness.observe_movie_guest_memory(
            self.movie, self.ref, self.native, movie_log or self.log["movie"],
            self.log["original"], native_log or self.log["native"],
            self.trace, self.source if source is None else source,
            self.reference_entry, self.native_entry, self.reference_result,
            self.native_result, observed_dump_frame=producer.observed_dump_frame,
            decode_sram=producer.decode_qa01_crawler_battery_sram)

    def test_exact_monotonic_source_script_with_unmodified_controller_input(self):
        script = witness.source_movie_scan_script(22000)
        self.assertTrue(script.startswith(
            "wait 12319\ndump source-bowl-switcher-334\n"))
        self.assertIn("wait 1\ndump source-bowl-switcher-341", script)
        self.assertTrue(script.endswith("wait 9661\ndump source-horizon\nquit\n"))
        self.assertNotIn("press ", script)
        self.assertNotIn("poke ", script)
        with self.assertRaisesRegex(witness.SourceMovieMemoryError, "horizon"):
            witness.source_movie_scan_script(12000)

    def test_true_three_guest_axes_and_source_original_difference(self):
        receipt = self.observe()
        self.assertEqual(receipt["sample_count"], len(witness.OFFSETS))
        self.assertEqual(receipt["first_movie_vs_fresh_original_named_difference_offset"], 341)
        self.assertEqual(receipt["first_movie_vs_fresh_native_named_difference_offset"], 342)
        self.assertEqual(receipt["first_movie_vs_fresh_original_raw_wram_difference_offset"], 341)
        # The first named state difference is a real WRAM difference.
        # The source and fresh original remain equal at +334..+340.
        self.assertTrue(receipt["all_source_and_fresh_ranked_bowl_scores_764"])
        self.assertTrue(receipt["movie_source_fresh_guest_clocks_independent"])
        self.assertEqual(receipt["release_complete_event_credit"], 0)
        self.assertFalse(receipt["every_source_or_guest_gameplay_frame_proven"])

    def test_unmasked_wram_sram_differences_do_not_hide_original_source(self):
        path = self.ref / "bowl-next-switcher-334.wram.bin"
        raw = bytearray(path.read_bytes())
        raw[0x01DE] = 73
        path.write_bytes(raw)
        path = self.native / "bowl-next-switcher-354.sram.bin"
        battery = bytearray(path.read_bytes())
        battery[0x10A7] = 12
        path.write_bytes(battery)
        receipt = self.observe()
        self.assertEqual(receipt["first_movie_vs_fresh_original_raw_wram_difference_offset"], 334)
        first = receipt["samples"][0]["fresh_guests"]["original"]["wram_source_vs_guest"]
        self.assertEqual(first["different_byte_count"], 1)
        self.assertEqual(first["first_16_difference_values"],
                         [{"offset": 0x01DE, "source_movie_byte": 0,
                           "fresh_guest_byte": 73}])
        self.assertEqual(first["excluded_bytes"], 0)
        last = receipt["samples"][-1]["fresh_guests"]["native"]["sram_source_vs_guest"]
        self.assertEqual(last["different_byte_count"], 1)
        self.assertEqual(last["first_16_difference_offsets"], [0x10A7])
        self.assertEqual(receipt["release_complete_event_credit"], 0)

    def test_bad_source_trace_tag_or_raw_capture_fails_closed(self):
        removed = self.movie / "source-bowl-switcher-341.wram.bin"
        removed.unlink()
        with self.assertRaisesRegex(witness.SourceMovieMemoryError, "missing actual"):
            self.observe()
        self._capture(self.movie, "source-bowl-switcher-341", False)
        trace = self.trace[11985 + 341]
        self.trace[11985 + 341] = dict(trace, track=2)
        with self.assertRaisesRegex(witness.SourceMovieMemoryError, "source trace"):
            self.observe()
        self.trace[11985 + 341] = trace
        badlog = self.log["movie"].replace(
            "script f=12327 dump source-bowl-switcher-342",
            "script f=12328 dump source-bowl-switcher-342")
        with self.assertRaisesRegex(witness.SourceMovieMemoryError, "wrong host"):
            self.observe(movie_log=badlog)
        bad = dict(self.source, source_result_to_next_active_entry_frames=341)
        with self.assertRaisesRegex(witness.SourceMovieMemoryError, "authenticated"):
            self.observe(source=bad)
