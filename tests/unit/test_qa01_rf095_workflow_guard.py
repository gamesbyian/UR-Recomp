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


if __name__ == '__main__':
    unittest.main()
