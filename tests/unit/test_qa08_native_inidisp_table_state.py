"""Adversarial live native channel7 descriptor/header discriminator."""
import copy
import json
from pathlib import Path
import unittest

from tools import check_qa08_native_inidisp_table_state as source
from tools import qa08_patch_hdma_coldata_source as patch

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "analysis/data/qa08-original-native-2p-brightness-split-channel7-handoff-20261014.json"


def retained():
    return json.loads(EVIDENCE.read_text(encoding="utf-8"))


# Entirely synthetic fixture. Native channel7 descriptor bytes have never
# been separately captured. The example counts are a MODEL PREDICTION,
# and are not treated as empirical original/native values.
def rows(counts=("6F", "6F", "02", "6F")):
    tags = (0, 2, 113, 115)
    src = ("2065", "2065", "2067", "2069")
    values = ("0F", "0F", "00", "0F")
    lines = []
    for i, tag in enumerate(tags):
        lines.append(
            f"UR_QA08_HDMA_INIDISP frame=2208 tagframe=2208 line={tag} "
            f"channel=7 bbus=00 value={values[i]} src=7E:{src[i]} "
            f"mode=0 indirect=0 table={int(src[i],16)+1:04X} bank=7E "
            f"live_inidisp={values[i]}")
        lines.append(
            f"UR_QA08_HDMA_INIDISP_TABLE_STATE frame=2208 tagframe=2208 "
            f"line={tag} channel=7 value={values[i]} src=7E:{src[i]} "
            f"table={int(src[i],16)+1:04X} count={counts[i]} transfer=1 "
            f"live_header={counts[i]} live_inidisp={values[i]}")
    return lines


class NativeChannel7DescriptorTests(unittest.TestCase):
    def test_true_source_anchor_and_falsifiable_model(self):
        self.assertIn("UR_QA08_HDMA_INIDISP_TABLE_STATE", patch.PATCH)
        self.assertIn("snes_read(dma->snes,", patch.PATCH)
        self.assertIn("(uint16_t)(aAdr - 1)", patch.PATCH)
        self.assertIn("ch->repCount", patch.PATCH)
        self.assertIn("ch->doTransfer", patch.PATCH)
        self.assertIn("snes_writeBBus(dma->snes, bAdr, val);", patch.PATCH)
        self.assertNotIn("ch->repCount =", patch.PATCH)

    def test_synthetic_expected_counterfactual_support(self):
        report = source.check("\n".join(rows()), retained())
        self.assertEqual(report["actual_after_BBUS_source_writes_checked"], 4)
        self.assertEqual(report["actual_first_two_distinct_descriptor_counts"], [111, 2])
        self.assertTrue(report["first_prime_and_duplicate_regular_transfer_same_rep_count"])
        self.assertTrue(report["model_first_two_lengths_111_2_supported_by_native_actual_counts"])
        self.assertFalse(report["native_rendering_changed_by_probe"])
        self.assertFalse(report["original_source_65816_channel7_header_writer_located"])

    def test_valid_observed_negative_disproves_specific_model(self):
        # Retained source already accepted 4 writes, but *does not* pin actual
        # descriptor headers. A different nonzero header must be reported as
        # falsifying the 111/2 inference, NOT silently rejected/retrofitted.
        report = source.check("\n".join(rows(("70", "70", "02", "6F"))), retained())
        self.assertEqual(report["actual_first_two_distinct_descriptor_counts"], [112, 2])
        self.assertFalse(report["model_first_two_lengths_111_2_supported_by_native_actual_counts"])

    def test_source_and_header_tampering_rejected(self):
        for old, new in (
            ("frame=2208", "frame=2209"),
            ("tagframe=2208", "tagframe=2209"),
            ("line=113", "line=114"),
            ("channel=7", "channel=5"),
            ("bbus=00", "bbus=31"),
            ("value=00", "value=80"),
            ("src=7E:2067", "src=7E:2068"),
            ("table=2068", "table=2069"),
            ("bank=7E", "bank=80"),
            ("mode=0", "mode=1"),
            ("indirect=0", "indirect=1"),
            ("live_inidisp=00", "live_inidisp=0F"),
            ("count=02", "count=00"),
            ("live_header=02", "live_header=00"),
            ("transfer=1", "transfer=3"),
        ):
            with self.subTest(field=old):
                log = "\n".join(rows()).replace(old, new)
                with self.assertRaises(ValueError):
                    source.check(log, retained())

    def test_incomplete_or_duplicate_actual_source_rejected(self):
        log = rows()
        with self.assertRaisesRegex(ValueError, "one-to-one"):
            source.check("\n".join(log[:-1]), retained())
        with self.assertRaisesRegex(ValueError, "one-to-one"):
            source.check("\n".join(log + [log[-1]]), retained())

    def test_reject_fake_independent_reference(self):
        wrong = copy.deepcopy(retained())
        wrong["native"]["run_id"] = 999
        with self.assertRaisesRegex(ValueError, "handoff changed"):
            source.check("\n".join(rows()), wrong)
        wrong = copy.deepcopy(retained())
        wrong["finished_source_frame_reference"]["mismatched_pixels_by_row"][1]["y"] = 112
        with self.assertRaises(ValueError):
            source.check("\n".join(rows()), wrong)


if __name__ == "__main__":
    unittest.main()
