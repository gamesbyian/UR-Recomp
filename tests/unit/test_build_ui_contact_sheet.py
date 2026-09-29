import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "build_ui_contact_sheet.py"


class UiContactSheetTests(unittest.TestCase):
    def test_embeds_framebuffer_and_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bmp = root / "frame.fb.bmp"
            bmp.write_bytes(b"BM" + b"\x00" * 64)
            atlas = root / "atlas.json"
            atlas.write_text(json.dumps({
                "summary": {"declared": 1, "ok": 1},
                "captures": [{
                    "tag": "main",
                    "state_id": "MAIN_MENU",
                    "variant": "1P",
                    "source_fixture": "fixture",
                    "frame": 123,
                    "status": "ok",
                    "files": {"framebuffer": str(bmp)},
                    "observed": {
                        "current_menu": "0xD7",
                        "selected_option": "0x00",
                    },
                    "mismatches": [],
                }],
            }))
            out = root / "atlas.html"
            proc = subprocess.run(
                [sys.executable, str(TOOL), "--atlas", str(atlas), "--out", str(out)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            page = out.read_text()
            self.assertIn("Uniracers UI Atlas", page)
            self.assertIn("MAIN_MENU", page)
            self.assertIn("0xD7", page)
            self.assertIn("data:image/bmp;base64,", page)

    def test_missing_frame_can_be_rendered_explicitly(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            atlas = root / "atlas.json"
            atlas.write_text(json.dumps({
                "summary": {"declared": 1, "missing": 1},
                "captures": [{
                    "tag": "future",
                    "state_id": "FUTURE",
                    "status": "missing",
                    "files": {},
                    "observed": {},
                    "mismatches": [],
                }],
            }))
            out = root / "atlas.html"
            proc = subprocess.run(
                [
                    sys.executable, str(TOOL),
                    "--atlas", str(atlas),
                    "--out", str(out),
                    "--include-missing",
                ],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("no canonical framebuffer yet", out.read_text())

    def test_reference_only_state_is_rendered(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            atlas = root / "atlas.json"
            atlas.write_text(json.dumps({
                "summary": {"declared": 0},
                "captures": [],
            }))
            refs = root / "refs.json"
            refs.write_text(json.dumps({
                "schema_version": 1,
                "entries": [{
                    "state_id": "VS_CHALLENGER",
                    "references": [{
                        "url": "https://example.test/vs",
                        "kind": "video",
                        "observation": "recognition lead",
                    }],
                }],
            }))
            out = root / "atlas.html"
            proc = subprocess.run(
                [
                    sys.executable, str(TOOL),
                    "--atlas", str(atlas),
                    "--reference-index", str(refs),
                    "--out", str(out),
                    "--include-missing",
                ],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            page = out.read_text()
            self.assertIn("VS_CHALLENGER", page)
            self.assertIn("reference-only", page)
            self.assertIn("https://example.test/vs", page)
            self.assertIn("recognition lead", page)


if __name__ == "__main__":
    unittest.main()
