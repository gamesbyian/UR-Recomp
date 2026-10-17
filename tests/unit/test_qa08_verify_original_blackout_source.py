"""Bounded original $2100 video/beam source record must fail closed."""
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import qa08_verify_original_blackout_source as source

class OriginalBlackoutSourceVerifierTest(unittest.TestCase):
    def test_real_original_blackout_frame_and_ring_bounds(self):
        self.assertEqual(source.FRAMES,(4015,4016,4017))
        self.assertEqual(source.BLACKOUT_CALLBACK,4015)
        self.assertEqual((source.START,source.END),(3998,4035))
        data=(
            "#original_frame_range=3998..4035\n"
            "frame\tvcounter\thcounter\taddr\tvalue\tsource\n"
            "4016\t225\t313\t2100\t80\tcpu\n"
            "#ring_earliest=3682\n#write_count=1\n#scan_complete=1\n"
        ).encode()
        result=source.parse_inidisp_journal(data)
        self.assertEqual(result["original_2100_port_write_records"],1)
        for corrupt in (
            data.replace(b"2100",b"2122"),
            data.replace(b"scan_complete=1",b"scan_complete=0"),
            data.replace(b"4016",b"9999"),
            data.replace(b"ring_earliest=3682",b"ring_earliest=4035"),
        ):
            with self.subTest(data=corrupt[-40:]):
                with self.assertRaises(ValueError):
                    source.parse_inidisp_journal(corrupt)
        self.assertNotIn("forcepoke",(
            ROOT/"tools/qa08_verify_original_blackout_source.py").read_text())

if __name__=="__main__":
    unittest.main()
