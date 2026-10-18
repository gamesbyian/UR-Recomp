"""Negative and receipt tests for the real late-result RF017 palette source join."""
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.qa08_verify_rf017_late_cgram_source_join import (
    PAIRS,COLORS,rgb15_group,original_groups,verify,ORIGINAL_SHA,CURRENT_SHA)
ROOT=Path(__file__).resolve().parents[2]

def sample():
    vals=(0x4210,0x4631,0x4a52,0x56b5)
    rows=[]
    for i,word in enumerate(vals):
        rows.extend([(225,100+i*10,0x2121,0x6c+i,"cpu"),
                     (225,102+i*10,0x2122,word&255,"cpu"),
                     (225,104+i*10,0x2122,word>>8,"cpu")])
    return rows

class ActualSourceControls(unittest.TestCase):
    def test_indexed_palette_matches_snes9x_source_group_contract(self):
        self.assertEqual(set(rgb15_group(sample()).values()),COLORS)
        for wrong in (sample()[:-1],sample()[:3]*4,
                      [(v,h,p,x,"hdma") for v,h,p,x,_ in sample()]):
            with self.assertRaises(ValueError):
                rgb15_group(wrong)
    def test_strict_original_archive_and_missing_native(self):
        with TemporaryDirectory() as tmp:
            p=Path(tmp)/"fake.zip";p.write_bytes(b"not authentic")
            with self.assertRaisesRegex(ValueError,"artifact changed"):
                verify(p,p)
        with self.assertRaisesRegex(ValueError,"source ring SHA"):
            original_groups(b"fake")
    def test_no_accidental_release_or_clock_promotion(self):
        self.assertEqual([x[0] for x in PAIRS],[5155,5162,5169,5176,5183,5190])
        self.assertEqual([x[2] for x in PAIRS[:4]],["direct"]*4)
        x=(ROOT/"analysis/data/qa08-current-rf017-late-cgram-original-writer-join-20261018.json")
        receipt=json.loads(x.read_text())
        self.assertEqual(receipt["source_original_archive_sha256"],ORIGINAL_SHA)
        self.assertEqual(receipt["source_native_archive_sha256"],CURRENT_SHA)
        self.assertEqual(receipt["exact_CGRAM_four_RGB15_word_source_matches"],6)
        self.assertFalse(receipt["source_timestamp_or_NMI_instruction_clock_root_cause_proven"])
        self.assertFalse(receipt["QA08_QA10_4K_art_or_release_accepted"])
if __name__=="__main__":unittest.main()
