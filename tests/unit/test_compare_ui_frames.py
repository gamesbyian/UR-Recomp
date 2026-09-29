import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "compare_ui_frames.py"


def write_bmp(path: Path, width: int, height: int, pixels):
    row_bytes = width * 3
    stride = (row_bytes + 3) & ~3
    pixel_offset = 54
    size = pixel_offset + stride * height
    header = bytearray(54)
    header[0:2] = b"BM"
    header[2:6] = size.to_bytes(4, "little")
    header[10:14] = pixel_offset.to_bytes(4, "little")
    header[14:18] = (40).to_bytes(4, "little")
    header[18:22] = width.to_bytes(4, "little", signed=True)
    header[22:26] = height.to_bytes(4, "little", signed=True)
    header[26:28] = (1).to_bytes(2, "little")
    header[28:30] = (24).to_bytes(2, "little")
    body = bytearray()
    for y in range(height - 1, -1, -1):
        row = bytearray()
        for x in range(width):
            r, g, b = pixels[y * width + x]
            row.extend((b, g, r))
        row.extend(b"\x00" * (stride - len(row)))
        body.extend(row)
    path.write_bytes(header + body)


class CompareUiFramesTests(unittest.TestCase):
    def test_reports_changed_pixels_and_bbox(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            dumps = root / "dumps"
            dumps.mkdir()
            before = [(0, 0, 0)] * 12
            after = list(before)
            after[1] = (255, 0, 0)   # x=1,y=0
            after[10] = (0, 128, 0)  # x=2,y=2
            write_bmp(dumps / "a.fb.bmp", 4, 3, before)
            write_bmp(dumps / "b.fb.bmp", 4, 3, after)

            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({
                "schema_version": 1,
                "pairs": [{"id": "p", "before": "a", "after": "b"}],
            }))
            out = root / "out.json"
            proc = subprocess.run(
                [sys.executable, str(TOOL), "--manifest", str(manifest),
                 "--dump-dir", str(dumps), "--out-json", str(out)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            result = json.loads(out.read_text())["pairs"][0]["result"]
            self.assertEqual(result["changed_pixels"], 2)
            self.assertEqual(result["change_bbox"], [1, 0, 2, 2])
            self.assertEqual(result["total_pixels"], 12)

    def test_missing_pair_is_nonfatal(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            dumps = root / "dumps"
            dumps.mkdir()
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({
                "schema_version": 1,
                "pairs": [{"id": "p", "before": "a", "after": "b"}],
            }))
            proc = subprocess.run(
                [sys.executable, str(TOOL), "--manifest", str(manifest),
                 "--dump-dir", str(dumps)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            result = json.loads(proc.stdout)["pairs"][0]["result"]
            self.assertEqual(result["status"], "missing")


if __name__ == "__main__":
    unittest.main()
