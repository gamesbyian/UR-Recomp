"""Fail closed when a source OAM match is forged, shifted, or abbreviated."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("qa08_full_oamdma",ROOT/"tools/qa08_original_native_full_oamdma_phase.py")
qa=importlib.util.module_from_spec(spec)
spec.loader.exec_module(qa)

class SourceFullOamPhaseTest(unittest.TestCase):
    def test_pinned_source_scope_and_negative_release(self):
        self.assertEqual(set(qa.ORIGINAL),{4032,4176})
        self.assertEqual(len(qa.FRAMES),12)
        self.assertEqual(qa.SLOTS,(96,97,98,99,112,113,114))
        self.assertEqual(len(qa.PINS["native"]),64)
        self.assertEqual(len(qa.PINS["original"]),64)

    def test_real_source_journal_544_bytes_and_visible_write_negative(self):
        field=4032
        raw=bytes(range(256))*2+bytes(32)
        head="#frame\tvcounter\thcounter\taddr\tvalue\tsource\n"
        rows=[f"{field}\t230\t{i%200}\t2104\t{v:02x}\tdma"
              for i,v in enumerate(raw)]
        self.assertEqual(qa.original_dma((head+"\n".join(rows)).encode(),field),raw)
        with self.assertRaises(ValueError):
            qa.original_dma((head+"\n".join(rows[:-1])).encode(),field)
        rows[0]=rows[0].replace("\t230\t","\t110\t")
        with self.assertRaises(ValueError):
            qa.original_dma((head+"\n".join(rows)).encode(),field)

    def test_untrusted_ZIP_and_wrong_source_cannot_be_admitted(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"invalid.zip"
            with zipfile.ZipFile(path,"w") as z:
                z.writestr("qa08-native-OAM-port-input.json","{}")
            with self.assertRaisesRegex(ValueError,"complete producer ZIP"):
                qa.analyze(path,path)

    def test_native_OAM_port_requires_all_12_frames(self):
        one="UR_QA08_WIN_OAM_PORT frame=4030 v=230 h=100 port=04 val=a2 src=1 adr=00 high=0 second=0 latch=00 oldlow=00 oldhigh=00"
        with self.assertRaises(ValueError):
            qa.native_payloads(one)
        with self.assertRaises(ValueError):
            qa.native_payloads(one.replace("src=1","src=3"))

    def test_report_will_not_claim_beam_or_CPU_fix(self):
        # The historical 2-field source lead does not authorize a
        # universal OAM tile transform or a new main/release candidate.
        self.assertEqual(qa.CRC,"c782121bdab59790cd11ba2cb02c567adf1ca4f0a6218c75da5a896b52f04876")
        self.assertNotIn("apply_candidate",qa.__doc__ or "")

if __name__=="__main__":
    unittest.main()
