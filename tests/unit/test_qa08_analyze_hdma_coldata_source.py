"""Strict synthetic log interpretation only, not another original-native run."""
import json
from pathlib import Path
import tempfile
import unittest

from tools import qa08_analyze_hdma_coldata_source as hdma


def accepted():
    return {
        "guest_frame":2208,
        "full_guest_CRC_equal":2473,
        "native_render_live_fixed_RGB15_by_row":{
            "50":"0x000F","162":"0x0260"
        },
        "native_main_BG3_subscreen_OBJ_palette_colour_confirmed_at_two_pixels":True,
    }


def event(**overrides):
    values={
        "frame":2208,"tagframe":2208,"line":111,
        "channel":5,"bbus":"32","value":"2F","src":"7E:2060",
        "mode":0,"indirect":0,"table":"2061","bank":"7E",
        "fixed15":"000F",
    }
    values.update(overrides)
    return (
        f"UR_QA08_HDMA_COLDATA frame={values['frame']} "
        f"tagframe={values['tagframe']} line={values['line']} "
        f"channel={values['channel']} bbus={values['bbus']} "
        f"value={values['value']} src={values['src']} "
        f"mode={values['mode']} indirect={values['indirect']} "
        f"table={values['table']} bank={values['bank']} "
        f"fixed15={values['fixed15']}"
    )


class NativeHdmaSourceReaderTests(unittest.TestCase):
    def test_exact_observed_write_and_real_pixel_receipt(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            src=root/"native.log"
            report=root/"accepted.json"
            report.write_text(json.dumps(accepted()))
            src.write_text(event()+"\n")
            output=hdma.parse(src,report)
            self.assertEqual(output["direct_native_HDMA_COLDATA_written_bytes"],1)
            self.assertEqual(output["HDMA_channels_recorded"],{5:1})
            self.assertEqual(output["records"][0]["A_bus_source"],"7E:2060")
            self.assertEqual(output["records"][0]["selector_R_G_B"],[True,False,False])
            self.assertFalse(output["pixel_row_to_specific_HDMA_channel_causality_proven"])
            self.assertFalse(output["physical_SNES_HDMA_timing_proven"])

    def test_malformed_frame_and_partial_provenance_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            src=root/"native.log"
            report=root/"accepted.json"
            report.write_text(json.dumps(accepted()))
            for line in (event(frame=2207),event(channel=9),
                         event(bbus="21"), event(tagframe=2210),
                         event(fixed15="FFFF"),event(mode=9),
                         event(line=262)):
                src.write_text(line+"\n")
                with self.assertRaises(ValueError):
                    hdma.parse(src,report)
            src.write_text(event()+"\n"+'UR_QA08_HDMA_COLDATA_OVERFLOW frame=2208 limit=2048\n')
            with self.assertRaisesRegex(ValueError,"truncated"):
                hdma.parse(src,report)
            src.write_text(event()+"\n")
            prior=accepted();prior["full_guest_CRC_equal"]=2472
            report.write_text(json.dumps(prior))
            with self.assertRaisesRegex(ValueError,"gate missing"):
                hdma.parse(src,report)

    def test_no_coldatabytes_is_not_source_evidence(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            src=root/"native.log"
            report=root/"accepted.json"
            report.write_text(json.dumps(accepted()))
            src.write_text("no original native HDMA bytes yet\n")
            with self.assertRaisesRegex(ValueError,"zero or truncated"):
                hdma.parse(src,report)


if __name__=="__main__":
    unittest.main()
