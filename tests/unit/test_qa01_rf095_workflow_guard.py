"""RF095 must not dispatch a replay that stops before the Bowl PCM window."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import textwrap
import unittest

WORKFLOW = Path(__file__).resolve().parents[2] / '.github/workflows/qa01-event-campaign.yml'


class RF095WorkflowPrerequisites(unittest.TestCase):
    def test_opt_in_requires_complete_zoo_to_bowl_replay(self):
        source = WORKFLOW.read_text(encoding='utf-8')
        anchor = '          if [[ "$QA01_RF095" == "true" &&'
        self.assertEqual(source.count(anchor), 1)
        start = source.index(anchor)
        end = source.index('          fi\n', start) + len('          fi\n')
        guard = 'set -euo pipefail\n' + textwrap.dedent(source[start:end])
        subprocess.run(['bash', '-n'], input=guard, text=True, check=True)

        complete = dict(QA01_RF095='true', QA01_RF094='true',
                        SELECTED='zoom-zoo', QA01_NEXT_BOWL='true',
                        QA01_FOLLOWTHROUGH='true')

        def check(values, expected):
            result = subprocess.run(['bash', '-c', guard],
                                    env={**os.environ, **values},
                                    capture_output=True, text=True, timeout=3)
            self.assertEqual(result.returncode, expected, result.stderr)

        check(complete, 0)
        check({**complete, 'QA01_RF095': 'false'}, 0)
        for name, value in (('QA01_RF094', 'false'),
                            ('SELECTED', 'bowl'),
                            ('QA01_NEXT_BOWL', 'false'),
                            ('QA01_FOLLOWTHROUGH', 'false')):
            with self.subTest(missing=name):
                check({**complete, name: value}, 1)

    def test_retains_raw_original_wav_for_independent_pcm_audit(self):
        source = WORKFLOW.read_text(encoding='utf-8')
        anchor = '      - name: Always retain per-case receipt and bounded diagnostic logs\n'
        self.assertEqual(source.count(anchor), 1)
        block = source.split(anchor, 1)[1].split('\n  aggregate:', 1)[0]
        self.assertIn('          path: |\n', block)
        paths = [line.strip() for line in
                 block.split('          path: |\n', 1)[1].splitlines()
                 if line.strip() and not line.lstrip().startswith('#')]
        root = '${{ runner.temp }}/qa01-case/work/${{ matrix.case }}/replay/'
        for required in (root + 'snesref_audio.wav',
                         root + 'rf095-original-map.csv',
                         root + 'rf095-native-map.csv',
                         root + 'rf095-native.pcm',
                         root + 'reference.log',
                         root + 'native.log',
                         '${{ runner.temp }}/qa01-case/qa01-rf095-pcm-receipt.json'):
            with self.subTest(evidence=required):
                self.assertEqual(paths.count(required), 1,
                                 'missing or duplicated immutable RF095 producer evidence')


    def test_source_scan_excludes_rf095_map_before_both_source_runs(self):
        producer = WORKFLOW.parents[2] / 'tools' / 'probe_original_event_complete.py'
        source = producer.read_text(encoding='utf-8')
        scan = source.split('def scan_source(', 1)[1].split(
            '\n\n# Reuse the pinned', 1)[0]
        guard = 'env.pop("SNESREF_PCM_FRAME_MAP", None)'
        self.assertEqual(scan.count(guard), 1)
        self.assertLess(scan.index(guard), scan.index('p = subprocess.run('))
        self.assertEqual(scan.count('env=env, cwd=scan'), 1)
        self.assertEqual(scan.count('env=anchor_env, cwd=scan'), 1)
        self.assertIn('anchor_env = dict(env, SNESREF_SCRIPT=str(anchor))', scan)


if __name__ == '__main__':
    unittest.main()
