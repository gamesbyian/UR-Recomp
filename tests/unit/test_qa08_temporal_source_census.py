"""ROM-free synthetic census controls for archived QA08 temporal phases."""
import hashlib
import io
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa08_temporal_source_census as qa

COLORS=("4210","4631","4a52","56b5")

def synthetic_log(*, omit=None, perturb=None):
    lines=[]
    for frame in range(5176,5187):
        phase=0 if frame==5176 else 1 if frame<=5183 else 2
        for anchor in range(8):
            if (frame,anchor)==omit:
                continue
            color=COLORS[(anchor+phase)%4]
            if (frame,anchor)==perturb:
                color=COLORS[(anchor+phase+1)%4]
            lines.append(f"UR_QA08_LATE_PPU_SOURCE frame={frame} x={anchor+10} "
                         f"logical_y={anchor+20} sub=0 selected_rgb555={color}")
    return ("\n".join(lines)+"\n").encode("ascii")

def archive(rows):
    buff=io.BytesIO()
    with zipfile.ZipFile(buff,"w",zipfile.ZIP_DEFLATED) as z:
        z.writestr("on-source.log",rows)
    return buff.getvalue()

class TemporalCensusTest(unittest.TestCase):
    def run_archive(self,raw):
        with tempfile.TemporaryDirectory() as d:
            file=Path(d)/"qa08.zip"
            file.write_bytes(raw)
            with patch.object(qa,"AUTH_SHA",hashlib.sha256(raw).hexdigest()):
                return qa.census(file)

    def test_eleven_frames_eight_anchors_two_complete_phase_transitions(self):
        result=self.run_archive(archive(synthetic_log()))
        self.assertEqual(result["phase_starts"],[5176,5177,5184])
        self.assertEqual([t["changed_anchors"] for t in result["transitions"]],
                         [8,0,0,0,0,0,0,8,0,0])
        self.assertEqual(len(result["anchors_xy"]),8)
        self.assertFalse(result["original_native_ppu_pixel_parity"])
        self.assertEqual(result["release_gate_credit"],0)

    def test_archive_sha_is_not_optional(self):
        raw=archive(synthetic_log())
        with tempfile.TemporaryDirectory() as d:
            file=Path(d)/"qa08.zip"
            file.write_bytes(raw)
            with self.assertRaisesRegex(ValueError,"untrusted archive epoch"):
                qa.census(file)

    def test_missing_source_record_rejected(self):
        with self.assertRaisesRegex(ValueError,"incomplete"):
            self.run_archive(archive(synthetic_log(omit=(5179,2))))

    def test_unexpected_one_anchor_transition_rejected(self):
        with self.assertRaisesRegex(ValueError,"unexpected authenticated temporal phase"):
            self.run_archive(archive(synthetic_log(perturb=(5181,2))))

if __name__=="__main__":
    unittest.main()
