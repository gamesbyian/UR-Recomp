"""Source-validated real Windows PPU $2121/$2122 writer witness gates."""
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import qa08_adjudicate_native_cgram_port_writer as port

def sample(frame:int,word:int)->list[tuple[int,int,int,int,int,str]]:
    return [(226,100+i*3,p,v,frame,"cpu") for i,(p,v) in enumerate(
        ((0x2121,0x6c),(0x2122,word&255),(0x2122,word>>8),
         (0x2121,0x6d),(0x2122,0x31),(0x2122,0x46),
         (0x2121,0x6e),(0x2122,0x52),(0x2122,0x4a),
         (0x2121,0x6f),(0x2122,0xb5),(0x2122,0x56)))]

class RealNativeCgramPortWriterTest(unittest.TestCase):
    def test_source_provenance_and_four_raw_palette_transactions(self):
        self.assertEqual(len(port.SOURCE_PAIRS),4)
        self.assertEqual(port.SOURCE_PAIRS[0][:2],(5169,5171))
        self.assertEqual(port.SOURCE_PAIRS[1][:2],(5176,5178))
        self.assertEqual(port.SOURCE_PAIRS[2][2],"cyclic_prior")
        self.assertEqual(set(port.SLOTS),{0x6c,0x6d,0x6e,0x6f})
        self.assertEqual(port.decode_group(sample(5169,0x4210)),
                         {0x6c:0x4210,0x6d:0x4631,0x6e:0x4a52,0x6f:0x56b5})
        with self.assertRaises(ValueError):
            port.decode_group(sample(5169,0x4210)[:-1])
        with self.assertRaises(ValueError):
            port.decode_group(sample(5169,0x4210)[:3]*4)
    def test_source_archives_fail_closed_and_release_not_inferred(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as root:
            p=Path(root)/"fake.zip"
            p.write_bytes(b"not a real source")
            with self.assertRaises(ValueError):
                port.checked_zip(p,port.ORIGINAL_ZIP)
        source=(ROOT/"tools/qa08_adjudicate_native_cgram_port_writer.py").read_text()
        self.assertIn("Windows_263_real_256x224_P7_frames_byte_identical",source)
        self.assertIn("complete_original_native_CPU_instruction_phase_proven",source)
        self.assertIn("QA08_10_and_release_gate_admitted",source)
        self.assertNotIn("forcepoke(",source)

if __name__=="__main__":
    unittest.main()
