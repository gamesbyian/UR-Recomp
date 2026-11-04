"""Contract tests for the opt-in cooperative Windows resource reservation."""
import importlib.util
from pathlib import Path
import tempfile
import threading
import unittest

SCRIPT = Path(__file__).resolve().parents[2] / "tools" / "hp_resource_reservation.py"
spec = importlib.util.spec_from_file_location("hp_resource_reservation", SCRIPT)
lease = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lease)


class LeaseTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)

    def test_mutual_exclusion_and_matching_release(self):
        first = lease.reserve(self.root, "github-actions", "run-123")
        self.assertTrue(first["ok"])
        second = lease.reserve(self.root, "hp-broker", "job-456")
        self.assertEqual(second["state"], "occupied")
        self.assertEqual(second["active"]["reservation_id"],
                         first["active"]["reservation_id"])
        rid = first["active"]["reservation_id"]
        self.assertEqual(lease.release(self.root, "hp-broker", "job-456", rid)["state"],
                         "not-owner")
        self.assertEqual(lease.release(self.root, "github-actions", "wrong", rid)["state"],
                         "not-owner")
        self.assertEqual(lease.release(self.root, "github-actions", "run-123",
                                       "0" * 32)["state"], "not-owner")
        self.assertIsNotNone(lease.status(self.root)["active"])
        self.assertTrue(lease.release(self.root, "github-actions", "run-123", rid)["ok"])
        next_reservation = lease.reserve(self.root, "hp-broker", "job-456")
        self.assertTrue(next_reservation["ok"])
        self.assertEqual(lease.release(self.root, "hp-broker", "job-456",
                                       rid)["state"], "not-owner")

    def test_corruption_fails_closed(self):
        self.root.mkdir(exist_ok=True)
        (self.root / "active.json").write_text("{bad", encoding="utf-8")
        result = lease.reserve(self.root, "github-actions", "run-123")
        self.assertEqual(result["state"], "occupied")
        self.assertIn("invalid", result["active"])
        self.assertEqual(lease.release(self.root, "github-actions", "run-123", "0" * 32)["state"],
                         "not-owner")
        self.assertTrue((self.root / "active.json").exists())

    def test_stale_operation_lock_fails_closed(self):
        (self.root / "operation.lock").mkdir()
        result = lease.locked(self.root, lambda: "unexpected", wait_s=0.01)
        self.assertFalse(result["ok"])
        self.assertEqual(result["state"], "lock-unavailable")
        self.assertTrue((self.root / "operation.lock").exists())

    def test_invalid_role_and_token_rejected(self):
        for role, token in (("admin", "a"), ("hp-broker", "../x"), ("github-actions", "")):
            with self.assertRaises(ValueError):
                lease.reserve(self.root, role, token)

    def test_race_only_one_reserves(self):
        barrier = threading.Barrier(4)
        results = []
        errors = []

        def worker(i):
            try:
                barrier.wait(timeout=3)
                results.append(lease.reserve(self.root, "hp-broker", "job-" + str(i)))
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)
        self.assertFalse(errors)
        self.assertEqual(sum(bool(r.get("ok")) for r in results), 1)
        self.assertEqual(len(results), 4)


if __name__ == "__main__":
    unittest.main()
