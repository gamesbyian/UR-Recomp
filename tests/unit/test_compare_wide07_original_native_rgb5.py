"""Bounded source/original vs native image comparison regression controls."""
import hashlib
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import compare_wide07_original_native_rgb5 as cmp

SHA1 = "a" * 40
SHA2 = "b" * 40


def bitmap(width, height, pixels):
    stride = ((3 * width + 3) // 4) * 4
    chunks = []
    for y in reversed(range(height)):
        row = b"".join(bytes((b, g, r)) for r, g, b in pixels[y * width:(y + 1) * width])
        chunks.append(row + b"\0" * (stride - len(row)))
    payload = b"".join(chunks)
    return (struct.pack("<2sIHHI", b"BM", 54 + len(payload), 0, 0, 54) +
            struct.pack("<IiiHHIIiiII", 40, width, height, 1, 24, 0,
                        len(payload), 0, 0, 0, 0) + payload)


def fixtures(o, n):
    tags = cmp.TAGS
    original = [(4, 8, 12)] * (256 * 224)
    fixed = [(5, 9, 13)] * (256 * 224)
    wider = [(30, 30, 30)] * (342 * 224)
    for y in range(224):
        wider[y * 342 + 43:y * 342 + 299] = fixed[y * 256:(y + 1) * 256]
    orig_payload = bitmap(256, 224, original)
    fixed_payload = bitmap(256, 224, fixed)
    wide_payload = bitmap(342, 224, wider)
    ref_obs = {
        "schema": "ur-wide07-genuine-original-usa-ppu-capture/1",
        "source_sha": SHA1,
        "original_snes9x_executed": True,
        "checkpoints": {
            tag: {"framebuffer_sha256":cmp.sha(orig_payload),
                  "metadata":{"frame":1000 + i}}
            for i, tag in enumerate(tags)},
    }
    native_obs = {
        "schema": "ur-wide07-hosted-fixed-wide-matched-frames/1",
        "source_sha":SHA2,
        "frame_pairs":{
            tag:{"original_sha256":cmp.sha(fixed_payload),
                 "wide_sha256":cmp.sha(wide_payload),
                 "guest_frame":1010 + i}
            for i,tag in enumerate(tags[1:],start=1)},
    }
    original_members = {
        "evidence/original-usa-ppu-observation.json":json.dumps(ref_obs).encode(),
        "execution-receipt.json":json.dumps({"source_sha":SHA1,"execution_step_outcome":"success"}).encode(),
        **{"evidence/frames/" + tag + ".fb.bmp":orig_payload for tag in tags},
    }
    native_members = {
        "evidence/matched-centre-observation.json":json.dumps(native_obs).encode(),
        "execution-receipt.json":json.dumps({"source_sha":SHA2,"execution_step_outcome":"success"}).encode(),
        **{"evidence/original/" + tag + ".fb.bmp":fixed_payload for tag in tags},
        **{"evidence/16x9/" + tag + ".fb.bmp":wide_payload for tag in tags},
    }
    for path, members in ((o,original_members),(n,native_members)):
        with zipfile.ZipFile(path,"w",compression=zipfile.ZIP_DEFLATED) as z:
            for name,data in members.items():
                z.writestr(name,data)


class Wide07OriginalNativeTests(unittest.TestCase):
    def test_bmp24_bottom_up_and_alignment(self):
        values=[(1,2,3),(4,5,6),(7,8,9),(10,11,12)]
        self.assertEqual(cmp.bmp24(bitmap(2,2,values)),(2,2,values))
        with self.assertRaisesRegex(ValueError,"BMP"):
            cmp.bmp24(bitmap(2,2,values)[:-1])
        with self.assertRaisesRegex(ValueError,"BMP"):
            cmp.bmp24(b"wrong")

    def test_rgb5_ignores_small_rgb8_rounding(self):
        orig = [(4,8,12)] * (256*224)
        native = [(5,9,13)] * (256*224)
        result=cmp.compare_images(orig,native,native)
        self.assertEqual(result["rgb5_equal"],57344)
        self.assertEqual(result["rgb5_differing"],0)
        self.assertEqual(result["rgb8_differing"],57344)
        self.assertEqual(result["native_fixed_vs_wide_center_rgb5_differing"],0)
        self.assertEqual(result["max_absolute_rgb8_channel_delta"],1)

    def test_one_pixel_blue_overlay_displacement_is_reported_not_waived(self):
        background=(8,16,24)
        arrow=(107,107,255)
        source=[background]*(256*224)
        native=[background]*(256*224)
        source[80*256+40]=arrow
        native[79*256+40]=arrow
        outcome=cmp.compare_images(source,native,native)
        self.assertEqual(outcome["rgb5_differing"],2)
        self.assertTrue(outcome["blue_overlay_xor_exactly_covers_rgb5_differences"])
        self.assertEqual(outcome["blue_overlay_mask_shift_down_one_residual_pixels"],0)

    def test_genuine_artifact_shape_and_unreviewed_scope(self):
        with tempfile.TemporaryDirectory() as d:
            original=Path(d)/"original.zip"
            native=Path(d)/"native.zip"
            fixtures(original,native)
            result=cmp.analyze(original,native)
            self.assertEqual(result["original_source_sha"],SHA1)
            self.assertEqual(result["native_source_sha"],SHA2)
            self.assertEqual(result["checkpoints"]["ws-product-race"]["rgb5_differing"],0)
            self.assertEqual(result["checkpoints"]["ws-product-after-scroll"]["native_fixed_vs_wide_center_rgb5_differing"],0)
            self.assertFalse(result["original_widened_margin_oracle"])
            self.assertEqual(result["usa_course_credit"],0)
            self.assertEqual(result["windows_gate_credit"],0)

    def test_source_receipt_mutation_refused(self):
        with tempfile.TemporaryDirectory() as d:
            original=Path(d)/"original.zip"
            native=Path(d)/"native.zip"
            fixtures(original,native)
            with zipfile.ZipFile(original,"a") as z:
                # Deliberately repeated member: refuse ambiguity, never use last writer.
                with self.assertWarns(UserWarning):
                    z.writestr("evidence/frames/ws-product-race.fb.bmp",b"fake")
            with self.assertRaisesRegex(ValueError,"Duplicate"):
                cmp.analyze(original,native)


    def test_full_memory_comparison_recovers_real_value_correspondence(self):
        tag = "ws-product-race"
        original = {}
        native = {}
        for ext, size in cmp.MEMORY_COMPONENT_SIZES.items():
            old = bytearray(size)
            fixed = bytearray(size)
            wide = bytearray(size)
            if ext == "wram.bin":
                old[0xC6] = 29
                fixed[0xC6] = wide[0xC6] = 5
                old[0x1CF] = 0
                fixed[0x1CF] = wide[0x1CF] = 14
            if ext == "sram.bin":
                old[0xF31] = 29
                fixed[0xF31] = wide[0xF31] = 5
                old[0x10A7] = 7
                fixed[0x10A7] = wide[0x10A7] = 9
            original["evidence/frames/" + tag + "." + ext] = bytes(old)
            native["evidence/original/" + tag + "." + ext] = bytes(fixed)
            native["evidence/16x9/" + tag + "." + ext] = bytes(wide)
        original_observation = {"checkpoints": {tag: {
            "wram_sha256": cmp.sha(original["evidence/frames/" + tag + ".wram.bin"]),
            "sram_sha256": cmp.sha(original["evidence/frames/" + tag + ".sram.bin"]),
        }}}
        native_observation = {"result": {tag: {"producer": {
            view: {"wram_sha256": cmp.sha(native["evidence/" + view + "/" + tag + ".wram.bin"])}
            for view in ("original", "16x9")
        }}}}
        report = cmp.compare_memory(
            tag, original, native, original_observation, native_observation)
        self.assertEqual(report["wram.bin"]["original_native_differing_bytes"], 2)
        self.assertEqual(report["sram.bin"]["original_native_differing_bytes"], 2)
        for ext in cmp.MEMORY_COMPONENT_SIZES:
            self.assertEqual(report[ext]["native_fixed_wide_differing_bytes"], 0)
        self.assertEqual(report["observed_plus_0x0e6b_wram_sram_correspondence"], [
            {"wram_offset": 0xC6, "sram_offset": 0xF31}])
        self.assertFalse(report["wram_sram_mirroring_causally_proven"])
        # An orphan WRAM mismatch is not silently recategorized as a mirror.
        native["evidence/original/" + tag + ".wram.bin"] = b"\0"
        with self.assertRaisesRegex(ValueError, "size"):
            cmp.compare_memory(
                tag, original, native, original_observation, native_observation)

    def test_reject_missing_native_guest_memory_in_strict_mode(self):
        with tempfile.TemporaryDirectory() as d:
            original = Path(d) / "old.zip"
            native = Path(d) / "new.zip"
            fixtures(original, native)
            with self.assertRaisesRegex(ValueError, "Required native guest memory"):
                cmp.analyze(original, native, require_memory=True)



    def test_original_source_course_words_match_actual_native_margin_format(self):
        tag = "ws-product-race"
        original = bytearray(131072)
        def write16(offset, value):
            original[offset:offset + 2] = value.to_bytes(2, "little")
        write16(0x04F1, 2)
        write16(0x04F3, 4)
        write16(0x0419, 100)
        write16(0x041D, 16)
        # Coarse records all point to the first complete 4x4 fine record.
        for i in range(8):
            write16(0x1000F + 2 * i, 0)
        for i in range(16):
            write16(0x1800F + 2 * i, 0x1234)
        source = {"evidence/frames/" + tag + ".wram.bin": bytes(original)}
        lines = []
        for column in range(2, 7):
            lines.append(
                "URWS_SHADOW_EXT provider=course-runtime margin=48 "
                + f"column={column} camx=100 edge=0042 count=16 "
                + "payload=" + "3412" * 16
                + f" camy=16 finex={column - 2} finey=0 edgey=FFFF county=0")
        native = {"evidence/16x9/moving-course-run.log":
                  ("\n".join(lines) + "\n").encode()}
        result = cmp.compare_source_margin_words(tag, source, native)
        self.assertEqual(result["total_compared_words"], 80)
        self.assertEqual(result["total_matching_words"], 80)
        self.assertFalse(result["source_ppu_per_scanline_margin_pixels_proven"])
        self.assertFalse(result["exact_original_native_frame_registration_proven"])
        self.assertEqual(result["usa_course_credit"], 0)
        self.assertEqual(cmp.source_course_tile(bytes(original), 4, 15), 0x1234)
        self.assertIsNone(cmp.source_course_tile(bytes(original), 8, 15))
        # Positive receipt cannot survive an actual wrong native tile word.
        bad = dict(native)
        bad["evidence/16x9/moving-course-run.log"] = native[
            "evidence/16x9/moving-course-run.log"].replace(
                b"3412", b"0000", 1)
        report = cmp.compare_source_margin_words(tag, source, bad)
        self.assertEqual(report["total_matching_words"], 79)
        self.assertIsNotNone(report["columns"][2]["first_differing_word"])
        duplicate = dict(native)
        duplicate["evidence/16x9/moving-course-run.log"] += (
            lines[0] + "\n").encode()
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            cmp.compare_source_margin_words(tag, source, duplicate)
        truncated = dict(native)
        truncated["evidence/16x9/moving-course-run.log"] = (
            native["evidence/16x9/moving-course-run.log"]
            .replace(b"3412" * 16, b"3412" * 15, 1))
        with self.assertRaisesRegex(ValueError, "payload"):
            cmp.compare_source_margin_words(tag, source, truncated)



if __name__ == "__main__":
    unittest.main()
