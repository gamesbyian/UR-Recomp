import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "progression_acceptance", ROOT / "tools/analyze_progression_sram_acceptance.py")
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MOD)
MODEL = json.loads((ROOT / "analysis/data/progression-model.json").read_text())


class ProgressionAcceptanceTests(unittest.TestCase):
    def test_checksum_matches_known_word_sum_shape(self):
        data = bytearray(8192)
        layout = MOD.layout(MODEL)
        for i in range(layout["checksum_words"]):
            off = layout["checksum_start"] + i * 2
            data[off:off + 2] = (i + 1).to_bytes(2, "little")
        self.assertEqual(
            MOD.checksum(data, MODEL),
            sum(range(1, layout["checksum_words"] + 1)) & 0xFFFF,
        )

    def test_region_changes_reports_exact_offsets(self):
        layout = MOD.layout(MODEL)
        a = bytearray(8192)
        b = bytearray(a)
        b[layout["medal_start"]] = 1
        b[layout["medal_start"] + 17] = 2
        self.assertEqual(
            MOD.region_changes(a, b, layout["medal_start"], layout["medal_end"]),
            [
                {"offset": layout["medal_start"], "before": 0, "after": 1},
                {"offset": layout["medal_start"] + 17, "before": 0, "after": 2},
            ],
        )

    def test_tier_prediction_comes_from_model_thresholds(self):
        layout = MOD.layout(MODEL)
        data = bytearray(8192)
        rider = 3
        stride = MODEL["medal_matrix"]["row_stride"]
        for row in range(4):
            data[layout["medal_start"] + row * stride + rider] = 1
        self.assertEqual(MOD.predict_tier(MODEL, data, rider), 1)
        for row in range(6):
            data[layout["medal_start"] + row * stride + rider] = 2
        self.assertEqual(MOD.predict_tier(MODEL, data, rider), 2)
        for row in range(8):
            data[layout["medal_start"] + row * stride + rider] = 3
        self.assertEqual(MOD.predict_tier(MODEL, data, rider), 3)


if __name__ == "__main__":
    unittest.main()
