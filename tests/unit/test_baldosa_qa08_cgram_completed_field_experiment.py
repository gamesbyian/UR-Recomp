"""Source-bound experimental CGRAM field snapshot cannot mutate live game."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import baldosa_qa08_cgram_completed_field_experiment as cgram


class OriginalFieldCgramTest(unittest.TestCase):
    def setUp(self):
        # All original exact source windows represented once. The transform
        # cannot silently alter unrelated PPU operations or move a field.
        self.source=("/* "+cgram.BRT_MARK+" */\n"+
                     "\n".join(original for original,_ in cgram.PATCHES))

    def test_completed_field_cgram_and_guest_backup_are_separate(self):
        updated=cgram.patch_source(self.source)
        self.assertEqual(cgram.patch_source(updated),updated)
        self.assertEqual(updated.count(cgram.MARK),1)
        self.assertIn("memcpy(s_field[s_raster_cur].cgram_complete",updated)
        self.assertIn("memcpy(ppu->cgram, f->cgram_complete",updated)
        self.assertIn("memcpy(s_raster_live_guest_cgram, ppu->cgram",updated)
        self.assertIn("memcpy(ppu->cgram, s_raster_live_guest_cgram",updated)
        self.assertIn("ppu->cgramPointer = s_raster_live_guest_cgramPointer",updated)
        self.assertIn("ppu->cgramSecondWrite = s_raster_live_guest_cgramSecondWrite",updated)
        self.assertIn("ppu->cgramBuffer = s_raster_live_guest_cgramBuffer",updated)
        restored=updated
        for before,after in reversed(cgram.PATCHES):
            restored=restored.replace(after,before,1)
        self.assertEqual(restored,self.source)

    def test_source_owner_drift_partial_and_duplicate_rejected(self):
        full=cgram.patch_source(self.source)
        for source in (
            self.source.replace(cgram.BRT_MARK,"unverified_other_game"),
            self.source.replace("s_raster_cur ^= 1","s_raster_cur |= 1"),
            full.replace("s_raster_live_guest_cgramSecondWrite",
                         "different_name",1),
            full+full,
            self.source.replace("ppu->oamBuffer = s_raster_port.oamBuffer;", "ppu->oamBuffer = 0;")
        ):
            with self.subTest(source=source[:65]),self.assertRaises(ValueError):
                cgram.patch_source(source)

    def test_strict_game_and_framework_pin_gate_before_mutation(self):
        with tempfile.TemporaryDirectory() as td:
            game=Path(td)
            file=game/cgram.REL
            file.parent.mkdir(parents=True)
            file.write_text(self.source)
            (game/"src/gen").mkdir(parents=True)
            (game/"src/gen/dispatch_v2.c").write_text("source")
            with patch.object(cgram,"pinned_revision",side_effect=["other",cgram.CORE_REV]):
                with self.assertRaisesRegex(ValueError,"source game"):
                    cgram.apply_game(game,write=True)
            self.assertEqual(file.read_text(),self.source)
            with patch.object(cgram,"pinned_revision",
                              side_effect=[cgram.GAME_REV,cgram.CORE_REV]):
                cgram.apply_game(game,write=True)
            self.assertEqual(file.read_text(),cgram.patch_source(self.source))

    def test_CI_requires_after_existing_brightness_and_v0_scenes(self):
        wf=(ROOT/".github/workflows/baldosa-windows-native-bridge.yml").read_text()
        experiment="python tools/baldosa_qa08_cgram_completed_field_experiment.py --game baldosa --apply-experiment"
        self.assertEqual(wf.count(experiment),1)
        self.assertLess(wf.index("python tools/baldosa_uniracers_brightness_pixel_lut_patch.py --game baldosa --apply-candidate"),
                        wf.index(experiment))
        self.assertLess(wf.index(experiment),wf.index("cmake -S baldosa -B baldosa/build-ur-win"))


if __name__=="__main__":
    unittest.main()
