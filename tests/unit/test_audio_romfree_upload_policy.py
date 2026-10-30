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
    """Read every upload-artifact path from its own YAML step, failing closed.

    This deliberately small stdlib scanner accepts only literal-block with.path
    in normal workflow steps. Unsupported YAML shapes are a test failure rather
    than an excuse to search forward into a different step's harmless paths.
    """
    lines = source.splitlines()
    # An unrecognised `uses` scalar can hide an uploader from a line scanner.
    # These four guarded workflows currently use only literal action refs.
    # Reject YAML aliases, anchors, folded scalars and flow-style steps rather
    # than silently treating a real upload-artifact step as another action.
    uses_line = re.compile(r"^\s*(?:-\s+)?uses:\s*(.*?)\s*$")
    literal_ref = re.compile(
        r"^(?:[A-Za-z0-9_./:@-]+|'[A-Za-z0-9_./:@-]+'|"
        r'"[A-Za-z0-9_./:@-]+")\s*(?:#.*)?$'
    )
    yaml_anchor = re.compile(
        r"^\s*(?:-\s*)?(?:[A-Za-z_][\w-]*:\s*)?[&*][A-Za-z_][\w-]*"
    )
    for row in lines:
        if not row.strip() or row.lstrip().startswith("#"):
            continue
        if yaml_anchor.match(row) or re.match(r"^\s*-\s*\{", row):
            raise ValueError("unsupported YAML anchor, alias or flow-style step")
        declaration = uses_line.match(row)
        if declaration is not None and not literal_ref.fullmatch(declaration.group(1)):
            raise ValueError("unsupported multiline or aliased uses scalar")
    collected: list[str] = []
    uploaders = 0
    # Any literal uploader mention missed by the recognised step parser is
    # a potential false-green (quoted/spaced YAML keys, complex mapping keys).
    raw_uploader_refs = sum(
        row.lower().count("actions/upload-artifact@")
        for row in lines if not row.lstrip().startswith("#")
    )
    step_start = re.compile(r"^(\s*)-\s+(?:name|uses|id|if|run|env|with):")
    uses_action = re.compile(
        r"^(\s*)(?:-\s+)?uses:\s*['\"]?(actions/upload-artifact@[^\s'\"#]+)",
        re.IGNORECASE,
    )
    for index, line in enumerate(lines):
        action = uses_action.match(line)
        if action is None:
            continue
        uploaders += 1
        uses_indent = len(action.group(1))
        if re.match(r"^\s*-\s+uses:", line):
            step_indent = uses_indent
        else:
            preceding = [
                len(match.group(1))
                for prior in lines[:index]
                if (match := step_start.match(prior))
                and len(match.group(1)) < uses_indent
            ]
            if not preceding:
                raise ValueError("upload-artifact action has no enclosing step")
            step_indent = preceding[-1]

        end = len(lines)
        for cursor in range(index + 1, len(lines)):
            row = lines[cursor]
            if not row.strip() or row.lstrip().startswith("#"):
                continue
            indent = len(row) - len(row.lstrip())
            if indent <= step_indent:
                end = cursor
                break

        with_rows = [
            (cursor, len(row) - len(row.lstrip()))
            for cursor in range(index + 1, end)
            if (row := lines[cursor]).strip() == "with:"
            and len(row) - len(row.lstrip()) == step_indent + 2
        ]
        if len(with_rows) != 1:
            raise ValueError("upload-artifact requires exactly one step-local with block")
        with_start, with_indent = with_rows[0]
        paths = []
        for cursor in range(with_start + 1, end):
            row = lines[cursor]
            if not row.strip() or row.lstrip().startswith("#"):
                continue
            indent = len(row) - len(row.lstrip())
            if indent <= with_indent:
                break
            match = re.match(r"^\s*path:\s*(.*?)\s*$", row)
            if match and indent == with_indent + 2:
                paths.append((cursor, indent, match.group(1)))
        if len(paths) != 1:
            raise ValueError("upload-artifact requires exactly one step-local path")
        path_start, path_indent, value = paths[0]
        if value not in {"|", "|-", "|+"}:
            raise ValueError("upload-artifact path must be a literal YAML block")
        entries = []
        for row in lines[path_start + 1:end]:
            if not row.strip():
                continue
            indent = len(row) - len(row.lstrip())
            if indent <= path_indent:
                break
            entries.append(row.strip())
        if not entries:
            raise ValueError("upload-artifact path block is empty")
        collected.extend(entries)
    if uploaders != raw_uploader_refs:
        raise ValueError("unrecognized upload-artifact action reference")
    if uploaders == 0:
        raise ValueError("audio workflow has no upload-artifact step")
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

    def test_upload_paths_never_borrow_later_step_path(self):
        workflow = """jobs:
  audio:
    steps:
      - name: dangerous uploader
        uses: actions/upload-artifact@v4
        with:
          path: ${{ runner.temp }}/audio-source/UR-Recomp-Windows-x64.zip
      - name: unrelated
        with:
          path: |
            ${{ runner.temp }}/safe-report.json
"""
        with self.assertRaisesRegex(ValueError, "literal YAML block"):
            artifact_paths(workflow)

    def test_version_pinned_uploader_is_not_invisible(self):
        workflow = """jobs:
  audio:
    steps:
      - name: dangerous version-pinned upload
        uses: actions/upload-artifact@v4.4.3
        with:
          path: |
            ${{ runner.temp }}/audio-source/UR-Recomp-Windows-x64.zip
      - name: safe uploader
        uses: actions/upload-artifact@v4
        with:
          path: |
            ${{ runner.temp }}/safe-report.json
"""
        self.assertEqual(artifact_paths(workflow), [
            "${{ runner.temp }}/audio-source/UR-Recomp-Windows-x64.zip",
            "${{ runner.temp }}/safe-report.json",
        ])

    def test_missing_step_local_path_is_rejected(self):
        workflow = """jobs:
  audio:
    steps:
      - uses: actions/upload-artifact@v4
        with:
          name: missing-path
      - name: next-step
        with:
          path: |
            ${{ runner.temp }}/safe-report.json
"""
        with self.assertRaisesRegex(ValueError, "step-local path"):
            artifact_paths(workflow)

    def test_duplicate_and_empty_paths_are_rejected(self):
        duplicate = """jobs:
  audio:
    steps:
      - uses: actions/upload-artifact@v4
        with:
          path: |
            ${{ runner.temp }}/safe-report.json
          path: |
            ${{ runner.temp }}/other-report.json
"""
        empty = """jobs:
  audio:
    steps:
      - uses: actions/upload-artifact@v4
        with:
          path: |
"""
        with self.assertRaisesRegex(ValueError, "exactly one step-local path"):
            artifact_paths(duplicate)
        with self.assertRaisesRegex(ValueError, "path block is empty"):
            artifact_paths(empty)

    def test_folded_and_literal_multiline_uses_cannot_hide_zip(self):
        for indicator in (">-", "|", "|-", ">+"):
            with self.subTest(indicator=indicator):
                workflow = """jobs:
  audio:
    steps:
      - name: unsafe folded uploader
        uses: INDICATOR
          actions/upload-artifact@v4
        with:
          path: |
            ${{ runner.temp }}/audio-source/UR-Recomp-Windows-x64.zip
      - uses: actions/upload-artifact@v4
        with:
          path: |
            ${{ runner.temp }}/safe-report.json
""".replace("INDICATOR", indicator)
                with self.assertRaisesRegex(ValueError, "unsupported multiline"):
                    artifact_paths(workflow)

    def test_aliased_uploaders_and_step_aliases_fail_closed(self):
        variants = (
            "uses: &uploader actions/upload-artifact@v4",
            "uses: *uploader",
            "uses: !!str actions/upload-artifact@v4",
        )
        for declaration in variants:
            with self.subTest(declaration=declaration):
                workflow = """jobs:
  audio:
    steps:
      - name: unsafe uploader
        DECLARATION
        with:
          path: |
            ${{ runner.temp }}/audio-source/UR-Recomp-Windows-x64.zip
      - uses: actions/upload-artifact@v4
        with:
          path: |
            ${{ runner.temp }}/safe-report.json
""".replace("DECLARATION", declaration)
                with self.assertRaises(ValueError):
                    artifact_paths(workflow)
        for step in ("- *uploader", "- &uploader uses: actions/upload-artifact@v4",
                     "- {uses: actions/upload-artifact@v4}"):
            with self.subTest(step=step):
                workflow = """jobs:
  audio:
    steps:
      STEP
      - uses: actions/upload-artifact@v4
        with:
          path: |
            ${{ runner.temp }}/safe-report.json
""".replace("STEP", step)
                with self.assertRaisesRegex(ValueError, "unsupported YAML"):
                    artifact_paths(workflow)

    def test_spaced_quoted_and_escaped_uses_keys_cannot_hide_zip(self):
        variants = (
            "uses : actions/upload-artifact@v4",
            "'uses': actions/upload-artifact@v4",
            '"uses": actions/upload-artifact@v4',
            r'"\u0075ses": actions/upload-artifact@v4',
            "? uses\n        : actions/upload-artifact@v4",
        )
        for declaration in variants:
            with self.subTest(declaration=declaration):
                workflow = """jobs:
  audio:
    steps:
      - name: unsafe uploader
        DECLARATION
        with:
          path: |
            ${{ runner.temp }}/audio-source/UR-Recomp-Windows-x64.zip
      - uses: actions/upload-artifact@v4
        with:
          path: |
            ${{ runner.temp }}/safe-report.json
""".replace("DECLARATION", declaration)
                with self.assertRaisesRegex(ValueError, "unrecognized upload-artifact"):
                    artifact_paths(workflow)

    def test_case_variant_upload_artifact_is_inspected(self):
        workflow = """jobs:
  audio:
    steps:
      - uses: Actions/Upload-Artifact@v4
        with:
          path: |
            ${{ runner.temp }}/audio-source/UR-Recomp-Windows-x64.zip
"""
        self.assertEqual(artifact_paths(workflow), [
            "${{ runner.temp }}/audio-source/UR-Recomp-Windows-x64.zip"
        ])

    def test_quoted_literal_action_refs_remain_supported(self):
        for action in ("'actions/upload-artifact@v4'", '"actions/upload-artifact@v4"'):
            workflow = """jobs:
  audio:
    steps:
      - uses: ACTION
        with:
          path: |
            ${{ runner.temp }}/safe-report.json
""".replace("ACTION", action)
            self.assertEqual(artifact_paths(workflow), [
                "${{ runner.temp }}/safe-report.json"
            ])

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
