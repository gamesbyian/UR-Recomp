"""H27 original-derived source/final duplicate evidence regression.

Only synthetic frame source records, not original/native capture or release QA.
"""
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
import qa08_probe_robustness as audit


class SourceFinalUniqueness(unittest.TestCase):
    def fixture(self, path, repeat=None):
        lines=[]
        for frame in range(5175,5186):
            for x in range(8):
                key=f'frame={frame} x={x} logical_y=3 ppu_line=4'
                lines.append(f'UR_QA08_LATE_PPU_SOURCE {key} sub=0 selected_rgb555=4210')
                lines.append(f'UR_QA08_LATE_PPU_SOURCE {key} sub=1 selected_rgb555=39ce')
                lines.append(f'UR_QA08_LATE_PPU_FINAL {key} RGB8=123,123,123')
        # Preserve the historical duplicate-specific regression while keeping
        # all 88 genuine three-stage groups present. Only one stage is
        # deliberately replaced by an earlier stage identity.
        if repeat == 'source':
            lines[3] = lines[0]
        if repeat == 'final':
            lines[5] = lines[2]
        with ZipFile(path,'w') as z:z.writestr('on-source.log','\n'.join(lines)+'\n')
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def test_88_triplets_admit_both_brightness_models(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'source.zip';digest=self.fixture(path)
            with patch.object(audit,'AUTHENTIC_SHA256',digest):
                result=audit.genuine_scale_compatibility(path)
            self.assertEqual(result['source_triplets'],88)
            self.assertEqual(result['compatible_scalings'],{'14/15':True,'187/200':True})
            self.assertFalse(result['chromatic_source_observed'])

    def test_repeated_source_stage_is_not_silent_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'source.zip';digest=self.fixture(path,'source')
            with patch.object(audit,'AUTHENTIC_SHA256',digest):
                with self.assertRaisesRegex(ValueError,'duplicate QA08 source stage'):
                    audit.genuine_scale_compatibility(path)

    def test_repeated_final_stage_is_not_silent_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'source.zip';digest=self.fixture(path,'final')
            with patch.object(audit,'AUTHENTIC_SHA256',digest):
                with self.assertRaisesRegex(ValueError,'duplicate QA08 final stage'):
                    audit.genuine_scale_compatibility(path)

    def test_even_well_formed_foreign_zip_requires_exact_source_sha(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'source.zip';self.fixture(path)
            with self.assertRaisesRegex(ValueError,'unauthenticated source archive'):
                audit.genuine_scale_compatibility(path)

if __name__=='__main__':unittest.main()
