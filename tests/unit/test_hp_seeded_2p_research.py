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
        self.assertIn("cron: '17 * * * *'", s)
        self.assertNotIn("17 */3 * * *", s)
        # Exactly one scheduled entry is admitted: no overlapping extra
        # cron, second scheduler, fork/PR dispatch or fast-path QA bypass.
        self.assertEqual(s.count("- cron:"), 1)
        self.assertIn("group: hp-seeded-2p-research-${{ github.ref }}", s)
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
        # The only execution of HP seeded research is the distinct trusted
        # schedule/manual HP caller. Ordinary main-push Windows builds and
        # hosted PR candidates never set hp_seeded_2p: true, so dispatching
        # them for pure research edits duplicates costly game/package QA and
        # does not test the changed research behavior. The complete tooling
        # suite, hygiene and next real scheduled HP run own that invalidation.
        for workflow in (WIN, OWNER, HOSTED):
            source = workflow.read_text()
            for path in ("tools/hp_seeded_2p_research.py",
                         "tools/qa02_native_2p_seeded_endurance.py",
                         "tests/unit/test_hp_seeded_2p_research.py",
                         ".github/workflows/owner-hp-seeded-2p-research.yml"):
                with self.subTest(workflow=workflow.name, path=path):
                    self.assertNotIn('      - "' + path + '"', source)
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

    def test_existing_research_work_root_cannot_be_reused_or_destroyed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env = _env(root)
            exe, rom = root / "game.exe", root / "retail.sfc"
            exe.write_bytes(b"synthetic Windows executable")
            rom.write_bytes(b"synthetic stock ROM")
            private = root / (
                f"hp-seeded-2p-{env['GITHUB_RUN_ID']}-{env['GITHUB_RUN_ATTEMPT']}")
            private.mkdir()
            marker = private / "historical-evidence.txt"
            marker.write_text("must not be replaced", encoding="utf-8")
            receipt = root / "new-receipt.json"
            with patch.object(hp.native, "run_shard") as guest:
                with self.assertRaisesRegex(ValueError, "already exists"):
                    hp.run(exe, rom, env, receipt)
                guest.assert_not_called()
            self.assertEqual(marker.read_text(encoding="utf-8"),
                             "must not be replaced")
            self.assertFalse(receipt.exists())

    def test_redirected_executable_and_stock_rom_refused_before_guest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env = _env(root)
            exe, rom = root / "game.exe", root / "retail.sfc"
            exe.write_bytes(b"synthetic Windows executable")
            rom.write_bytes(b"synthetic stock ROM")
            redirected_exe = root / "redirected.exe"
            redirected_rom = root / "redirected.sfc"
            try:
                redirected_exe.symlink_to(exe.name)
                redirected_rom.symlink_to(rom.name)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"fixture symlinks unavailable: {type(exc).__name__}")
            self.assertTrue(redirected_exe.is_file())
            self.assertTrue(redirected_rom.is_file())
            receipt = root / "new-receipt.json"
            work = root / (
                f"hp-seeded-2p-{env['GITHUB_RUN_ID']}-{env['GITHUB_RUN_ATTEMPT']}")
            with patch.object(hp.native, "run_shard") as guest:
                for target_exe, target_rom in (
                    (redirected_exe, rom), (exe, redirected_rom),
                ):
                    with self.subTest(exe=target_exe.name, rom=target_rom.name):
                        with self.assertRaisesRegex(
                                ValueError, "missing/redirected exact game"):
                            hp.run(target_exe, target_rom, env, receipt)
                guest.assert_not_called()
            self.assertFalse(work.exists())
            self.assertFalse(receipt.exists())

    def test_eight_workers_fit_unique_bounded_source_owned_namespaces(self):
        self.assertEqual(hp.WORKERS, 8)
        source = (ROOT / "tools/hp_seeded_2p_research.py").read_text()
        self.assertIn("ThreadPoolExecutor(max_workers=WORKERS)", source)
        self.assertIn("seeds = tuple(base + (i // 2) * 25_000_000 for i in range(WORKERS))", source)
        self.assertIn("work=private / f\"worker-{i}\"", source)
        run_id = 41244390541
        base = run_id % 10_000_000
        bases = [base + (worker // 2) * 25_000_000
                 for worker in range(hp.WORKERS)]
        seeds = [b + (worker % 2) * 1_000_003
                 for worker, b in enumerate(bases)]
        self.assertEqual(len(set(seeds)), hp.WORKERS)
        self.assertLess(max(seeds), 100_000_000)
        self.assertEqual([s - bases[i] for i, s in enumerate(seeds)],
                         [0, 1_000_003] * (hp.WORKERS // 2))

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
            self.assertEqual(result["accepted_cases"], hp.WORKERS)
            self.assertEqual(result["real_guest_processes"], 4 * hp.WORKERS)
            self.assertEqual(len(calls), hp.WORKERS)
            self.assertEqual(len(set((shard, base) for shard, base in calls)), hp.WORKERS)
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
        for index in range(hp.WORKERS):
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
            for worker in range(hp.WORKERS):
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
        for worker in range(hp.WORKERS):
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
            self.assertEqual(sorted(seen), list(range(hp.WORKERS)))
            self.assertEqual(row["status"], "research_failure")
            self.assertEqual(row["issues"][0]["reason"], "worker exception")
            self.assertEqual(row["issues"][0]["kind"], "ValueError")
            self.assertIn("base_seed", row["issues"][0])
            self.assertNotIn("secret", json.dumps(row))
            self.assertNotIn("retail.sfc", json.dumps(row))
            self.assertEqual(row["release_gate_credit"], 0)

    def test_failed_hp_campaign_retains_sealed_partial_research_without_acceptance(self):
        # The historical four-worker HP run had trial-2/3 RuntimeErrors.
        # Simulate that failure pattern across the current worker population;
        # its strict aggregate discarded earlier
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
        self.assertEqual(result["source_attested_pre_failure_cases"], 2 * hp.WORKERS)
        self.assertEqual(result["source_attested_pre_failure_native_processes"], 8 * hp.WORKERS)
        self.assertEqual(len(result["issues"]), 2 * hp.WORKERS)
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

    def test_typed_guest_exit_survives_truncated_private_tail(self):
        # Native producer slices the last 700 chars, which can discard the
        # original RuntimeError prefix after 900 chars of guest output.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            done = type("Done", (), {"returncode": 3,
                                     "stdout": "X" * 900,
                                     "stderr": "C:/private/ROM.sfc"})()
            with patch.object(native.subprocess, "run", return_value=done):
                with self.assertRaises(native.GuestProcessError) as raised:
                    native.execute(root / "game.exe", root / "retail.sfc",
                                   root / "input", root / "script",
                                   root / "nonzero", 90)
            self.assertEqual(raised.exception.failure_category, "guest_nonzero_exit")
            truncated = str(raised.exception)[-700:]
            self.assertEqual(hp.safe_failure_category("RuntimeError", truncated),
                             "unclassified")
            source, run_id = "a" * 40, 41223647258
            rows = []
            for worker in range(hp.WORKERS):
                base = run_id % 10000000 + (worker // 2) * 25000000
                shard = worker % 2
                row = _report(root, source, base, shard)
                row.update(disposition="invariant_violation", attempted_cases=2,
                           passed_cases=1, failed_cases=1,
                           stop_reason="invariant_failure",
                           failures=[{"trial_index": 1,
                                      "seed": base + shard * 1000003 + 1,
                                      "kind": "GuestProcessError",
                                      "error": truncated,
                                      "failure_category": "guest_nonzero_exit"}])
                row["receipt_sha256"] = native.hash_object({
                    k: v for k, v in row.items() if k != "receipt_sha256"})
                rows.append({"worker": worker, "report": row})
            result = hp.collect(rows, source, run_id, 306.063)
            self.assertEqual(result["status"], "research_failure")
            self.assertEqual(result["accepted_cases"], 0)
            self.assertEqual(result["real_guest_processes"], 0)
            self.assertEqual(result["source_attested_pre_failure_cases"], hp.WORKERS)
            self.assertEqual({i["failure_category"] for i in result["issues"]},
                             {"guest_nonzero_exit"})
            self.assertNotIn("private", json.dumps(result))
            self.assertEqual(result["release_gate_credit"], 0)

    def test_typed_timeout_and_contradictory_categories_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            timeout = native.subprocess.TimeoutExpired(cmd="guest", timeout=90)
            with patch.object(native.subprocess, "run", side_effect=timeout):
                with self.assertRaises(native.GuestProcessError) as raised:
                    native.execute(root / "game.exe", root / "retail.sfc",
                                   root / "input", root / "script",
                                   root / "timeout", 90)
            self.assertEqual(raised.exception.failure_category, "guest_timeout")
        self.assertEqual(hp.safe_failure_category(
            "RuntimeError", "guest exited 0; stdout/stderr tail=bad"), "unclassified")
        source, run_id = "a" * 40, 41223647258
        base = run_id % 10000000
        for kind, category, error in (
            ("GuestProcessError", "other", "guest exited 2; x"),
            ("GuestProcessError", "guest_timeout", "guest exited 2; x"),
            ("ValueError", "guest_nonzero_exit", "arbitrary"),
        ):
            with self.subTest(kind=kind, category=category):
                row = _report(Path("unused"), source, base, 0)
                row.update(disposition="invariant_violation", attempted_cases=2,
                           passed_cases=1, failed_cases=1,
                           stop_reason="invariant_failure",
                           failures=[{"trial_index": 1, "seed": base + 1,
                                      "kind": kind, "error": error,
                                      "failure_category": category}])
                self.assertEqual(hp.source_owned_failure_notes(
                    row, source, 0, run_id), [])

    def test_shard_captures_typed_category_before_error_tail(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            message = "guest exited 3; stdout/stderr tail=" + "X" * 900
            with patch.object(native, "identity", return_value={}), \
                 patch.object(native, "trial",
                              side_effect=native.GuestProcessError(
                                  "guest_nonzero_exit", message)):
                row = native.run_shard(
                    exe=root / "game.exe", rom=root / "retail.sfc",
                    source_sha="a" * 40, shard=0, base_seed=1234,
                    minutes=15, max_cases=10, timeout=90,
                    work=root / "shard", wall_seconds=120)
            self.assertEqual(row["failed_cases"], 2)
            self.assertEqual(row["passed_cases"], 0)
            self.assertEqual({f["failure_category"] for f in row["failures"]},
                             {"guest_nonzero_exit"})
            self.assertEqual({f["kind"] for f in row["failures"]},
                             {"GuestProcessError"})
            self.assertTrue(all(len(f["error"]) == 700 for f in row["failures"]))


    def test_result_first_summary_reports_rate_only_on_positive_campaign(self):
        row = {
            "status": "completed_positive", "source_sha": "a" * 40,
            "run_id": 41244390541, "workers": 8,
            "elapsed_seconds": 120.0, "accepted_cases": 16,
            "real_guest_processes": 64, "issues": [],
            "per_worker": [{"case_count": 2} for _ in range(8)],
            "source_attested_pre_failure_cases": 0,
        }
        message = hp.result_summary(row)
        self.assertIn("**8.00 accepted cases/min**", message)
        self.assertIn("**32.00 guest processes/min**", message)
        self.assertIn("Per-worker accepted case range: **2–2**", message)
        self.assertIn("excludes build and QA", message)
        self.assertIn("Zero original/native event", message)
        self.assertNotIn("speedup inferred from", message)
        zero = dict(row, elapsed_seconds=0.0)
        self.assertNotIn("cases/min", hp.result_summary(zero))

    def test_result_first_failure_summary_is_causal_bounded_and_private(self):
        row = {
            "status": "research_failure", "source_sha": "a" * 40,
            "run_id": 41223647258, "workers": 8,
            "elapsed_seconds": 306.063, "accepted_cases": 0,
            "real_guest_processes": 0, "per_worker": [],
            "source_attested_pre_failure_cases": 16,
            "issues": [
                {"worker": 0, "reason": "source-owned trial invariant failure",
                 "failure_category": "guest_timeout", "seed": 47258,
                 "error": "C:/private/retail.sfc"},
                {"worker": 1, "reason": "worker exception", "kind": "OSError",
                 "error": "C:/private/retail.sfc"},
                {"worker": 2, "reason": "C:/private/secret.txt",
                 "failure_category": "arbitrary-private-string",
                 "seed": "C:/private/retail.sfc"},
            ],
        }
        message = hp.result_summary(row)
        for expected in (
            "research_failure", "306.1s", "guest_timeout",
            "replay seed=47258", "worker exception",
            "unclassified collector issue", "zero acceptance credit",
            "Zero original/native event",
        ):
            self.assertIn(expected, message)
        self.assertNotIn("cases/min", message)
        self.assertNotIn("private", message)
        self.assertNotIn("OSError", message)
        self.assertNotIn("arbitrary-private-string", message)
        self.assertNotIn("16 distinct", message)
        self.assertLess(len(message), 2000)

    def test_main_emits_failure_summary_without_accepting_failed_research(self):
        row = {
            "status": "research_failure", "source_sha": "a" * 40,
            "run_id": 41223647258, "workers": 8,
            "elapsed_seconds": 306.0, "accepted_cases": 0,
            "real_guest_processes": 0, "per_worker": [],
            "source_attested_pre_failure_cases": 0,
            "issues": [{"worker": 0, "reason": "invalid source-owned research receipt"}],
        }
        with tempfile.TemporaryDirectory() as temp:
            summary = Path(temp) / "github-summary.md"
            with patch.object(hp, "run", return_value=row), \\
                 patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": str(summary)}), \\
                 patch("sys.argv", ["hp_seeded_2p_research",
                                    "--exe", "unused.exe", "--rom", "unused.sfc",
                                    "--receipt", str(Path(temp) / "receipt.json")]):
                self.assertEqual(hp.main(), 1)
            text = summary.read_text(encoding="utf-8")
            self.assertIn("invalid source-owned receipt", text)
            self.assertIn("No campaign accepted", text)


if __name__ == "__main__":
    unittest.main()
