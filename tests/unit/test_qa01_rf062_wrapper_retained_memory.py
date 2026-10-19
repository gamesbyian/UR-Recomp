"""Full 128KiB/8KiB guest memory cross-build A/B, no ROM and no guest emulator."""
import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf062_wrapper_substitution_compare as audit
from qa01_zoo_raw_archive_audit import BOWL_OFFSETS

class ActualRawMemoryPopulation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        cls.root=Path(cls.temp.name)
        cls.a=cls.root/"wrapped"
        cls.b=cls.root/"control"
        cls.frames=[0,*range(1,64),*range(5034,5047),5120]
        assert len(cls.frames)==78
        cls.report={"zoo_race_mesh":{"samples":[{"race_relative_frame":n} for n in cls.frames]},
                    "zoo_next_bowl_handoff":{"sample_offsets":list(BOWL_OFFSETS)}}
        cls.tags=[("race-entered" if f==0 else f"scene-{f:05d}")
                  for f in cls.frames]+[f"zoo-next-bowl-{n:03d}" for n in BOWL_OFFSETS]
        for root in (cls.a,cls.b):
            for side in ("ref","native"):
                folder=root/"work"/"zoom-zoo"/"replay"/side
                folder.mkdir(parents=True)
                for tag in cls.tags:
                    for kind,size in (("wram",131072),("sram",8192)):
                        with (folder/(tag+"."+kind+".bin")).open("wb") as fp:
                            fp.truncate(size)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_all_712_unmasked_bytes_and_phase_labels_reopened(self):
        verdict=audit.retained_memory_control(self.a,self.b,self.report,self.report)
        self.assertTrue(verdict["original_and_native_exact_variant_raw_memory_equal"])
        self.assertEqual(verdict["full_raw_images_independently_reopened"],712)
        self.assertEqual(verdict["unique_relative_race_frames"],78)
        self.assertEqual(verdict["earned_Bowl_handoff_offsets"],11)
        self.assertFalse(verdict["every_unsampled_CPU_opcode_or_frame_proven_equivalent"])

    def test_changed_native_sound_window_wram_byte_preserved_as_negative(self):
        path=self.a/"work"/"zoom-zoo"/"replay"/"native"/"scene-05040.wram.bin"
        with path.open("r+b") as out:
            out.seek(0x63)
            out.write(b"\xD0")
        try:
            verdict=audit.retained_memory_control(self.a,self.b,self.report,self.report)
            self.assertFalse(verdict["original_and_native_exact_variant_raw_memory_equal"])
            self.assertEqual(verdict["number_of_between_variant_raw_memory_differences"],1)
            first=verdict["first_12_between_variant_raw_memory_differences"][0]
            self.assertEqual((first["phase"],first["offset"],first["guest"],first["memory"]),
                             ("course",5040,"native","wram"))
            self.assertEqual(first["number_of_changed_bytes"],1)
        finally:
            with path.open("r+b") as out:
                out.seek(0x63)
                out.write(b"\x00")

    def test_changed_source_input_frame_or_missing_full_raw_image_rejected(self):
        bad={"zoo_race_mesh":{"samples":self.report["zoo_race_mesh"]["samples"][:-1]},
             "zoo_next_bowl_handoff":{"sample_offsets":list(BOWL_OFFSETS)}}
        with self.assertRaisesRegex(ValueError,"78 full frame"):
            audit.retained_memory_control(self.a,self.b,bad,self.report)
        path=self.b/"work"/"zoom-zoo"/"replay"/"ref"/"scene-05035.sram.bin"
        path.unlink()
        with self.assertRaisesRegex(ValueError,"incomplete actual original/native full raw"):
            audit.retained_memory_control(self.a,self.b,self.report,self.report)

if __name__=="__main__":
    unittest.main()
