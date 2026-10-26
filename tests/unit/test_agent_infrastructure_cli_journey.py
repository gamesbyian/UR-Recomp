"""Real subprocess journey through existing agent evidence/navigation CLIs.

No GitHub calls, ROM, secrets, Windows binaries, or release gate mutations.
The test exercises actual cross-script JSON interfaces, not only pure helpers.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
REPO = "gamesbyian/UR-Recomp"


def cli(*args, success=True):
    process = subprocess.run(
        [sys.executable, *map(str, args)], cwd=ROOT,
        text=True, capture_output=True, timeout=30,
    )
    if success and process.returncode:
        raise AssertionError(
            f"CLI failed: {args[0]}: {process.stderr[-1500:]}")
    return process


@unittest.skipUnless((ROOT / ".git").exists(), "source-bound CLIs need Git checkout")
class AgentInfrastructureCliJourneyTests(unittest.TestCase):
    def test_source_receipt_retention_preflight_and_handoff(self):
        head = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        self.assertRegex(head, r"^[0-9a-f]{40}$")
        when = datetime.now(timezone.utc)
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            def save(name, value):
                path = folder / name
                path.write_text(json.dumps(value), encoding="utf-8")
                return path

            receipt = save("receipt.json", {
                "schema": "UR-CI-UNIT-RESULT/1",
                "authority": "diagnostic-only", "source": {"pr_head_sha": head},
                "outcome": "pass", "total_tests_observed": 2,
                "shards": [{"outcome": "pass"}], "missing_evidence": [],
                "release_gate_credit": 0,
            })
            db = folder / "receipts.sqlite"
            cli("tools/index_ci_receipts.py", "ingest", "--db", db, receipt)
            run = save("run.json", {
                "id": 9001, "name": "fixture run", "head_sha": head,
                "status": "completed", "conclusion": "success",
            })
            artifacts = save("artifacts.json", {
                "total_count": 1, "artifacts": [{
                    "id": 88, "name": "ROM-free synthetic contract",
                    "size_in_bytes": 1024, "digest": "sha256:" + "a" * 64,
                    "created_at": (when - timedelta(minutes=5)).isoformat(),
                    "expires_at": (when + timedelta(days=3)).isoformat(),
                    "expired": False,
                    "workflow_run": {"id": 9001, "head_sha": head},
                }],
            })
            retention = folder / "retention.json"
            cli("tools/artifact_retention_preflight.py",
                "--saved-run", run, "--saved-artifacts", artifacts,
                "--expected-sha", head, "--json-out", retention)
            self.assertEqual(json.loads(retention.read_text())
                             ["artifacts"][0]["availability"],
                             "metadata_ready_for_independent_byte_audit")

            snapshot = save("snapshot.json", {
                "schema": "UR-GITHUB-PR-SNAPSHOT/1",
                "repository": REPO, "main_sha": head,
                "open_census_complete": True, "open_prs": [],
                "closed_census_complete": False, "closed_prs_sample": [],
            })
            preflight = folder / "control.json"
            cli("tools/agent_release_control.py", "--snapshot", snapshot,
                "--lane", "ci", "--receipt-db", db,
                "--artifact-availability", retention, "--json-out", preflight)
            report = json.loads(preflight.read_text())
            self.assertEqual(report["main_sha"], head)
            self.assertEqual(report["evidence_index_scope"], "local_only")
            self.assertEqual(len(report["indexed_main_producer_receipts"]), 1)
            self.assertEqual(report["artifact_retention"]["source_sha"], head)
            self.assertTrue(report["artifact_retention"]
                            ["artifacts"][0]["metadata_ready_for_byte_review"])
            self.assertEqual(report["artifact_retention"]
                             ["artifacts"][0]["release_gate_credit"], 0)
            self.assertEqual(report["release"]["decision"],
                             "HOLD_independent_source_zip_hardware_and_gameplay_review")

            handoff = folder / "handoff.json"
            cli("tools/agent_action_handoff.py", "ci", "--json-out", handoff)
            packet = json.loads(handoff.read_text())
            self.assertEqual(packet["checkout_commit"], head)
            self.assertEqual(packet["next_step"]["gate"], None)
            self.assertEqual(packet["source_changes"]["state"],
                             "baseline_not_supplied")
            self.assertEqual(packet["release"]["accepted_gate_count_as_recorded"],
                             report["release"]["passed_recorded"])

            # A handoff cannot silently reuse data labelled for another source.
            altered = json.loads(retention.read_text())
            altered["expected_sha"] = "b" * 40
            wrong = save("wrong-retention.json", altered)
            fail = cli("tools/agent_release_control.py",
                       "--snapshot", snapshot, "--lane", "ci",
                       "--artifact-availability", wrong, success=False)
            self.assertNotEqual(fail.returncode, 0)
            self.assertIn("artifact availability not source-qualified",
                          fail.stderr)


if __name__ == "__main__":
    unittest.main()
