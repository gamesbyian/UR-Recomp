import struct
import tempfile
import unittest
from pathlib import Path

from tools.measure_widescreen_exposure import (
    OAM_HIGH, OAM_LOW, classify_objects, composite_visibility, course_lookahead,
)

W, H, M = 342, 224, 43
BG = (0, 0, 255)


def write_bmp(path: Path, dots=()) -> None:
    pixels = bytearray()
    for y in range(H):
        for x in range(W):
            b, g, r = (74, 74, 74) if (x, y) in dots else BG
            pixels += bytes((b, g, r, 0))
    header = b"BM" + struct.pack("<IHHI", 54 + len(pixels), 0, 0, 54)
    info = struct.pack("<IiiHHIIiiII", 40, W, -H, 1, 32, 0, len(pixels), 0, 0, 0, 0)
    path.write_bytes(header + info + bytes(pixels))


def wram(sprites, camera=0) -> bytes:
    w = bytearray(0x20000)
    for i in range(128):
        w[OAM_LOW + i * 4 + 1] = 0xE0  # parked off every line
    for i, (x, y, high) in sprites.items():
        w[OAM_LOW + i * 4] = x
        w[OAM_LOW + i * 4 + 1] = y
        w[OAM_HIGH + i // 4] |= high << ((i % 4) * 2)
    w[0x0419] = camera & 0xFF
    w[0x041A] = camera >> 8
    return bytes(w)


class WidescreenExposureTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def frame(self, d: Path, n: int, dots, sprites, camera=0):
        d.mkdir(exist_ok=True)
        write_bmp(d / f"frame_{n:06d}.bmp", dots)
        (d / f"frame_{n:06d}_wram.bin").write_bytes(wram(sprites, camera))

    def test_margin_only_and_extending_objects(self):
        obj = self.root / "obj"
        # Sprite 0 parked at X=-32 (224 with X bit 8): wholly in the left margin.
        self.frame(obj, 1, {(M - 17, 8)}, {0: (224, 0, 1)})
        # Sprite 99 large at X=-20: extends from the stock view into the margin.
        self.frame(obj, 2, {(M - 5, 120), (M + 10, 120)}, {99: (236, 112, 3)})
        # A margin sprite that draws nothing is not counted.
        self.frame(obj, 3, set(), {0: (224, 0, 1)})
        result = classify_objects(obj, M, split=False)
        self.assertEqual(result["frames"], 3)
        self.assertEqual(result["counts"], {"margin_only_left": 1, "extends_left": 1})
        self.assertEqual(result["margin_only_regions"], {"0:left": [-32, 0, 0, 32]})

    def test_split_band_uses_rip_values(self):
        obj = self.root / "obj"
        # Sprite 98 at X=10: shown (large) in the top band, hidden at X-256 below.
        self.frame(obj, 1, {(M + 12, 20)}, {98: (10, 0, 0)})
        result = classify_objects(obj, M, split=True)
        self.assertEqual(result["counts"], {})

    def test_composite_visibility_and_lookahead(self):
        full, noobj = self.root / "full", self.root / "noobj"
        self.frame(full, 1, {(26, 8)}, {}, camera=100)
        self.frame(noobj, 1, set(), {}, camera=100)
        self.frame(full, 2, set(), {}, camera=115)
        self.frame(noobj, 2, set(), {}, camera=115)
        vis = composite_visibility(full, noobj, {"0:left": [-32, 0, 0, 32]}, M)
        self.assertEqual(vis["obj_in_margin_frames"], 1)
        self.assertEqual(vis["margin_only_region_visible_frames"], {"0:left": 1})
        look = course_lookahead(full, [0x0419], M)["0x0419"]
        self.assertEqual(look["median_px_per_frame"], 15)
        self.assertEqual(look["lead_frames_at_median"], round(43 / 15, 2))


if __name__ == "__main__":
    unittest.main()
