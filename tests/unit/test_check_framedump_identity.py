import struct
import tempfile
import unittest
from pathlib import Path

from tools.check_framedump_identity import check, compare_dirs


def write_frames(root: Path, count: int, *, poke: int | None = None) -> None:
    root.mkdir(parents=True, exist_ok=True)
    for i in range(count):
        wram = bytearray(64)
        wram[0] = i & 0xFF
        if poke == i:
            wram[1] = 1
        (root / f"frame_{i:06d}_wram.bin").write_bytes(bytes(wram))
        (root / f"frame_{i:06d}.json").write_text(f'{{"frame": {i}}}\n')


def write_bmp(path: Path, width: int, height: int, pixels: bytes) -> None:
    row_stride = ((width * 4 + 3) // 4) * 4
    payload = bytearray(row_stride * height)
    for y in range(height):
        src = y * width * 4
        dst = (height - 1 - y) * row_stride
        payload[dst:dst + width * 4] = pixels[src:src + width * 4]
    header = bytearray(54)
    header[:2] = b"BM"
    struct.pack_into("<I", header, 2, 54 + len(payload))
    struct.pack_into("<I", header, 10, 54)
    struct.pack_into("<I", header, 14, 40)
    struct.pack_into("<i", header, 18, width)
    struct.pack_into("<i", header, 22, height)
    struct.pack_into("<H", header, 26, 1)
    struct.pack_into("<H", header, 28, 32)
    path.write_bytes(header + payload)


class FramedumpIdentityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_identical_runs_accepted(self):
        write_frames(self.root / "a", 5)
        write_frames(self.root / "b", 5)
        env = check("r", (self.root / "a", self.root / "b"), None, 5)
        self.assertEqual(env["outcome"], "accepted")
        self.assertEqual(env["metrics"]["frames"]["frames_compared"], 5)

    def test_first_divergent_frame_located(self):
        write_frames(self.root / "a", 6)
        write_frames(self.root / "b", 6, poke=3)
        result = compare_dirs(self.root / "a", self.root / "b")
        self.assertEqual(result["differing_files"], 1)
        self.assertEqual(result["first_differing_frame"], 3)
        env = check("r", (self.root / "a", self.root / "b"), None, 1)
        self.assertEqual(env["outcome"], "rejected")

    def test_frame_set_and_coverage_enforced(self):
        write_frames(self.root / "a", 4)
        write_frames(self.root / "b", 3)
        env = check("r", (self.root / "a", self.root / "b"), None, 1)
        self.assertEqual(env["outcome"], "rejected")
        write_frames(self.root / "b", 4)
        self.assertEqual(check("r", (self.root / "a", self.root / "b"), None, 1)["outcome"],
                         "accepted")
        self.assertEqual(check("r", (self.root / "a", self.root / "b"), None, 10)["outcome"],
                         "rejected")

    def test_bmp_overlay_rect_masks_only_declared_pixels(self):
        a = self.root / "a"
        b = self.root / "b"
        a.mkdir()
        b.mkdir()
        base = bytearray(4 * 4 * 4)
        candidate = bytearray(base)
        candidate[(1 * 4 + 2) * 4:(1 * 4 + 2) * 4 + 4] = b"\x10\x20\x30\xff"
        write_bmp(a / "frame_000000.bmp", 4, 4, bytes(base))
        write_bmp(b / "frame_000000.bmp", 4, 4, bytes(candidate))

        self.assertEqual(compare_dirs(a, b)["differing_files"], 1)
        masked = compare_dirs(a, b, allowed_bmp_rect=(2, 1, 1, 1))
        self.assertEqual(masked["differing_files"], 0)
        self.assertEqual(masked["masked_bmp_files"], 1)

        candidate[(3 * 4 + 0) * 4:(3 * 4 + 0) * 4 + 4] = b"\x40\x50\x60\xff"
        write_bmp(b / "frame_000000.bmp", 4, 4, bytes(candidate))
        escaped = compare_dirs(a, b, allowed_bmp_rect=(2, 1, 1, 1))
        self.assertEqual(escaped["differing_files"], 1)


    def test_checkpoint_dumps_compared(self):
        write_frames(self.root / "a", 2)
        write_frames(self.root / "b", 2)
        for side, value in (("da", b"\x01"), ("db", b"\x01")):
            (self.root / side).mkdir()
            (self.root / side / "cp.wram.bin").write_bytes(value)
        dirs = (self.root / "a", self.root / "b")
        dumps = (self.root / "da", self.root / "db")
        self.assertEqual(check("r", dirs, dumps, 1)["outcome"], "accepted")
        (self.root / "db" / "cp.wram.bin").write_bytes(b"\x02")
        self.assertEqual(check("r", dirs, dumps, 1)["outcome"], "rejected")
        (self.root / "db" / "cp.wram.bin").unlink()
        (self.root / "da" / "cp.wram.bin").unlink()
        # An empty checkpoint set proves nothing.
        self.assertEqual(check("r", dirs, dumps, 1)["outcome"], "rejected")


if __name__ == "__main__":
    unittest.main()
