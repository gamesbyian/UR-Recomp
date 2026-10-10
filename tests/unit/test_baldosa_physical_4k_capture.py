"""Strict PPU 342/256 -> genuine 4x internal -> physical 3840x2160 oracle."""
from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from tools.check_baldosa_physical_4k_capture import (
    OUT_W, OUT_H, assess, nearest_index,
)


def pam(width: int, height: int, rgba: bytes) -> bytes:
    return (
        f"P7\nWIDTH {width}\nHEIGHT {height}\nDEPTH 4\n"
        "MAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n"
    ).encode() + rgba


def source_raster(width: int) -> bytes:
    # Every source margin, split band, screen edge and near-match color has
    # independently variable channels. This is not a uniform or gradient
    # framebuffer for which wrong scaling could accidentally pass.
    return b"".join(
        bytes(((x * 11 + y) & 255, (x ^ y) & 255,
               ((x < 43) * 101 + (x >= width - 43) * 37 +
                (y >= 112) * 83 + x // 16) & 255, 255))
        for y in range(224) for x in range(width)
    )


def internal_four_x(source: bytes, width: int) -> bytes:
    out = bytearray()
    for y in range(224):
        row = b"".join(
            source[(y * width + x) * 4:(y * width + x + 1) * 4] * 4
            for x in range(width))
        out.extend(row * 4)
    return bytes(out)


def physical_four_k(source: bytes, width: int) -> bytes:
    # This fixture follows the independent textbook center-of-texel
    # nearest-reference rule. The oracle must compare complete output
    # rows, not a few easy solid-color corners.
    viewport_width = 3840 if width == 342 else 2880
    x_offset = 0 if width == 342 else 480
    bars = b"\x00\x00\x00\xff" * x_offset
    mapped = [min(width - 1, (2 * x + 1) * width //
                  (2 * viewport_width)) for x in range(viewport_width)]
    cached_rows = []
    for sy in range(224):
        row = source[sy * width * 4:(sy + 1) * width * 4]
        cached_rows.append(
            bars + b"".join(row[x * 4:x * 4 + 4] for x in mapped) + bars
        )
    return b"".join(
        cached_rows[min(223, (2 * y + 1) * 224 // (2 * OUT_H))]
        for y in range(OUT_H)
    )


class PhysicalFourKParityTests(unittest.TestCase):
    def test_native_full_world_with_real_4k_sized_source_oracle(self):
        self.assertEqual(nearest_index(0, OUT_H, 224), 0)
        self.assertEqual(nearest_index(OUT_H - 1, OUT_H, 224), 223)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            w = 342
            src = source_raster(w)
            density = internal_four_x(src, w)
            screenshot = physical_four_k(src, w)
            one = root / "source-001872.pam"
            four = root / "density-001872.pam"
            physical = root / "physical-001872.pam"
            one.write_bytes(pam(w, 224, src))
            four.write_bytes(pam(w * 4, 896, density))
            physical.write_bytes(pam(OUT_W, OUT_H, screenshot))
            result = assess(one, four, physical, 1872)
            self.assertEqual(result["status"],
                             "exact-native-capture-pixel-parity")
            self.assertEqual(result["output_viewport"], [0, 0, 3840, 2160])
            self.assertEqual(result["native_density_size"], [1368, 896])
            self.assertNotEqual(result["rgba_capture_sha256"],
                                result["rgba_density_sha256"])

            # A one-pixel error at the split seam must be detected, even
            # when every other 4K output pixel is correct.
            damaged = bytearray(screenshot)
            offset = (1080 * OUT_W + 42) * 4
            damaged[offset] ^= 1
            physical.write_bytes(pam(OUT_W, OUT_H, damaged))
            with self.assertRaisesRegex(ValueError,
                                        r"physical 4K mismatch at \(42,1080\)"):
                assess(one, four, physical, 1872)

            # A 4x raster with one invalid original pixel may still look
            # detailed, but must not gain physical-output QA credit.
            four_bad = bytearray(density)
            four_bad[(112 * 4 * w * 4 + 43 * 4) * 4] ^= 1
            four.write_bytes(pam(w * 4, 896, four_bad))
            with self.assertRaisesRegex(ValueError,
                                        "not an exact native 4x"):
                assess(one, four, physical, 1872)

    def test_native_source_zero_alpha_becomes_opaque_only_at_sdl_output(self):
        # Actual stock Baldosa PPU pixels use 0x00RRGGBB, whereas its
        # SDL presenter explicitly forces the output texture opaque.
        # Exact logical 1x -> 4x identity must still include the zero byte.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            w = 342
            src = bytearray(source_raster(w))
            src[3::4] = bytes(len(src) // 4)
            src = bytes(src)
            dense = internal_four_x(src, w)
            # The displayed SDL canvas has alpha=255 for every texel,
            # without changing any of the original source RGB channels.
            opaque = bytearray(physical_four_k(src, w))
            opaque[3::4] = bytes([255]) * (len(opaque) // 4)
            one = root / "source-001856.pam"
            four = root / "density-001856.pam"
            physical = root / "physical-001856.pam"
            one.write_bytes(pam(w, 224, src))
            four.write_bytes(pam(w * 4, 896, dense))
            physical.write_bytes(pam(OUT_W, OUT_H, opaque))
            result = assess(one, four, physical, 1856)
            self.assertEqual(result["status"], "exact-native-capture-pixel-parity")
            self.assertEqual(result["opaque_sdl_drawable_alpha_expected"], 255)
            # A zero-alpha *screen* pixel must not be silently accepted.
            opaque[3] = 0
            physical.write_bytes(pam(OUT_W, OUT_H, opaque))
            with self.assertRaisesRegex(ValueError, "physical 4K mismatch"):
                assess(one, four, physical, 1856)

    def test_fixed_original_is_centered_with_7_to_6_par(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            w = 256
            src = source_raster(w)
            one = root / "logical-001220.pam"
            four = root / "density-001220.pam"
            physical = root / "output-001220.pam"
            one.write_bytes(pam(w, 224, src))
            four.write_bytes(pam(w * 4, 896, internal_four_x(src, w)))
            full = physical_four_k(src, w)
            physical.write_bytes(pam(OUT_W, OUT_H, full))
            result = assess(one, four, physical, 1220)
            self.assertEqual(result["output_viewport"],
                             [480, 0, 2880, 2160])
            self.assertEqual(full[0:4], b"\x00\x00\x00\xff")
            self.assertEqual(full[(OUT_W - 1) * 4:OUT_W * 4],
                             b"\x00\x00\x00\xff")
            self.assertEqual(full[480 * 4:480 * 4 + 4], src[:4])

            fake = root / "output-001221.pam"
            fake.write_bytes(pam(OUT_W, OUT_H, full))
            with self.assertRaisesRegex(ValueError,
                                        "no exact same-frame"):
                assess(one, four, fake, 1220)
            physical.write_bytes(pam(1368, 896,
                                     internal_four_x(src, w)[:1368*896*4]))
            with self.assertRaisesRegex(ValueError,
                                        "truncated or oversized|not a real"):
                assess(one, four, physical, 1220)

    def test_malformed_pam_and_invalid_source_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            one = root / "logical-000100.pam"
            four = root / "density-000100.pam"
            physical = root / "output-000100.pam"
            one.write_bytes(b"not a real PAM")
            four.write_bytes(b"")
            physical.write_bytes(b"")
            with self.assertRaisesRegex(ValueError, "invalid 8-bit"):
                assess(one, four, physical, 100)
            with self.assertRaisesRegex(ValueError, "negative guest frame"):
                assess(one, four, physical, -1)


if __name__ == "__main__":
    unittest.main()
