"""Scheduled owner HP seeded two-seat execution and research acceptance policy."""
from __future__ import annotations
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
           "base_seed": seed,
           "identity": {
               "source_commit": source,
               "native_executable_sha256": "b" * 64,
               "rom_sha256": native.ROM_SHA,
               "stock_input_sha256": "c" * 64,
               "stock_script_sha256": "d" * 64,
           },
           "disposition": "completed_positive", "attempted_cases": 1,
           "passed_cases": 1, "failed_cases": 0,
           "total_real_native_processes": 4, "elapsed_seconds": 0.1,
           "release_gate_credit": 0,
           "case_results": [{
               "seed": seed + shard * 1000003,
               "input_sha256": f"{seed + shard*1000003:064x}",
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
                              failed_cases=1, total_real_native_processes=0,
                              case_results=[],
                              failures=[{"seed": case_seed, "trial_index": 0,
                                         "kind": "TimeoutExpired",
                                         "error": "C:/Users/secret/roms/retail.sfc"}])
                report.pop("receipt_sha256")
                report["receipt_sha256"] = native.hash_object(report)
            rows.append({"worker": index, "report": report})
        result = hp.collect(rows, source, 123456, 1.0)
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
        unbound = hp.collect(rows, source, 123456, 1.0)
        self.assertEqual(unbound["issues"][0]["reason"],
                         "unverifiable source-owned failure")
        self.assertNotIn("seed", unbound["issues"][0])

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
                    raise ValueError("intentional source guest failure")
                return _report(kwargs["work"], kwargs["source_sha"],
                               kwargs["base_seed"], kwargs["shard"])
            with patch.object(hp.native, "run_shard", side_effect=fail_one):
                row = hp.run(exe, rom, _env(root), root / "partial.json")
            self.assertEqual(sorted(seen), list(range(4)))
            self.assertEqual(row["status"], "research_failure")
            self.assertIn("intentional source guest failure", row["issues"][0]["reason"])
            self.assertEqual(row["release_gate_credit"], 0)


if __name__ == "__main__":
    unittest.main()
