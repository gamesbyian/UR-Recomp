import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
SPEC=importlib.util.spec_from_file_location("ws_accept",ROOT/"tools/analyze_native_widescreen_hook_acceptance.py")
MOD=importlib.util.module_from_spec(SPEC); assert SPEC.loader; SPEC.loader.exec_module(MOD)

PAYLOAD="00112233445566778899AABBCCDDEEFF"*2

class NativeWidescreenHookAcceptanceTests(unittest.TestCase):
    def dump(self,path:Path,tweak=None):
        raw=bytearray(0x20000)
        for i,(_,addr) in enumerate(MOD.PROTECTED_WORDS.items(),1):
            raw[addr]=i
        if tweak is not None: raw[tweak]=0xEE
        path.write_bytes(raw)

    def logs(self, *, payload=PAYLOAD, terminal_pending=True):
        primary=[]
        widened=[]
        for i in range(320):
            stock_camx=108+i
            wide_camx=100+i
            primary.append(
                f"URWS_PRIMARY margin=0 camx={stock_camx} edge=0D81 count=16 payload={payload}\n"
            )
            widened.append(
                f"URWS_PRIMARY margin=8 camx={wide_camx} edge=0D80 count=16 payload={PAYLOAD}\n"
            )
            if i:
                widened.append("URWS_CLEANUP margin=8\n")
            widened.append(
                f"URWS_PREP margin=8 camx={wide_camx} edge=0D81 count=16 payload={PAYLOAD}\n"
            )
        if not terminal_pending:
            widened.append("URWS_CLEANUP margin=8\n")
        return {
            0:"".join(primary),
            8:"".join(widened),
            16:"URWS_LIMIT margin=16 required_extra_columns=2 stock_extra_horizontal_lanes=1 first_constraint=secondary-lane-capacity\n",
            24:"URWS_LIMIT margin=24 required_extra_columns=3 stock_extra_horizontal_lanes=1 first_constraint=secondary-lane-capacity\n",
        }

    def dumps(self, root:Path, tweak8=None):
        dumps={}
        for m in (0,8,16,24):
            p=root/f"{m}.bin"
            self.dump(p, tweak8 if m==8 else None)
            dumps[m]=p
        return dumps

    def test_accepts_exact_future_stock_contract_with_terminal_pending_payload(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            r=MOD.analyze(self.logs(),self.dumps(root))
            self.assertTrue(r["accepted"])
            self.assertTrue(r["native_runtime"]["margin8_terminal_payload_pending"])
            self.assertGreaterEqual(r["native_runtime"]["margin8_exact_future_stock_matches"],309)
            self.assertGreaterEqual(r["native_runtime"]["margin8_longest_consecutive_exact_match_run"],14)
            self.assertEqual(r["native_runtime"]["margin8_stock_compatible_prepared_edges"],320)
            self.assertTrue(r["checks"]["margin8_all_preparation_steps_stock_compatible"])
            self.assertEqual(r["first_generalization_constraint"],"secondary-lane-capacity")

    def test_accepts_unobserved_adjacency_event_when_comparable_contract_stays_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            logs=self.logs()
            first="URWS_PRIMARY margin=8 camx=100 edge=0D80 count=16 payload="+PAYLOAD+"\n"
            logs[8]=logs[8].replace(first,"",1)
            r=MOD.analyze(logs,self.dumps(root))
            self.assertTrue(r["accepted"])
            self.assertEqual(r["native_runtime"]["margin8_step_unobserved_events"],1)
            self.assertEqual(r["native_runtime"]["margin8_step_comparable_events"],319)

    def test_accepts_fully_cleaned_final_payload(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            r=MOD.analyze(self.logs(terminal_pending=False),self.dumps(root))
            self.assertTrue(r["accepted"])
            self.assertFalse(r["native_runtime"]["margin8_terminal_payload_pending"])

    def test_ring_adjacency_ignores_upper_segment_bits(self):
        self.assertTrue(MOD._ring_adjacent(0x0031, 0x0052))
        self.assertTrue(MOD._ring_adjacent(0x019F, 0x0180))
        self.assertFalse(MOD._ring_adjacent(0x0031, 0x0053))

    def test_rejects_nonadjacent_prepared_edge(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            logs=self.logs()
            logs[8]=logs[8].replace("edge=0D80 count=16", "edge=0D7E count=16", 1)
            r=MOD.analyze(logs,self.dumps(root))
            self.assertFalse(r["accepted"])
            self.assertFalse(r["checks"]["margin8_all_preparation_steps_stock_compatible"])

    def test_rejects_protected_state_change(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            self.assertFalse(MOD.analyze(self.logs(),self.dumps(root,0x0411))["accepted"])

    def test_rejects_nonmatching_future_stock_payloads(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            wrong="FF"*32
            r=MOD.analyze(self.logs(payload=wrong),self.dumps(root))
            self.assertFalse(r["accepted"])
            self.assertFalse(r["checks"]["margin8_future_stock_exact_matches"])

if __name__=="__main__":
    unittest.main()
