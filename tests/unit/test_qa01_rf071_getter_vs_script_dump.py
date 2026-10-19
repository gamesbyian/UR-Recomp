"""ROM-free adversarial tests for actual RF071 physical read phase projection.

Fixture rows are deliberately NONAUTHENTIC. A separate offline Actions job
reopens the real source ZIP, source original SMV, and six actual WRAM images.
"""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))

import qa01_rf071_getter_vs_script_dump as consumer


def example():
    return {
        "ordinal": 1,
        "bus_kind": "rw",
        "host_frame": 1018,
        "physical_bus_address": "00:01ED",
        "returned": "9726",
        "source_getset_scanline": 100,
        "source_getset_cycles": 333,
        "post_call_scanline": 100,
        "post_call_cycles": 341,
        "real_getset_entry_PC_context": "82:9000",
    }


class OriginalRealGetterProjection(unittest.TestCase):
    def test_actual_source_getset_entry_not_forged_post_call_or_opfetch(self):
        report=consumer.project_getset([example()])
        self.assertEqual(report,[{
            "frame":1018,"base":0x01ed,"width":2,"returned":0x9726,
            "source_getset_scanline":100,"source_getset_cycles":333,
            "source_PC_context_only":"82:9000"}])
        self.assertEqual(len(report),1)

    def test_real_video_scanline_crossing_is_legal_with_monotonic_vh(self):
        obj=example()
        obj["source_getset_scanline"]=100
        obj["source_getset_cycles"]=1320
        obj["post_call_scanline"]=101
        obj["post_call_cycles"]=14
        self.assertEqual(len(consumer.project_getset([obj])),1)

    def test_bad_read_identity_clock_and_order_are_rejected(self):
        for name, key, value in (
            ("wrong_kind", "bus_kind", "write"),
            ("word_size_forged", "returned", "26"),
            ("wrong_bank", "physical_bus_address", "7E:01ED"),
            ("outside_stack", "physical_bus_address", "00:0FFF"),
            ("missing_frame", "host_frame", "1018"),
            ("negative_cycle", "source_getset_cycles", -1),
            ("return_precedes_read", "post_call_cycles", 332),
            ("duplicate_ordinal", "ordinal", 2),
        ):
            with self.subTest(name=name):
                record={**example(),key:value}
                with self.assertRaises(ValueError):
                    consumer.project_getset([record])

    def test_all_actual_original_source_reads_need_unique_ordinals(self):
        e1=example()
        e2={**e1,"ordinal":2,"physical_bus_address":"00:01EF",
            "returned":"D482"}
        self.assertEqual(len(consumer.project_getset([e1,e2])),2)
        with self.assertRaises(ValueError):
            consumer.project_getset([e1,e1])
        with self.assertRaises(ValueError):
            consumer.project_getset([])


if __name__=="__main__":
    unittest.main()
