"""Keep HP-only PowerShell maintenance syntax checked without executing it."""

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "hp-powershell-parse.yml"


class HpPowerShellParsePolicyTests(unittest.TestCase):
    def test_narrow_pr_trigger_and_hosted_only_runner(self):
        src = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("pull_request:", src)
        self.assertIn('      - "tools/devnode_benchmark/*.ps1"', src)
        self.assertIn('      - ".github/workflows/hp-powershell-parse.yml"', src)
        self.assertIn("runs-on: windows-2022", src)
        self.assertIn("timeout-minutes: 5", src)
        self.assertNotIn("self-hosted\",\"Windows", src)
        self.assertNotIn("runs-on: self-hosted", src)
        self.assertIn("persist-credentials: false", src)

    def test_parser_only_never_executes_owner_maintenance(self):
        src = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("Parser]::ParseFile(", src)
        self.assertIn("Get-ChildItem -LiteralPath $dir -Filter '*.ps1' -File", src)
        self.assertIn("if ($parseErrors.Count -gt 0)", src)
        self.assertIn("HP_POWERSHELL_PARSE_FAILED", src)
        self.assertIn("HP_POWERSHELL_PARSE_OK", src)
        for forbidden in (
            "Invoke-Expression", "Start-Process", "Stop-Process",
            "pwsh -File", "powershell.exe -File",
            "iex ", "Invoke-Command",
        ):
            self.assertNotIn(forbidden, src)


if __name__ == "__main__":
    unittest.main()
