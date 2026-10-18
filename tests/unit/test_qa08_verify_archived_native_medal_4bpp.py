"""Negative controls for genuine Windows 4bpp medal-source archive replay."""
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tools import qa08_verify_archived_native_medal_4bpp as v

class ActualMedal4BppArchive(unittest.TestCase):
    def test_untrusted_artifact_rejected_before_member_processing(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"impostor.zip"
            p.write_bytes(b"not the actual archived Windows source")
            with self.assertRaisesRegex(ValueError,"outer SHA mismatch"):
                v.verify_archive(p)
        with self.assertRaisesRegex(ValueError,"source log SHA"):
            v.replay(b"fake Windows log")

    def test_real_4bpp_plane_and_encoded_zbuffer_checks(self):
        row={"frame":"4032","x":"225","raster_y":"96",
            "slot":"97","oam":"58db","attrs":"1bce",
            "oam_tile":"ce","used_tile":"0de","objadr":"7000",
            "row":"8","src_col":"0","px":"6","palette":"d0",
            "priority":"100","pixel":"e","plane":"02030201",
            "writer_obj":"64de"}
        parsed=v.checked_fetch(row)
        self.assertEqual(parsed["pixel"],14)
        self.assertEqual(parsed["priority"],100)
        self.assertEqual(parsed["writer_obj"],0x64de)
        bad=[
            dict(row,plane="00000000"),
            dict(row,writer_obj="64df"),
            dict(row,slot="129"),
            dict(row,priority="101"),
            dict(row,raster_y="97"),
            dict(row,attrs="1bcf"),
            dict(row,px="8"),
        ]
        for candidate in bad:
            with self.subTest(x=candidate),self.assertRaises(ValueError):
                v.checked_fetch(candidate)

    def test_declared_source_and_no_acceptance_boundaries(self):
        self.assertEqual(v.ARTIFACT_ID,12134793278)
        self.assertEqual(v.RUN_ID,39123459879)
        self.assertEqual(v.LOG_SHA,
            "ff0ca813911fb4b8d3c61cadc358df49e8b409e82eae9619956a09ce3433a602")
        self.assertEqual(len(v.POINTS)*len(v.FRAMES),25)
        script=(ROOT/"tools/qa08_verify_archived_native_medal_4bpp.py").read_text()
        for claim in (
          '"strict_5484_frame_CRC_recomputed_from_this_log":False',
          '"original_2014_Snes9x_effective_pixel_owner_identical_proven":False',
          '"global_video_shift_or_tile_reindex_authorized":False',
          '"renderer_or_release_approved":False',
        ):
            self.assertIn(claim,script)

if __name__=="__main__":
    unittest.main()
