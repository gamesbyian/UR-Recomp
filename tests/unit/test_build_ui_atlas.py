import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "build_ui_atlas.py"


def _write_bmp(path: Path, width: int = 256, height: int = 224) -> None:
    row = width * 3
    size = 54 + row * height
    hdr = bytearray(54)
    hdr[0:2] = b"BM"
    hdr[2:6] = size.to_bytes(4, "little")
    hdr[10:14] = (54).to_bytes(4, "little")
    hdr[14:18] = (40).to_bytes(4, "little")
    hdr[18:22] = width.to_bytes(4, "little", signed=True)
    hdr[22:26] = height.to_bytes(4, "little", signed=True)
    hdr[26:28] = (1).to_bytes(2, "little")
    hdr[28:30] = (24).to_bytes(2, "little")
    path.write_bytes(hdr + bytes(row * height))


class BuildUiAtlasTests(unittest.TestCase):
    def test_reports_state_and_discovery(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            dumps = root / "dumps"
            dumps.mkdir()

            manifest = {
                "schema_version": 1,
                "fields": {
                    "current_menu": {"wram_offset": "0x009F", "width": 1},
                    "selected_option": {"wram_offset": "0x009B", "width": 1},
                    "menu_row": {"wram_offset": "0x000E", "width": 1},
                    "menu_col": {"wram_offset": "0x0C63", "width": 1},
                    "in_race": {"wram_offset": "0x0313", "width": 1},
                },
                "captures": [
                    {
                        "tag": "options",
                        "state_id": "OPTIONS_MENU",
                        "expect": {"selected_option": "0x04"},
                        "discover": ["current_menu"],
                    }
                ],
            }
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(manifest))

            wram = bytearray(0x20000)
            wram[0x009F] = 0xAA
            wram[0x009B] = 0x04
            (dumps / "options.wram.bin").write_bytes(wram)
            _write_bmp(dumps / "options.fb.bmp")
            (dumps / "options.info.json").write_text(json.dumps({"frame": 123}))

            out_json = root / "atlas.json"
            out_md = root / "atlas.md"
            proc = subprocess.run(
                [
                    sys.executable,
                    str(TOOL),
                    "--manifest",
                    str(manifest_path),
                    "--dump-dir",
                    str(dumps),
                    "--out-json",
                    str(out_json),
                    "--out-md",
                    str(out_md),
                    "--strict",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)

            report = json.loads(out_json.read_text())
            capture = report["captures"][0]
            self.assertEqual(capture["status"], "ok")
            self.assertEqual(capture["frame"], 123)
            self.assertEqual(capture["observed"]["current_menu"], "0xAA")
            self.assertEqual(capture["observed"]["selected_option"], "0x04")
            self.assertEqual(capture["framebuffer"]["width"], 256)
            self.assertEqual(capture["framebuffer"]["height"], 224)
            self.assertEqual(len(capture["framebuffer"]["sha256"]), 64)

            md = out_md.read_text()
            self.assertIn("OPTIONS_MENU", md)
            self.assertIn("current_menu = `0xAA`", md)

    def test_strict_rejects_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            dumps = root / "dumps"
            dumps.mkdir()

            manifest = {
                "schema_version": 1,
                "fields": {
                    "current_menu": {"wram_offset": "0x009F", "width": 1},
                    "selected_option": {"wram_offset": "0x009B", "width": 1},
                    "menu_row": {"wram_offset": "0x000E", "width": 1},
                    "menu_col": {"wram_offset": "0x0C63", "width": 1},
                    "in_race": {"wram_offset": "0x0313", "width": 1},
                },
                "captures": [
                    {
                        "tag": "main",
                        "state_id": "MAIN_MENU",
                        "expect": {"current_menu": "0xD7"},
                    }
                ],
            }
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(manifest))

            wram = bytearray(0x20000)
            wram[0x009F] = 0x00
            (dumps / "main.wram.bin").write_bytes(wram)
            _write_bmp(dumps / "main.fb.bmp")

            proc = subprocess.run(
                [
                    sys.executable,
                    str(TOOL),
                    "--manifest",
                    str(manifest_path),
                    "--dump-dir",
                    str(dumps),
                    "--strict",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 2)
            report = json.loads(proc.stdout)
            self.assertEqual(report["captures"][0]["status"], "mismatch")

    def test_optional_missing_capture_does_not_fail_strict_mode(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            dumps = root / "dumps"
            dumps.mkdir()

            manifest = {
                "schema_version": 1,
                "fields": {
                    "current_menu": {"wram_offset": "0x009F", "width": 1},
                    "selected_option": {"wram_offset": "0x009B", "width": 1},
                    "menu_row": {"wram_offset": "0x000E", "width": 1},
                    "menu_col": {"wram_offset": "0x0C63", "width": 1},
                    "in_race": {"wram_offset": "0x0313", "width": 1},
                },
                "captures": [
                    {
                        "tag": "future-screen",
                        "state_id": "FUTURE_SCREEN",
                        "required": False,
                        "discover": ["current_menu"],
                    }
                ],
            }
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(manifest))

            proc = subprocess.run(
                [
                    sys.executable,
                    str(TOOL),
                    "--manifest",
                    str(manifest_path),
                    "--dump-dir",
                    str(dumps),
                    "--strict",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            report = json.loads(proc.stdout)
            self.assertEqual(report["captures"][0]["status"], "missing")
            self.assertFalse(report["captures"][0]["required"])


if __name__ == "__main__":
    unittest.main()
