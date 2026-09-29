import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "query_ui_state.py"


class QueryUiStateTests(unittest.TestCase):
    def test_queries_hex_and_decimal_ids(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            index = Path(td) / "index.json"
            index.write_text(json.dumps({
                "address": "7E:009F",
                "entries": [
                    {"value": "0x99", "state_id": "RESULT_RACE", "status": "historical", "source": "bot.lua"}
                ],
            }))
            for value in ("0x99", "153"):
                proc = subprocess.run(
                    [sys.executable, str(TOOL), "--index", str(index), "--menu-id", value],
                    capture_output=True, text=True, check=False,
                )
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertIn("RESULT_RACE", proc.stdout)
                self.assertIn("0x99", proc.stdout)

    def test_state_query_is_case_insensitive(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            index = Path(td) / "index.json"
            index.write_text(json.dumps({
                "address": "7E:009F",
                "entries": [
                    {"value": "0xD7", "state_id": "MAIN_MENU", "status": "verified", "source": "fixture"}
                ],
            }))
            proc = subprocess.run(
                [sys.executable, str(TOOL), "--index", str(index), "--state", "main_menu", "--json"],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            result = json.loads(proc.stdout)
            self.assertEqual(result[0]["value"], "0xD7")

    def test_unknown_returns_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            index = Path(td) / "index.json"
            index.write_text(json.dumps({"address": "7E:009F", "entries": []}))
            proc = subprocess.run(
                [sys.executable, str(TOOL), "--index", str(index), "--menu-id", "0x42"],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(proc.returncode, 1)


if __name__ == "__main__":
    unittest.main()
