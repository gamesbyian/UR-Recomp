import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
SPEC=importlib.util.spec_from_file_location("ws_accept",ROOT/"tools/analyze_native_widescreen_hook_acceptance.py")
MOD=importlib.util.module_from_spec(SPEC); assert SPEC.loader; SPEC.loader.exec_module(MOD)

class NativeWidescreenHookAcceptanceTests(unittest.TestCase):
    def dump(self,path:Path,tweak=None):
        raw=bytearray(0x20000)
        for i,(_,addr) in enumerate(MOD.PROTECTED_WORDS.items(),1):
            raw[addr]=i
        if tweak is not None: raw[tweak]=0xEE
        path.write_bytes(raw)

    def test_accepts_plus8_and_capacity_stop(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); dumps={}
            for m in (0,8,16,24):
                p=root/f"{m}.bin"; self.dump(p); dumps[m]=p
            logs={
                0:"",
                8:"URWS_PREP margin=8 edge=0D81 count=16\nURWS_CLEANUP margin=8\n",
                16:"URWS_LIMIT margin=16 required_extra_columns=2 stock_extra_horizontal_lanes=1 first_constraint=secondary-lane-capacity\n",
                24:"URWS_LIMIT margin=24 required_extra_columns=3 stock_extra_horizontal_lanes=1 first_constraint=secondary-lane-capacity\n",
            }
            r=MOD.analyze(logs,dumps)
            self.assertTrue(r["accepted"])
            self.assertEqual(r["first_generalization_constraint"],"secondary-lane-capacity")

    def test_accepts_one_final_live_payload_at_fixture_exit(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); dumps={}
            for m in (0,8,16,24):
                p=root/f"{m}.bin"; self.dump(p); dumps[m]=p
            logs={
                0:"",
                8:(
                    "URWS_PREP margin=8 edge=0D81 count=16\n"
                    "URWS_CLEANUP margin=8\n"
                    "URWS_PREP margin=8 edge=0D82 count=16\n"
                ),
                16:"URWS_LIMIT margin=16 required_extra_columns=2 stock_extra_horizontal_lanes=1 first_constraint=secondary-lane-capacity\n",
                24:"URWS_LIMIT margin=24 required_extra_columns=3 stock_extra_horizontal_lanes=1 first_constraint=secondary-lane-capacity\n",
            }
            r=MOD.analyze(logs,dumps)
            self.assertTrue(r["accepted"])
            self.assertTrue(r["native_runtime"]["margin8_final_payload_live_at_exit"])
            self.assertTrue(r["checks"]["margin8_cleanup_lifecycle_valid"])

    def test_rejects_double_prepare_without_cleanup(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); dumps={}
            for m in (0,8,16,24):
                p=root/f"{m}.bin"; self.dump(p); dumps[m]=p
            logs={
                0:"",
                8:(
                    "URWS_PREP margin=8 edge=0D81 count=16\n"
                    "URWS_PREP margin=8 edge=0D82 count=16\n"
                ),
                16:"URWS_LIMIT margin=16 required_extra_columns=2 stock_extra_horizontal_lanes=1 first_constraint=secondary-lane-capacity\n",
                24:"URWS_LIMIT margin=24 required_extra_columns=3 stock_extra_horizontal_lanes=1 first_constraint=secondary-lane-capacity\n",
            }
            self.assertFalse(MOD.analyze(logs,dumps)["accepted"])

    def test_rejects_protected_state_change(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); dumps={}
            for m in (0,8,16,24):
                p=root/f"{m}.bin"; self.dump(p,0x0411 if m==8 else None); dumps[m]=p
            logs={
                0:"",
                8:"URWS_PREP margin=8 edge=0D81 count=16\nURWS_CLEANUP margin=8\n",
                16:"URWS_LIMIT margin=16 required_extra_columns=2 stock_extra_horizontal_lanes=1 first_constraint=secondary-lane-capacity\n",
                24:"URWS_LIMIT margin=24 required_extra_columns=3 stock_extra_horizontal_lanes=1 first_constraint=secondary-lane-capacity\n",
            }
            self.assertFalse(MOD.analyze(logs,dumps)["accepted"])

if __name__=="__main__":
    unittest.main()
