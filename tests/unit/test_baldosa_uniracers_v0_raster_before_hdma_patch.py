"""Game-only source-proven V0 HDMA register replay order and safety."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import baldosa_uniracers_v0_raster_before_hdma_patch as v0


class OriginalV0RasterBeforeHdmaTest(unittest.TestCase):
    def setUp(self):
        self.source=(
            "#include \"beam_frame_driver.h\"\n"+
            v0.FUNCTION+"\n  int line;\n"+v0.BEFORE+
            "\n    dma_doHdma(g_snes->dma);\n  }\n"
            "  ppu_rasterRenderEnd(g_ppu);\n}\n"+v0.NEXT+"\n}\n"
        )

    def test_original_v0_register_writes_now_precede_real_firstline_HDMA(self):
        actual=v0.patch_source(self.source)
        self.assertEqual(v0.patch_source(actual),actual)
        self.assertEqual(actual.count(v0.MARK),1)
        self.assertEqual(actual.replace(v0.AFTER,v0.BEFORE),self.source)
        self.assertLess(actual.index("ppu_rasterApplyLine(g_ppu, 0)"),
                        actual.index("dma_initHdma(g_snes->dma)"))
        self.assertLess(actual.index("dma_initHdma(g_snes->dma)"),
                        actual.index("dma_primeHdmaFirstLine(g_snes->dma)"))
        self.assertLess(actual.index("dma_primeHdmaFirstLine(g_snes->dma)"),
                        actual.index("ppu_runLine(g_ppu, line)"))
        self.assertIn("ppu_rasterApplyLine(g_ppu, line - 1);",actual)
        self.assertIn("if (line > 1)",actual)
        self.assertEqual(actual.count("dma_doHdma(g_snes->dma)"),1)
        self.assertEqual(actual.count("ppu_rasterRenderEnd(g_ppu)"),1)

    def test_reject_foreign_source_partial_candidate_and_competing_change(self):
        correct=v0.patch_source(self.source)
        for candidate in (
            "",
            self.source.replace("dma_primeHdmaFirstLine","badprime"),
            self.source+self.source,
            correct.replace("if (line > 1)", "if (line > 2)"),
            correct+v0.MARK
        ):
            with self.subTest(case=candidate[:60]),self.assertRaises(ValueError):
                v0.patch_source(candidate)

    def test_pin_before_any_write_and_unchanged_guest(self):
        with tempfile.TemporaryDirectory() as tmp:
            game=Path(tmp)
            f=game/v0.REL
            f.parent.mkdir(parents=True)
            f.write_text(self.source)
            (game/"src/gen").mkdir(parents=True)
            (game/"src/gen/dispatch_v2.c").write_text("guest")
            with patch.object(v0,"pinned_revision",
                              side_effect=["other",v0.CORE_REV]):
                with self.assertRaises(ValueError):
                    v0.apply_game(game,write=True)
            self.assertEqual(f.read_text(),self.source)
            with patch.object(v0,"pinned_revision",
                              side_effect=[v0.GAME_REV,v0.CORE_REV]):
                v0.apply_game(game,write=True)
            self.assertEqual(f.read_text(),v0.patch_source(self.source))

    def test_ci_stages_V0_only_after_existing_hdma_advance(self):
        workflow=(ROOT/".github/workflows/baldosa-windows-native-bridge.yml").read_text()
        first="python tools/baldosa_uniracers_hdma_firstline_patch.py --game baldosa --apply-candidate"
        v="python tools/baldosa_uniracers_v0_raster_before_hdma_patch.py --game baldosa --apply-candidate"
        self.assertEqual(workflow.count(first),1)
        self.assertEqual(workflow.count(v),1)
        self.assertLess(workflow.index(first),workflow.index(v))
        self.assertLess(workflow.index(v),workflow.index("cmake -S baldosa -B baldosa/build-ur-win"))


if __name__=="__main__":
    unittest.main()
