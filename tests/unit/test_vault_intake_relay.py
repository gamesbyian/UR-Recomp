"""ROM-free tests for the Vault intake log relay."""
import hashlib
from pathlib import Path
import tempfile
import unittest

from tools import vault_intake_relay as relay


class VaultIntakeRelayTests(unittest.TestCase):
    def test_triage_lists_members_and_main_matches(self):
        report = {"listed_files": 2, "errors": [{"id": "x" * 20, "error": "boom"}],
                  "downloads": [{"id": "A" * 20, "bytes": 5, "sha256": "ab" * 32,
                                 "path": "z.zip",
                                 "zip": {"crosswalk": {"source_like_members": 2},
                                         "members": [{"member": "a.py", "bytes": 3,
                                                      "sha256": "cd" * 32, "source_like": True,
                                                      "exact_on_main": False, "staged": True}]}}]}
        text = "\n".join(relay.triage_lines(report))
        self.assertIn("UR-TRIAGE listed=2 downloads=1 errors=1", text)
        self.assertIn("UR-TRIAGE-ERROR", text)
        self.assertIn("source=1 main=0 staged=1 a.py", text)
        self.assertIn("source_like_members=2", text)

    def test_staged_text_is_prefixed_so_it_cannot_be_a_runner_command(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "id").mkdir()
            (root / "id" / "x.py").write_text("::set-output name=a::b\nprint(1)\n", encoding="utf-8")
            lines = relay.relay_staged(root)
        self.assertTrue(lines[0].startswith("UR-STAGED-BEGIN bytes="))
        body = lines[1:-1]
        self.assertTrue(all(row.startswith(relay.PREFIX) for row in body))
        self.assertEqual(relay.PREFIX + "::set-output name=a::b", body[0])
        self.assertEqual(lines[-1], "UR-STAGED-END")

    def test_round_trip_reconstructs_exact_bytes(self):
        data = "alpha\n\n  indented\ntrailing space \n"
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "f.py").write_text(data, encoding="utf-8")
            lines = relay.relay_staged(root)
        header = lines[0].split()
        body = "\n".join(row[len(relay.PREFIX):] for row in lines[1:-1])
        self.assertEqual(body.encode(), data.encode())
        self.assertIn("sha256=" + hashlib.sha256(data.encode()).hexdigest(), header)

    def test_binary_and_over_budget_files_are_skipped(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "bin.py").write_bytes(b"\xff\xfe\x00")
            (root / "big.py").write_text("x" * 50, encoding="utf-8")
            lines = relay.relay_staged(root, budget=10)
        self.assertTrue(all(line.startswith("UR-STAGED-SKIP") for line in lines))
        self.assertEqual(len(lines), 2)


if __name__ == "__main__":
    unittest.main()
