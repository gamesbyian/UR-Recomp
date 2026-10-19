"""ROM-free negative contracts for four actual supplied original/native input files."""
from __future__ import annotations

import copy
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa01_verify_supplied_controller_streams as source


class SourceBoundControllerStreamTests(unittest.TestCase):
    def fixture(self, root: Path, backend="pinned-baldosa"):
        src = b"1017:3:4\n1022:2:1a\n1030:5:fff\n"
        nat = (b"1019:3:004\n1024:2:01a\n1032:5:fff\n"
               if backend == "pinned-baldosa" else
               b"1019:3:4:0\n1024:2:1a:0\n1032:5:fff:0\n")
        outputs = {}
        for mode in ("off", "on"):
            for guest in ("original", "native"):
                name = mode+"_"+guest
                path = root/(name+".input")
                path.write_bytes(src if guest == "original" else nat)
                outputs[name] = path
        original = {
            "schema_version": 1,
            "admission": "investigative candidate; not a release-ledger pass",
            "rom_sha256": "a" * 64,
            "original_movie_sha256": "b" * 64,
            "original_movie_window_sha256": "c" * 64,
            "reference_core_sha256": "d" * 64,
            "native_executable_sha256": "e" * 64,
            "source_sram_sha256": "f" * 64,
            "reference_entry": 1017,
            "native_entry": 1019,
            "native_backend": backend,
        }
        captured = copy.deepcopy(original)
        for mode, obj in (("off", original), ("on", captured)):
            obj["qa01_capture_ab_control"] = {
                "schema": source.AB,
                "repository_source_sha": "0" * 40,
                "controller_movie_window_sha256": "c" * 64,
                "reference_supplied_input_sha256": hashlib.sha256(src).hexdigest(),
                "native_supplied_input_sha256": hashlib.sha256(nat).hexdigest(),
                "reference_supplied_input_bytes": len(src),
                "native_supplied_input_bytes": len(nat),
                "capturing_continuous_frames": mode == "on",
                "cpu_joypad_reads_proven": False,
                "full_event_accepted": False,
            }
        return original, captured, outputs

    def test_two_real_distinct_guest_formats_normalize_on_own_entry_clocks(self):
        for backend in ("pinned-baldosa", "native"):
            with self.subTest(backend=backend), tempfile.TemporaryDirectory() as temp:
                baseline, captured, paths = self.fixture(Path(temp), backend)
                result = source.audit(baseline, captured, paths)
                self.assertEqual(result["normalized_segment_population"], 3)
                self.assertEqual(result["normalized_segments"], [
                    {"start_relative_to_actual_guest_entry": 0,
                     "duration_frames": 3, "nonzero_mask_hex": "004"},
                    {"start_relative_to_actual_guest_entry": 5,
                     "duration_frames": 2, "nonzero_mask_hex": "01a"},
                    {"start_relative_to_actual_guest_entry": 13,
                     "duration_frames": 5, "nonzero_mask_hex": "fff"},
                ])
                self.assertEqual(result["first_and_last_source_segment"][0], {
                    "start_relative_to_actual_guest_entry": 0,
                    "duration_frames": 3,
                    "nonzero_mask_hex": "004",
                })
                self.assertEqual(result["first_and_last_source_segment"][-1]
                                 ["start_relative_to_actual_guest_entry"], 13)
                self.assertTrue(result[
                    "original_native_normalized_source_controller_segments_equal"])
                self.assertFalse(result["actual_CPU_or_SPC_input_consumption_proven"])
                self.assertEqual(result["accepted_USA_events"], 0)

    def test_missing_modified_shifted_or_misrepresented_input_fails_closed(self):
        for fault in ("missing", "symlink", "tamper", "rehashed_native_mask",
                      "overlap", "bad_native_format", "wrong_origin",
                      "unsupported_poll_claim", "changed_on_source_sha"):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                base, on, paths = self.fixture(root)
                if fault == "missing":
                    paths["on_original"].unlink()
                elif fault == "symlink":
                    path = paths["off_native"]
                    path.unlink()
                    path.symlink_to(paths["on_native"])
                elif fault == "tamper":
                    paths["on_original"].write_bytes(b"1017:3:5\n1022:2:1a\n1030:5:fff\n")
                elif fault == "rehashed_native_mask":
                    data = b"1019:3:005\n1024:2:01a\n1032:5:fff\n"
                    for mode in ("off", "on"):
                        paths[mode+"_native"].write_bytes(data)
                        c = (base if mode == "off" else on)["qa01_capture_ab_control"]
                        c.update(native_supplied_input_sha256=hashlib.sha256(data).hexdigest(),
                                 native_supplied_input_bytes=len(data))
                elif fault == "overlap":
                    data = b"1017:3:4\n1018:2:1a\n1030:5:fff\n"
                    for mode in ("off", "on"):
                        paths[mode+"_original"].write_bytes(data)
                        c = (base if mode == "off" else on)["qa01_capture_ab_control"]
                        c.update(reference_supplied_input_sha256=hashlib.sha256(data).hexdigest(),
                                 reference_supplied_input_bytes=len(data))
                elif fault == "bad_native_format":
                    data = b"1019:3:004:0\n1024:2:01a:0\n1032:5:fff:0\n"
                    for mode in ("off", "on"):
                        paths[mode+"_native"].write_bytes(data)
                        c = (base if mode == "off" else on)["qa01_capture_ab_control"]
                        c.update(native_supplied_input_sha256=hashlib.sha256(data).hexdigest(),
                                 native_supplied_input_bytes=len(data))
                elif fault == "wrong_origin":
                    on["native_entry"] = 1020
                    base["native_entry"] = 1020
                elif fault == "unsupported_poll_claim":
                    on["qa01_capture_ab_control"]["cpu_joypad_reads_proven"] = True
                else:
                    on["qa01_capture_ab_control"]["repository_source_sha"] = "1" * 40
                with self.assertRaises(ValueError):
                    source.audit(base, on, paths)

    def test_unknown_extra_transport_field_and_source_window_tamper_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            base, on, paths = self.fixture(Path(temp))
            on["qa01_capture_ab_control"]["controller_movie_window_sha256"] = "0"*64
            with self.assertRaisesRegex(ValueError, "controller-window"):
                source.audit(base, on, paths)


if __name__ == "__main__":
    unittest.main()
