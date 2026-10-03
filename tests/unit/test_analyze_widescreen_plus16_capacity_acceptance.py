import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "ws_capacity", ROOT / "tools/analyze_widescreen_plus16_capacity_acceptance.py"
)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MOD)

PAYLOAD_A = "00112233445566778899AABBCCDDEEFF" * 2
PAYLOAD_B = "102132435465768798A9BACBDCEDFE0F" * 2


class WidescreenPlus24CapacityTests(unittest.TestCase):
    def fixture(self):
        p8 = []
        log = []
        control = []
        oracle = []
        for i, camx in enumerate((100, 101)):
            primary_edge = 0x0D80 + i * 4
            guest_edge = primary_edge + 1
            host2_edge = primary_edge + 2
            host3_edge = primary_edge + 3
            payload = PAYLOAD_A if i == 0 else PAYLOAD_B
            p8.append({
                "camx": camx, "edge": guest_edge, "count": 16, "payload": payload
            })
            log.append(
                f"URWS_PRIMARY margin=24 camx={camx} edge={primary_edge:04X} "
                f"count=16 payload={payload} camy=0 edgey=FFFF county=0\n"
            )
            if i:
                log.append("URWS_CLEANUP24 shadows=2\n")
            log.append(
                f"URWS_PREP24 camx={camx} edge={guest_edge:04X} count=16 "
                f"payload={payload} camy=0\n"
            )
            log.append(
                f"URWS_SHADOW24 provider=course-runtime column=2 camx={camx} "
                f"edge={host2_edge:04X} count=16 payload={payload} camy=0 "
                f"finex={18+i} finey=0 edgey=FFFF county=0\n"
            )
            log.append(
                f"URWS_SHADOW24 provider=course-runtime column=3 camx={camx} "
                f"edge={host3_edge:04X} count=16 payload={payload} camy=0 "
                f"finex={19+i} finey=0 edgey=FFFF county=0\n"
            )
            control.append({
                "camx": camx, "edge": primary_edge, "count": 16,
                "payload": payload, "camy": 0, "edgey": 0xFFFF,
                "county": 0, "finey": 0,
            })
            oracle.extend([
                {
                    "camx": camx + 20, "edge": host2_edge, "count": 16,
                    "payload": payload, "camy": 0, "edgey": 0xFFFF,
                    "county": 0, "finey": 0,
                },
                {
                    "camx": camx + 21, "edge": host3_edge, "count": 16,
                    "payload": payload, "camy": 0, "edgey": 0xFFFF,
                    "county": 0, "finey": 0,
                },
            ])
        state = {"player_x": 1, "camera_x": 2, "progress": 3}
        return "".join(log), p8, control, oracle, state

    def test_accepts_two_host_columns_with_no_guest_lane_growth(self):
        log, p8, control, oracle, state = self.fixture()
        r = MOD.analyze_margin(24, log, p8, oracle, control, state, dict(state))
        self.assertTrue(r["accepted"])
        self.assertEqual(r["expected_host_columns"], 2)
        self.assertEqual(r["counts"]["host_shadow_events"], 4)
        self.assertTrue(r["checks"]["margin24_all_host_columns_materialized"])
        self.assertTrue(r["checks"]["margin24_ring_chain_adjacent"])
        self.assertTrue(r["checks"]["margin24_same_view_payloads_exact"])
        self.assertTrue(r["checks"]["margin24_protected_state_equal"])

    def test_rejects_missing_third_column(self):
        log, p8, control, oracle, state = self.fixture()
        needle = (
            "URWS_SHADOW24 provider=course-runtime column=3 camx=100 "
            "edge=0D83 count=16 payload=" + PAYLOAD_A +
            " camy=0 finex=19 finey=0 edgey=FFFF county=0\n"
        )
        log = log.replace(needle, "", 1)
        r = MOD.analyze_margin(24, log, p8, oracle, control, state, dict(state))
        self.assertFalse(r["accepted"])
        self.assertFalse(r["checks"]["margin24_all_host_columns_materialized"])

    def test_rejects_authoritative_state_change(self):
        log, p8, control, oracle, state = self.fixture()
        changed = dict(state)
        changed["progress"] = 4
        r = MOD.analyze_margin(24, log, p8, oracle, control, state, changed)
        self.assertFalse(r["accepted"])
        self.assertFalse(r["checks"]["margin24_protected_state_equal"])


if __name__ == "__main__":
    unittest.main()
