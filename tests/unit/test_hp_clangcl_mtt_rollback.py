"""Keep the owner HP ClangCL PCH build free of the failed MTT experiment."""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / '.github' / 'workflows' / 'windows-native-smoke.yml'


class HpClangClMttRollbackTests(unittest.TestCase):
    def test_hp_build_restores_single_bounded_cmake_invocation(self):
        source = WORKFLOW.read_text(encoding='utf-8')
        build = source.split('      - name: Configure and build (Visual Studio, ClangCL, SDL3)', 1)[1]
        build = build.split('      - name: ', 1)[0]
        self.assertEqual(build.count('cmake --build "$ROOT/build" --config Release --parallel "$HP_BUILD_JOBS"'), 1)
        for broken in ('UseMultiToolTask=true', 'EnforceProcessCountAcrossBuilds=true',
                       'CL_MPCount=10', 'MultiProcMaxCount=10',
                       'HP_COMPILE_SCHEDULER mode=MultiToolTask'):
            with self.subTest(property=broken):
                self.assertNotIn(broken, build)
        self.assertIn('HP_COMPILE_PROBE jobs=$HP_BUILD_JOBS phase=build_start', build)
        self.assertIn('HP_COMPILE_PROBE jobs=$HP_BUILD_JOBS phase=build_end', build)


if __name__ == '__main__':
    unittest.main()
