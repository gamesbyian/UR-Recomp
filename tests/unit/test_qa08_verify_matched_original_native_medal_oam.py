"""Original/native source medal OAM evidence cannot be recoloured or rephased."""
from pathlib import Path
import importlib.util
import tempfile
import unittest
import zipfile
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location(
 "qa08_matched_medal",ROOT/"tools/qa08_verify_matched_original_native_medal_oam.py")
qa=importlib.util.module_from_spec(spec)
spec.loader.exec_module(qa)

class OriginalNativeMatchedMedalOAMTest(unittest.TestCase):
    def test_source_OAM_slot_decoder_signed_coordinates_and_high_bits(self):
        raw=bytearray(544)
        raw[4*112:4*112+4]=bytes((200,91,0xa2,0x1b))
        x=qa.source_slot(raw,112)
        self.assertEqual((x["x"],x["y"],x["tile"],x["attr"]),(200,91,162,27))
        self.assertEqual((x["OBJ_palette"],x["OBJ_priority"]), (5,1))
        self.assertEqual(x["highOAM"],0)
        raw[4*112]=250
        raw[512+112//4] |= 1<<((112%4)*2)
        self.assertEqual(qa.source_slot(raw,112)["x"],-6)
        with self.assertRaises(ValueError):
            qa.source_slot(raw[:-1],112)
        with self.assertRaises(ValueError):
            qa.source_slot(raw,12)

    def test_known_real_two_field_tile_deltas_preserve_object_attributes(self):
        medals={112:(0xa2,"1ba0"),113:(0xa4,"1da2"),114:(0xa6,"1fa4")}
        neighbors={96:(0xcc,"1bce"),97:(0xcc,"1bce"),
                   98:(0xe6,"1be6"),99:(0xe6,"1be6")}
        for slot,(tile,native) in (medals|neighbors).items():
            original={"slot":slot,"tile":tile,"attr":int(native[:2],16),
                      "highOAM":0,"large_sprite_bit":0,
                      "OBJ_palette":(int(native[:2],16)>>1)&7,
                      "OBJ_priority":1}
            row=qa.slot_delta(original,native,0,slot)
            expect=-2 if slot in medals else 2 if slot in (96,97) else 0
            self.assertEqual(row["native_minus_original_tile"],expect)
            for bad in ("0bae", "beef", "????"):
                with self.assertRaises(ValueError):
                    qa.slot_delta(original,bad,0,slot)
            with self.assertRaises(ValueError):
                qa.slot_delta(original,native,1,slot)

    def test_real_original_OAMDMA_entire_byte_stream_and_VBlank_only(self):
        raw=bytes(range(256))*2+bytes(32)
        def journal(changes=None, limit=544):
            lines=["#frame\tvcounter\thcounter\taddr\tvalue\tsource"]
            for i in range(limit):
                values=["4031",str(226+i//300),str(i%300),
                        "2104",f"{raw[i]:02X}","dma"]
                if changes and i in changes:
                    for k,v in changes[i].items():values[k]=v
                lines.append("\t".join(values))
            return ("\n".join(lines)+"\n").encode("ascii")
        valid=journal()
        with patch.dict(qa.ORIGINAL_OAM_PPU_JOURNAL_SHA256,{4031:qa.sha(valid)}):
            result=qa.verify_original_dma_oam(4031,valid,raw)
        self.assertEqual(result["original_OAMDATA_DMA_write_count"],544)
        self.assertTrue(result["zero_recorded_active_visible_line_OAMDATA_writes"])
        self.assertTrue(result["entire_original_OAMDMA_byte_stream_matches_original_PPU_OAM"])
        invalid=[
          journal(limit=543),
          journal({500:{1:"112"}}), # active visible beam
          journal({0:{5:"hdma"}}),  # wrong OAM port writer provenance
          journal({450:{4:"FF"}}),  # incomplete/corrupt DMA OAM payload
        ]
        for bad in invalid:
            with self.subTest(sha=qa.sha(bad)),patch.dict(
                qa.ORIGINAL_OAM_PPU_JOURNAL_SHA256,{4031:qa.sha(bad)}):
                with self.assertRaises(ValueError):
                    qa.verify_original_dma_oam(4031,bad,raw)
        with self.assertRaises(ValueError):
            qa.verify_original_dma_oam(999,valid,raw)
        with self.assertRaises(ValueError):
            qa.verify_original_dma_oam(4031,valid,raw)

    def test_source_callback_and_host_screenshot_cannot_be_silently_equated(self):
        a=bytes(256*224*4)
        b=bytearray(a)
        for i in range(778):
            b[i*4]=1
        self.assertEqual(qa.pixel_difference_count(a,b),778)
        self.assertEqual(qa.sha(a),qa.sha(bytes(a)))
        self.assertNotEqual(qa.sha(a),qa.sha(bytes(b)))
        with self.assertRaises(ValueError):
            qa.pixel_difference_count(a,b[:-1])
        self.assertEqual(qa.FIELDS[4031]["wrong"],778)
        self.assertEqual(qa.FIELDS[4175]["wrong"],766)
        self.assertEqual(qa.FIELDS[1279]["wrong"],216)

    def test_archive_fail_closed_before_untrusted_zip_members(self):
        with tempfile.TemporaryDirectory() as tmp:
            f=Path(tmp)/"forged.zip"
            with zipfile.ZipFile(f,"w") as z:
                z.writestr("qa08-original-2p-fullroute.json","{}")
            for kind in qa.SHA:
                with self.subTest(kind=kind),self.assertRaisesRegex(ValueError,"outer source ZIP"):
                    qa.open_zip(f,kind)
        self.assertEqual(qa.SHA["original_263"],
                         "72b7b152d08d8abb3636053bfd132db64926a5bf188f4dbba7e30b20d9583e9e")
        self.assertEqual(len(qa.SHA),3)

    def test_immutable_evidence_exactly_two_medal_results_and_no_release_authority(self):
        self.assertEqual(sorted(qa.ORIGINAL_TILE),[4031,4175])
        self.assertEqual(sorted(qa.NATIVE_TILE),[4032,4176])
        self.assertEqual(qa.SLOTS,(96,97,98,99,112,113,114))
        for orig,guest in ((4031,4032),(4175,4176)):
            for slot in qa.SLOTS:
                expected=(-2 if slot in (112,113,114) else
                          2 if slot in (96,97) else 0)
                self.assertEqual(qa.NATIVE_TILE[guest][slot]-qa.ORIGINAL_TILE[orig][slot],
                                 expected)
        with self.assertRaises(ValueError):
            qa.check(1,2,"wrong fake source")

if __name__=="__main__":
    unittest.main()
