"""Read-only original Snes9x PPU journal route must not modify controller timing."""
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import qa08_original_twoplayer_ppu_register_trace as ppu


class OriginalTwopadPpuRegisterTraceTest(unittest.TestCase):
    def test_authentic_route_has_three_zero_frame_dumps_and_same_buttons(self):
        route=(ROOT/"reference/imported/reverse-engineering/"
               "baldosa-uniracers-recomp/tests/routes/race_2p.txt").read_bytes()
        observed=ppu.build_script(route)
        self.assertEqual(route.count(b"turbo on\n"),1)
        self.assertEqual(observed.count(b"dump qa08_"),3)
        self.assertEqual(len(ppu.DUMPS),3)
        self.assertEqual(ppu.DUMP_FRAMES["qa08_before_finish"],3622)
        self.assertEqual(ppu.DUMP_FRAMES["qa08_finish_fade"],3683)
        self.assertEqual(ppu.DUMP_FRAMES["qa08_results_cgram"],5184)
        restored=observed
        for tag in ppu.DUMPS:
            restored=restored.replace(b"dump "+tag.encode()+b"\n",b"")
        self.assertEqual(restored,route.replace(b"turbo on\n",b""))

    def test_rejects_changed_buttons_waits_or_missing_stock_route(self):
        route=(ROOT/"reference/imported/reverse-engineering/"
               "baldosa-uniracers-recomp/tests/routes/race_2p.txt").read_bytes()
        for altered in (
            route.replace(b"p2:right",b"p2:left",1),
            route.replace(b"right+p2:right 1500",b"right+p2:right 1499"),
            route.replace(b"turbo on\n",b""),
            route+b"dump arbitrary\n",
        ):
            with self.subTest(source=altered[-50:]),self.assertRaises(ValueError):
                ppu.build_script(altered)

    def test_no_game_logic_source_modified_by_trace(self):
        source=(ROOT/"tools/qa08_original_twoplayer_ppu_register_trace.py").read_text()
        self.assertIn("all_263_original_PPU_BRGX_raw_frames_byte_exact",source)
        self.assertIn("actual_zero_frame_dump_only_script_sha256",source)
        self.assertNotIn("forcepoke",source)
        self.assertNotIn("patch_guest",source)


if __name__=="__main__":
    unittest.main()
