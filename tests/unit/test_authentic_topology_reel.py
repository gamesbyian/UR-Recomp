"""ROM-free admission tests for authentic three-topology recruiting footage.

Tests do not pretend source videos exist. Only verify the independent
human/model visual review contract and the source-locked guest proof policy.
"""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools/showcase/assemble_authentic_topology_reel.py"
SPEC = importlib.util.spec_from_file_location("authentic_topology_montage", SCRIPT)
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)

SOURCES = (
    ("looper-p1-leads", "Looper", "loop"),
    ("megajump-p2-leads", "MegaJump", "ramp"),
    ("hill-climb-p2-leads", "Hill Climb", "hill"),
)


def fixture():
    ledger = {"schema": m.LEDGER, "routes": {}}
    review = {
        "schema": m.SCHEMA, "reviewer": "Independent QA reviewer",
        "review_method": "human_video_screening",
        "asserts_source_sessions_are_distinct": True,
        "shots": [],
    }
    for name, course, feature in SOURCES:
        ledger["routes"][name] = {
            "movie": f"native-{name}-900f.mp4",
            "course": course,
            "sha256": "0" * 63 + str(len(name) % 10),
            "capture_frame_start_end": [2200,3099],
            "real_guest_world_position_witnesses": [
                {"raw_abs_x_difference": 78, "raw_abs_y_difference": 0},
                {"raw_abs_x_difference": 90, "raw_abs_y_difference": 0},
                {"raw_abs_x_difference": 144, "raw_abs_y_difference": 4}
            ],
        }
        review["shots"].append({
            "route": name,
            "source_sha256": ledger["routes"][name]["sha256"],
            "observed_feature": feature,
            "first_source_ordinal": 210,
            "frame_count": 240,
            "source_gameplay_visually_observed": True,
            "full_two_player_raster_visible": True,
            "two_racers_visibly_separated": True,
            "source_video_guest_state_modified": False,
            "observation": "Actual original unaltered course geometry traversed by both independently moving racers in the verified footage; original HUD visible.",
        })
    return ledger, review


class AuthenticTopologyReelGatesTest(unittest.TestCase):
    def test_complete_true_loop_ramp_hill_visual_gate(self):
        a,b=fixture()
        accepted=m.accepted_shots(a,b)
        self.assertEqual([s["observed_feature"] for s in accepted],
                         ["loop","ramp","hill"])
        self.assertEqual([s["first_guest_frame"] for s in accepted],
                         [2410]*3)
        self.assertEqual([s["last_guest_frame"] for s in accepted],
                         [2649]*3)

    def test_missing_any_of_three_real_features_is_rejected(self):
        a,b=fixture()
        for remove in range(3):
            _,c=fixture()
            del c["shots"][remove]
            with self.subTest(missing=remove), self.assertRaises(m.AdmissionError):
                m.accepted_shots(a,c)

    def test_cannot_call_a_course_name_visual_evidence(self):
        a,b=fixture()
        for field,value in [
            ("source_gameplay_visually_observed",False),
            ("two_racers_visibly_separated",False),
            ("full_two_player_raster_visible",False),
            ("source_video_guest_state_modified",True),
            ("observation","Jump!")
        ]:
            _,c=fixture()
            c["shots"][0][field]=value
            with self.subTest(field=field), self.assertRaises(m.AdmissionError):
                m.accepted_shots(a,c)

    def test_reject_wrong_clip_identity_or_witness(self):
        for variant in ("wrongsha","no_player_delta","no_capture"):
            a,b=fixture()
            if variant=="wrongsha":
                b["shots"][1]["source_sha256"]="z"*64
            elif variant=="no_player_delta":
                a["routes"]["looper-p1-leads"]["real_guest_world_position_witnesses"] = [
                    {"raw_abs_x_difference":0,"raw_abs_y_difference":0}]*3
            else:
                a["routes"]["looper-p1-leads"]["capture_frame_start_end"]=[2199,3000]
            with self.subTest(variant=variant), self.assertRaises(m.AdmissionError):
                m.accepted_shots(a,b)

    def test_reject_reordered_or_out_of_range_media_spans(self):
        for first,count in [(-1,240),(0,179),(800,240),(0,421),(True,200)]:
            a,b=fixture()
            b["shots"][1]["first_source_ordinal"]=first
            b["shots"][1]["frame_count"]=count
            with self.subTest(start=first,count=count), self.assertRaises(m.AdmissionError):
                m.accepted_shots(a,b)

    def test_cannot_mix_distinct_sessions_without_disclosure(self):
        a,b=fixture()
        b["asserts_source_sessions_are_distinct"]=False
        with self.assertRaises(m.AdmissionError):
            m.accepted_shots(a,b)
        b["asserts_source_sessions_are_distinct"]=True
        b["review_method"]="automated_input_only"
        with self.assertRaises(m.AdmissionError):
            m.accepted_shots(a,b)


if __name__ == "__main__":
    unittest.main()
