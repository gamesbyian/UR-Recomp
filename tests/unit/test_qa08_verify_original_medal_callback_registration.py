"""ROM-free adversarial QA08 source-original callback registrar tests."""
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools import qa08_verify_original_medal_callback_registration as reg


def synthetic_archives(root: Path, *, bad_pixel=False, bad_depth=False,
                       bad_label=False, suppress_sprite=False):
    inputs = ("\n".join(f"[input] frame={i*100} mask={i%4:03x}"
                        for i in range(26)) + "\n").encode()
    stage_lines, call_lines, callback_rows, image_members = [], [], [], {}
    frames = (*range(4028, 4037), *range(4172, 4181))
    colors = (0x71c9, 0x8183, 0x8430, 0xCDF1, 0x83CD)
    for frame in frames:
        for i, (x, y) in enumerate(reg.PIXELS):
            obj = i != 2
            for stage, bg in (("OBJ", -1), ("BG", 0), ("BG", 1), ("FINAL", -1)):
                depth = 0 if (not obj and stage == "OBJ") else (0x28 if obj else 0x27)
                if bad_depth and frame == 4031 and i == 0 and stage == "FINAL":
                    depth = 0x27
                stage_lines.append(
                    f"UR_QA08_ORIGINAL_MEDAL_LAYER frame={frame} range=0,223 "
                    f"x={x} y={y} stage={stage} bg={bg} bgmode=3 "
                    f"depth={depth:02x} rgb565={colors[i]:04x} "
                    "source_callback_proven=0 native_frame_proven=0"
                )
        for _ in range(2):
            for x, y, slot, wrote in (
                (207, 91, 112, 1), (205, 115, 113, 1), (205, 139, 114, 0),
                (225, 96, 97, 0), (225, 96, 99, 1),
                (225, 120, 96, 0), (225, 120, 98, 1),
            ):
                if suppress_sprite and frame == 4031 and x == 207:
                    wrote = 0
                call_lines.append(
                    f"UR_QA08_ORIGINAL_ACTIVE_MEDAL_TILE frame={frame} y={y} x={x} "
                    f"slot={slot} objname=1a4 palette=5 priority=1 "
                    f"src_tile=15a4 tileline=0 tile_span={x},{x+8} drawmode=3 "
                    f"zbefore=00 zafter=28 rgbbefore=ffff rgbafter=ffff "
                    f"changed_z={wrote} changed_rgb=0 original_guest_phase_proven=0"
                )
        if frame not in reg.FRAMES:
            continue
        data = bytearray(256 * 224 * 4)
        for i, (x, y) in enumerate(reg.PIXELS):
            r, g, b = reg.rgb565_to_rgb8(colors[i])
            offset = (y * 256 + x) * 4
            data[offset:offset + 4] = bytes((b, g, r, 0))
        if bad_pixel and frame == 4031:
            x, y = reg.PIXELS[0]
            data[(y * 256 + x) * 4 + 2] ^= 1
        name = f"frames/frame_{frame:06d}_256x224.raw"
        image_members[name] = bytes(data)
        callback_rows.append({
            "real_original_snes9x_callback_frame": frame,
            "original_1based_frame": frame + (2 if bad_label else 1),
            "original_unchanged_BGRX_sha256": reg.digest(image_members[name])
        })
    # Model the complete 263-label metadata census without any original ROM
    # images: only the two selected frames require image bytes in this test.
    for unused in range(261):
        callback_rows.append({
            "real_original_snes9x_callback_frame": unused,
            "original_1based_frame": unused + 1,
            "original_unchanged_BGRX_sha256": "0" * 64
        })
    script = b"synthetic route only; no original assets"
    manifest = {
        "actual_callbacks_captured": 263, "actual_script_quit_frame": 5484,
        "exact_original_two_pad_route_LF_without_turbo_sha256": reg.digest(script),
        "each_authentic_callback": callback_rows
    }
    source, painter = root / "original.zip", root / "painter.zip"
    with zipfile.ZipFile(source, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("qa08-original-2p-fullroute.json", json.dumps(manifest))
        z.writestr("original.script", script)
        z.writestr("original.log", inputs)
        for name, data in image_members.items():
            z.writestr(name, data)
    with zipfile.ZipFile(painter, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr(reg.PAINTER_LOG, inputs)
        z.writestr(reg.STAGES_PATH, "\n".join(stage_lines) + "\n")
        z.writestr(reg.CALLS_PATH, "\n".join(call_lines) + "\n")
    return source, painter, reg.digest(inputs)


class OriginalCallbackRegression(unittest.TestCase):
    def fixture(self, *, bad_pixel=False, bad_depth=False,
                bad_label=False, suppress_sprite=False, reject=False):
        with tempfile.TemporaryDirectory() as tmp:
            source, painter, inputs = synthetic_archives(
                Path(tmp), bad_pixel=bad_pixel, bad_depth=bad_depth,
                bad_label=bad_label, suppress_sprite=suppress_sprite
            )
            # Rehash synthetic archives to test *semantic* guards independently
            # of the outer source-identity SHA256 rejection.
            with (mock.patch.object(reg, "ORIGINAL_ZIP_SHA", reg.digest(source.read_bytes())),
                  mock.patch.object(reg, "PAINTER_ZIP_SHA", reg.digest(painter.read_bytes())),
                  mock.patch.object(reg, "INPUT_SHA", inputs)):
                if reject:
                    with self.assertRaises(ValueError):
                        reg.verify(source, painter)
                else:
                    result = reg.verify(source, painter)
                    self.assertEqual(result["matched_pixels"], 10)
                    self.assertEqual(result["wrong_pixels"], 0)
                    self.assertFalse(result["native_frame_registration_proven"])
                    self.assertEqual(
                        [p["owner"] for p in result["pixels"][:5]],
                        ["OBJ112", "OBJ113", "BG0", "OBJ99", "OBJ98"]
                    )
                    self.assertEqual(
                        (result["pixels"][0]["original_internal_frame"],
                         result["pixels"][0]["original_1based_output_frame"]),
                        (4031, 4032)
                    )

    def test_source_rgb565_bit_replication(self):
        self.assertEqual(reg.rgb565_to_rgb8(0x71C9), (115, 56, 74))
        self.assertEqual(reg.rgb565_to_rgb8(0x8183), (132, 48, 24))
        self.assertEqual(reg.rgb565_to_rgb8(0xCDF1), (206, 190, 140))

    def test_accept_true_population_shape(self):
        self.fixture()

    def test_detect_rehashed_wrong_callback_pixel(self):
        self.fixture(bad_pixel=True, reject=True)

    def test_detect_bg_sprite_owner_conflict(self):
        self.fixture(bad_depth=True, reject=True)

    def test_reject_off_by_one_callback_registration(self):
        self.fixture(bad_label=True, reject=True)

    def test_reject_sprite_inferred_from_depth_only(self):
        self.fixture(suppress_sprite=True, reject=True)


if __name__ == "__main__":
    unittest.main()
