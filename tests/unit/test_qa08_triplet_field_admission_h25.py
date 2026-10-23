"""ROM-free strict QA08 field admission against authentic log grammar.

Source basis: held Agent5 review evidence of merged PR #2313, where four
malformed triplet classes were erroneously accepted. No PPU/release claims.
"""
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from zipfile import ZipFile
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
import qa08_probe_robustness as qa08


def rows():
    result = []
    for x in range(88):
        identity = f'frame=5176 x={x} logical_y=41 ppu_line=42'
        result.extend((
            f'UR_QA08_LATE_PPU_SOURCE {identity} sub=0 selected_rgb555=4a52',
            f'UR_QA08_LATE_PPU_SOURCE {identity} sub=1 selected_rgb555=39ce',
            f'UR_QA08_LATE_PPU_FINAL {identity} RGB8=138,138,138',
        ))
    return result


def check(entries):
    data = BytesIO()
    with ZipFile(data, 'w') as z:
        z.writestr('on-source.log', ('\n'.join(entries) + '\n').encode('ascii'))
    raw = data.getvalue()
    with TemporaryDirectory() as d:
        path = Path(d) / 'source.zip'
        path.write_bytes(raw)
        with patch.object(qa08, 'AUTHENTIC_SHA256', sha256(raw).hexdigest()):
            return qa08.genuine_scale_compatibility(path)


class QA08FieldAdmission(unittest.TestCase):
    def test_positive_source_stage_triplets(self):
        self.assertEqual(check(rows())['source_triplets'], 88)

    def test_missing_second_substage_colour_refused(self):
        source = rows()
        source[1] = source[1].replace(' selected_rgb555=39ce', '')
        with self.assertRaisesRegex(ValueError, 'missing QA08 source/final'):
            check(source)

    def test_malformed_second_substage_colour_refused(self):
        source = rows()
        source[1] = source[1].replace('selected_rgb555=39ce', 'selected_rgb555=ffff')
        with self.assertRaisesRegex(ValueError, 'malformed QA08 source RGB555'):
            check(source)

    def test_missing_beam_field_from_all_triplets_refused(self):
        source = [row.replace(' ppu_line=42', '') for row in rows()]
        with self.assertRaisesRegex(ValueError, 'missing QA08 source/final'):
            check(source)

    def test_nonnumeric_frame_all_triplets_refused(self):
        source = [row.replace('frame=5176', 'frame=bogus') for row in rows()]
        with self.assertRaisesRegex(ValueError, 'invalid QA08 source stage coordinate'):
            check(source)

    def test_negative_or_overlarge_coordinate_refused(self):
        for value in ('-1', '512', '1.5', '0001'):
            with self.subTest(value=value):
                source = [row.replace('ppu_line=42', f'ppu_line={value}') for row in rows()]
                with self.assertRaisesRegex(ValueError, 'invalid QA08 source stage coordinate'):
                    check(source)

    def test_valid_second_substage_colour_is_not_assumed_equal_to_first(self):
        # Distinct substage words are genuine in the original source log.
        self.assertEqual(check(rows())['compatible_scalings'],
                         {'14/15': True, '187/200': True})


if __name__ == '__main__':
    unittest.main()
