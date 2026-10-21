"""Guard the earned-1P Windows CI export against source-journey contamination.

The exporter deliberately treats the source journey as immutable. Keep the
workflow's output and artifact-upload path *outside* that source directory.
This is configuration verification, not a source-earned or physical QA oracle.
"""
from __future__ import annotations

from pathlib import Path, PurePosixPath
import re
import unittest


WORKFLOW = (Path(__file__).resolve().parents[2] / '.github' / 'workflows'
            / 'baldosa-windows-native-bridge.yml')


def validate_earned_run_export_paths(workflow: str) -> tuple[str, str]:
    """Return verified source/output paths, or refuse an unsafe CI contract."""
    command = 'python tools/export_baldosa_earned_1p_run.py'
    if workflow.count(command) != 1:
        raise ValueError('Expected exactly one earned-1P exporter invocation')
    section = workflow.split(command, 1)[1].split('\n\n', 1)[0]
    paths = {}
    for option in ('journey', 'out'):
        match = re.search(r'(?m)^\s*--' + option + r' "(\$RUNNER_TEMP/[^"\n]+)"(?:\s*\\)?\s*$', section)
        if not match:
            raise ValueError('Missing or noncanonical exporter ' + option)
        raw = match.group(1)
        relative = raw.removeprefix('$RUNNER_TEMP/')
        if not relative or any(part in ('', '.', '..') for part in relative.split('/')):
            raise ValueError('Nonportable exporter path')
        paths[option] = PurePosixPath(relative)
    source, output = paths['journey'], paths['out']
    if source == output or source in output.parents:
        raise ValueError('Earned run output is inside the immutable journey')

    artifact_name = 'name: baldosa-win32-native-earned-1p-run'
    if workflow.count(artifact_name) != 1:
        raise ValueError('Expected exactly one earned-1P artifact')
    block = workflow.split(artifact_name, 1)[1].split('\n\n', 1)[0]
    uploaded = re.search(r'(?m)^\s*path: \$\{\{ runner\.temp \}\}/([^\n]+?)\s*$', block)
    if not uploaded:
        raise ValueError('Missing earned-1P upload path')
    artifact_rel = uploaded.group(1).rstrip('/')
    if any(part in ('', '.', '..') for part in artifact_rel.split('/')):
        raise ValueError('Nonportable earned-1P upload path')
    if PurePosixPath(artifact_rel) != output:
        raise ValueError('Earned-1P artifact path differs from exporter output')
    return str(source), str(output)


class CIExportPathContractTests(unittest.TestCase):
    @staticmethod
    def fixture():
        return '''      - name: Export original source-earned 1P run for independent QA
        run: |
          python tools/export_baldosa_earned_1p_run.py \\
            --journey "$RUNNER_TEMP/UR Baldosa Win32 Pause Route/native_first_racer_earned_records" \\
            --out "$RUNNER_TEMP/UR Baldosa Win32 Pause Route/ci-owned-earned-1p-run"

      - name: Retain bounded evidence
        with:
          name: baldosa-win32-native-earned-1p-run
          path: \${{ runner.temp }}/UR Baldosa Win32 Pause Route/ci-owned-earned-1p-run/

'''

    def test_actual_workflow_export_and_upload_contract(self):
        source, output = validate_earned_run_export_paths(WORKFLOW.read_text(encoding='utf-8'))
        self.assertEqual(source, 'UR Baldosa Win32 Pause Route/native_first_racer_earned_records')
        self.assertEqual(output, 'UR Baldosa Win32 Pause Route/ci-owned-earned-1p-run')

    def test_refuses_output_nested_inside_immutable_source(self):
        original = self.fixture()
        bad = original.replace('UR Baldosa Win32 Pause Route/ci-owned-earned-1p-run',
                               'UR Baldosa Win32 Pause Route/native_first_racer_earned_records/ci-owned-earned-1p-run')
        with self.assertRaisesRegex(ValueError, 'inside the immutable journey'):
            validate_earned_run_export_paths(bad)

    def test_refuses_upload_destination_disagreeing_with_output(self):
        bad = self.fixture().replace('          path: \${{ runner.temp }}/UR Baldosa Win32 Pause Route/ci-owned-earned-1p-run/',
                                     '          path: \${{ runner.temp }}/UR Baldosa Win32 Pause Route/elsewhere/')
        with self.assertRaisesRegex(ValueError, 'differs from exporter output'):
            validate_earned_run_export_paths(bad)

    def test_refuses_noncanonical_paths_and_missing_exporter(self):
        cases = [
            self.fixture().replace('Route/ci-owned-earned-1p-run', 'Route/../ci-owned-earned-1p-run'),
            self.fixture().replace('python tools/export_baldosa_earned_1p_run.py', 'python missing.py'),
            self.fixture().replace('name: baldosa-win32-native-earned-1p-run', 'name: other-name'),
        ]
        for bad in cases:
            with self.subTest(bad=bad[:70]), self.assertRaises(ValueError):
                validate_earned_run_export_paths(bad)


if __name__ == '__main__':
    unittest.main()
