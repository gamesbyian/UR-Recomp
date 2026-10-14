"""Original Snes9x full raw frame/PPUW integrity, no false native parity."""
from pathlib import Path
import json
import tempfile
import unittest
from tools import qa08_original_snesref_raster_source as subject


def files(root: Path):
    for tag,frame in subject.TAG_FRAMES.items():
        info={"tag":tag,"frame":frame,"fb_frame":frame,"fb_width":256,
              "fb_height":224,"fb_dump_format":"BGRX8888",
              "ppuw_entries":2,"ppuw_truncated":False,"no_colormath":False,
              "no_clip":False,"layer_mask":"1F","snesref_dbg_version":1}
        (root/(tag+".info.json")).write_text(json.dumps(info),encoding="utf8")
        (root/(tag+".fb.bgrx")).write_bytes(bytes([5,13,27,0])*(256*224))
        (root/(tag+".ppuw.tsv")).write_text(
            "#frame\tvcounter\thcounter\taddr\tvalue\tsource\n"
            f"{frame}\t225\t0\t2131\t04\thdma\n"
            f"{frame}\t0\t3\t2132\t2F\thdma\n",encoding="ascii")


class OriginalReferenceScreenshotTests(unittest.TestCase):
    def test_original_reference_image_and_ppuw_are_hash_pinned(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);files(root)
            a=subject.check(root)
            self.assertEqual(a["original_two_player_script_checkpoint_frames"],[1989,2473])
            self.assertTrue(a["full_source_FB_and_original_PPU_journal_complete"])
            self.assertFalse(a["original_native_pixel_parity_proven"])
            for row in a["observed_original_Snes9x_source_samples"]:
                self.assertEqual(row["source_image_samples_not_native_aligned"][0]["original_RGB8"],[27,13,5])
                self.assertEqual(row["source_register_writes"]["hdma_CGADSUB_writes"],1)
                self.assertEqual(row["source_register_writes"]["hdma_COLDATA_writes"],1)

    def test_frame_shape_or_stale_source_fails(self):
        for change in ("wrong_frame","different_fb_frame","wrong_width","wrong_layers","clipped",
                       "no_debug","short_frame","mismatch_count","truncated"):
            with self.subTest(change=change),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);files(root)
                p=root/"go.info.json";obj=json.loads(p.read_text())
                if change=="wrong_frame": obj["frame"]=1988
                if change=="different_fb_frame": obj["fb_frame"]=1988
                if change=="wrong_width": obj["fb_width"]=342
                if change=="wrong_layers": obj["layer_mask"]="0F"
                if change=="clipped": obj["no_clip"]=True
                if change=="no_debug": obj["snesref_dbg_version"]=0
                if change=="mismatch_count": obj["ppuw_entries"]=3
                if change=="truncated": obj["ppuw_truncated"]=True
                p.write_text(json.dumps(obj))
                if change=="short_frame": (root/"go.fb.bgrx").write_bytes(b"tiny")
                with self.assertRaises(ValueError):
                    subject.check(root)

    def test_ppu_journal_source_and_beam_order_fail_closed(self):
        for bad in ("wrongframe","badregister","badsource","hcounter","beam_reversed",
                    "badhex","truncated"):
            with self.subTest(change=bad),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);files(root)
                p=root/"go.ppuw.tsv";s=p.read_text()
                if bad=="wrongframe": s=s.replace("1989\t225","1988\t225")
                if bad=="badregister": s=s.replace("2131","0004")
                if bad=="badsource": s=s.replace("hdma","emulator")
                if bad=="hcounter": s=s.replace("\t225\t0","\t225\t500")
                if bad=="beam_reversed":
                    rows=s.splitlines()
                    s="\n".join([rows[0],rows[2],rows[1]])+"\n"
                if bad=="badhex": s=s.replace("2131","21FG")
                if bad=="truncated": s=s.replace("#frame", "#truncated\n#frame",1)
                p.write_text(s)
                with self.assertRaises(ValueError):
                    subject.check(root)

    def test_duplicate_metadata_keys_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);files(root)
            (root/"go.info.json").write_text('{"tag":"go","tag":"fake"}')
            with self.assertRaisesRegex(ValueError,"duplicate"):
                subject.check(root)


if __name__=="__main__":
    unittest.main()
