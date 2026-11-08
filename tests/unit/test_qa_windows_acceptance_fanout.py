"""ROM-free, fail-closed contract tests for exact Windows fan-out."""
from contextlib import contextmanager
import hashlib
from contextlib import nullcontext
import threading
import json
import sys
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa_windows_acceptance_fanout as fanout
import run_baldosa_parallel_windows_journeys as bridge
import baldosa_native_practice_courses_probe as practice

SHA = "a" * 40
WHO = {"source_sha": SHA, "exe_sha256": "b" * 64,
       "fixture_sha256": "c" * 64, "zip_sha256": "d" * 64}


class Win32MockCall:
    """Callable with writable ctypes argtypes/restype for ROM-free tests."""
    def __init__(self, delegate):
        self.delegate = delegate
    def __call__(self, *args):
        return self.delegate(*args)


def packet(group, who=None):
    indices = fanout.GROUPS[group]
    original_hashes = fanout.original_script_hashes()
    rows = [{"index": i, "name": bridge.STEPS[i],
             "script_sha256": original_hashes[i], "exit_code": 0,
             "elapsed_seconds": 1.5, "log": "step-%02d.log" % i,
             "summary": "step-%02d.md" % i,
             "log_sha256": "b" * 64, "log_bytes": 82,
             "summary_sha256": "c" * 64, "summary_bytes": 16}
            for i in indices]
    mode = ({"requested_workers": 1, "reported_workers": 1,
             "report_sha256": "a" * 64, "report_cases": 10}
            if group == "independent" else
            {"requested_workers": 1, "reported_workers": None,
             "report_sha256": None, "report_cases": None})
    seed_mode = ({"requested_workers": 1, "effective_workers": 1,
                  "source_seed_sha256": "e" * 64,
                  "invocation_windows": [
                      {"index": 1, "started_ns": 100, "ended_ns": 200},
                      {"index": 2, "started_ns": 201, "ended_ns": 301},
                  ],
                  "invocation_overlap_ns": 0,
                  "native_process_overlap_verified": False}
                 if group == "seed-dependent" else
                 fanout.seed_mode_default(group, 1))
    result = {"schema": fanout.SCHEMA, "group": group,
              "practice_mode": mode, "seed_followup_mode": seed_mode,
              "candidate_identity": dict(who or WHO),
              "expected_indices": list(indices), "cases": rows,
              "all_passed": True, "release_gate_credit": 0,
              "independent_physical_qa": False,
              "elapsed_seconds": 12.0}
    result["receipt_sha256"] = fanout.digest(result)
    return result


class WindowsAcceptanceFanoutTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path = Path(tmp.name)
        for group in fanout.GROUPS:
            dest = self.path / ("windows-fanout-" + group)
            dest.mkdir()
            (dest / "result.json").write_text(json.dumps(packet(group)))

    def update(self, group, receipt):
        (self.path / ("windows-fanout-" + group) / "result.json").write_text(
            json.dumps(receipt))

    @staticmethod
    def practice_source_report(*, reported_workers=1, exe=None):
        seed = practice.tier2_seed()
        table = (("tier0_never_played", practice.TIER0),
                 ("tier2_formatted_save", practice.TIER2))
        return {
            "experimental_practice_case_workers": reported_workers,
            "source_binding": {
                "github_sha": SHA,
                "exe_sha256": hashlib.sha256(exe.read_bytes()).hexdigest()
                if exe else WHO["exe_sha256"],
                "rom_sha256": practice.USA_SHA256},
            "cases": [
                {"group": group, "case": label, "picker_steps": steps,
                 "track": track, "course": name}
                for group, cases in table for label, steps, track, name in cases
            ],
            "courses_admitted": 10,
            "pause_options_in_practice": ["sdl_keys", "p1_pad_semantic"],
            "restart_in_practice": "pause_delayed_restart_rewound_sram_equal",
            "available_tier0": 20, "available_tier2": 40,
            "hunter_admitted": False, "player_save_bytes_unchanged": True,
            "practice_results_published": False,
            "physical_gamepad_certified": False, "release_gate_credit": 0,
            "tier2_seed_sha256": hashlib.sha256(seed).hexdigest(),
        }

    def test_exact_full_inventory(self):
        r = fanout.aggregate(self.path, SHA)
        self.assertTrue(r["transport_complete"])
        self.assertEqual(r["observed_cases"], 13)
        self.assertEqual([row["index"] for row in r["cases"]], list(range(13)))
        self.assertEqual(r["release_gate_credit"], 0)
        self.assertEqual(r["schema"], fanout.AGGREGATE_SCHEMA)
        self.assertEqual(r["cases"][0]["script_sha256"],
                         fanout.original_script_hashes()[0])

    def test_missing_group_is_rejected(self):
        (self.path / "windows-fanout-independent" / "result.json").unlink()
        self.assertFalse(fanout.aggregate(self.path, SHA)["transport_complete"])

    def test_changed_executable_is_rejected(self):
        self.update("independent", packet("independent",
                    {**WHO, "exe_sha256": "e" * 64}))
        r = fanout.aggregate(self.path, SHA)
        self.assertFalse(r["transport_complete"])
        self.assertIn("different source", " ".join(r["issues"]))

    def test_modified_receipt_is_rejected(self):
        bad = packet("independent")
        bad["cases"][0]["elapsed_seconds"] = 9
        self.update("independent", bad)
        self.assertFalse(fanout.aggregate(self.path, SHA)["transport_complete"])

    def test_missing_case_is_rejected_even_with_matching_digest(self):
        bad = packet("independent")
        bad["cases"].pop()
        bad["receipt_sha256"] = fanout.digest(
            {k: v for k, v in bad.items() if k != "receipt_sha256"})
        self.update("independent", bad)
        self.assertFalse(fanout.aggregate(self.path, SHA)["transport_complete"])

    def test_failed_case_is_actionable_without_private_log_contents(self):
        bad = packet("independent")
        bad["cases"][4]["exit_code"] = 9
        bad["all_passed"] = False
        bad["receipt_sha256"] = fanout.digest(
            {k: v for k, v in bad.items() if k != "receipt_sha256"})
        self.update("independent", bad)
        result = fanout.aggregate(self.path, SHA)
        self.assertFalse(result["transport_complete"])
        self.assertEqual(result["failed_cases"], [{
            "group": "independent", "index": 7, "name": bridge.STEPS[7],
            "reason": "nonzero_exit", "exit_code": 9}])
        self.assertNotIn("genuine-script-output", json.dumps(result))
        self.assertEqual(result["release_gate_credit"], 0)

    def test_failure_receipt_with_missing_case_never_claims_full_inventory(self):
        bad = packet("seed-dependent")
        bad["cases"] = bad["cases"][:1]
        bad["all_passed"] = False
        bad["receipt_sha256"] = fanout.digest(
            {k: v for k, v in bad.items() if k != "receipt_sha256"})
        self.update("seed-dependent", bad)
        result = fanout.aggregate(self.path, SHA)
        self.assertFalse(result["transport_complete"])
        self.assertTrue(any("missing" in issue or "case" in issue
                            for issue in result["issues"]))

    def test_summarizer_never_invents_missing_case_success(self):
        rows = packet("seed-dependent")["cases"][:1]
        problems = fanout.summarize_case_failures("seed-dependent", rows)
        self.assertEqual([(r["index"], r["reason"], r["exit_code"])
                          for r in problems],
                         [(1, "missing_case", None), (2, "missing_case", None)])

    def test_real_original_script_failure_is_rejected(self):
        bad = packet("seed-dependent")
        bad["cases"][0]["exit_code"] = 1
        bad["all_passed"] = False
        bad["receipt_sha256"] = fanout.digest(
            {k: v for k, v in bad.items() if k != "receipt_sha256"})
        self.update("seed-dependent", bad)
        self.assertFalse(fanout.aggregate(self.path, SHA)["transport_complete"])

    def test_false_release_gate_promotion_is_rejected(self):
        bad = packet("seed-dependent")
        bad["release_gate_credit"] = 1
        bad["receipt_sha256"] = fanout.digest(
            {k: v for k, v in bad.items() if k != "receipt_sha256"})
        self.update("seed-dependent", bad)
        self.assertFalse(fanout.aggregate(self.path, SHA)["transport_complete"])

    def test_mode_attestation_fails_closed_on_changed_selection(self):
        for selected, effective, group in (
            ("0", "1", "independent"), ("3", "3", "independent"),
            ("2", "1", "independent"), ("1", "2", "seed-dependent"),
            ("2", "2", "seed-dependent"), (None, "1", "independent"),
            ("1", None, "seed-dependent")):
            with self.subTest(selected=selected, effective=effective, group=group):
                with self.assertRaisesRegex(ValueError, "Practice worker selection"):
                    fanout.selected_practice_workers(
                        {"UR_PRACTICE_SELECTED_WORKERS": selected,
                         "UR_PRACTICE_CASE_WORKERS": effective}, group)

    def test_mode_attestation_rejects_old_schema_even_with_new_fields(self):
        data = packet("independent")
        data["schema"] = "ur-win32-acceptance-fanout/3"
        data["receipt_sha256"] = fanout.digest(
            {k: v for k, v in data.items() if k != "receipt_sha256"})
        self.update("independent", data)
        r = fanout.aggregate(self.path, SHA)
        self.assertFalse(r["transport_complete"])

    def test_recomputed_digest_cannot_forge_selected_mode(self):
        for changed in (
            {"requested_workers": 2},
            {"reported_workers": 2},
            {"report_cases": 9},
            {"report_sha256": None},
            {"reported_workers": True},
            {"requested_workers": "2"}):
            with self.subTest(changed=changed):
                data = packet("independent")
                data["practice_mode"].update(changed)
                data["receipt_sha256"] = fanout.digest(
                    {k: v for k, v in data.items() if k != "receipt_sha256"})
                self.update("independent", data)
                self.assertFalse(fanout.aggregate(self.path, SHA)["transport_complete"])

    def test_group_receipt_mode_disagreement_fails_even_with_valid_digests(self):
        for group in fanout.GROUPS:
            self.update(group, packet(group))
        seed = packet("seed-dependent")
        seed["practice_mode"]["requested_workers"] = 2
        seed["receipt_sha256"] = fanout.digest(
            {k: v for k, v in seed.items() if k != "receipt_sha256"})
        self.update("seed-dependent", seed)
        aggregate = fanout.aggregate(self.path, SHA)
        self.assertFalse(aggregate["transport_complete"])
        self.assertIn("worker mode differs", " ".join(aggregate["issues"]))

    def test_record_mode_denies_forged_serial_as_parallel(self):
        for selected, effective, overlap in (
            (2, 1, 0), (2, 2, 0), (1, 2, 0), (1, 1, 100),
            (True, 1, 0), ("2", 2, 100),
        ):
            with self.subTest(selected=selected, effective=effective,
                              overlap=overlap):
                data = packet("seed-dependent")
                data["seed_followup_mode"].update({
                    "requested_workers": selected,
                    "effective_workers": effective,
                    "invocation_overlap_ns": overlap,
                })
                data["receipt_sha256"] = fanout.digest(
                    {k: v for k, v in data.items() if k != "receipt_sha256"})
                self.update("seed-dependent", data)
                self.assertFalse(fanout.aggregate(self.path, SHA)["transport_complete"])

    def test_records_parallel_bridge_windows_but_no_native_process_proof(self):
        seed = packet("seed-dependent")
        seed["seed_followup_mode"].update({
            "requested_workers": 2, "effective_workers": 2,
            "invocation_windows": [
                {"index": 1, "started_ns": 100, "ended_ns": 300},
                {"index": 2, "started_ns": 200, "ended_ns": 400},
            ],
            "invocation_overlap_ns": 100,
        })
        seed["receipt_sha256"] = fanout.digest(
            {k: v for k, v in seed.items() if k != "receipt_sha256"})
        self.update("seed-dependent", seed)
        receipt = fanout.aggregate(self.path, SHA)
        self.assertTrue(receipt["transport_complete"])
        self.assertEqual(receipt["seed_followup_mode"]["requested_workers"], 2)
        self.assertEqual(receipt["seed_followup_mode"]["invocation_overlap_ns"], 100)
        self.assertFalse(receipt["native_records_process_overlap_qualified"])
        self.assertFalse(receipt["seed_followup_mode"]["native_process_overlap_verified"])

    def test_records_worker_mode_rejects_missing_invalid_and_old_receipts(self):
        for changed in (
            {"source_seed_sha256": None},
            {"native_process_overlap_verified": True},
            {"invocation_windows": []},
            {"invocation_overlap_ns": -1},
            {"effective_workers": 0},
        ):
            with self.subTest(changed=changed):
                data = packet("seed-dependent")
                data["seed_followup_mode"].update(changed)
                data["receipt_sha256"] = fanout.digest(
                    {k: v for k, v in data.items() if k != "receipt_sha256"})
                self.update("seed-dependent", data)
                self.assertFalse(fanout.aggregate(self.path, SHA)["transport_complete"])
        for old in ("ur-win32-acceptance-fanout/3",
                    "ur-win32-acceptance-fanout/4"):
            with self.subTest(schema=old):
                data = packet("seed-dependent")
                data["schema"] = old
                data["receipt_sha256"] = fanout.digest(
                    {k: v for k, v in data.items() if k != "receipt_sha256"})
                self.update("seed-dependent", data)
                self.assertFalse(fanout.aggregate(self.path, SHA)["transport_complete"])

    def test_independent_group_cannot_claim_records_execution(self):
        for changed in ({"requested_workers": 2},
                        {"effective_workers": 2},
                        {"source_seed_sha256": "a" * 64}):
            with self.subTest(changed=changed):
                data = packet("independent")
                data["seed_followup_mode"].update(changed)
                data["receipt_sha256"] = fanout.digest(
                    {k: v for k, v in data.items() if k != "receipt_sha256"})
                self.update("independent", data)
                self.assertFalse(fanout.aggregate(self.path, SHA)["transport_complete"])

    def _seed_followup_fake_inputs(self):
        env = {"GITHUB_SHA": SHA, "RUNNER_TEMP": str(self.path),
               "GITHUB_STEP_SUMMARY": str(self.path / "summary.md"),
               "UR_PRACTICE_SELECTED_WORKERS": "1",
               "UR_PRACTICE_CASE_WORKERS": "1"}
        paths = [self.path / "candidate.exe", self.path / "fixture.exe",
                 self.path / "candidate.zip"]
        for path in paths:
            path.write_bytes(path.name.encode())
        return env, paths

    def test_win32_seed_sharing_guard_fails_closed_without_windows(self):
        # This is why synthetic Linux overlap tests explicitly mock the guard.
        if os.name == "nt":
            self.skipTest("negative non-Windows host required")
        with self.assertRaisesRegex(ValueError, "actual Windows"):
            with fanout.protect_windows_seed_readonly(self.path / "seed.srm"):
                self.fail("unsupported host bypassed seed guard")

    def test_win32_seed_sharing_guard_uses_read_only_share_and_closes(self):
        class Kernel:
            def __init__(self):
                self.request = None
                self.closed = []
                self.handle = 0x1234
                self.CreateFileW = Win32MockCall(self.open)
                self.CloseHandle = Win32MockCall(self.close)
            def open(self, *args):
                self.request = args
                return self.handle
            def close(self, handle):
                self.closed.append(handle)
                return 1
        kernel = Kernel()
        path = self.path / "seed.srm"
        with mock.patch.object(fanout.os, "name", "nt"), \
             mock.patch.object(fanout.ctypes, "WinDLL",
                               return_value=kernel, create=True):
            with fanout.protect_windows_seed_readonly(path):
                self.assertEqual(kernel.request[0], str(path))
                self.assertEqual(kernel.request[1], 0x80000000)
                self.assertEqual(kernel.request[2], 0x00000001)
                self.assertEqual(kernel.request[4], 3)
                self.assertEqual(kernel.request[5], 0x00000080)
                self.assertEqual(kernel.closed, [])
        self.assertEqual(kernel.closed, [0x1234])

    @unittest.skipUnless(os.name == "nt", "real Win32 share-mode control")
    def test_real_windows_share_guard_blocks_writes_delete_and_releases(self):
        # This is the real OS negative, not the Linux-compatible API mock.
        # It runs only when an independently authorized Windows unit suite
        # actually executes this unchanged code; no new CI run is enabled.
        original = bytes(range(256)) * 32
        seed = self.path / "real-win32-source.srm"
        seed.write_bytes(original)
        with fanout.protect_windows_seed_readonly(seed):
            self.assertEqual(seed.read_bytes(), original)
            with self.assertRaises(OSError):
                seed.write_bytes(bytes(8192))
            with self.assertRaises(OSError):
                seed.unlink()
            self.assertEqual(seed.read_bytes(), original)
        # The file must become writable once the read-sharing handle closes.
        seed.write_bytes(bytes(8192))
        self.assertEqual(seed.read_bytes(), bytes(8192))
        seed.unlink()
        self.assertFalse(seed.exists())

    @unittest.skipUnless(os.name == "nt", "real Win32 share-mode control")
    def test_real_windows_share_guard_releases_after_child_failure(self):
        seed = self.path / "real-win32-failure-source.srm"
        seed.write_bytes(bytes(8192))
        with self.assertRaisesRegex(RuntimeError, "synthetic game failure"):
            with fanout.protect_windows_seed_readonly(seed):
                raise RuntimeError("synthetic game failure")
        seed.write_bytes(b"recovered")
        self.assertEqual(seed.read_bytes(), b"recovered")

    def test_win32_seed_sharing_guard_refuses_invalid_open_handle(self):
        class Kernel:
            def __init__(self):
                self.CreateFileW = Win32MockCall(lambda *args: 0)
                self.CloseHandle = Win32MockCall(lambda *args: 1)
        with mock.patch.object(fanout.os, "name", "nt"), \
             mock.patch.object(fanout.ctypes, "WinDLL",
                               return_value=Kernel(), create=True), \
             mock.patch.object(fanout.ctypes, "get_last_error",
                               return_value=32, create=True):
            with self.assertRaisesRegex(OSError, "write-only|read-only|read-only Windows"):
                with fanout.protect_windows_seed_readonly(self.path / "seed.srm"):
                    self.fail("invalid handle accepted")

    def test_opt_in_records_invocations_overlap_after_original_seed(self):
        env, (exe, fixture, archive) = self._seed_followup_fake_inputs()
        barrier = threading.Barrier(2, timeout=5)
        seed = (self.path / "UR Baldosa Win32 Pause Route" / "baseline" /
                "Modern Player Data With Spaces" / "saves" / "save.srm")
        def runner(i, script, work, environ):
            if i == 0:
                seed.parent.mkdir(parents=True, exist_ok=False)
                seed.write_bytes(bytes(range(256)) * 32)
            else:
                self.assertEqual(seed.read_bytes(), bytes(range(256)) * 32)
                barrier.wait()
            (work / ("step-%02d.log" % i)).write_text("synthetic case")
            (work / ("step-%02d.md" % i)).write_text("synthetic summary")
            return {"index": i, "name": bridge.STEPS[i], "exit_code": 0,
                    "elapsed_seconds": 1.0, "log": "step-%02d.log" % i,
                    "summary": "step-%02d.md" % i}
        with mock.patch.object(bridge, "EXE", exe), \
             mock.patch.object(bridge, "FIXTURE", fixture), \
             mock.patch.object(bridge, "run_one", side_effect=runner), \
             mock.patch.object(fanout, "protect_windows_seed_readonly",
                               side_effect=lambda path: nullcontext()):
            output = fanout.run_group(
                "seed-dependent", SHA, archive, self.path / "parallel-records",
                env, seed_followup_workers=2)
        mode = output["seed_followup_mode"]
        self.assertTrue(output["all_passed"])
        self.assertEqual([r["index"] for r in output["cases"]], [0, 1, 2])
        self.assertEqual(mode["requested_workers"], 2)
        self.assertEqual(mode["effective_workers"], 2)
        self.assertGreater(mode["invocation_overlap_ns"], 0)
        self.assertEqual(mode["source_seed_sha256"],
                         hashlib.sha256(seed.read_bytes()).hexdigest())
        self.assertFalse(mode["native_process_overlap_verified"])
        fanout.validate_receipt(output, "seed-dependent", SHA)

    def test_records_guard_spans_both_parallel_original_invocations(self):
        env, (exe, fixture, archive) = self._seed_followup_fake_inputs()
        seed = (self.path / "UR Baldosa Win32 Pause Route" /
                "baseline" / "Modern Player Data With Spaces" /
                "saves" / "save.srm")
        barrier = threading.Barrier(2, timeout=5)
        live = threading.Event()
        trace = []
        @contextmanager
        def guard(actual):
            self.assertEqual(actual, seed)
            self.assertEqual(trace, [0])
            live.set()
            try:
                yield
            finally:
                live.clear()
                trace.append("released")
        def runner(index, script, work, environ):
            trace.append(index)
            if index == 0:
                seed.parent.mkdir(parents=True)
                seed.write_bytes(bytes(8192))
            else:
                self.assertTrue(live.is_set())
                barrier.wait()
            (work / ("step-%02d.log" % index)).write_text("synthetic log")
            (work / ("step-%02d.md" % index)).write_text("synthetic summary")
            return {"index": index, "name": bridge.STEPS[index],
                    "exit_code": 0, "elapsed_seconds": 1.0,
                    "log": "step-%02d.log" % index,
                    "summary": "step-%02d.md" % index}
        with mock.patch.multiple(bridge, EXE=exe, FIXTURE=fixture):
            with mock.patch.object(bridge, "run_one", side_effect=runner):
                with mock.patch.object(fanout, "protect_windows_seed_readonly",
                                       side_effect=guard):
                    receipt = fanout.run_group(
                        "seed-dependent", SHA, archive,
                        self.path / "guarded-parallel", env,
                        seed_followup_workers=2)
        self.assertTrue(receipt["all_passed"])
        self.assertEqual(trace[0], 0)
        self.assertEqual(set(trace[1:-1]), {1, 2})
        self.assertEqual(trace[-1], "released")
        self.assertFalse(live.is_set())
        self.assertFalse(receipt["seed_followup_mode"]
                         ["native_process_overlap_verified"])

    def test_records_guard_acquisition_failure_starts_no_followups(self):
        env, (exe, fixture, archive) = self._seed_followup_fake_inputs()
        seed = (self.path / "UR Baldosa Win32 Pause Route" /
                "baseline" / "Modern Player Data With Spaces" /
                "saves" / "save.srm")
        calls = []
        def runner(index, script, work, environ):
            calls.append(index)
            self.assertEqual(index, 0)
            seed.parent.mkdir(parents=True)
            seed.write_bytes(bytes(8192))
            (work / "step-00.log").write_text("baseline")
            (work / "step-00.md").write_text("baseline summary")
            return {"index": 0, "name": bridge.STEPS[0],
                    "exit_code": 0, "elapsed_seconds": 1.0,
                    "log": "step-00.log", "summary": "step-00.md"}
        def reject(actual):
            self.assertEqual(actual, seed)
            raise OSError(32, "simulated Windows sharing violation")
        destination = self.path / "guard-open-denied"
        with mock.patch.multiple(bridge, EXE=exe, FIXTURE=fixture):
            with mock.patch.object(bridge, "run_one", side_effect=runner):
                with mock.patch.object(fanout, "protect_windows_seed_readonly",
                                       side_effect=reject):
                    with self.assertRaisesRegex(
                            OSError, "simulated Windows sharing violation"):
                        fanout.run_group(
                            "seed-dependent", SHA, archive, destination,
                            env, seed_followup_workers=2)
        self.assertEqual(calls, [0])
        self.assertFalse((destination / "result.json").exists())

    def test_records_guard_releases_after_parallel_child_exception(self):
        env, (exe, fixture, archive) = self._seed_followup_fake_inputs()
        seed = (self.path / "UR Baldosa Win32 Pause Route" /
                "baseline" / "Modern Player Data With Spaces" /
                "saves" / "save.srm")
        barrier = threading.Barrier(2, timeout=5)
        state = {"held": False, "releases": 0}
        @contextmanager
        def guard(actual):
            self.assertEqual(actual, seed)
            state["held"] = True
            try:
                yield
            finally:
                state["held"] = False
                state["releases"] += 1
        def runner(index, script, work, environ):
            if index == 0:
                seed.parent.mkdir(parents=True)
                seed.write_bytes(bytes(8192))
            else:
                self.assertTrue(state["held"])
                barrier.wait()
                if index == 1:
                    raise RuntimeError("simulated original Records child failure")
            (work / ("step-%02d.log" % index)).write_text("synthetic log")
            (work / ("step-%02d.md" % index)).write_text("synthetic summary")
            return {"index": index, "name": bridge.STEPS[index],
                    "exit_code": 0, "elapsed_seconds": 1.0,
                    "log": "step-%02d.log" % index,
                    "summary": "step-%02d.md" % index}
        destination = self.path / "guarded-child-error"
        with mock.patch.multiple(bridge, EXE=exe, FIXTURE=fixture):
            with mock.patch.object(bridge, "run_one", side_effect=runner):
                with mock.patch.object(fanout, "protect_windows_seed_readonly",
                                       side_effect=guard):
                    with self.assertRaisesRegex(
                            RuntimeError, "simulated original Records child failure"):
                        fanout.run_group(
                            "seed-dependent", SHA, archive, destination,
                            env, seed_followup_workers=2)
        self.assertEqual(state["releases"], 1)
        self.assertFalse(state["held"])
        self.assertFalse((destination / "result.json").exists())

    def test_parallel_records_reject_mutated_original_seed_without_receipt(self):
        env, (exe, fixture, archive) = self._seed_followup_fake_inputs()
        barrier = threading.Barrier(2, timeout=5)
        seed = (self.path / "UR Baldosa Win32 Pause Route" / "baseline" /
                "Modern Player Data With Spaces" / "saves" / "save.srm")
        def runner(i, script, work, environ):
            if i == 0:
                seed.parent.mkdir(parents=True, exist_ok=False)
                seed.write_bytes(bytes(8192))
            else:
                barrier.wait()
                if i == 1:
                    seed.write_bytes(b"X" + bytes(8191))
            (work / ("step-%02d.log" % i)).write_text("synthetic case")
            (work / ("step-%02d.md" % i)).write_text("synthetic summary")
            return {"index": i, "name": bridge.STEPS[i], "exit_code": 0,
                    "elapsed_seconds": 1.0, "log": "step-%02d.log" % i,
                    "summary": "step-%02d.md" % i}
        with mock.patch.object(bridge, "EXE", exe), \
             mock.patch.object(bridge, "FIXTURE", fixture), \
             mock.patch.object(bridge, "run_one", side_effect=runner), \
             mock.patch.object(fanout, "protect_windows_seed_readonly",
                               side_effect=lambda path: nullcontext()):
            with self.assertRaisesRegex(ValueError, "baseline SRAM changed"):
                fanout.run_group(
                    "seed-dependent", SHA, archive, self.path / "mutated-records",
                    env, seed_followup_workers=2)
        self.assertFalse((self.path / "mutated-records" / "result.json").exists())

    def test_parallel_records_missing_authentic_seed_stays_unqualified(self):
        env, (exe, fixture, archive) = self._seed_followup_fake_inputs()
        calls = []
        def runner(i, script, work, environ):
            calls.append(i)
            (work / ("step-%02d.log" % i)).write_text("no actual seed")
            (work / ("step-%02d.md" % i)).write_text("synthetic summary")
            return {"index": i, "name": bridge.STEPS[i], "exit_code": 0,
                    "elapsed_seconds": 1.0, "log": "step-%02d.log" % i,
                    "summary": "step-%02d.md" % i}
        with mock.patch.object(bridge, "EXE", exe), \
             mock.patch.object(bridge, "FIXTURE", fixture), \
             mock.patch.object(bridge, "run_one", side_effect=runner):
            result = fanout.run_group(
                "seed-dependent", SHA, archive,
                self.path / "missing-records-seed", env,
                seed_followup_workers=2)
        self.assertEqual(calls, [0])
        self.assertFalse(result["all_passed"])
        self.assertEqual(result["seed_followup_mode"]["requested_workers"], 2)
        self.assertEqual(result["seed_followup_mode"]["effective_workers"], 0)
        self.assertIsNone(result["seed_followup_mode"]["source_seed_sha256"])
        with self.assertRaises(ValueError):
            fanout.validate_receipt(result, "seed-dependent", SHA)

    def test_parallel_records_nonzero_original_case_never_reports_success(self):
        env, (exe, fixture, archive) = self._seed_followup_fake_inputs()
        barrier = threading.Barrier(2, timeout=5)
        seed = (self.path / "UR Baldosa Win32 Pause Route" / "baseline" /
                "Modern Player Data With Spaces" / "saves" / "save.srm")
        def runner(i, script, work, environ):
            if i == 0:
                seed.parent.mkdir(parents=True, exist_ok=False)
                seed.write_bytes(bytes(8192))
            else:
                barrier.wait()
            (work / ("step-%02d.log" % i)).write_text("synthetic source case")
            (work / ("step-%02d.md" % i)).write_text("synthetic summary")
            return {"index": i, "name": bridge.STEPS[i],
                    "exit_code": 7 if i == 2 else 0,
                    "elapsed_seconds": 1.0, "log": "step-%02d.log" % i,
                    "summary": "step-%02d.md" % i}
        with mock.patch.object(bridge, "EXE", exe), \
             mock.patch.object(bridge, "FIXTURE", fixture), \
             mock.patch.object(bridge, "run_one", side_effect=runner), \
             mock.patch.object(fanout, "protect_windows_seed_readonly",
                               side_effect=lambda path: nullcontext()):
            receipt = fanout.run_group(
                "seed-dependent", SHA, archive,
                self.path / "failed-records-case", env,
                seed_followup_workers=2)
        self.assertFalse(receipt["all_passed"])
        self.assertEqual(receipt["cases"][2]["exit_code"], 7)
        self.assertFalse(receipt["seed_followup_mode"]["native_process_overlap_verified"])
        fanout.validate_receipt(receipt, "seed-dependent", SHA)

    def test_parallel_records_refuses_reused_output_before_new_baseline(self):
        env, (exe, fixture, archive) = self._seed_followup_fake_inputs()
        existing = (self.path / "UR Baldosa Win32 Pause Route" /
                    "native_real_1p_records")
        existing.mkdir(parents=True)
        marker = existing / "keep-existing-evidence.txt"
        marker.write_text("keep this file")
        with mock.patch.object(bridge, "EXE", exe), \
             mock.patch.object(bridge, "FIXTURE", fixture), \
             mock.patch.object(bridge, "run_one") as runner:
            with self.assertRaisesRegex(ValueError, "output root already exists"):
                fanout.run_group(
                    "seed-dependent", SHA, archive, self.path / "poisoned",
                    env, seed_followup_workers=2)
            runner.assert_not_called()
        self.assertEqual(marker.read_text(), "keep this file")
        self.assertFalse((self.path / "poisoned").exists())

    def test_parallel_records_rejects_baseline_created_child_output(self):
        env, (exe, fixture, archive) = self._seed_followup_fake_inputs()
        seed = (self.path / "UR Baldosa Win32 Pause Route" / "baseline" /
                "Modern Player Data With Spaces" / "saves" / "save.srm")
        child = self.path / "UR Baldosa Win32 Pause Route" / "native_real_1p_records"
        calls = []
        def runner(i, script, work, environ):
            calls.append(i)
            if i == 0:
                seed.parent.mkdir(parents=True, exist_ok=False)
                seed.write_bytes(bytes(8192))
                child.mkdir()
                (child / "existing.txt").write_text("cannot overwrite")
            (work / ("step-%02d.log" % i)).write_text("synthetic case")
            (work / ("step-%02d.md" % i)).write_text("synthetic summary")
            return {"index": i, "name": bridge.STEPS[i], "exit_code": 0,
                    "elapsed_seconds": 1.0, "log": "step-%02d.log" % i,
                    "summary": "step-%02d.md" % i}
        with mock.patch.object(bridge, "EXE", exe), \
             mock.patch.object(bridge, "FIXTURE", fixture), \
             mock.patch.object(bridge, "run_one", side_effect=runner):
            with self.assertRaisesRegex(ValueError, "baseline created a Records output root"):
                fanout.run_group(
                    "seed-dependent", SHA, archive, self.path / "child-during-baseline",
                    env, seed_followup_workers=2)
        self.assertEqual(calls, [0])
        self.assertEqual((child / "existing.txt").read_text(), "cannot overwrite")
        self.assertFalse((self.path / "child-during-baseline" / "result.json").exists())

    def test_parallel_records_rejects_redirected_seed_ancestor(self):
        env, (exe, fixture, archive) = self._seed_followup_fake_inputs()
        seed = (self.path / "UR Baldosa Win32 Pause Route" / "baseline" /
                "Modern Player Data With Spaces" / "saves" / "save.srm")
        private = self.path / "redirected-external-sram"
        private.mkdir()
        def runner(i, script, work, environ):
            if i == 0:
                seed.parent.parent.mkdir(parents=True, exist_ok=False)
                try:
                    seed.parent.symlink_to(private, target_is_directory=True)
                except (OSError, NotImplementedError):
                    self.skipTest("directory symlinks unavailable")
                seed.write_bytes(bytes(8192))
            (work / ("step-%02d.log" % i)).write_text("synthetic case")
            (work / ("step-%02d.md" % i)).write_text("synthetic summary")
            return {"index": i, "name": bridge.STEPS[i], "exit_code": 0,
                    "elapsed_seconds": 1.0, "log": "step-%02d.log" % i,
                    "summary": "step-%02d.md" % i}
        with mock.patch.object(bridge, "EXE", exe), \
             mock.patch.object(bridge, "FIXTURE", fixture), \
             mock.patch.object(bridge, "run_one", side_effect=runner):
            with self.assertRaisesRegex(ValueError, "redirected original Records seed parent"):
                fanout.run_group(
                    "seed-dependent", SHA, archive, self.path / "redirected-seed",
                    env, seed_followup_workers=2)
        self.assertTrue((private / "save.srm").is_file())
        self.assertFalse((self.path / "redirected-seed" / "result.json").exists())

    def test_parallel_records_same_bytes_new_source_inode_fails_closed(self):
        env, (exe, fixture, archive) = self._seed_followup_fake_inputs()
        seed = (self.path / "UR Baldosa Win32 Pause Route" / "baseline" /
                "Modern Player Data With Spaces" / "saves" / "save.srm")
        original = bytes(range(256)) * 32
        barrier = threading.Barrier(2, timeout=5)
        def runner(i, script, work, environ):
            if i == 0:
                seed.parent.mkdir(parents=True, exist_ok=False)
                seed.write_bytes(original)
            else:
                barrier.wait()
                if i == 1:
                    replacement = seed.with_suffix(".new")
                    replacement.write_bytes(original)
                    replacement.replace(seed)
            (work / ("step-%02d.log" % i)).write_text("synthetic journey")
            (work / ("step-%02d.md" % i)).write_text("synthetic summary")
            return {"index": i, "name": bridge.STEPS[i], "exit_code": 0,
                    "elapsed_seconds": 1.0, "log": "step-%02d.log" % i,
                    "summary": "step-%02d.md" % i}
        with mock.patch.object(bridge, "EXE", exe), \
             mock.patch.object(bridge, "FIXTURE", fixture), \
             mock.patch.object(bridge, "run_one", side_effect=runner), \
             mock.patch.object(fanout, "protect_windows_seed_readonly",
                               side_effect=lambda path: nullcontext()):
            with self.assertRaisesRegex(ValueError, "SRAM identity changed"):
                fanout.run_group(
                    "seed-dependent", SHA, archive, self.path / "replace-records",
                    env, seed_followup_workers=2)
        self.assertEqual(seed.read_bytes(), original)
        self.assertFalse((self.path / "replace-records" / "result.json").exists())

    def test_parallel_records_reject_changed_original_seed_source(self):
        env, (exe, fixture, archive) = self._seed_followup_fake_inputs()
        old = bridge.extract_commands(bridge.WORKFLOW.read_text())
        bad = list(old)
        bad[1] = bad[1].replace(
            "baseline/Modern Player Data With Spaces/saves/save.srm",
            "unrecognized/saves/save.srm")
        with mock.patch.object(bridge, "EXE", exe), \
             mock.patch.object(bridge, "FIXTURE", fixture), \
             mock.patch.object(bridge, "extract_commands", return_value=bad), \
             mock.patch.object(bridge, "run_one") as runner:
            with self.assertRaisesRegex(ValueError, "seed source changed"):
                fanout.run_group(
                    "seed-dependent", SHA, archive, self.path / "bad-seed-source",
                    env, seed_followup_workers=2)
            runner.assert_not_called()
        self.assertFalse((self.path / "bad-seed-source").exists())

    def test_record_followup_invalid_worker_setting_fails_before_io(self):
        for invalid in (0, -1, 3, True, "2", None):
            with self.subTest(mode=invalid), self.assertRaisesRegex(
                    ValueError, "invalid Records seed-followup worker count"):
                fanout.run_group("seed-dependent", SHA, self.path / "no-archive",
                                 self.path / "bad-mode",
                                 seed_followup_workers=invalid)
        with self.assertRaisesRegex(ValueError, "seed-dependent group"):
            fanout.run_group("independent", SHA, self.path / "no-archive",
                             self.path / "bad-mode", seed_followup_workers=2)
        self.assertFalse((self.path / "bad-mode").exists())

    def test_real_source_report_binds_worker_cases_exe_and_seed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            workflow = bridge.extract_commands(bridge.WORKFLOW.read_text())
            output = root / bridge.OUT_RE.findall(workflow[12])[0]
            output.mkdir(parents=True)
            fixture = self.practice_source_report(reported_workers=2)
            path = output / "report.json"
            path.write_text(json.dumps(fixture))
            env = {"RUNNER_TEMP": str(root)}
            witness = fanout.practice_report_witness(workflow, env, WHO, 2)
            self.assertEqual(witness["reported_workers"], 2)
            self.assertEqual(witness["report_cases"], 10)
            self.assertEqual(witness["report_sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
            modifications = (
                ("experimental_practice_case_workers", 1),
                ("source_binding", {**fixture["source_binding"], "github_sha": "f"*40}),
                ("source_binding", {**fixture["source_binding"], "exe_sha256": "0"*64}),
                ("courses_admitted", 9),
                ("cases", fixture["cases"][:-1]),
                ("player_save_bytes_unchanged", False),
                ("physical_gamepad_certified", True),
                ("tier2_seed_sha256", "0"*64))
            for field, replacement in modifications:
                with self.subTest(field=field):
                    path.write_text(json.dumps({**fixture, field: replacement}))
                    with self.assertRaises(ValueError):
                        fanout.practice_report_witness(workflow, env, WHO, 2)
            path.write_text(json.dumps(fixture))
            path.unlink()
            with self.assertRaisesRegex(ValueError, "missing or redirected"):
                fanout.practice_report_witness(workflow, env, WHO, 2)
            path.symlink_to(root / "not-present.json")
            with self.assertRaisesRegex(ValueError, "missing or redirected"):
                fanout.practice_report_witness(workflow, env, WHO, 2)

    def test_mode_attestation_seed_group_never_claims_original_practice(self):
        seed = packet("seed-dependent")
        seed["practice_mode"]["reported_workers"] = 1
        seed["receipt_sha256"] = fanout.digest(
            {k: v for k, v in seed.items() if k != "receipt_sha256"})
        self.update("seed-dependent", seed)
        self.assertFalse(fanout.aggregate(self.path, SHA)["transport_complete"])

    def test_no_duplicate_or_replaced_source_scenarios(self):
        source = bridge.WORKFLOW.read_text(encoding="utf-8")
        commands = bridge.extract_commands(source)
        self.assertEqual(len(commands), 13)
        self.assertEqual(set(fanout.GROUPS["seed-dependent"]), {0, 1, 2})
        self.assertEqual(set(fanout.GROUPS["independent"]), set(range(3, 13)))
        self.assertEqual([i for i in bridge.INDEPENDENT_PRIORITY if
                          i in fanout.GROUPS["independent"]].__len__(), 10)
        self.assertTrue(all("baseline/" not in commands[i] for i in range(3, 13)))

    def test_recomputed_receipt_digest_does_not_mask_changed_script(self):
        bad = packet("independent")
        bad["cases"][0]["script_sha256"] = "0" * 64
        bad["receipt_sha256"] = fanout.digest(
            {k: v for k, v in bad.items() if k != "receipt_sha256"})
        self.update("independent", bad)
        result = fanout.aggregate(self.path, SHA)
        self.assertFalse(result["transport_complete"])
        self.assertIn("script identity changed", " ".join(result["issues"]))

    def test_missing_script_hash_fails_even_with_valid_receipt_digest(self):
        bad = packet("seed-dependent")
        del bad["cases"][0]["script_sha256"]
        bad["receipt_sha256"] = fanout.digest(
            {k: v for k, v in bad.items() if k != "receipt_sha256"})
        self.update("seed-dependent", bad)
        self.assertFalse(fanout.aggregate(self.path, SHA)["transport_complete"])

    def test_same_names_changed_original_shell_body_is_not_equivalent(self):
        current = bridge.WORKFLOW.read_text(encoding="utf-8")
        changed = current.replace("--expected-frames 2473",
                                  "--expected-frames 2474", 1)
        self.assertNotEqual(current, changed)
        alternate = self.path / "changed-original-workflow.yml"
        alternate.write_text(changed, encoding="utf-8")
        with mock.patch.object(bridge, "WORKFLOW", alternate):
            result = fanout.aggregate(self.path, SHA)
        self.assertFalse(result["transport_complete"])
        self.assertIn("script identity changed", " ".join(result["issues"]))

    def test_historical_v2_group_receipts_not_silently_promoted(self):
        old = packet("seed-dependent")
        old["schema"] = "ur-win32-acceptance-fanout/2"
        for row in old["cases"]:
            del row["script_sha256"]
        old["receipt_sha256"] = fanout.digest(
            {k: v for k, v in old.items() if k != "receipt_sha256"})
        self.update("seed-dependent", old)
        self.assertFalse(fanout.aggregate(self.path, SHA)["transport_complete"])

    def test_authenticate_three_independent_source_hashes(self):
        names = ("exe", "fixture", "zip")
        for name in names:
            (self.path / name).write_bytes(name.encode())
        got = fanout.candidate_identity(SHA, *(self.path / x for x in names))
        self.assertEqual(got["exe_sha256"], hashlib.sha256(b"exe").hexdigest())

    def test_missing_original_group_output_cannot_pass(self):
        # The seed-dependent group can stop after a failed seed producer.
        old = packet("seed-dependent")
        old["cases"] = old["cases"][:1]
        old["all_passed"] = True
        old["receipt_sha256"] = fanout.digest(
            {k: v for k, v in old.items() if k != "receipt_sha256"})
        self.update("seed-dependent", old)
        self.assertFalse(fanout.aggregate(self.path, SHA)["transport_complete"])

    def test_exact_original_script_groups_execute_without_rebuilding(self):
        # Synthetic subprocess seam, not a substitute Windows/game witness.
        env = {"GITHUB_SHA": SHA, "RUNNER_TEMP": str(self.path),
               "GITHUB_STEP_SUMMARY": str(self.path / "summary.md"),
               "UR_PRACTICE_SELECTED_WORKERS": "1",
               "UR_PRACTICE_CASE_WORKERS": "1"}
        exe = self.path / "candidate.exe"
        fixture = self.path / "fixture.exe"
        archive = self.path / "candidate.zip"
        for path in (exe, fixture, archive):
            path.write_bytes(path.name.encode())

        def fake_runner(i, script, work, environ):
            (work / ("step-%02d.log" % i)).write_text("genuine-script-output")
            (work / ("step-%02d.md" % i)).write_text("original-step-summary")
            if i == 0:
                save = (self.path / "UR Baldosa Win32 Pause Route" /
                        "baseline" / "Modern Player Data With Spaces" /
                        "saves" / "save.srm")
                save.parent.mkdir(parents=True, exist_ok=True)
                save.write_bytes(bytes(8192))
            if i == 12:
                report = self.practice_source_report(
                    reported_workers=int(environ["UR_PRACTICE_CASE_WORKERS"]),
                    exe=exe)
                original_out = bridge.OUT_RE.findall(script)[0]
                output = Path(environ["RUNNER_TEMP"]) / original_out
                output.mkdir(parents=True, exist_ok=False)
                (output / "report.json").write_text(json.dumps(report))
            return {"index": i, "name": bridge.STEPS[i], "exit_code": 0,
                    "elapsed_seconds": 1.0, "log": "step-%02d.log" % i,
                    "summary": "step-%02d.md" % i}

        with mock.patch.object(bridge, "EXE", exe), \
             mock.patch.object(bridge, "FIXTURE", fixture), \
             mock.patch.object(bridge, "run_one", side_effect=fake_runner):
            seed = fanout.run_group("seed-dependent", SHA, archive,
                                    self.path / "seed-work", env)
            self.assertEqual([r["index"] for r in seed["cases"]], [0, 1, 2])
            self.assertTrue(seed["all_passed"])
            self.assertEqual(seed["seed_followup_mode"]["requested_workers"], 1)
            self.assertEqual(seed["seed_followup_mode"]["effective_workers"], 1)
            self.assertEqual(seed["seed_followup_mode"]["invocation_overlap_ns"], 0)
            self.assertFalse(seed["seed_followup_mode"]["native_process_overlap_verified"])
            # Two independent Windows jobs have separate ephemeral temp roots.
            fresh = self.path / "other-runner"
            fresh.mkdir()
            new_env = {**env, "RUNNER_TEMP": str(fresh)}
            independent = fanout.run_group(
                "independent", SHA, archive, fresh / "work", new_env)
            self.assertEqual([r["index"] for r in independent["cases"]],
                             list(range(3, 13)))
            self.assertTrue(independent["all_passed"])
            self.assertEqual(independent["practice_mode"]["reported_workers"], 1)
            self.assertEqual(independent["practice_mode"]["report_cases"], 10)
            self.assertEqual(len(independent["practice_mode"]["report_sha256"]), 64)

    def test_pre_digest_v1_receipt_cannot_be_misread_as_current(self):
        old = packet("seed-dependent")
        old["schema"] = "ur-win32-acceptance-fanout/1"
        for row in old["cases"]:
            for key in ("log_sha256", "log_bytes", "summary_sha256", "summary_bytes"):
                row.pop(key)
        old["receipt_sha256"] = fanout.digest(
            {k: v for k, v in old.items() if k != "receipt_sha256"})
        self.update("seed-dependent", old)
        self.assertFalse(fanout.aggregate(self.path, SHA)["transport_complete"])

    def test_tampered_private_output_digest_is_rejected(self):
        value = packet("seed-dependent")
        value["cases"][0]["log_sha256"] = "not-a-real-sha"
        value["receipt_sha256"] = fanout.digest(
            {k: v for k, v in value.items() if k != "receipt_sha256"})
        self.update("seed-dependent", value)
        self.assertFalse(fanout.aggregate(self.path, SHA)["transport_complete"])

    def test_private_log_digest_is_actual_file_content(self):
        work = self.path / "proof"
        work.mkdir()
        rows = [{"index": 8, "log": "step-08.log",
                 "summary": "step-08.md"}]
        contents = b"test-only-genuine-source-log\n"
        (work / rows[0]["log"]).write_bytes(contents)
        (work / rows[0]["summary"]).write_bytes(b"summary")
        fanout.attest_private_case_files(rows, work)
        self.assertEqual(rows[0]["log_sha256"],
                         hashlib.sha256(contents).hexdigest())
        self.assertEqual(rows[0]["summary_bytes"], len(b"summary"))
        self.assertEqual(rows[0]["log_bytes"], len(contents))

    def test_missing_private_original_log_is_not_success(self):
        work = self.path / "missing-proof"
        work.mkdir()
        with self.assertRaisesRegex(ValueError, "missing original Windows log"):
            fanout.attest_private_case_files(
                [{"index": 0, "log": "step-00.log",
                  "summary": "step-00.md"}], work)

    def test_optional_original_summary_records_explicit_absence(self):
        work = self.path / "optional-summary"
        work.mkdir()
        (work / "step-03.log").write_bytes(b"original log")
        rows = [{"index": 3, "log": "step-03.log",
                 "summary": "step-03.md"}]
        fanout.attest_private_case_files(rows, work)
        self.assertIsNone(rows[0]["summary_sha256"])
        self.assertEqual(rows[0]["summary_bytes"], 0)

    def test_redirected_private_original_log_is_rejected(self):
        work = self.path / "redirect"
        work.mkdir()
        source = self.path / "outside-log"
        source.write_bytes(b"source")
        try:
            (work / "step-00.log").symlink_to(source)
        except OSError:
            self.skipTest("symlinks unavailable")
        with self.assertRaisesRegex(ValueError, "redirected original Windows"):
            fanout.attest_private_case_files(
                [{"index": 0, "log": "step-00.log",
                  "summary": "step-00.md"}], work)

    def test_aggregate_cli_publishes_fail_closed_machine_receipt(self):
        import subprocess
        outfile = self.path / "aggregate.json"
        p = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "qa_windows_acceptance_fanout.py"),
             "aggregate", "--source-sha", SHA, "--results", str(self.path),
             "--out", str(outfile)],
            capture_output=True, text=True, timeout=15
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertTrue(json.loads(outfile.read_text())["transport_complete"])


if __name__ == "__main__":
    unittest.main()
