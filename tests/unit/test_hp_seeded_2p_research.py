"""Scheduled owner HP seeded two-seat execution and research acceptance policy."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import hp_seeded_2p_research as hp
from tools import qa02_native_2p_seeded_endurance as native

ROOT = Path(__file__).resolve().parents[2]
WIN = ROOT / ".github/workflows/windows-native-smoke.yml"
OWNER = ROOT / ".github/workflows/owner-hp-main-windows-smoke.yml"
HOSTED = ROOT / ".github/workflows/qa05-qa09-windows-candidate.yml"
SCHEDULE = ROOT / ".github/workflows/owner-hp-seeded-2p-research.yml"
VERIFY = ROOT / "tools/devnode_benchmark/verify_hp_ninja.py"
UPLOAD = ROOT / "tools/ci/check_windows_smoke_upload_policy.py"


def _env(root: Path, event: str = "schedule") -> dict[str, str]:
    return {"RUNNER_NAME": "hpmini-ur-recomp",
            "GITHUB_REPOSITORY": "gamesbyian/UR-Recomp",
            "GITHUB_REF": "refs/heads/main", "GITHUB_EVENT_NAME": event,
            "GITHUB_RUN_ID": "41151999999", "GITHUB_RUN_ATTEMPT": "1",
            "GITHUB_SHA": "a" * 40, "RUNNER_TEMP": str(root)}


def _report(work: Path, source: str, seed: int, shard: int) -> dict:
    row = {"schema": native.SCHEMA, "shard": shard, "minutes_budget": hp.MINUTES,
           "max_unique_cases": hp.MAX_CASES, "wall_seconds_budget": hp.WALL_SECONDS,
           "base_seed": seed, "stop_reason": "wall_budget",
           "identity": {
               "source_commit": source,
               "native_executable_sha256": "b" * 64,
               "rom_sha256": native.ROM_SHA,
               "stock_input_sha256": hashlib.sha256(native.base_source()[0].encode()).hexdigest(),
               "stock_script_sha256": hashlib.sha256(native.base_source()[1].encode()).hexdigest(),
           },
           "disposition": "completed_positive", "attempted_cases": 1,
           "passed_cases": 1, "failed_cases": 0,
           "total_real_native_processes": 4, "elapsed_seconds": 0.1,
           "release_gate_credit": 0, "failures": [],
           "original_native_fidelity_accepted": False,
           "complete_two_player_result_accepted": False,
           "physical_gamepads_tested": False,
           "case_results": [{
               "seed": seed + shard * 1000003,
               "input_sha256": hp.expected_treatment_digest(
                   native.base_source()[0], seed + shard * 1000003),
               "script_sha256": hp.expected_script_digest(native.base_source()[1]),
               "real_native_processes": 4,
               "bit_exact_replay": True,
               "two_seats_observably_active": True,
           }]}
    row["receipt_sha256"] = native.hash_object(row)
    return row


class HpScheduledResearchTests(unittest.TestCase):
    def test_windows_and_linux_execute_same_source_oracle(self):
        exe, rom, config, script = (Path(s) for s in ("game.exe", "retail.sfc", "config.ini", "route.script"))
        win = native.guest_command(exe, rom, config, script, windows=True)
        linux = native.guest_command(exe, rom, config, script, windows=False)
        self.assertEqual(win[0], str(exe))
        self.assertEqual(linux, ["xvfb-run", "-a", *win])
        source = (ROOT / "tools/qa02_native_2p_seeded_endurance.py").read_text()
        self.assertIn('env["SDL_VIDEODRIVER"] = "offscreen"', source)
        self.assertIn('wall_seconds if wall_seconds is not None else minutes * 60', source)
        self.assertIn('run.add_argument("--wall-seconds", type=int, default=None', source)

    def test_schedule_uses_only_trusted_hp_main_and_no_new_compiler(self):
        s = SCHEDULE.read_text()
        win = WIN.read_text()
        self.assertIn("cron: '17 */3 * * *'", s)
        for expected in ("github.repository == 'gamesbyian/UR-Recomp'",
                         "github.ref == 'refs/heads/main'",
                         "github.event_name == 'schedule'",
                         "uses: ./.github/workflows/windows-native-smoke.yml",
                         "run_on_hp: true", "hp_ninja_auto: true",
                         "hp_seeded_2p: true", "cancel-in-progress: false"):
            self.assertIn(expected, s)
        for expected in ("(!inputs.hp_seeded_2p ||", "github.event_name == 'schedule'",
                         "if: inputs.hp_seeded_2p",
                         "python -m tools.hp_seeded_2p_research",
                         '            --exe "$EXE"',
                         "HP_NINJA_AUTO=verified_source_bound"):
            self.assertIn(expected, win)
        hosted = HOSTED.read_text()
        self.assertNotIn("hp_seeded_2p: true", hosted)
        self.assertNotIn("hp_seeded_2p: true", OWNER.read_text())
        for workflow in (WIN, OWNER, HOSTED):
            source = workflow.read_text()
            for path in ("tools/hp_seeded_2p_research.py",
                         "tools/qa02_native_2p_seeded_endurance.py",
                         "tests/unit/test_hp_seeded_2p_research.py",
                         ".github/workflows/owner-hp-seeded-2p-research.yml"):
                self.assertIn('      - "' + path + '"', source)
        self.assertIn("--allow-trusted-main-schedule", VERIFY.read_text())

    def test_read_only_archive_free_receipt_allowed_but_raw_data_not_uploaded(self):
        import tools.ci.check_windows_smoke_upload_policy as policy
        s = WIN.read_text(encoding="utf-8")
        policy.check_workflow(s)
        self.assertIn('"${{ runner.temp }}/hp-seeded-2p-research-receipt.json"', UPLOAD.read_text())
        self.assertNotIn("${{ runner.temp }}/hp-seeded-2p-*/", s.split("      - name: Upload Windows evidence")[-1])
        self.assertIn("!${{ runner.temp }}/**/*.sram.bin", s)

    def test_authorization_rejects_pr_rogue_ref_runner_and_bad_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            good = _env(root)
            self.assertEqual(hp.authorize(good), (41151999999, "a" * 40))
            for key, value in (
                ("GITHUB_EVENT_NAME", "pull_request"),
                ("GITHUB_REF", "refs/heads/not-main"),
                ("RUNNER_NAME", "not-owner"),
                ("GITHUB_REPOSITORY", "other/repo"),
                ("GITHUB_SHA", "none"),
                ("GITHUB_RUN_ID", "-1"),
            ):
                with self.subTest(field=key):
                    altered = dict(good, **{key: value})
                    with self.assertRaises(ValueError):
                        hp.authorize(altered)

    def test_all_workers_join_and_distinct_cases_accept(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            exe, rom = root / "game.exe", root / "retail.sfc"
            exe.write_bytes(b"synthetic game")
            rom.write_bytes(b"synthetic ROM fixture")
            receipt = root / "result.json"
            calls = []
            def fake_shard(**kwargs):
                calls.append((kwargs["shard"], kwargs["base_seed"]))
                return _report(kwargs["work"], kwargs["source_sha"],
                               kwargs["base_seed"], kwargs["shard"])
            with patch.object(hp.native, "run_shard", side_effect=fake_shard):
                result = hp.run(exe, rom, _env(root), receipt)
            self.assertEqual(result["status"], "completed_positive")
            self.assertEqual(result["accepted_cases"], 4)
            self.assertEqual(result["real_guest_processes"], 16)
            self.assertEqual(len(calls), 4)
            self.assertEqual(len(set((shard, base) for shard, base in calls)), 4)
            self.assertEqual(json.loads(receipt.read_text())["receipt_sha256"], result["receipt_sha256"])
            self.assertEqual(result["release_gate_credit"], 0)
            self.assertFalse(result["physical_gamepads_tested"])

    def test_positive_receipts_reject_wrong_seed_namespace_and_digest(self):
        source, run_id = "a" * 40, 41151999999

        def rows():
            result = []
            for worker in range(hp.WORKERS):
                base = run_id % 10000000 + (worker // 2) * 25000000
                result.append({"worker": worker, "report": _report(
                    Path("unused"), source, base, worker % 2)})
            return result

        self.assertEqual(hp.collect(rows(), source, run_id, 1.0)["status"],
                         "completed_positive")
        for mutation in ("base", "seed", "digest", "valid_wrong_digest",
                         "script_missing", "script_wrong", "stop", "stop_case_cap", "bool_attempts", "failures",
                         "fidelity", "two_player", "physical",
                         "elapsed_negative", "elapsed_nan", "elapsed_bool"):
            with self.subTest(mutation=mutation):
                candidate = rows()
                report = candidate[2]["report"]
                if mutation == "base":
                    report["base_seed"] += 1
                elif mutation == "seed":
                    report["case_results"][0]["seed"] += 1
                elif mutation == "digest":
                    report["case_results"][0]["input_sha256"] = "not-a-sha"
                elif mutation == "valid_wrong_digest":
                    report["case_results"][0]["input_sha256"] = "0" * 64
                elif mutation == "script_missing":
                    report["case_results"][0].pop("script_sha256")
                elif mutation == "script_wrong":
                    report["case_results"][0]["script_sha256"] = "0" * 64
                elif mutation == "stop":
                    report["stop_reason"] = "invariant_failure"
                elif mutation == "stop_case_cap":
                    report["stop_reason"] = "case_cap"
                elif mutation == "bool_attempts":
                    report["attempted_cases"] = True
                elif mutation == "failures":
                    report["failures"] = [{"trial_index": 0, "kind": "RuntimeError"}]
                elif mutation == "fidelity":
                    report["original_native_fidelity_accepted"] = True
                elif mutation == "two_player":
                    report["complete_two_player_result_accepted"] = True
                elif mutation == "physical":
                    report["physical_gamepads_tested"] = True
                elif mutation == "elapsed_negative":
                    report["elapsed_seconds"] = -0.1
                elif mutation == "elapsed_nan":
                    report["elapsed_seconds"] = float("nan")
                else:
                    report["elapsed_seconds"] = True
                report["receipt_sha256"] = native.hash_object({
                    k: v for k, v in report.items() if k != "receipt_sha256"})
                outcome = hp.collect(candidate, source, run_id, 1.0)
                self.assertEqual(outcome["status"], "research_failure")
                self.assertTrue(any(row.get("worker") == 2
                                    for row in outcome["issues"]))

    def test_full_case_cap_stop_reason_and_windows_digest(self):
        source, run_id = "a" * 40, 41151999999
        prefix = native.base_source()[0]
        seed = run_id % 10000000
        rendered = native.render_input(prefix, native.input_plan(seed)[0], None)
        with patch.object(hp.os, "linesep", "\r\n"):
            self.assertEqual(hp.expected_treatment_digest(prefix, seed),
                             hashlib.sha256(rendered.replace(
                                 "\n", "\r\n").encode("utf-8")).hexdigest())
            rendered_script = native.render_script(native.base_source()[1])
            self.assertEqual(hp.expected_script_digest(native.base_source()[1]),
                             hashlib.sha256(rendered_script.replace(
                                 "\n", "\r\n").encode("utf-8")).hexdigest())
        rows = []
        for worker in range(hp.WORKERS):
            base = run_id % 10000000 + (worker // 2) * 25000000
            report = _report(Path("unused"), source, base, worker % 2)
            report["case_results"] = []
            for i in range(hp.MAX_CASES):
                case_seed = base + (worker % 2) * 1000003 + i
                report["case_results"].append({
                    "seed": case_seed,
                    "input_sha256": hp.expected_treatment_digest(prefix, case_seed),
                    "script_sha256": hp.expected_script_digest(native.base_source()[1]),
                    "real_native_processes": 4,
                    "bit_exact_replay": True,
                    "two_seats_observably_active": True,
                })
            report.update(attempted_cases=hp.MAX_CASES, passed_cases=hp.MAX_CASES,
                          total_real_native_processes=4 * hp.MAX_CASES,
                          stop_reason="case_cap")
            report["receipt_sha256"] = native.hash_object({
                k: v for k, v in report.items() if k != "receipt_sha256"})
            rows.append({"worker": worker, "report": report})
        self.assertEqual(hp.collect(rows, source, run_id, 1.0)["status"],
                         "completed_positive")
        rows[2]["report"]["stop_reason"] = "wall_budget"
        rows[2]["report"]["receipt_sha256"] = native.hash_object({
            k: v for k, v in rows[2]["report"].items() if k != "receipt_sha256"})
        self.assertEqual(hp.collect(rows, source, run_id, 1.0)["status"],
                         "research_failure")

    def test_negative_replay_requires_exact_prior_success_input_and_script(self):
        source, run_id = "a" * 40, 12345

        def rows():
            results = []
            for worker in range(hp.WORKERS):
                base = run_id % 10000000 + (worker // 2) * 25000000
                report = _report(Path("unused"), source, base, worker % 2)
                if worker == 2:
                    report.update(disposition="invariant_violation",
                                  attempted_cases=2, passed_cases=1,
                                  failed_cases=1, total_real_native_processes=4,
                                  stop_reason="invariant_failure",
                                  failures=[{"trial_index": 1, "seed": base + 1,
                                             "kind": "RuntimeError",
                                             "error": "bounded synthetic failure"}])
                report["receipt_sha256"] = native.hash_object({
                    k: v for k, v in report.items() if k != "receipt_sha256"})
                results.append({"worker": worker, "report": report})
            return results

        good = hp.collect(rows(), source, run_id, 1.0)
        self.assertEqual(good["status"], "research_failure")
        self.assertEqual(good["issues"][0]["seed"], 25012346)
        self.assertEqual(good["issues"][0]["trial_index"], 1)
        for field in ("input_sha256", "script_sha256"):
            with self.subTest(field=field):
                forged = rows()
                report = forged[2]["report"]
                report["case_results"][0][field] = "0" * 64
                report["receipt_sha256"] = native.hash_object({
                    k: v for k, v in report.items() if k != "receipt_sha256"})
                outcome = hp.collect(forged, source, run_id, 1.0)
                self.assertEqual(outcome["status"], "research_failure")
                self.assertEqual(outcome["issues"][0]["reason"],
                                 "unverifiable source-owned failure")
                self.assertNotIn("seed", outcome["issues"][0])

    def test_authentic_failure_receipt_retains_seed_without_local_path(self):
        source = "a" * 40
        rows = []
        for index in range(4):
            seed = 12345 + (index // 2) * 25000000
            report = _report(Path("unused"), source, seed, index % 2)
            if index == 2:
                case_seed = seed
                report.update(disposition="invariant_violation",
                              attempted_cases=1, passed_cases=0,
                              failed_cases=1, stop_reason="invariant_failure",
                              total_real_native_processes=0,
                              case_results=[],
                              failures=[{"seed": case_seed, "trial_index": 0,
                                         "kind": "TimeoutExpired",
                                         "error": "C:/Users/secret/roms/retail.sfc"}])
                report.pop("receipt_sha256")
                report["receipt_sha256"] = native.hash_object(report)
            rows.append({"worker": index, "report": report})
        result = hp.collect(rows, source, 12345, 1.0)
        self.assertEqual(result["status"], "research_failure")
        self.assertEqual(result["release_gate_credit"], 0)
        self.assertEqual(result["issues"][0]["worker"], 2)
        self.assertEqual(result["issues"][0]["seed"], 25012345)
        self.assertEqual(result["issues"][0]["trial_index"], 0)
        self.assertEqual(result["issues"][0]["kind"], "TimeoutExpired")
        self.assertNotIn("secret", json.dumps(result))
        self.assertNotIn("retail.sfc", json.dumps(result))
        # Missing original source identity must not publish even the seed.
        report = rows[2]["report"]
        report["identity"]["source_commit"] = "f" * 40
        report.pop("receipt_sha256")
        report["receipt_sha256"] = native.hash_object(report)
        unbound = hp.collect(rows, source, 12345, 1.0)
        self.assertEqual(unbound["issues"][0]["reason"],
                         "unverifiable source-owned failure")
        self.assertNotIn("seed", unbound["issues"][0])
        # A checksum-valid but wrongly attributed seed is not replay evidence.
        report["identity"]["source_commit"] = source
        report["failures"][0]["seed"] += 1
        report.pop("receipt_sha256")
        report["receipt_sha256"] = native.hash_object(report)
        mismatch = hp.collect(rows, source, 12345, 1.0)
        self.assertEqual(mismatch["issues"][0]["reason"],
                         "unverifiable source-owned failure")
        self.assertNotIn("seed", mismatch["issues"][0])

    def test_recomputed_negative_receipts_cannot_publish_foreign_provenance(self):
        source, run_id = "a" * 40, 12345
        def rows():
            results = []
            for worker in range(4):
                base = run_id + (worker // 2) * 25000000
                report = _report(Path("unused"), source, base, worker % 2)
                if worker == 2:
                    report.update(disposition="invariant_violation",
                                  stop_reason="invariant_failure",
                                  attempted_cases=1, passed_cases=0, failed_cases=1,
                                  total_real_native_processes=0, case_results=[],
                                  failures=[{"trial_index": 0, "seed": base,
                                             "kind": "RuntimeError",
                                             "error": "C:/private/foreign.rom"}])
                report["receipt_sha256"] = native.hash_object(
                    {k: v for k, v in report.items() if k != "receipt_sha256"})
                results.append({"worker": worker, "report": report})
            return results
        valid = hp.collect(rows(), source, run_id, 1.0)
        self.assertEqual(valid["issues"][0]["seed"], 25012345)
        self.assertEqual(valid["candidate_identity"]["rom_sha256"], native.ROM_SHA)
        self.assertNotIn("private", json.dumps(valid))
        self.assertEqual(valid["release_gate_credit"], 0)
        for key, replacement in (
            ("native_executable_sha256", "e" * 64),
            ("rom_sha256", "e" * 64),
            ("stock_input_sha256", "e" * 64),
            ("stock_script_sha256", "e" * 64),
            ("source_commit", "e" * 40),
        ):
            changed = rows()
            receipt = changed[2]["report"]
            receipt["identity"][key] = replacement
            receipt["receipt_sha256"] = native.hash_object(
                {k: v for k, v in receipt.items() if k != "receipt_sha256"})
            result = hp.collect(changed, source, run_id, 1.0)
            self.assertEqual(result["issues"][0]["reason"],
                             "unverifiable source-owned failure", key)
            self.assertNotIn("seed", result["issues"][0], key)
        for key, replacement in (
            ("attempted_cases", 2), ("passed_cases", 1),
            ("total_real_native_processes", 4), ("stop_reason", "case_cap"),
            ("base_seed", 4), ("minutes_budget", 60),
        ):
            changed = rows()
            receipt = changed[2]["report"]
            receipt[key] = replacement
            receipt["receipt_sha256"] = native.hash_object(
                {k: v for k, v in receipt.items() if k != "receipt_sha256"})
            result = hp.collect(changed, source, run_id, 1.0)
            self.assertNotIn("seed", result["issues"][0], key)
        for invalid in (1, hp.MAX_CASES):
            changed = rows()
            receipt = changed[2]["report"]
            receipt["failures"][0]["trial_index"] = invalid
            receipt["failures"][0]["seed"] = 25012345 + invalid
            receipt["receipt_sha256"] = native.hash_object(
                {k: v for k, v in receipt.items() if k != "receipt_sha256"})
            result = hp.collect(changed, source, run_id, 1.0)
            self.assertNotIn("seed", result["issues"][0])
        changed = rows()
        del changed[2]["report"]["identity"]["stock_script_sha256"]
        receipt = changed[2]["report"]
        receipt["receipt_sha256"] = native.hash_object(
            {k: v for k, v in receipt.items() if k != "receipt_sha256"})
        self.assertNotIn("seed", hp.collect(changed, source, run_id, 1.0)["issues"][0])

    def test_cross_worker_negative_identity_mismatch_redacts_all_replay_seeds(self):
        source, run_id = "a" * 40, 12345
        rows = []
        for worker in range(4):
            base = run_id + (worker // 2) * 25000000
            receipt = _report(Path("unused"), source, base, worker % 2)
            if worker in (1, 2):
                receipt.update(disposition="invariant_violation",
                               stop_reason="invariant_failure",
                               attempted_cases=1, passed_cases=0, failed_cases=1,
                               total_real_native_processes=0, case_results=[],
                               failures=[{"trial_index": 0,
                                          "seed": base + (worker % 2) * 1000003,
                                          "kind": "RuntimeError",
                                          "error": "C:/private/foreign.rom"}])
            if worker == 2:
                receipt["identity"]["native_executable_sha256"] = "e" * 64
            receipt["receipt_sha256"] = native.hash_object(
                {k: v for k, v in receipt.items() if k != "receipt_sha256"})
            rows.append({"worker": worker, "report": receipt})
        result = hp.collect(rows, source, run_id, 1.0)
        self.assertEqual(result["status"], "research_failure")
        self.assertTrue(result["issues"])
        self.assertTrue(all("seed" not in issue for issue in result["issues"]))
        self.assertNotIn("private", json.dumps(result))

    def test_worker_failure_is_rejected_after_all_join_without_fabricated_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            exe, rom = root / "game.exe", root / "rom.sfc"
            exe.write_bytes(b"x")
            rom.write_bytes(b"y")
            seen = []
            def fail_one(**kwargs):
                i = int(kwargs["work"].name.rsplit("-", 1)[-1])
                seen.append(i)
                if i == 2:
                    raise ValueError("C:/Users/secret/roms/retail.sfc")
                return _report(kwargs["work"], kwargs["source_sha"],
                               kwargs["base_seed"], kwargs["shard"])
            with patch.object(hp.native, "run_shard", side_effect=fail_one):
                row = hp.run(exe, rom, _env(root), root / "partial.json")
            self.assertEqual(sorted(seen), list(range(4)))
            self.assertEqual(row["status"], "research_failure")
            self.assertEqual(row["issues"][0]["reason"], "worker exception")
            self.assertEqual(row["issues"][0]["kind"], "ValueError")
            self.assertIn("base_seed", row["issues"][0])
            self.assertNotIn("secret", json.dumps(row))
            self.assertNotIn("retail.sfc", json.dumps(row))
            self.assertEqual(row["release_gate_credit"], 0)

    def test_failed_hp_campaign_retains_sealed_partial_research_without_acceptance(self):
        # The first post-fix scheduled HP run had four authenticated workers
        # with trial-2/3 RuntimeErrors. Its aggregate discarded earlier
        # source-sealed positive cases and reduced reported processes to zero.
        source, run_id = "a" * 40, 41223647258
        rows = []
        stock_input, _ = native.base_source()
        for worker in range(hp.WORKERS):
            base = run_id % 10000000 + (worker // 2) * 25000000
            shard = worker % 2
            first = base + shard * 1000003
            row = _report(Path("unused"), source, base, shard)
            second = dict(row["case_results"][0])
            second["seed"] = first + 1
            second["input_sha256"] = hp.expected_treatment_digest(
                stock_input, first + 1)
            row.update(
                disposition="invariant_violation", attempted_cases=4,
                passed_cases=2, failed_cases=2,
                total_real_native_processes=8,
                stop_reason="invariant_failure",
                case_results=[row["case_results"][0], second],
                failures=[
                    {"trial_index": 2, "seed": first + 2,
                     "kind": "RuntimeError",
                     "error": "real guest process timeout (20s)"},
                    {"trial_index": 3, "seed": first + 3,
                     "kind": "RuntimeError",
                     "error": "guest exited 1; stdout/stderr tail=C:/private/ROM.sfc"},
                ],
            )
            row["receipt_sha256"] = native.hash_object({
                k: v for k, v in row.items() if k != "receipt_sha256"})
            rows.append({"worker": worker, "report": row})
        result = hp.collect(rows, source, run_id, 306.063)
        self.assertEqual(result["status"], "research_failure")
        self.assertEqual(result["accepted_cases"], 0)
        self.assertEqual(result["real_guest_processes"], 0)
        self.assertEqual(result["source_attested_pre_failure_cases"], 8)
        self.assertEqual(result["source_attested_pre_failure_native_processes"], 32)
        self.assertEqual(len(result["issues"]), 8)
        self.assertEqual({i["failure_category"] for i in result["issues"]},
                         {"guest_timeout", "guest_nonzero_exit"})
        self.assertNotIn("private", json.dumps(result))
        self.assertEqual(result["original_native_event_credit"], 0)
        self.assertEqual(result["release_gate_credit"], 0)

    def test_failure_category_refuses_arbitrary_private_text(self):
        self.assertEqual(hp.safe_failure_category(
            "RuntimeError", "real guest process timeout (90s)"), "guest_timeout")
        self.assertEqual(hp.safe_failure_category(
            "RuntimeError", "guest exited -1; stderr=C:/private/file"),
            "guest_nonzero_exit")
        for kind, detail in (
            ("RuntimeError", "C:/private/ROM.sfc"),
            ("ValueError", "real guest process timeout (90s)"),
            ("RuntimeError", "real guest process timeout (9999s)"),
            ("RuntimeError", None),
        ):
            with self.subTest(kind=kind, detail=detail):
                self.assertEqual(hp.safe_failure_category(kind, detail),
                                 "unclassified")


if __name__ == "__main__":
    unittest.main()
