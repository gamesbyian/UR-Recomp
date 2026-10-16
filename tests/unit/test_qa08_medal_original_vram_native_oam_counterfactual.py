"""Adversarial 4bpp sprite and palette decoding with source-only provenance."""
import sys
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import qa08_medal_original_vram_native_oam_counterfactual as x

class MedalsCounterfactualTest(unittest.TestCase):
    def test_planar_4bit_and_name_row_column_offset(self):
        raw=bytearray(65536)
        base=0xc000
        name=0x1a2
        at=(base+name*32)&65535
        raw[at]=0b10000000
        raw[at+1]=0b01000000
        raw[at+16]=0b00100000
        raw[at+17]=0b00010000
        self.assertEqual([x.indexed(raw,name,base,0,i,0) for i in range(4)],[1,2,4,8])
        self.assertEqual(x.indexed(raw,name,base,0,15,0,hf=True),1)
        self.assertEqual(x.indexed(raw,name,base,0,0,15,vf=True),1)
    def test_bad_index_sprite_cgram_or_source_bytes_rejected(self):
        raw=bytes(65536)
        for n in (-1,512):
            with self.assertRaises(ValueError):
                x.indexed(raw,n,0,0,0,0)
        with self.assertRaises(ValueError):
            x.indexed(raw,0,0,0,-1,0)
        with self.assertRaises(ValueError):
            x.indexed(b"bad",0,0,0,0,0)
        with self.assertRaises(ValueError):
            x.cgram_word(bytes(512),8,0)
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as folder:
            p=Path(folder)/"false.zip";p.write_bytes(b"fake")
            with self.assertRaisesRegex(ValueError,"source ZIP"):
                x.verify(p,p,p)
    def test_original_observed_frames_are_true_two_pad_registered_callbacks(self):
        self.assertEqual(x.PAIRS,((4031,4032),(4175,4176)))
        self.assertEqual([q[2] for q in x.POINTS],[112,113,114,99,98])
if __name__=="__main__":
    unittest.main()
