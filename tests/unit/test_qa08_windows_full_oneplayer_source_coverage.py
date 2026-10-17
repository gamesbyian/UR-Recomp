"""Bounded source raster coverage, not an alternative 1P gameplay oracle."""
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import qa08_windows_full_oneplayer_source_coverage as one  # noqa: E402


class OnePlayerCoverageTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.folder=Path(self.temp.name)
        self.crc=["0x00123456"]*5447
        self.frames=(1280,1296,1808,1824,5136,5152)
        self.pix=one.SOURCE_HEADER+b"\x00\x00\x00\xff"*(256*224)

    def tearDown(self):
        self.temp.cleanup()

    def save(self,frame,blob=None):
        (self.folder/f"ur-baldosa-original-source-{frame:06d}.pam").write_bytes(
            self.pix if blob is None else blob)

    def log(self,frame):
        return (f"UR_QA08_WINDOWS_ORIGINAL_SOURCE frame={frame} "
                "logical=256x224 saved=1 "
                "source=post-original-ppu-before-present\n")

    def test_actual_source_input_contract_and_minimum_three_scene_regions(self):
        for frame in self.frames:self.save(frame)
        report=one.inspect(self.folder,"".join(self.log(f) for f in self.frames),self.crc)
        self.assertEqual(report["actual_source_callback_count"],6)
        self.assertEqual(report["possible_callbacks"],261)
        self.assertEqual(report["callback_frame_selection_window"],[1280,5440,16])
        self.assertEqual(len(report["observed_regions"]["race_entry_and_countdown"]),2)
        self.assertEqual(len(report["observed_regions"]["moving_race_and_camera"]),2)
        self.assertEqual(len(report["observed_regions"]["finish_result_return_menu"]),2)
        self.assertFalse(report["same_original_snes9x_raster_parity_proven"])
        self.assertFalse(report["release_quality_ledger_admitted"])

    def test_no_images_invented_and_missing_callback_does_not_substitute(self):
        for frame in self.frames[:-1]:self.save(frame)
        with self.assertRaises(ValueError):
            one.inspect(self.folder,"".join(self.log(f) for f in self.frames),self.crc)
        missing="".join(self.log(f) for f in self.frames[:-1])
        with self.assertRaisesRegex(ValueError,"three scene regions"):
            one.inspect(self.folder,missing,self.crc)

    def test_reject_wrong_or_cropped_frames_repeats_and_guest_crc_mutations(self):
        for frame in self.frames:self.save(frame)
        log="".join(self.log(f) for f in self.frames)
        with self.assertRaises(ValueError):one.inspect(self.folder,log*2,self.crc)
        with self.assertRaises(ValueError):one.inspect(self.folder,log,self.crc[:-1])
        self.save(1312,self.pix[:-1])
        with self.assertRaises(ValueError):one.inspect(self.folder,log,self.crc)
        (self.folder/"ur-baldosa-original-source-001312.pam").unlink()
        self.save(1297)
        with self.assertRaises(ValueError):one.inspect(self.folder,log,self.crc)
        (self.folder/"ur-baldosa-original-source-001297.pam").unlink()
        self.save(1280,self.pix[:-1])
        with self.assertRaises(ValueError):one.inspect(self.folder,log,self.crc)

    def test_solely_opt_in_post_ppu_capture_and_original_four_case_stays_default(self):
        cpp=(ROOT/"tools/baldosa_qa08_windows_original_capture.cpp").read_text()
        self.assertIn("constexpr unsigned kFrame[] = {1856, 2192, 2208, 2224};",cpp)
        self.assertIn("kOnePlayerFirst = 1280",cpp)
        self.assertIn("kOnePlayerLast = 5440",cpp)
        self.assertIn("kOnePlayerStep = 16",cpp)
        self.assertIn('std::strcmp(mode, "oneplayer-coverage") == 0',cpp)
        self.assertIn('std::getenv("UR_QA08_WINDOWS_ORIGINAL_SOURCE_DIR")',cpp)
        self.assertIn("post-original-ppu-before-present",cpp)
        self.assertNotIn("draw_ppu_frame();",cpp)
        self.assertNotIn("RtlRunFrame(",cpp)


if __name__=="__main__":
    unittest.main()
