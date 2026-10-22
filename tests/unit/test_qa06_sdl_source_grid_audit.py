"""ROM-free paired source-grid admission, no physical/native release credit."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from qa06_sdl_source_grid_audit import audit_pair, extract_grid, GEOMETRIES


def source_grid(changed=False):
    grid = bytearray()
    for y in range(224):
        for x in range(256):
            grid += bytes(((x * 11 + int(changed)) % 256, (y * 7) % 256,
                           (x + y) % 256, 255))
    return bytes(grid)


def surface(path, width, height, grid, *, bad_matte=False):
    left, crop_width = GEOMETRIES[(width, height)]
    blank = bytes(left * 4)
    rows = []
    for sy in range(224):
        row = grid[sy * 256 * 4:(sy + 1) * 256 * 4]
        pixels = bytearray(blank)
        for x in range(crop_width):
            sx = min(255, ((2 * x + 1) * 256) // (2 * crop_width))
            pixels += row[sx * 4:sx * 4 + 4]
        pixels += bytes((width - left - crop_width) * 4)
        if bad_matte and left:
            pixels[0] = 1
        rows.append(bytes(pixels))
    output = bytearray()
    for y in range(height):
        sy = min(223, ((2 * y + 1) * 224) // (2 * height))
        output += rows[sy]
    header = (f"P7\nWIDTH {width}\nHEIGHT {height}\nDEPTH 4\n"
              "MAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n").encode()
    path.write_bytes(header + output)


class OriginalGridTests(unittest.TestCase):
    def test_same_source_can_be_attested_without_source_claim(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            compact, wide = root / "compact.pam", root / "wide.pam"
            src = source_grid()
            surface(compact, 1024, 768, src)
            surface(wide, 1280, 720, src)
            result = audit_pair(compact, wide)
            self.assertEqual(result["source_grid"], [256, 224])
            self.assertEqual(result["wide_matte_rgba_pixels"], 230400)
            self.assertFalse(result["source_bound_by_independent_rebuild"])
            self.assertFalse(result["physical_device_approved"])
            self.assertEqual(result["release_gate_credit"], 0)

    def test_one_pixel_mutation_refuses_even_when_sample_hash_can_match(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "compact.pam"
            surface(p, 1024, 768, source_grid())
            raw = bytearray(p.read_bytes())
            at = raw.index(b"ENDHDR\n") + len(b"ENDHDR\n") + (1 * 1024 + 1) * 4
            raw[at] ^= 1
            p.write_bytes(raw)
            with self.assertRaisesRegex(ValueError, "non-nearest-neighbour"):
                extract_grid(p, 1024, 768)

    def test_both_valid_surfaces_must_have_same_source(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            compact, wide = root / "compact.pam", root / "wide.pam"
            surface(compact, 1024, 768, source_grid())
            surface(wide, 1280, 720, source_grid(changed=True))
            with self.assertRaisesRegex(ValueError, "source grids differ"):
                audit_pair(compact, wide)

    def test_nonblank_matte_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "wide.pam"
            surface(p, 1280, 720, source_grid(), bad_matte=True)
            with self.assertRaisesRegex(ValueError, "matte has nonzero"):
                extract_grid(p, 1280, 720)

    def test_trailing_pixel_and_invalid_geometry_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "compact.pam"
            surface(p, 1024, 768, source_grid())
            with self.assertRaisesRegex(ValueError, "unsupported"):
                extract_grid(p, True, 768)
            with p.open("ab") as output:
                output.write(b"extra")
            with self.assertRaisesRegex(ValueError, "truncated or trailing"):
                extract_grid(p, 1024, 768)


if __name__ == "__main__":
    unittest.main()
