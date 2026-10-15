"""QA-08 source-qualified original Snes9x 5-bit brightness candidate guards."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import baldosa_uniracers_brightness_pixel_lut_patch as bright  # noqa: E402


PINNED=(
    "int ppu_draw(void) {\n" + bright.BEFORE + bright.OLD + "\n" +
    bright.AFTER + "  }\n"
)

class SourceBrightnessTest(unittest.TestCase):
    def test_2014_mul_brightness_source_matched_all_512_entries(self):
        # Pinned 2014 Snes9x globals.cpp table is exactly nearest i*b/15.
        # Representative full original row14 included as an independent
        # literal from the original core, not derived from the formula.
        row14=[0,1,2,3,4,5,6,7,7,8,9,10,11,12,13,14,
               15,16,17,18,19,20,21,21,22,23,24,25,26,27,28,29]
        self.assertEqual([bright.mul_snes9x_2014(14,i) for i in range(32)],row14)
        for b in range(16):
            for c in range(32):
                value=bright.mul_snes9x_2014(b,c)
                self.assertGreaterEqual(value,0)
                self.assertLessEqual(value,31)
                self.assertEqual(bright.expanded_snes9x_brightness(b,c),
                                 (value<<3)|(value>>2))
        self.assertEqual(bright.expanded_snes9x_brightness(14,15),115)
        self.assertEqual(bright.expanded_snes9x_brightness(14,21),165)
        self.assertEqual(bright.expanded_snes9x_brightness(14,17),132)
        self.assertEqual(bright.expanded_snes9x_brightness(14,18),140)
        self.assertEqual(bright.expanded_snes9x_brightness(7,31),115)
        self.assertEqual(bright.expanded_snes9x_brightness(15,31),255)
        with self.assertRaises(ValueError):bright.mul_snes9x_2014(16,1)
        with self.assertRaises(ValueError):bright.mul_snes9x_2014(14,32)

    def test_patch_changes_only_last_5bit_brightness_rhs(self):
        changed=bright.patch_source(PINNED)
        self.assertEqual(bright.patch_source(changed),changed)
        self.assertNotIn(bright.OLD,changed)
        self.assertEqual(changed.count(bright.MARK),1)
        self.assertEqual(changed.replace(bright.NEW,bright.OLD),PINNED)
        self.assertEqual(changed.count("brightnessMultHalf[i * 2]"),1)
        self.assertEqual(changed.count("brightnessMult[i]"),1)

    def test_unknown_modified_pinned_source_fails_closed(self):
        good=bright.patch_source(PINNED)
        for bad in ("",PINNED.replace("lastBrightnessMult","other"),
                    PINNED.replace("i << 3","i << 4"),
                    PINNED+PINNED,good.replace(" + 7", " + 8"),
                    good+bright.MARK):
            with self.subTest(desc=bad[:60]),self.assertRaises(ValueError):
                bright.patch_source(bad)

    def test_core_or_title_pin_failure_never_changes_disposable_game(self):
        with tempfile.TemporaryDirectory() as tmp:
            game=Path(tmp)
            (game/"src/gen").mkdir(parents=True)
            (game/"src/gen/dispatch_v2.c").write_text("title generated")
            p=game/bright.FILE
            p.parent.mkdir(parents=True)
            p.write_text(PINNED)
            with patch.object(bright,"pinned_revision",side_effect=["bad",bright.CORE_REV]):
                with self.assertRaisesRegex(ValueError,"title source"):
                    bright.apply_game(game,write=True)
            self.assertEqual(p.read_text(),PINNED)
            with patch.object(bright,"pinned_revision",
                              side_effect=[bright.GAME_REV,"unknown-framework"]):
                with self.assertRaisesRegex(ValueError,"framework"):
                    bright.apply_game(game,write=True)
            self.assertEqual(p.read_text(),PINNED)
            with patch.object(bright,"pinned_revision",
                              side_effect=[bright.GAME_REV,bright.CORE_REV]):
                bright.apply_game(game,write=True)
            self.assertEqual(p.read_text(),bright.patch_source(PINNED))

    def test_real_windows_bridge_stages_brightness_after_hdma_before_compile(self):
        workflow=(ROOT/".github/workflows/baldosa-windows-native-bridge.yml").read_text()
        self.assertEqual(workflow.count(
            "python tools/baldosa_uniracers_brightness_pixel_lut_patch.py --game baldosa --apply-candidate"),1)
        self.assertEqual(workflow.count(
            "python tests/unit/test_baldosa_uniracers_brightness_pixel_lut_patch.py"),1)
        self.assertLess(workflow.index("python tools/baldosa_uniracers_hdma_firstline_patch.py"),
                        workflow.index("python tools/baldosa_uniracers_brightness_pixel_lut_patch.py"))
        self.assertLess(workflow.index("python tools/baldosa_uniracers_brightness_pixel_lut_patch.py"),
                        workflow.index("cmake -S baldosa -B baldosa/build-ur-win"))


if __name__=="__main__":
    unittest.main()
