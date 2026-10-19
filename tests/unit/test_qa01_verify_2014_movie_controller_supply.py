"""ROM-free source-authentic 2014 Zoo SMV and guest supplied input audit tests."""
from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import extract_historical_smv_scene_window as smv
import qa01_verify_2014_movie_controller_supply as source


MOVIE = ROOT / "reference/imported/tas-bots/dessyreqt-4250-submission.smv"
META = ROOT / "analysis/generated/historical-2014-smv-metadata.json"


class Original2014ZooSuppliedInputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        meta = json.loads(META.read_text())
        raw, _ = smv.read_movie(MOVIE)
        cls.movie_window = smv.window(raw, meta, source.MOVIE_RACE_ENTRY,
                                      source.SOURCE_WINDOW_FRAMES)
        cls.parts = [p for p in cls.movie_window["relative_input_segments"]
                     if int(p["mask"], 16)]

    def make(self, root):
        inputs = {}
        first, second = 1017, 1019
        for mode in ("off", "on"):
            for guest, origin in (("original", first), ("native", second)):
                name = mode + "_" + guest
                path = root / (name + ".input")
                path.write_text("".join(
                    f"{origin+p['start']}:{p['duration']}:" +
                    (f"{int(p['mask'],16):x}" if guest == "original"
                     else f"{int(p['mask'],16):03x}") + "\n"
                    for p in self.parts), encoding="ascii")
                inputs[name] = path
        event = {
            "original_entry_frame": source.MOVIE_RACE_ENTRY,
            "original_result_frame": source.MOVIE_RACE_RESULT,
            "source_active_frames_to_result": source.SOURCE_RACE_RESULT_RELATIVE,
        }
        off = {
            "name": "zoom-zoo", "course_id": "course:02",
            "schema_version": 1,
            "admission": "investigative candidate; not a release-ledger pass",
            "original_movie_sha256": source.PINNED_MOVIE_CONTAINER_SHA256,
            "original_movie_window_sha256": source.PINNED_RAW_WINDOW_SHA256,
            "original_source_event": event,
            "zoo_next_bowl_handoff": {"source_followthrough": "observed"},
            "native_backend": "pinned-baldosa",
            "reference_entry": first, "native_entry": second,
            "rom_sha256": "1" * 64,
            "reference_core_sha256": "2" * 64,
            "native_executable_sha256": "3" * 64,
            "source_sram_sha256": "4" * 64,
        }
        on = copy.deepcopy(off)
        for mode, record in (("off", off), ("on", on)):
            record["qa01_capture_ab_control"] = {
                "schema": "ur-qa01-capture-ab-replay-control/1",
                "repository_source_sha": "a" * 40,
                "controller_movie_window_sha256":
                    source.PINNED_RAW_WINDOW_SHA256,
                "reference_supplied_input_sha256":
                    hashlib.sha256(inputs[mode + "_original"].read_bytes()).hexdigest(),
                "native_supplied_input_sha256":
                    hashlib.sha256(inputs[mode + "_native"].read_bytes()).hexdigest(),
                "reference_supplied_input_bytes":
                    inputs[mode + "_original"].stat().st_size,
                "native_supplied_input_bytes":
                    inputs[mode + "_native"].stat().st_size,
                "capturing_continuous_frames": mode == "on",
                "cpu_joypad_reads_proven": False,
                "full_event_accepted": False,
            }
        return off, on, inputs

    def test_real_original_2014_movie_produces_exact_unshifted_guest_supplied_segments(self):
        with tempfile.TemporaryDirectory() as temp:
            off, on, inp = self.make(Path(temp))
            result = source.audit(off, on, inp, MOVIE, META)
            self.assertTrue(result[
                "exact_movie_to_guest_supplied_controller_segments_equal"])
            self.assertEqual(
                result["source_movie_nonzero_input_segments"], len(self.parts))
            self.assertEqual(result["movie_window_inclusive_frame_range"],
                             [3190, 3190 + source.SOURCE_WINDOW_FRAMES - 1])
            self.assertEqual(
                result["actual_movie_window_controller_sha256"],
                source.PINNED_RAW_WINDOW_SHA256)
            self.assertFalse(
                result["original_guest_real_input_poll_consumption_proven"])
            self.assertEqual(result["full_USA_events_accepted"], 0)

    def test_source_metadata_mismatch_and_forged_smv_do_not_pass(self):
        for mutation in ("wrong_meta", "wrong_movie"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                off, on, inp = self.make(root)
                meta, movie = META, MOVIE
                if mutation == "wrong_meta":
                    d = json.loads(META.read_text())
                    d["rom_info"]["crc32"] = "00000000"
                    meta = root / "false-metadata.json"
                    meta.write_text(json.dumps(d))
                else:
                    movie = root / "not-2014-movie.smv"
                    movie.write_bytes(b"forged source movie")
                with self.assertRaises(ValueError):
                    source.audit(off, on, inp, movie, meta)

    def test_modified_guest_input_even_with_rehashed_claim_rejected_against_source(self):
        for mutation in ("first_mask", "last_duration", "source_entry",
                         "movie_digest", "source_window", "fake_cpu_consumption"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temp:
                off, on, inp = self.make(Path(temp))
                if mutation in ("first_mask", "last_duration"):
                    target = "off_native"
                    raw = inp[target].read_text()
                    lines = raw.splitlines()
                    if mutation == "first_mask":
                        parts = lines[0].split(":")
                        parts[2] = ("001" if parts[2] != "001" else "002")
                        lines[0] = ":".join(parts)
                    else:
                        parts = lines[-1].split(":")
                        parts[1] = str(int(parts[1]) + 1)
                        lines[-1] = ":".join(parts)
                    inp[target].write_text("\n".join(lines) + "\n")
                    # Even a new self-consistent producer receipt must fail
                    # cross-guest or capture-off/on equivalence.
                    off["qa01_capture_ab_control"][
                        "native_supplied_input_sha256"] = hashlib.sha256(
                            inp[target].read_bytes()).hexdigest()
                    off["qa01_capture_ab_control"][
                        "native_supplied_input_bytes"] = inp[target].stat().st_size
                elif mutation == "source_entry":
                    on["original_source_event"]["original_entry_frame"] += 1
                elif mutation == "movie_digest":
                    on["original_movie_sha256"] = "0" * 64
                elif mutation == "source_window":
                    off["original_movie_window_sha256"] = "0" * 64
                    on["original_movie_window_sha256"] = "0" * 64
                    for d in (off, on):
                        d["qa01_capture_ab_control"][
                            "controller_movie_window_sha256"] = "0" * 64
                else:
                    on["qa01_capture_ab_control"]["cpu_joypad_reads_proven"] = True
                with self.assertRaises(ValueError):
                    source.audit(off, on, inp, MOVIE, META)


if __name__ == "__main__":
    unittest.main()
