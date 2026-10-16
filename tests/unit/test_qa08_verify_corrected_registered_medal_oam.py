"""Fail-closed original Snes9x postrun-frame vs real video callback registration."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
import zipfile
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location(
    "qa08_source_corrected",ROOT/"tools/qa08_verify_corrected_registered_medal_oam.py")
p=importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)

class RegisteredMedalSourceTest(unittest.TestCase):
    def test_preincrement_callback_and_postrun_host_are_different_labels(self):
        self.assertEqual(p.CALLBACKS,{1280:1279,4032:4031,4176:4175})
        self.assertEqual(p.TAGS[4032],"qa08_medal_4032")
        self.assertEqual(p.EXPECTED_ORIGINAL[4032],("cc","cc","e6","e6","a2","a4","a6"))
        for guest in (4032,4176):
            for i,slot in enumerate(p.SLOTS):
                a=int(p.EXPECTED_ORIGINAL[guest][i],16)
                b=int(p.EXPECTED_NATIVE[guest][i],16)
                self.assertEqual(b-a,-2 if slot>=112 else 2 if slot<=97 else 0)
        self.assertNotIn(4031,p.CALLBACKS)

    def test_genuine_544_byte_VBlank_DMA_stream_and_active_line_refused(self):
        frame=4032
        oam=bytes(range(256))*2+bytes(32)
        lines=["#frame\tvcounter\thcounter\taddr\tvalue\tsource"]
        for i,v in enumerate(oam):
            lines.append(f"{frame}\t{226+i//200}\t{i%200}\t2104\t{v:02x}\tdma")
        log=("\n".join(lines)+"\n").encode()
        result=p.real_original_DMA(frame,log,oam)
        self.assertEqual(result["DMA_OAM_bytes"],544)
        self.assertTrue(result["original_544byte_DMA_equals_actual_OAM"])
        bad=log.replace(b"\t2104\t00\tdma",b"\t2104\t00\thdma",1)
        with self.assertRaises(ValueError):p.real_original_DMA(frame,bad,oam)
        with self.assertRaises(ValueError):p.real_original_DMA(frame,log,oam[:-1])
        with self.assertRaises(ValueError):p.real_original_DMA(frame,log.replace(b"\t226\t",b"\t100\t",1),oam)

    def test_original_signed_OAM_and_foreign_zip_sha_are_rejected(self):
        raw=bytearray(544)
        raw[4*112:4*112+4]=bytes((200,91,0xa2,0x1b))
        row=p.source_slot(raw,112)
        self.assertEqual((row["x"],row["y"],row["tile"],row["palette"],row["priority"]),
                         (200,91,162,5,1))
        with self.assertRaises(ValueError):p.source_slot(raw[:543],112)
        with tempfile.TemporaryDirectory() as tmp:
            fake=Path(tmp)/"bad.zip"
            with zipfile.ZipFile(fake,"w") as z:z.writestr("data","forged")
            with self.assertRaisesRegex(ValueError,"complete ZIP"):
                p.verify(fake,fake,fake)

    def test_never_implicitly_grants_gameplay_graphics_or_release(self):
        self.assertEqual(len(p.SHA),3)
        self.assertEqual(len(p.SLOTS),7)
        self.assertEqual(len(p.CALLBACKS),3)
        for slot in p.SLOTS:self.assertIn(slot,range(128))

if __name__=="__main__":
    unittest.main()
