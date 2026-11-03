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

    def test_single_worker_lock(self):
        (self.root / "worker.lock").mkdir()
        self.assertEqual(broker.run_once(self.root, self.repo)["state"], "busy")

    def test_failed_job_keeps_receipt(self):
        job = broker.submit(self.root, self.repo, "agent-selector", self.sha, "agent-2")
        result = broker.run_once(self.root, self.repo)
        self.assertEqual(result["state"], "failed")
        self.assertIn("agent_control.py", result.get("stderr", ""))
        self.assertTrue((self.root / "failed" / (job["job_id"] + ".json")).exists())


if __name__ == "__main__":
    unittest.main()
