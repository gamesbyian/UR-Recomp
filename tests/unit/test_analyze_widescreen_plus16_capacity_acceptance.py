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


class WidescreenCapacityTests(unittest.TestCase):
    def fixture(self, margin: int):
        host_count = margin // 8 - 1
        p8 = []
        log = []
        control = []
        oracle = []
        for i, camx in enumerate((100, 101)):
            primary_edge = 0x0D80 + i * 10
            guest_edge = primary_edge + 1
            payload = PAYLOAD_A if i == 0 else PAYLOAD_B
            p8.append({"camx": camx, "edge": guest_edge, "count": 16, "payload": payload})
            log.append(
                f"URWS_PRIMARY margin={margin} camx={camx} edge={primary_edge:04X} "
                f"count=16 payload={payload} camy=0 edgey=FFFF county=0\n"
            )
            if i:
                if margin == 16:
                    log.append("URWS_CLEANUP16 shadows=1\n")
                elif margin == 24:
                    log.append("URWS_CLEANUP24 shadows=2\n")
                else:
                    log.append(f"URWS_CLEANUP_EXT margin={margin} shadows={host_count}\n")
            if margin == 16:
                log.append(
                    f"URWS_PREP16 camx={camx} edge={guest_edge:04X} count=16 "
                    f"payload={payload} camy=0\n"
                )
            elif margin == 24:
                log.append(
                    f"URWS_PREP24 camx={camx} edge={guest_edge:04X} count=16 "
                    f"payload={payload} camy=0\n"
                )
            else:
                log.append(
                    f"URWS_PREP_EXT margin={margin} camx={camx} edge={guest_edge:04X} "
                    f"count=16 payload={payload} camy=0\n"
                )
            for h in range(host_count):
                col = h + 2
                edge = primary_edge + col
                finex = 18 + h + i
                if margin == 16:
                    prefix = "URWS_SHADOW16 provider=course-runtime"
                elif margin == 24:
                    prefix = "URWS_SHADOW24 provider=course-runtime"
                else:
                    prefix = f"URWS_SHADOW_EXT provider=course-runtime margin={margin}"
                log.append(
                    f"{prefix} column={col} camx={camx} edge={edge:04X} count=16 "
                    f"payload={payload} camy=0 finex={finex} finey=0 edgey=FFFF county=0\n"
                )
                oracle.append({
                    "camx": camx + 20 + h,
                    "edge": edge,
                    "count": 16,
                    "payload": payload,
                    "camy": 0,
                    "edgey": 0xFFFF,
                    "county": 0,
                    "finey": 0,
                })
            control.append({
                "camx": camx,
                "edge": primary_edge,
                "count": 16,
                "payload": payload,
                "camy": 0,
                "edgey": 0xFFFF,
                "county": 0,
                "finey": 0,
            })
        state = {"player_x": 1, "camera_x": 2, "progress": 3}
        return "".join(log), p8, control, oracle, state

    def test_accepts_two_host_columns_with_no_guest_lane_growth(self):
        log, p8, control, oracle, state = self.fixture(24)
        r = MOD.analyze_margin(24, log, p8, oracle, control, state, dict(state))
        self.assertTrue(r["accepted"])
        self.assertEqual(r["expected_host_columns"], 2)
        self.assertEqual(r["counts"]["host_shadow_events"], 4)

    def test_accepts_seven_host_columns_at_plus64_probe_depth(self):
        log, p8, control, oracle, state = self.fixture(64)
        r = MOD.analyze_margin(64, log, p8, oracle, control, state, dict(state))
        self.assertTrue(r["accepted"])
        self.assertEqual(r["expected_host_columns"], 7)
        self.assertEqual(r["counts"]["host_shadow_events"], 14)
        self.assertTrue(r["checks"]["margin64_all_host_columns_materialized"])
        self.assertTrue(r["checks"]["margin64_ring_chain_adjacent"])
        self.assertTrue(r["checks"]["margin64_same_view_payloads_exact"])

    def test_rejects_missing_deep_host_column(self):
        log, p8, control, oracle, state = self.fixture(64)
        needle = (
            "URWS_SHADOW_EXT provider=course-runtime margin=64 column=8 camx=100 "
            "edge=0D88 count=16 payload=" + PAYLOAD_A +
            " camy=0 finex=24 finey=0 edgey=FFFF county=0\n"
        )
        log = log.replace(needle, "", 1)
        r = MOD.analyze_margin(64, log, p8, oracle, control, state, dict(state))
        self.assertFalse(r["accepted"])
        self.assertFalse(r["checks"]["margin64_all_host_columns_materialized"])

    def test_rejects_authoritative_state_change(self):
        log, p8, control, oracle, state = self.fixture(64)
        changed = dict(state)
        changed["progress"] = 4
        r = MOD.analyze_margin(64, log, p8, oracle, control, state, changed)
        self.assertFalse(r["accepted"])
        self.assertFalse(r["checks"]["margin64_protected_state_equal"])


if __name__ == "__main__":
    unittest.main()
