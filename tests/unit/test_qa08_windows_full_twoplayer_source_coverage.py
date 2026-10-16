"""Original-size source-only 2P split/race/terminal Windows observer gates."""
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import qa08_windows_full_twoplayer_source_coverage as two


class TwoPlayerSourceTest(unittest.TestCase):
    def test_exact_real_source_window_and_terminal_scene_coverage(self):
        self.assertEqual((two.FIRST,two.LAST,two.STEP),(1280,5472,16))
        self.assertEqual(len(range(1280,5473,16)),263)
        self.assertEqual(len([f for f in range(1280,5473,16) if f>=5136]),22)

    def test_fake_or_truncated_native_guest_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            with self.assertRaises(ValueError):
                two.inspect(folder,"",["0x00000000"]*5484)
            log=("UR_QA08_WINDOWS_ORIGINAL_SOURCE frame=1280 "
                 "logical=256x224 saved=1 "
                 "source=post-original-ppu-before-present\n")
            with self.assertRaisesRegex(ValueError,"missing"):
                two.inspect(folder,log,["0x00000000"]*5484)
            with self.assertRaisesRegex(ValueError,"never reached"):
                two.inspect(folder,log,["0x00000000"]*100)

    def test_native_inidisp_colourmath_cgram_state_is_read_only_and_source_bound(self):
        line=lambda f,y,b: (
            f"UR_QA08_WIN_PPU_STATE frame={f} line={y} "
            f"inidisp={b:02x} brightness={b} forced_blank=0 "
            "cgadsub=04 cgwsel=02 fixedcolor=0180 cg6c=56b5 cg6d=4a52 cg6e=4631 cg6f=4210 cgram_fnv=2345abcd\n")
        log=line(3683,1,7)+line(3683,112,0)+line(3683,114,7)+line(4064,1,14)
        result=two.inspect_native_ppu_registers(log)
        self.assertEqual(result["actual_state_line_count"],4)
        self.assertEqual([x["brightness"] for x in
                          result["per_line_native_PPU_state"]],[7,0,7,14])
        self.assertFalse(result["release_gate_accepted"])
        self.assertEqual(result["per_line_native_PPU_state"][-1]
                         ["real_native_CGRAM_slots_6c_to_6f"],
                         {"6c":"56b5","6d":"4a52","6e":"4631","6f":"4210"})
        with self.assertRaises(ValueError):
            two.inspect_native_ppu_registers("")
        with self.assertRaises(ValueError):
            two.inspect_native_ppu_registers(log+line(3683,1,7))
        with self.assertRaises(ValueError):
            two.inspect_native_ppu_registers(line(3683,1,7))


    def test_native_cgram_writer_requires_real_phase_and_valid_boundaries(self):
        def record(f,addr,ptr,second,val,v=226,h=60,src=0):
            return (f"UR_QA08_WIN_CGRAM_WRITE frame={f} v={v} h={h} "
                    f"adr={addr} val={val} src={src} ptr={ptr} second={second}\n")
        data=record(5176,"21","6f",0,"6f")*12+record(5183,"22","6c",1,"56")*12
        result=two.inspect_native_cgram_port_history(data)
        self.assertEqual(result["actual_bounded_port_writes"],24)
        self.assertEqual(result["write_frames"],[5176,5183])
        self.assertFalse(result["raster_fix_approved"])
        with self.assertRaises(ValueError):
            two.inspect_native_cgram_port_history("")
        with self.assertRaises(ValueError):
            two.inspect_native_cgram_port_history(data+"UR_QA08_WIN_CGRAM_WRITE corrupted\n")
        with self.assertRaises(ValueError):
            two.inspect_native_cgram_port_history(
                record(6000,"22","6c",1,"56")*24)

    def test_read_only_two_pad_observer_retains_prior_frozen_controls(self):
        cpp=(ROOT/"tools/baldosa_qa08_windows_original_capture.cpp").read_text()
        self.assertIn('std::strcmp(mode, "twoplayer-fullroute") == 0',cpp)
        self.assertIn('std::strcmp(mode, "oneplayer-coverage") == 0',cpp)
        self.assertIn("kTwoPlayerLast = 5472",cpp)
        self.assertIn("kOnePlayerLast = 5440",cpp)
        self.assertIn("g_seen_default[4]",cpp)
        self.assertIn("g_seen_twoplayer[kTwoPlayerSlots]",cpp)
        self.assertIn("source=post-original-ppu-before-present",cpp)
        self.assertNotIn("ppu_render_pixel(",cpp)

    def test_ci_wires_2p_qa_only_once_after_1p_in_same_windows_title(self):
        workflow=(ROOT/".github/workflows/baldosa-windows-native-bridge.yml").read_text()
        entry="python tools/qa08_windows_full_twoplayer_source_coverage.py"
        self.assertEqual(workflow.count(entry),1)
        self.assertLess(workflow.index(
            "python tools/qa08_windows_full_oneplayer_source_coverage.py"),
            workflow.index(entry))
        self.assertEqual(workflow.count(
            "python tests/unit/test_qa08_windows_full_twoplayer_source_coverage.py"),1)


if __name__=="__main__":
    unittest.main()
