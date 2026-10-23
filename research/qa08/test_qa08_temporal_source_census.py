"""ROM-free negative controls for the authenticated QA08 temporal census."""
import hashlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile, ZIP_DEFLATED

from qa08_temporal_source_census import census


class TemporalSourceCensusTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'source.zip'
        self.anchors = [(i, 12) for i in range(8)]
        self.classes = ['4210', '4210', '4631', '4631',
                        '4a52', '4a52', '56b5', '56b5']

    def rows(self):
        lines = ['OTHER_SOURCE_EVENT ignored=1']
        for frame in range(5176, 5187):
            phase = 0 if frame == 5176 else (1 if frame < 5184 else 2)
            for i, (x, y) in enumerate(self.anchors):
                # Swap all eight selected values at each phase boundary,
                # without changing the per-frame four-class histogram.
                word = self.classes[(i + 2 * phase) % 8]
                lines.append(f'UR_QA08_LATE_PPU_SOURCE frame={frame} '
                             f'x={x} logical_y={y} sub=0 selected_rgb555={word}')
        return lines

    def evaluate(self, lines):
        with ZipFile(self.path, 'w', ZIP_DEFLATED) as z:
            z.writestr('on-source.log', '\n'.join(lines) + '\n')
        digest = hashlib.sha256(self.path.read_bytes()).hexdigest()
        with patch('qa08_temporal_source_census.AUTH_SHA', digest):
            return census(self.path)

    def test_complete_three_phase_census(self):
        report = self.evaluate(self.rows())
        self.assertEqual(report['phase_starts'], [5176, 5177, 5184])
        self.assertEqual([t['changed_anchors'] for t in report['transitions']],
                         [8, 0, 0, 0, 0, 0, 0, 8, 0, 0])
        self.assertEqual(len(report['anchors_xy']), 8)
        self.assertIs(report['original_native_ppu_pixel_parity'], False)
        self.assertEqual(report['release_gate_credit'], 0)

    def test_archive_epoch_mismatch_rejected(self):
        self.evaluate(self.rows())
        with self.assertRaisesRegex(ValueError, 'untrusted archive epoch'):
            census(self.path)

    def test_missing_anchor_rejected(self):
        lines = self.rows()
        self.evaluate(lines)
        with self.assertRaisesRegex(ValueError, 'incomplete source anchor census'):
            self.evaluate(lines[:-1])

    def test_duplicate_observation_rejected(self):
        lines = self.rows()
        with self.assertRaisesRegex(ValueError, 'duplicate main-source observation'):
            self.evaluate(lines + [lines[-1]])

    def test_wrong_phase_boundary_rejected(self):
        lines = self.rows()
        # Delay the 5184 transition by copying the preceding phase's class
        # for each anchor, without changing the histogram.
        for i, row in enumerate(lines):
            if 'frame=5184 ' in row:
                x = int(row.split('x=')[1].split()[0])
                current = self.classes[(x + 4) % 8]
                prior = self.classes[(x + 2) % 8]
                lines[i] = row.replace('selected_rgb555=' + current,
                                       'selected_rgb555=' + prior)
        with self.assertRaisesRegex(ValueError, 'unexpected authenticated temporal phase'):
            self.evaluate(lines)

    def test_palette_histogram_mutation_rejected(self):
        lines = self.rows()
        lines[1] = lines[1].replace('selected_rgb555=4210', 'selected_rgb555=7fff')
        with self.assertRaisesRegex(ValueError, 'per-frame palette-class census'):
            self.evaluate(lines)


if __name__ == '__main__':
    unittest.main()
