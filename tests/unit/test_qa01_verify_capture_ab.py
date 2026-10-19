"""ROM-free adversarial A/B contract tests; synthetic bytes are NOT event credit."""
from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa01_frame_fingerprint as fingerprint
import qa01_verify_capture_ab as ab


class CaptureABTests(unittest.TestCase):
    def sample(self, root: Path):
        controls = {
            "schema": ab.CONTROL,
            "repository_source_sha": "a" * 40,
            "controller_movie_window_sha256": "b" * 64,
            "reference_supplied_input_sha256": "c" * 64,
            "native_supplied_input_sha256": "d" * 64,
            "reference_supplied_input_bytes": 42,
            "native_supplied_input_bytes": 44,
            "reference_guest_log_sha256": "e" * 64,
            "native_guest_log_sha256": "f" * 64,
            "reference_replay_wall_seconds": 1.0,
            "native_replay_wall_seconds": 2.0,
            "reference_script_sha256": "0" * 64,
            "native_script_sha256": "0" * 64,
            "capturing_continuous_frames": False,
            "cpu_joypad_reads_proven": False,
            "full_event_accepted": False,
        }
        base = {
            "schema_version": 1,
            "admission": "investigative candidate; not a release-ledger pass",
            "qa01_capture_ab_control": copy.deepcopy(controls),
            "qa01_continuous_memory_capture": None,
        }
        for f in ab.IDENTITIES:
            base[f] = "field_" + f
        for f in ab.SEMANTIC_FIELDS:
            base[f] = {"authoritative_observation": f}
        base.update(
            name="zoom-zoo", course_id="course:02", native_backend="pinned-baldosa",
            rom_sha256="1" * 64, original_movie_sha256="2" * 64,
            source_sram_sha256="3" * 64,
            native_executable_sha256="4" * 64,
            reference_core_sha256="5" * 64,
            original_movie_window_sha256="b" * 64,
            reference_entry=1017, native_entry=2017, native_frame_shift=1000,
        )
        captured = copy.deepcopy(base)
        captured["qa01_capture_ab_control"].update(
            capturing_continuous_frames=True,
            reference_replay_wall_seconds=1.1,
            native_replay_wall_seconds=2.3,
            reference_script_sha256="6" * 64,
            native_script_sha256="6" * 64,
        )
        oid = {
            "source_sha": "a" * 40, "rom_sha256": "1" * 64,
            "movie_sha256": "2" * 64, "input_sha256": "b" * 64,
            "observation_phase": "post-script-dump",
            "original_frame_origin": 1017, "native_frame_origin": 2017,
            "masked_wram_bytes": 0, "masked_sram_bytes": 0,
        }
        o = root/"o"
        n = root/"n"
        o.mkdir()
        n.mkdir()
        for rel in range(1, 4):
            for kind, length in (("wram", fingerprint.WRAM),
                                 ("sram", fingerprint.SRAM)):
                a = bytes(length)
                b = bytearray(length)
                if rel == 2 and kind == "wram":
                    b[0x1ed] = 0x83
                fingerprint.snapshot_path(o, 1017+rel, kind).write_bytes(a)
                fingerprint.snapshot_path(n, 2017+rel, kind).write_bytes(b)
        retained = root/"retained"
        record = fingerprint.audit(oid, o, n, 1, 3, retained=retained)
        reportfile = root/"report.json"
        reportfile.write_text(json.dumps(record))
        metrics = {
            "window": {"start": 1, "end": 3, "count": 3},
            "original_guest_acknowledged_frames": 3,
            "native_guest_acknowledged_frames": 3,
            "retained_full_raw_image_bytes": 6*(fingerprint.WRAM+fingerprint.SRAM),
        }
        captured["qa01_continuous_memory_capture"] = {
            "accepted_complete_USA_events": 0,
            "actual_cpu_joypad_poll_consumption_proven": False,
            "capture_overhead_vs_identical_no-capture_control_measured": False,
            "fingerprints_sha256": ab.sha(reportfile),
            "native_binary_sha256": "4" * 64,
            "reference_core_sha256": "5" * 64,
            "original_controller_supplied_file_sha256": "c" * 64,
            "native_controller_supplied_file_sha256": "d" * 64,
            "source_controller_window_sha256": "b" * 64,
            "metrics": metrics,
        }
        return base, captured, record, retained, ab.sha(reportfile)

    def test_identical_source_and_semantic_controls_with_real_raw_reverify(self):
        with tempfile.TemporaryDirectory() as tmp:
            a,b,fp,root,sha = self.sample(Path(tmp))
            r=ab.audit(a,b,fp,root,sha)
            self.assertTrue(r["existing_semantic_observations_unchanged"])
            self.assertEqual(r["actual_complete_consecutive_frame_acknowledgments"],3)
            self.assertEqual(r["time"]["reference"]["relative_overhead_pct"],10)
            self.assertEqual(r["time"]["native"]["relative_overhead_pct"],15)
            self.assertEqual(r["admitted_usa_events"],0)

    def test_four_authentic_format_guest_logs_reopened_and_incomplete_rejected(self):
        for fault in ("none", "missing", "bad_success", "shift", "tampered_baseline"):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                a, b, fp, retained, fingerprint_hash = self.sample(root)
                logs = {}
                for mode in ("baseline", "captured"):
                    for guest, origin in (("original", 1017), ("native", 2017)):
                        name = mode + "_" + guest
                        path = root / (name + ".log")
                        if mode == "captured":
                            suffix = ("fb=256x224 RGB565 sram=8192 ppuw=0"
                                      if guest == "original" else "ok")
                            path.write_text("".join(
                                f"script f={origin + rel} dump "
                                f"qa01-frame-{rel:06d} {suffix}\n"
                                for rel in range(1, 4)))
                        else:
                            path.write_text("script f=0 dump result-onset ok\n")
                        logs[name] = path
                        control = (a if mode == "baseline" else b)[
                            "qa01_capture_ab_control"]
                        key = ("reference_guest_log_sha256"
                               if guest == "original" else "native_guest_log_sha256")
                        control[key] = ab.sha(path)
                witness = b["qa01_continuous_memory_capture"]
                witness["reference_guest_acknowledgment_log_sha256"] = ab.sha(
                    logs["captured_original"])
                witness["native_guest_acknowledgment_log_sha256"] = ab.sha(
                    logs["captured_native"])
                if fault != "none":
                    path = logs["captured_native"] if fault != "tampered_baseline" else logs[
                        "baseline_original"]
                    if fault == "missing":
                        path.write_text(path.read_text().replace(
                            "script f=2019 dump qa01-frame-000002 ok\n", ""))
                    elif fault == "bad_success":
                        path.write_text(path.read_text().replace(
                            "qa01-frame-000002 ok", "qa01-frame-000002 FAILED"))
                    elif fault == "shift":
                        path.write_text(path.read_text().replace(
                            "script f=2019 dump", "script f=2020 dump"))
                    else:
                        path.write_text(path.read_text() + "tampered\n")
                    if fault != "tampered_baseline":
                        b["qa01_capture_ab_control"]["native_guest_log_sha256"] = ab.sha(path)
                        witness["native_guest_acknowledgment_log_sha256"] = ab.sha(path)
                if fault == "none":
                    result = ab.audit(a, b, fp, retained, fingerprint_hash,
                                      guest_logs=logs)
                    self.assertTrue(result[
                        "captured_successful_guest_acknowledgment_logs_independently_reopened"])
                    self.assertTrue(result[
                        "four_original_native_on_off_guest_log_hashes_rechecked"])
                    self.assertEqual(result["admitted_usa_events"], 0)
                else:
                    with self.assertRaises(ValueError):
                        ab.audit(a, b, fp, retained, fingerprint_hash,
                                 guest_logs=logs)

    def test_changed_source_inputs_emulator_semantics_and_flags_refused(self):
        names=[
            ("identity",lambda x:x["captured"].__setitem__("reference_core_sha256","9"*64)),
            ("input",lambda x:x["captured"]["qa01_capture_ab_control"].__setitem__(
                "native_supplied_input_sha256","9"*64)),
            ("source",lambda x:x["captured"]["qa01_capture_ab_control"].__setitem__(
                "repository_source_sha","f"*40)),
            ("result",lambda x:x["captured"]["comparison"].__setitem__(
                "actual_result_frame",1000)),
            ("sram",lambda x:x["captured"].__setitem__("source_sram_sha256","9"*64)),
            ("polls",lambda x:x["captured"]["qa01_capture_ab_control"].__setitem__(
                "cpu_joypad_reads_proven",True)),
            ("retention",lambda x:x["captured"]["qa01_continuous_memory_capture"]["metrics"].__setitem__(
                "native_guest_acknowledged_frames",2)),
            ("fingerprint",lambda x:x["captured"]["qa01_continuous_memory_capture"].__setitem__(
                "fingerprints_sha256","0"*64)),
        ]
        for name,mutate in names:
            with self.subTest(name=name),tempfile.TemporaryDirectory() as tmp:
                a,b,fp,root,sha = self.sample(Path(tmp))
                mutate({"baseline":a,"captured":b})
                with self.assertRaises(ValueError):
                    ab.audit(a,b,fp,root,sha)

    def test_raw_byte_corruption_rejected_even_if_all_json_controls_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            a,b,fp,root,sha = self.sample(Path(tmp))
            member = next(x for x in root.iterdir() if x.name.startswith("native"))
            member.write_bytes(member.read_bytes()[:-1]+b"\x01")
            with self.assertRaises(ValueError):
                ab.audit(a,b,fp,root,sha)


if __name__ == "__main__":
    unittest.main()
