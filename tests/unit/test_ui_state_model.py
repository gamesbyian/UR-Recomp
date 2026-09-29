import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ROUTE = ROOT / "tools" / "query_ui_route.py"
VALIDATE = ROOT / "tools" / "validate_ui_state_model.py"


class UiStateModelTests(unittest.TestCase):
    def test_repository_ui_contracts_are_consistent(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(VALIDATE), "--root", str(ROOT)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("UI state model valid", proc.stdout)

    def test_route_planner_respects_evidence_ceiling(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            contract = Path(td) / "contract.json"
            contract.write_text(json.dumps({
                "schema_version": 1,
                "status_meanings": {
                    "verified": "",
                    "documented": "",
                    "historical": "",
                    "hypothesis": "",
                },
                "edges": [
                    {"id": "a-b", "from": "A", "to": "B", "trigger": "x", "status": "verified"},
                    {"id": "b-c", "from": "B", "to": "C", "trigger": "y", "status": "hypothesis"},
                ],
            }))

            blocked = subprocess.run(
                [
                    sys.executable, str(ROUTE),
                    "--contract", str(contract),
                    "--from", "A", "--to", "C",
                    "--max-status", "documented",
                ],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(blocked.returncode, 1)
            self.assertIn("no route", blocked.stdout)

            allowed = subprocess.run(
                [
                    sys.executable, str(ROUTE),
                    "--contract", str(contract),
                    "--from", "A", "--to", "C",
                    "--max-status", "hypothesis",
                    "--json",
                ],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(allowed.returncode, 0, allowed.stderr)
            route = json.loads(allowed.stdout)
            self.assertEqual([e["id"] for e in route], ["a-b", "b-c"])

    def test_route_planner_prefers_shortest_route(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            contract = Path(td) / "contract.json"
            contract.write_text(json.dumps({
                "schema_version": 1,
                "status_meanings": {
                    "verified": "",
                    "documented": "",
                    "historical": "",
                    "hypothesis": "",
                },
                "edges": [
                    {"id": "long-1", "from": "A", "to": "B", "trigger": "x", "status": "verified"},
                    {"id": "long-2", "from": "B", "to": "C", "trigger": "x", "status": "verified"},
                    {"id": "short", "from": "A", "to": "C", "trigger": "y", "status": "verified"},
                ],
            }))
            proc = subprocess.run(
                [
                    sys.executable, str(ROUTE),
                    "--contract", str(contract),
                    "--from", "A", "--to", "C",
                    "--json",
                ],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            route = json.loads(proc.stdout)
            self.assertEqual([e["id"] for e in route], ["short"])

    def test_route_planner_excludes_open_capability_blockers(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            contract = Path(td) / "contract.json"
            contract.write_text(json.dumps({
                "schema_version": 1,
                "status_meanings": {
                    "verified": "",
                    "documented": "",
                    "historical": "",
                    "hypothesis": "",
                },
                "capability_dependencies": {
                    "p2": {"status": "open"},
                },
                "edges": [
                    {"id": "a-b", "from": "A", "to": "B", "trigger": "x", "status": "verified"},
                    {
                        "id": "b-c",
                        "from": "B",
                        "to": "C",
                        "trigger": "p2 confirm",
                        "status": "documented",
                        "blocked_by": "p2",
                    },
                ],
            }))

            blocked = subprocess.run(
                [
                    sys.executable, str(ROUTE),
                    "--contract", str(contract),
                    "--from", "A", "--to", "C",
                    "--max-status", "documented",
                ],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(blocked.returncode, 1)
            self.assertIn("no route", blocked.stdout)

            diagnostic = subprocess.run(
                [
                    sys.executable, str(ROUTE),
                    "--contract", str(contract),
                    "--from", "A", "--to", "C",
                    "--max-status", "documented",
                    "--allow-blocked",
                    "--json",
                ],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(diagnostic.returncode, 0, diagnostic.stderr)
            route = json.loads(diagnostic.stdout)
            self.assertEqual([e["id"] for e in route], ["a-b", "b-c"])


if __name__ == "__main__":
    unittest.main()
