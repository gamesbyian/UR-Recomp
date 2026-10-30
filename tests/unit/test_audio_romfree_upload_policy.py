"""Ensure exact-ROM rehydration never leaks locally reconstructed packages to CI artifacts."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / ".github" / "workflows"
AUDIO_WORKFLOWS = (
    "windows-modern-restart-audio-probe.yml",
    "windows-modern-resume-audio-probe.yml",
    "windows-exit-frontend-audio-probe.yml",
    "windows-native-audio-output.yml",
)


def artifact_paths(source: str) -> list[str]:
    """Extract upload-artifact paths only, not other unrelated workflow paths."""
    lines = source.splitlines()
    collected = []
    for index, line in enumerate(lines):
        if line.strip() != "uses: actions/upload-artifact@v4":
            continue
        block = lines[index + 1:]
        start = next(
            (i for i, row in enumerate(block) if row.strip() == "path: |"), None
        )
        if start is None:
            raise ValueError("audio evidence uploader lacks a bounded path block")
        for row in block[start + 1:]:
            if not row.startswith("            "):
                break
            if row.strip():
                collected.append(row.strip())
    return collected


class AudioRomfreeUploadPolicy(unittest.TestCase):
    def test_every_exact_zip_rehydrator_uploads_only_allowlisted_diagnostics(self):
        allowed = re.compile(
            r"^\$\{\{ runner\.temp \}\}/[A-Za-z0-9_.-]*\*?"
            r"[A-Za-z0-9_.-]*\.(?:log|json|txt)$"
        )
        for filename in AUDIO_WORKFLOWS:
            with self.subTest(filename=filename):
                text = (WORKFLOWS / filename).read_text(encoding="utf-8")
                self.assertIn(
                    "python -m tools.ci.rehydrate_windows_romfree_package", text
                )
                self.assertIn("--expected-source", text)
                self.assertIn("name: windows-native-smoke", text)
                sources = artifact_paths(text)
                self.assertGreater(len(sources), 0)
                for source in sources:
                    self.assertRegex(source, allowed)
                    self.assertNotIn("audio-source", source)
                    self.assertNotIn(".zip", source)
                    self.assertNotIn(".raw", source)
                    self.assertNotIn("**", source)

    def test_source_hash_contract_is_checked_before_audio_execution(self):
        source = (
            ROOT / "tools" / "ci" / "rehydrate_windows_romfree_package.py"
        ).read_text(encoding="utf-8")
        for required in (
            "original_portable_zip_sha256",
            "original_manifest_sha256",
            "executable_sha256",
            "source_commit",
            "unknown",
            "package.verify_archive(staging_archive)",
            "reconstructed ZIP differs from exact original producer",
        ):
            if required == "unknown":
                self.assertIn("unsupported producer assets", source)
            else:
                self.assertIn(required, source)


if __name__ == "__main__":
    unittest.main()
