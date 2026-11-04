"""Contract tests for the allowlisted HP remote job broker."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[2] / "tools" / "hp_safe_job_broker.py"
spec = importlib.util.spec_from_file_location("hp_safe_job_broker", SCRIPT)
broker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(broker)


class BrokerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for state in broker.STATES:
            (self.root / state).mkdir()
        self.repo = self.root / "repo"
        self.repo.mkdir()
        subprocess.run(["git", "-C", str(self.repo), "init", "-q"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "-c", "user.name=Test",
                        "-c", "user.email=test@example.invalid", "commit", "--allow-empty",
                        "-qm", "test"], check=True)
        self.sha = broker.git(self.repo, "rev-parse", "HEAD")
        subprocess.run(["git", "-C", str(self.repo), "update-ref",
                        "refs/remotes/origin/main", self.sha], check=True)

    def test_allowlisted_job_and_persistent_result(self):
        job = broker.submit(self.root, self.repo, "repo-status", self.sha, "agent-1")
        result = broker.run_once(self.root, self.repo)
        self.assertEqual(result["state"], "complete")
        self.assertEqual(result["job_id"], job["job_id"])
        self.assertIn(self.sha, result["stdout"])
        self.assertEqual(json.loads((self.root / "complete" / (job["job_id"] + ".json"))
                                    .read_text())["exit_code"], 0)
        self.assertEqual(broker.run_once(self.root, self.repo)["state"], "empty")

    def test_rejects_untrusted_and_arbitrary_commands(self):
        with self.assertRaises(ValueError):
            broker.submit(self.root, self.repo, "powershell", self.sha, "agent-1")
        with self.assertRaises(ValueError):
            broker.submit(self.root, self.repo, "repo-status", "bad-sha", "agent-1")
        with self.assertRaises(ValueError):
            broker.submit(self.root, self.repo, "repo-status", self.sha, "agent-99")

    def test_bounded_capture_rejects_noisy_child(self):
        import os
        import sys
        result = broker.bounded_process(
            [sys.executable, "-c",
             "import sys; sys.stdout.write('x'*2000000); sys.stderr.write('y'*2000000)"],
            self.repo, os.environ.copy(), timeout=15, output_limit=2048)
        self.assertTrue(result["output_overflow"])
        self.assertLessEqual(len(result["stdout"].encode("utf-8")), 2048)
        self.assertLessEqual(len(result["stderr"].encode("utf-8")), 2048)

    def test_bounded_capture_normal_output(self):
        import os
        import sys
        result = broker.bounded_process(
            [sys.executable, "-c", "print('safe')"],
            self.repo, os.environ.copy(), timeout=15)
        self.assertEqual(result["returncode"], 0)
        self.assertEqual(result["stdout"].strip(), "safe")
        self.assertFalse(result["output_overflow"])
        self.assertFalse(result["pipe_read_incomplete"])

    def test_direct_child_timeout_is_recorded(self):
        import os
        import sys
        result = broker.bounded_process(
            [sys.executable, "-c", "import time; time.sleep(15)"],
            self.repo, os.environ.copy(), timeout=0.1)
        self.assertTrue(result["timed_out"])
        self.assertFalse(result["termination_unconfirmed"])
        self.assertFalse(result["pipe_read_incomplete"])

    def test_git_helper_rejects_output_overflow(self):
        with patch.object(broker, "bounded_process", return_value={
            "returncode": 0, "output_overflow": True, "timed_out": False,
            "termination_unconfirmed": False, "pipe_read_incomplete": False,
            "stderr": "", "stdout": "x" * broker.MAX_OUTPUT}):
            with self.assertRaises(RuntimeError):
                broker.git(self.repo, "status", "--porcelain")

    def test_single_worker_lock(self):
        (self.root / "worker.lock").mkdir()
        self.assertEqual(broker.run_once(self.root, self.repo)["state"], "busy")

    def test_stranded_job_blocks_next_without_consumer_side_effect(self):
        old = broker.submit(self.root, self.repo, "repo-status", self.sha, "agent-1")
        (self.root / "pending" / (old["job_id"] + ".json")).rename(
            self.root / "running" / (old["job_id"] + ".json"))
        pending = broker.submit(self.root, self.repo, "repo-status", self.sha, "agent-2")
        result = broker.run_once(self.root, self.repo)
        self.assertEqual(result["state"], "blocked")
        self.assertEqual(result["running_job_ids"], [old["job_id"]])
        self.assertTrue((self.root / "pending" / (pending["job_id"] + ".json")).exists())
        self.assertFalse((self.root / "worker.lock").exists())

    def test_diagnostics_only_report_stranded_jobs(self):
        self.assertFalse(broker.diagnose(self.root)["needs_operator_inspection"])
        lock = self.root / "worker.lock"
        lock.mkdir()
        broker.atomic_json(lock / "owner.json", {"pid": 12345, "started_utc": "test"})
        job = broker.submit(self.root, self.repo, "repo-status", self.sha, "agent-1")
        (self.root / "pending" / (job["job_id"] + ".json")).rename(
            self.root / "running" / (job["job_id"] + ".json"))
        finding = broker.diagnose(self.root)
        self.assertTrue(finding["needs_operator_inspection"])
        self.assertEqual(finding["owner"]["pid"], 12345)
        self.assertEqual(finding["running_jobs"][0]["job_id"], job["job_id"])
        self.assertTrue((self.root / "running" / (job["job_id"] + ".json")).exists())

    def test_failed_job_keeps_receipt(self):
        job = broker.submit(self.root, self.repo, "agent-selector", self.sha, "agent-2")
        result = broker.run_once(self.root, self.repo)
        self.assertEqual(result["state"], "failed")
        self.assertIn("agent_control.py", result.get("stderr", ""))
        self.assertTrue((self.root / "failed" / (job["job_id"] + ".json")).exists())


if __name__ == "__main__":
    unittest.main()
