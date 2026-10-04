import unittest
from tools.evaluate_widescreen_capacity_probe import evaluate_probe

class EvaluateWidescreenCapacityProbeTest(unittest.TestCase):
    def test_accepts_observed_events_and_all_depths(self):
        generated = {"fixture":"vs-first-race","protected_state_equal_at_all_checkpoints":True,"geometry_accepted":True,"plus24_frame_geometry":[304,224]}
        lines=[]
        for player, events in ((1,2),(2,1)):
            for _ in range(events):
                lines.append(f"URWS_VS_MATERIALIZER margin=24 player={player} calibrated=1")
            for depth in (1,2):
                for _ in range(events):
                    lines.append(f"URWS_VS_SHADOW_EXT provider=course-runtime margin=24 player={player} depth={depth}")
        self.assertEqual(evaluate_probe(generated,"\n".join(lines),24)["outcome"], "accepted")

if __name__ == "__main__":
    unittest.main()
