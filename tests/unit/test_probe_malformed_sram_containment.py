import json
import os
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import probe_malformed_sram_containment as probe  # noqa: E402

# tests/native/run_malformed_sram_boot_acceptance.sh points this at a fresh
# native run so CI checks the same expectations as the committed evidence.
EVIDENCE = pathlib.Path(
    os.environ.get(
        "UR_MALFORMED_SRAM_EVIDENCE",
        ROOT / "analysis" / "generated" / "malformed-sram-containment.json",
    )
)

EXPECTED_GUEST = {
    "valid_progressed_control": "accepted_with_stock_boot_writes",
    "truncated_half": "accepted_with_stock_boot_writes",
    "empty_file": "reformatted_to_fresh_image",
    "oversized": "accepted_with_stock_boot_writes",
    "medal_checksum_mismatch": "accepted_with_stock_boot_writes",
    "records_checksum_mismatch": "accepted_with_stock_boot_writes",
    "medal_value_out_of_range": "accepted_with_stock_boot_writes",
    "record_value_out_of_range": "accepted_with_stock_boot_writes",
    "tour_flag_out_of_range": "accepted_with_stock_boot_writes",
    "play_mode_out_of_range": "accepted_with_stock_boot_writes",
    "header_signature_damaged": "reformatted_to_fresh_image",
}


class SynthesisTests(unittest.TestCase):
    def setUp(self):
        self.clean = probe.CLEAN_SRAM.read_bytes()
        self.images = probe.synthesize(self.clean)
        self.base = self.images["valid_progressed_control"]

    def test_clean_and_base_are_checksum_valid(self):
        self.assertEqual(probe.checksums_valid(self.clean), {"medal": True, "records": True})
        self.assertEqual(probe.checksums_valid(self.base), {"medal": True, "records": True})
        self.assertEqual(self.base[probe.MEDAL_MIKE_CRAWLER], 2)
        self.assertEqual(probe.word(self.base, probe.RECORDS), 3000)

    def test_each_class_is_malformed_in_exactly_its_intended_way(self):
        im = self.images
        self.assertEqual(len(im["truncated_half"]), 4096)
        self.assertEqual(im["empty_file"], b"")
        self.assertEqual(im["oversized"][:8192], self.base)
        self.assertEqual(len(im["oversized"]), 8208)
        self.assertEqual(probe.checksums_valid(im["medal_checksum_mismatch"]),
                         {"medal": False, "records": True})
        self.assertEqual(probe.checksums_valid(im["records_checksum_mismatch"]),
                         {"medal": True, "records": False})
        for name in ("medal_value_out_of_range", "record_value_out_of_range",
                     "tour_flag_out_of_range", "play_mode_out_of_range",
                     "header_signature_damaged"):
            self.assertEqual(probe.checksums_valid(im[name]), {"medal": True, "records": True}, name)
        self.assertEqual(im["medal_value_out_of_range"][probe.MEDAL_MIKE_CRAWLER], 7)
        self.assertEqual(probe.word(im["record_value_out_of_range"], probe.RECORDS), 0xFFFF)
        self.assertEqual(im["tour_flag_out_of_range"][probe.TOUR_FLAGS], 0xFF)
        self.assertEqual(im["play_mode_out_of_range"][probe.PLAY_MODE], 0x7F)
        self.assertNotEqual(im["header_signature_damaged"][:12], self.clean[:12])
        self.assertEqual(im["header_signature_damaged"][12:], self.base[12:])

    def test_synthesis_is_deterministic(self):
        again = probe.synthesize(self.clean)
        self.assertEqual({k: probe.sha256(v) for k, v in again.items()},
                         {k: probe.sha256(v) for k, v in self.images.items()})

    def test_classify_distinguishes_reformat_accept_and_partial(self):
        fresh = self.clean
        after = bytearray(self.base)
        after[0x1FFF] = 0x56
        after[probe.PLAY_MODE] = 0
        self.assertEqual(
            probe.classify(self.base, bytes(after), fresh)["guest_outcome"],
            "accepted_with_stock_boot_writes")
        self.assertEqual(
            probe.classify(self.images["header_signature_damaged"], fresh,
                           fresh)["guest_outcome"],
            "reformatted_to_fresh_image")
        after[probe.MEDAL_MIKE_CRAWLER] = 0
        result = probe.classify(self.base, bytes(after), fresh)
        self.assertEqual(result["guest_outcome"], "partial_or_other")
        self.assertFalse(result["input_progress_kept"])
        # A short read leaves the zeroed cart-RAM tail in place.
        self.assertEqual(probe.framework_load(b"\x01\x02"), b"\x01\x02" + bytes(8190))


class EvidenceTests(unittest.TestCase):
    def test_committed_evidence_matches_synthesis_and_expected_outcomes(self):
        report = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        self.assertEqual(report["schema"], "ur-recomp-malformed-sram-containment-v1")
        images = probe.synthesize(probe.CLEAN_SRAM.read_bytes())
        self.assertEqual(set(report["cases"]), set(EXPECTED_GUEST))
        for mode in ("authentic", "modern"):
            self.assertTrue(report["fresh_format"][mode]["equals_clean_stock_sram"], mode)
        for name, expected in EXPECTED_GUEST.items():
            case = report["cases"][name]
            self.assertEqual(case["input_sha256"], probe.sha256(images[name]), name)
            for mode in ("authentic", "modern"):
                self.assertEqual(case[mode]["guest_outcome"], expected, (mode, name))
                self.assertTrue(case[mode]["persisted_on_exit_equals_live"], (mode, name))
                self.assertEqual(case[mode]["input_progress_kept"],
                                 expected != "reformatted_to_fresh_image", (mode, name))
            self.assertTrue(case["modern"]["host_profile_read_only"], name)
            self.assertFalse(case["modern"]["host_profile_created"], name)
            # Stock never repairs a checksum at boot.
            if name in ("medal_checksum_mismatch", "records_checksum_mismatch"):
                self.assertEqual(case["authentic"]["after_checksums_valid"],
                                 case["input_checksums_valid"], name)


if __name__ == "__main__":
    unittest.main()
