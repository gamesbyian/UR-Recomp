"""ROM-free security contract for owner-opt-in Windows original source one-click."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT/"tools/art/Prepare-Original-Racer-Corpus.ps1"
LAUNCHER = ROOT/"tools/art/Prepare-Original-Racer-Corpus.cmd"
EXPORTER = ROOT/"tools/art/export_registered_original_racer_corpus.py"
FREEZER = ROOT/"tools/art/freeze_racer_source_family_splits.py"


class PrivateOriginalSourceWindowsLauncherTests(unittest.TestCase):
    def setUp(self):
        self.ps = SCRIPT.read_text(encoding="utf-8")
        self.cmd = LAUNCHER.read_text(encoding="utf-8").lower()
        self.exporter = EXPORTER.read_text(encoding="utf-8")
        self.freezer = FREEZER.read_text(encoding="utf-8")

    def test_owner_file_dialog_and_correct_original_rom_preflight_before_export(self):
        self.assertIn("System.Windows.Forms.OpenFileDialog", self.ps)
        self.assertIn('Get-FileHash -LiteralPath $romFile.FullName -Algorithm SHA256', self.ps)
        self.assertIn('859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478', self.ps)
        self.assertIn('$ExpectedRomBytes = 2097152', self.ps)
        self.assertLess(self.ps.index('$realSha = '),
                        self.ps.index('Invoke-CheckedPython $runtime @('))
        self.assertLess(self.ps.index('if ($realSha -ne $ExpectedRomSha256)'),
                        self.ps.index('Invoke-CheckedPython $runtime @('))
        self.assertIn('"--rom", $romFile.FullName', self.ps)
        self.assertIn('CANONICAL_ROM_SHA256', self.exporter)

    def test_owner_explicit_one_click_requires_adjacent_repository_tooling(self):
        self.assertIn('prepare-original-racer-corpus.ps1', self.cmd)
        self.assertIn('powershell.exe -nologo -noprofile -executionpolicy bypass', self.cmd)
        self.assertIn('set "exitcode=%errorlevel%"', self.cmd)
        self.assertIn('pause', self.cmd)
        self.assertIn('Join-Path $PSScriptRoot "..\\.."', self.ps)
        self.assertIn('This launcher must remain inside a current UR-Recomp repository checkout.', self.ps)
        self.assertIn('Python 3.10+ is required', self.ps)

    def test_original_source_stays_private_and_cannot_replace_foreign_folder(self):
        self.assertIn('"UR-Recomp\\private-original-racer-corpora"', self.ps)
        self.assertIn('privateParent.StartsWith($repoPrefix', self.ps)
        self.assertIn('Join-Path $runRoot "source-corpus"', self.ps)
        self.assertIn('Join-Path $runRoot "research"', self.ps)
        self.assertIn('Test-Path -LiteralPath $runRoot', self.ps)
        self.assertIn('Test-Path -LiteralPath $receipt -PathType Leaf', self.ps)
        self.assertIn('[System.IO.FileMode]::CreateNew', self.ps)
        self.assertIn('source-corpus.json', self.ps)
        self.assertIn('publish_private_corpus_stage(stage, out)', self.exporter)
        self.assertIn('out.resolve().is_relative_to(ROOT.resolve())', self.exporter)

    def test_role_assignment_is_conservative_and_no_holdout_is_fabricated(self):
        self.assertIn('$FreezeScript $receipt "--template"', self.ps)
        self.assertIn('roles-draft-all-diagnostic.json', self.ps)
        self.assertIn('source-family-diagnostic-groups.json', self.ps)
        self.assertIn('"diagnostic" for name', self.freezer)
        self.assertIn('"withheld_candidate_is_an_independent_3d_camera": False', self.freezer)
        self.assertIn('No fit/heldout family or original 1994 camera was declared verified.', self.ps)

    def test_no_network_upload_rom_download_or_background_registration(self):
        forbidden = (
            "Invoke-WebRequest", "Invoke-RestMethod", "Start-BitsTransfer",
            "curl ", "wget ", "gh auth", "gh api", "git push",
            "git clone", "New-ScheduledTask", "schtasks", "Register-ScheduledTask",
            "UploadFile", "github.com", "net.WebClient", "Copy-Item -Destination",
        )
        for token in forbidden:
            with self.subTest(token=token):
                self.assertNotIn(token.lower(), self.ps.lower())
        self.assertNotIn('start /b', self.cmd)

    def test_cli_arguments_match_the_existing_real_exporter_and_splitter(self):
        for arg in ('"--rom"', '"--registry"', '"--out"'):
            self.assertIn(arg, self.ps)
        for arg in ('parser.add_argument("--rom"', 'parser.add_argument("--registry"',
                    'parser.add_argument("--out"'):
            self.assertIn(arg, self.exporter)
        self.assertIn('ap.add_argument("--template"', self.freezer)
        self.assertIn('ap.add_argument("roles"', self.freezer)


if __name__ == "__main__":
    unittest.main()
