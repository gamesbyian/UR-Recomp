"""Bounded Windows service-account atomic Job Object qualification tests."""
import importlib.util
import os
from pathlib import Path
import unittest

SCRIPT = Path(__file__).resolve().parents[2] / "tools" / "hp_service_account_job_probe.py"
spec = importlib.util.spec_from_file_location("hp_service_account_job_probe", SCRIPT)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


@unittest.skipUnless(os.name == "nt", "Windows-only native Job Object API")
class WindowsServiceProbeTests(unittest.TestCase):
    def test_native_atomic_job_creation_and_termination(self):
        result = probe.native_probe()
        self.assertEqual(result["atomic_job_list"], "pass")
        self.assertEqual(result["kill_on_close"], "pass")
        self.assertEqual(result["pointer_bits"], 64)
        self.assertIsInstance(result["runner_already_in_job"], bool)


if __name__ == "__main__":
    unittest.main()
