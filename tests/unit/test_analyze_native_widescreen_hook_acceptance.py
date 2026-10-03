import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
SPEC=importlib.util.spec_from_file_location(
    "ws_accept", ROOT/"tools/analyze_native_widescreen_hook_acceptance.py"
)
MOD=importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MOD)

P0="00"*32
P1="11"*32
P2="22"*32

class NativeWidescreenHookAcceptanceTests(unittest.TestCase):
    def dump(self,path:Path,tweak=None):
        raw=bytearray(0x20000)
        for i,(_,addr) in enumerate(MOD.PROTECTED_WORDS.items(),1):
            raw[addr]=i
        if tweak is not None:
            raw[tweak]=0xEE
        path.write_bytes(raw)

    def dumps(self,root:Path,tweak16=None):
        out={}
        for m in (0,8,16,24):
            p=root/f"{m}.bin"
            self.dump(p,tweak16 if m==16 else None)
            out[m]=p
        return out

    def logs(self):
        control=[]
        plus8=[]
        plus16=[]
        for i in range(340):
            cam=100+i
            # Retain exact future-stock rows at +8 and +16 camera advances.
            control.append(
                f"URWS_PRIMARY margin=0 camx={cam} edge=0D80 count=16 payload={P0}\n"
            )
            control.append(
                f"URWS_PRIMARY margin=0 camx={cam+8} edge=0D81 count=16 payload={P1}\n"
            )
            control.append(
                f"URWS_PRIMARY margin=0 camx={cam+16} edge=0D82 count=16 payload={P2}\n"
            )

            plus8.append(
                f"URWS_PRIMARY margin=8 camx={cam} edge=0D80 count=16 payload={P0}\n"
            )
            if i:
                plus8.append("URWS_CLEANUP margin=8\n")
            plus8.append(
                f"URWS_PREP margin=8 camx={cam} edge=0D81 count=16 payload={P1}\n"
            )

            plus16.append(
                f"URWS_PRIMARY margin=16 camx={cam} edge=0D80 count=16 payload={P0}\n"
            )
            if i:
                plus16.append("URWS_CLEANUP16 shadow=1\n")
            plus16.append(
                f"URWS_PREP16 camx={cam} edge=0D81 count=16 payload={P1}\n"
            )
            plus16.append(
                f"URWS_SHADOW16 camx={cam} edge=0D82 count=16 payload={P2}\n"
            )

        return {
            0:"".join(control),
            8:"".join(plus8),
            16:"".join(plus16),
            24:(
                "URWS_LIMIT margin=24 required_extra_columns=3 "
                "guest_extra_horizontal_lanes=1 host_shadow_columns=1 "
                "first_constraint=host-shadow-capacity\n"
            ),
        }

    def test_accepts_host_shadow_plus16_contract(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            r=MOD.analyze(self.logs(),self.dumps(root))
            self.assertTrue(r["accepted"])
            self.assertEqual(r["architecture"]["synthetic_guest_descriptor_lanes"],0)
            self.assertEqual(r["runtime"]["margin16_first_column_events"],340)
            self.assertEqual(r["runtime"]["margin16_shadow_column_events"],340)
            self.assertGreaterEqual(
                r["runtime"]["margin16_first_exact_future_stock_matches"],100
            )
            self.assertGreaterEqual(
                r["runtime"]["margin16_second_exact_future_stock_matches"],100
            )

    def test_rejects_nonadjacent_shadow_column(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            logs=self.logs()
            logs[16]=logs[16].replace("edge=0D82","edge=0D83",1)
            r=MOD.analyze(logs,self.dumps(root))
            self.assertFalse(r["accepted"])
            self.assertFalse(
                r["checks"]["margin16_both_steps_ring_adjacent_and_stock_compatible"]
            )

    def test_rejects_missing_shadow_event(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            logs=self.logs()
            needle=f"URWS_SHADOW16 camx=100 edge=0D82 count=16 payload={P2}\n"
            logs[16]=logs[16].replace(needle,"",1)
            r=MOD.analyze(logs,self.dumps(root))
            self.assertFalse(r["accepted"])
            self.assertFalse(r["checks"]["margin16_two_columns_per_event"])

    def test_rejects_protected_state_change(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            r=MOD.analyze(self.logs(),self.dumps(root,0x0411))
            self.assertFalse(r["accepted"])
            self.assertFalse(r["checks"]["margin16_protected_state_equal"])

    def test_ring_adjacency_ignores_upper_segment_bits(self):
        self.assertTrue(MOD._ring_adjacent(0x0031,0x0052))
        self.assertTrue(MOD._ring_adjacent(0x019F,0x0180))
        self.assertFalse(MOD._ring_adjacent(0x0031,0x0053))

if __name__=="__main__":
    unittest.main()
