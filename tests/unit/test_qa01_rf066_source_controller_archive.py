"""ROM-free original movie → real input guest replay archive forensic tests."""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import extract_historical_smv_scene_window as smv
import qa01_rf066_source_controller_archive as qa
import qa01_verify_2014_movie_controller_supply as pin


MOVIE = ROOT / "reference/imported/tas-bots/dessyreqt-4250-submission.smv"
META = ROOT / "analysis/generated/historical-2014-smv-metadata.json"


class RealSMVCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        meta = json.loads(META.read_text())
        raw, _ = smv.read_movie(MOVIE)
        cls.window = smv.window(
            raw, meta, pin.MOVIE_RACE_ENTRY, pin.SOURCE_WINDOW_FRAMES)
        cls.segments = [r for r in cls.window["relative_input_segments"]
                        if int(r["mask"], 16)]

    def fixture(self, root: Path):
        entries = {}
        controls = {}
        for guest, origin in (("original", 1017), ("native", 1019)):
            name = qa.ORIGINAL_INPUT if guest == "original" else qa.NATIVE_INPUT
            source = "".join(
                f"{origin + item['start']}:{item['duration']}:"
                + (f"{int(item['mask'], 16):x}" if guest == "original"
                   else f"{int(item['mask'], 16):03x}") + "\n"
                for item in self.segments).encode("ascii")
            entries[name] = source
            label = "reference" if guest == "original" else "native"
            controls[label + "_supplied_input_sha256"] = qa.digest(source)
            controls[label + "_supplied_input_bytes"] = len(source)
            tail = ("fb=256x224 RGB565 sram=8192 ppuw=0"
                    if guest == "original" else "ok")
            log = "".join(
                f"script f={origin + frame} dump {tag} {tail}\n"
                for frame, tag in (
                    (0, "race-entered"), (5163, "result-onset"),
                    (5169, "result-stable"))).encode("ascii")
            entries[qa.ORIGINAL_LOG if guest == "original" else qa.NATIVE_LOG] = log
            controls[label + "_guest_log_sha256"] = qa.digest(log)
        report = {
            "schema_version": 1,
            "admission": "investigative candidate; not a release-ledger pass",
            "name": "zoom-zoo",
            "course_id": "course:02",
            "native_backend": "pinned-baldosa",
            "original_movie_sha256": pin.PINNED_MOVIE_CONTAINER_SHA256,
            "original_movie_window_sha256": pin.PINNED_RAW_WINDOW_SHA256,
            "original_source_event": {
                "original_entry_frame": 3190,
                "original_result_frame": 8353,
                "source_active_frames_to_result": 5163,
            },
            "reference_entry": 1017,
            "native_entry": 1019,
            "comparison": {"terminal_result_guest_frame": {
                "reference_relative": 5163, "native_relative": 5163}},
            "zoo_next_bowl_handoff": {
                "source_next_bowl_active_entry_offset": 267},
            "qa01_continuous_memory_capture": None,
            "qa01_capture_ab_control": {
                "schema": "ur-qa01-capture-ab-replay-control/1",
                "repository_source_sha": qa.PINNED_SOURCE_SHA,
                "controller_movie_window_sha256":
                    pin.PINNED_RAW_WINDOW_SHA256,
                "capturing_continuous_frames": False,
                "cpu_joypad_reads_proven": False,
                "full_event_accepted": False,
                **controls,
            },
        }
        entries[qa.REPORT] = json.dumps(report).encode()
        return entries

    def review(self, root, entries):
        archive = root / "case.zip"
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
            for name, value in entries.items():
                z.writestr(name, value)
        return qa.verify(archive, MOVIE, META, qa.digest(archive.read_bytes()))

    @staticmethod
    def mutate_report(entries, mutate):
        doc = json.loads(entries[qa.REPORT])
        mutate(doc)
        entries[qa.REPORT] = json.dumps(doc).encode()

    def test_real_movie_bytes_join_two_actual_guest_file_formats(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = self.review(root, self.fixture(root))
            self.assertEqual(
                result["source_original_native_segment_population"], len(self.segments))
            self.assertEqual(result["original_2014_controller_frames_reopened"], 5449)
            self.assertEqual(result["original_actual_guest_race_entry_host_frame"], 1017)
            self.assertEqual(result["native_actual_guest_race_entry_host_frame"], 1019)
            self.assertTrue(result["all_actual_2014_movie_to_supplied_guest_segments_equal"])
            self.assertFalse(result["actual_CPU_joypad_poll_consumption_proven"])
            self.assertEqual(result["accepted_USA_events"], 0)

    def test_forged_native_pad_value_rejected_even_with_new_sha_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            entries = self.fixture(root)
            name = qa.NATIVE_INPUT
            data = entries[name].replace(b"1019:1:080", b"1019:1:081", 1)
            self.assertNotEqual(data, entries[name])
            entries[name] = data
            self.mutate_report(entries, lambda d: d[
                "qa01_capture_ab_control"].update(
                    native_supplied_input_sha256=qa.digest(data),
                    native_supplied_input_bytes=len(data)))
            with self.assertRaisesRegex(ValueError, "segments differ"):
                self.review(root, entries)

    def test_missing_or_bad_guest_success_receipt_rejected(self):
        for which in ("missing", "failed", "shifted", "forged_result"):
            with self.subTest(which=which), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                entries = self.fixture(root)
                name = qa.NATIVE_LOG
                value = entries[name]
                if which == "missing":
                    value = b""
                elif which == "failed":
                    value = value.replace(b"result-onset ok", b"result-onset FAILED")
                elif which == "shifted":
                    value = value.replace(b"script f=6182 dump result-onset",
                                          b"script f=6183 dump result-onset")
                else:
                    self.mutate_report(entries, lambda d: d["comparison"][
                        "terminal_result_guest_frame"].update(native_relative=5164))
                    with self.assertRaises(ValueError):
                        self.review(root, entries)
                    continue
                entries[name] = value
                self.mutate_report(entries, lambda d: d[
                    "qa01_capture_ab_control"].update(
                    native_guest_log_sha256=qa.digest(value)))
                with self.assertRaises(ValueError):
                    self.review(root, entries)

    def test_zip_manifest_raw_input_and_movie_provenance_fail_closed(self):
        for kind in ("duplicate", "missing_input", "tamper_input", "wrong_movie"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                entries = self.fixture(root)
                if kind == "wrong_movie":
                    film = root / "fake-movie.smv"
                    film.write_bytes(b"not original")
                    archive = root / "case.zip"
                    with zipfile.ZipFile(archive, "w") as z:
                        for name, value in entries.items():
                            z.writestr(name, value)
                    with self.assertRaisesRegex(ValueError, "movie ZIP SHA256"):
                        qa.verify(archive, film, META,
                                  qa.digest(archive.read_bytes()))
                    continue
                if kind == "missing_input":
                    entries.pop(qa.ORIGINAL_INPUT)
                elif kind == "tamper_input":
                    entries[qa.ORIGINAL_INPUT] += b"garbage"
                if kind == "duplicate":
                    archive = root / "case.zip"
                    with zipfile.ZipFile(archive, "w") as z:
                        for name, value in entries.items():
                            z.writestr(name, value)
                        z.writestr(qa.ORIGINAL_INPUT, entries[qa.ORIGINAL_INPUT])
                    with self.assertRaisesRegex(ValueError, "duplicate/unsafe"):
                        qa.verify(archive, MOVIE, META,
                                  qa.digest(archive.read_bytes()))
                else:
                    with self.assertRaises(ValueError):
                        self.review(root, entries)


if __name__ == "__main__":
    unittest.main()
