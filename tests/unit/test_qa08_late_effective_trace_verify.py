"""Adversarial ROM-free source-stage QA08 effective observer log tests."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools import qa08_late_effective_trace_verify as witness


def source(x=70, y=58, frame=5184, sub=0, word="56b5", direct=0):
    return (
        f"UR_QA08_LATE_PPU_SOURCE frame={frame} x={x} logical_y={y} "
        f"ppu_line={y+1} sub={sub} layer=0 directcolor={direct} "
        f"index=6c selected_rgb555={word} cgram_index_word={word} "
        "cgram6c=56b5 cgram6d=4a52 cgram6e=4631 cgram6f=4210 "
        "inidisp=0f cgadsub=00 cgwsel=00"
    )


def final(x=70, y=58, frame=5184, rgb="136,136,136"):
    return (
        f"UR_QA08_LATE_PPU_FINAL frame={frame} x={x} logical_y={y} "
        f"ppu_line={y+1} RGB8={rgb} inidisp=0f fixed=0000 tm=01 ts=00"
    )


class LateEffectiveSourceProof(unittest.TestCase):
    def test_typed_production_source_and_final_logger_rows(self):
        kind, row = witness.parse_row(source())
        self.assertEqual(kind, "source")
        self.assertEqual(row["cgram_index_word"], 0x56b5)
        self.assertEqual(row["index"], 0x6c)
        self.assertEqual(row["ppu_line"], 59)
        kind, row = witness.parse_row(final())
        self.assertEqual(kind, "final")
        self.assertEqual(row["RGB8"], (136,136,136))
        self.assertIsNone(witness.parse_row("unrelated Windows output"))

    def test_all_eight_authenticated_guest5184_pixels(self):
        lines = "\n".join(source(x,y) + "\n" + final(x,y)
                          for x,y in witness.POINTS)
        result = witness.summarize_trace(lines)
        self.assertEqual(result["guest5184_anchor_count"], 8)
        self.assertEqual(result["bounded_source_observations"], 8)
        self.assertEqual(result["bounded_final_observations"], 8)
        self.assertEqual(result["anchors"][0]["main_actual_resolved_rgb555"], "56b5")
        self.assertEqual(result["anchors"][0]["new_native_final_RGB5"], [17]*3)
        self.assertFalse(result["instrumentation_noninterference_proven_by_text"])
        self.assertFalse(result["QA08_QA10_or_release_authorized"])

    def test_full_window_requires_every_main_source_and_composed_pixel(self):
        rows = []
        for frame in range(5176, 5187):
            for x, y in witness.POINTS:
                rows.extend((source(x, y, frame=frame),
                             final(x, y, frame=frame)))
        full = "\n".join(rows)
        result = witness.summarize_trace(full, require_full_window=True)
        self.assertEqual(result["bounded_source_observations"], 88)
        self.assertEqual(result["bounded_final_observations"], 88)
        with self.assertRaisesRegex(ValueError, "incomplete 11-frame"):
            witness.summarize_trace("\n".join(rows[:-1]),
                                    require_full_window=True)
        with self.assertRaisesRegex(ValueError, "incomplete 11-frame"):
            witness.summarize_trace("\n".join(rows[1:]),
                                    require_full_window=True)

    def test_mixed_renderer_across_different_frames_refused(self):
        rows = []
        for frame in range(5176, 5187):
            for x, y in witness.POINTS:
                rows.extend((source(x, y, frame=frame),
                             final(x, y, frame=frame)))
        rows[0] = rows[0].replace("UR_QA08_LATE_PPU_SOURCE ",
                                  "UR_QA08_LATE_SPAN_SOURCE ")
        with self.assertRaisesRegex(ValueError, "mixed renderer identities"):
            witness.summarize_trace("\n".join(rows),
                                    require_full_window=True)

    def test_duplicate_missing_and_changing_selected_CGRAM_rejected(self):
        lines = "\n".join(source(x,y) + "\n" + final(x,y)
                          for x,y in witness.POINTS)
        with self.assertRaisesRegex(ValueError, "duplicate"):
            witness.summarize_trace(lines + "\n" + source())
        with self.assertRaisesRegex(ValueError, "missing guest5184"):
            witness.summarize_trace(lines.replace(final(), "absent"))
        with self.assertRaisesRegex(ValueError, "selected colour disagrees"):
            witness.parse_row(source().replace("selected_rgb555=56b5",
                                               "selected_rgb555=4210"))

    def test_indexed_cgram_word_must_match_logged_slot_on_both_renderers(self):
        for renderer in ("UR_QA08_LATE_PPU_SOURCE ", "UR_QA08_LATE_SPAN_SOURCE "):
            row = source().replace("UR_QA08_LATE_PPU_SOURCE ", renderer)
            with self.subTest(renderer=renderer):
                with self.assertRaisesRegex(ValueError, "indexed effective CGRAM"):
                    witness.parse_row(row.replace("cgram6c=56b5", "cgram6c=4a52"))
                self.assertEqual(witness.parse_row(row)[1]["index"], 0x6c)
                direct = row.replace("directcolor=0", "directcolor=1")
                witness.parse_row(direct.replace("cgram6c=56b5", "cgram6c=4a52"))

    def test_directcolor_is_not_mislabeled_CGRAM(self):
        kind,row=witness.parse_row(
            source(direct=1).replace("selected_rgb555=56b5",
                                     "selected_rgb555=4210"))
        self.assertEqual(kind, "source")
        self.assertEqual(row["directcolor"], 1)
        with self.assertRaisesRegex(ValueError, "direct color cannot"):
            witness.parse_row(source(direct=1).replace("layer=0", "layer=4"))

    def test_host_frame_source_y_channels_and_bounds_fail_closed(self):
        for row in (
            source(frame=5175), source(x=71), source().replace("ppu_line=59","ppu_line=58"),
            source().replace("index=6c", "index=abcde"),
            source().replace("sub=0", "sub=9"),
            final().replace("RGB8=136,136,136", "RGB8=300,0,0"),
            source()+" stray", source().replace("index=6c","index=6c index=6c")
        ):
            with self.subTest(row=row[:65]):
                with self.assertRaises(ValueError):
                    witness.parse_row(row)
        with self.assertRaisesRegex(ValueError, "unbounded"):
            witness.summarize_trace("x" * 24_000_001)

    def test_real_span_prefix_and_explicit_renderer_identity(self):
        line = source().replace("UR_QA08_LATE_PPU_SOURCE ",
                                "UR_QA08_LATE_SPAN_SOURCE ")
        end = final().replace("UR_QA08_LATE_PPU_FINAL ",
                              "UR_QA08_LATE_SPAN_FINAL ")
        k, row = witness.parse_row(line)
        self.assertEqual((k,row["renderer"]),("source","span"))
        k, row = witness.parse_row(end)
        self.assertEqual((k,row["renderer"]),("final","span"))
        lines = "\n".join(
            source(x,y).replace("UR_QA08_LATE_PPU_SOURCE ","UR_QA08_LATE_SPAN_SOURCE ")
            + "\n" + final(x,y).replace("UR_QA08_LATE_PPU_FINAL ","UR_QA08_LATE_SPAN_FINAL ")
            for x,y in witness.POINTS)
        result = witness.summarize_trace(lines)
        self.assertEqual(result["observed_span_anchors"],8)
        self.assertTrue(result["all_anchors_actual_span_renderer"])
        with self.assertRaisesRegex(ValueError,"mixed renderer identities|different renderer"):
            witness.summarize_trace(lines.replace(
                "UR_QA08_LATE_SPAN_FINAL ","UR_QA08_LATE_PPU_FINAL ",1))

    def test_host_object_override_is_explicit_negative_evidence(self):
        with self.assertRaisesRegex(ValueError,"host OBJ palette override"):
            witness.parse_row("UR_QA08_LATE_SPAN_OBJECT_OVERRIDE "
                              "frame=5184 x=70 logical_y=58 layer=4 index=6c "
                              "selected_rgb555=56b5")
        with self.assertRaisesRegex(ValueError,"host OBJ palette override"):
            witness.summarize_trace(
                source() + "\n" + final() + "\nUR_QA08_LATE_SPAN_OBJECT_OVERRIDE x=70")

    def test_missing_genuine_CRC_never_promoted_to_source_witness(self):
        with patch.object(witness.Path,"read_bytes",return_value=b"forged"):
            with self.assertRaisesRegex(ValueError,"SHA mismatch"):
                witness.verify(Path("on"),Path("off"),Path("original"),
                               Path("CRC-on"),Path("CRC-off"),
                               Path("route-on"),Path("route-off"),Path("native-outer"))

    def test_archived_native_P7_identity_is_independently_bound(self):
        self.assertEqual(witness.ARCHIVED_NATIVE_OUTER,
                         "832c08263e2d3013d5b15df82b2b0574fabfd3114194b7cbef9f6bb1b2959727")
        self.assertEqual(witness.ARCHIVED_NATIVE_INNER,
                         "c36fdd0238735e739219b013d25665e42a008a7827ee97631a322217c9f4f0cd")
        self.assertEqual(witness.ARCHIVED_NATIVE_5184_P7,
                         "8dae60c1433aa26cd6edc20edda980d1dec17e8935a799d7edc6d0878ae387a8")
        self.assertEqual(witness.P7_HEADER,
                         b"P7\nWIDTH 256\nHEIGHT 224\nDEPTH 4\nMAXVAL 255\n"
                         b"TUPLTYPE RGB_ALPHA\nENDHDR\n")
        with patch.object(witness.Path, "read_bytes", return_value=b"forged"):
            with self.assertRaisesRegex(ValueError, "outer ZIP SHA"):
                witness.verify_archived_native_pixels(Path("fake.zip"))

    def test_historical_sha_and_negative_evidence_gates(self):
        self.assertEqual(witness.ORIGINAL_ZIP,
                         "72b7b152d08d8abb3636053bfd132db64926a5bf188f4dbba7e30b20d9583e9e")
        self.assertEqual(witness.ORIGINAL_5183_BGRX,
                         "f0ee58c682776592d8a93003a42c508629c49973b206d6a6da2c71ec9dc993b7")
        self.assertEqual(len(witness.POINTS), 8)
        self.assertEqual(set(witness.POINTS),set(witness.EXPECTED_GRAY))
        self.assertEqual(set(witness.EXPECTED_GRAY.values()),
                         {(15,20),(16,15),(17,16),(20,17)})


if __name__ == "__main__":
    unittest.main()
