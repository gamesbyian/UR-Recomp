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


def _fixture_manifest(captures: list[dict[str, object]]) -> dict[str, object]:
    return {
        "schema_version": 1,
        "fields": {
            "current_menu": {"wram_offset": "0x009F", "width": 1},
            "selected_option": {"wram_offset": "0x009B", "width": 1},
            "menu_row": {"wram_offset": "0x000E", "width": 1},
            "menu_col": {"wram_offset": "0x0C63", "width": 1},
            "in_race": {"wram_offset": "0x0313", "width": 1},
        },
        "captures": captures,
    }


def _write_ok_capture(dumps: Path, tag: str) -> None:
    (dumps / f"{tag}.wram.bin").write_bytes(bytes(0x20000))
    _write_bmp(dumps / f"{tag}.fb.bmp")


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

    def test_reads_sram_backed_field(self) -> None:
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
                    "participant_owner_raw": {
                        "source": "sram",
                        "sram_offset": "0x0743",
                        "width": 1,
                    },
                },
                "captures": [
                    {
                        "tag": "vs-p1",
                        "state_id": "VS_SELECT",
                        "discover": ["participant_owner_raw"],
                    }
                ],
            }
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(manifest))

            wram = bytearray(0x20000)
            wram[0x009F] = 0x3E
            (dumps / "vs-p1.wram.bin").write_bytes(wram)
            sram = bytearray(0x2000)
            sram[0x0743] = 0x04
            (dumps / "vs-p1.sram.bin").write_bytes(sram)
            _write_bmp(dumps / "vs-p1.fb.bmp")

            out_json = root / "atlas.json"
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
            self.assertEqual(capture["observed"]["participant_owner_raw"], "0x04")
            self.assertIn("sram", capture["files"])

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

    def test_include_unclassified_surfaces_raw_dump_tag(self) -> None:
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
                "captures": [],
            }
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(manifest))

            _write_bmp(dumps / "mystery.fb.bmp", width=4, height=3)

            out_json = root / "atlas.json"
            proc = subprocess.run(
                [
                    sys.executable,
                    str(TOOL),
                    "--manifest",
                    str(manifest_path),
                    "--dump-dir",
                    str(dumps),
                    "--include-unclassified",
                    "--out-json",
                    str(out_json),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            report = json.loads(out_json.read_text())
            self.assertEqual(report["summary"]["declared"], 0)
            self.assertEqual(report["summary"]["unclassified"], 1)
            self.assertEqual(report["summary"]["total_cards"], 1)
            capture = report["captures"][0]
            self.assertEqual(capture["state_id"], "UNCLASSIFIED")
            self.assertEqual(capture["tag"], "mystery")
            self.assertEqual(capture["classification_status"], "unclassified")


    def test_filters_by_source_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            dumps = root / "dumps"
            dumps.mkdir()
            fields = {
                "current_menu": {"wram_offset": "0x009F", "width": 1},
                "selected_option": {"wram_offset": "0x009B", "width": 1},
                "menu_row": {"wram_offset": "0x000E", "width": 1},
                "menu_col": {"wram_offset": "0x0C63", "width": 1},
                "in_race": {"wram_offset": "0x0313", "width": 1},
            }
            manifest = {
                "schema_version": 1,
                "fields": fields,
                "captures": [
                    {"tag": "one", "state_id": "GAMEPLAY", "source_fixture": "fixture-a"},
                    {"tag": "two", "state_id": "GAMEPLAY", "source_fixture": "fixture-b"},
                ],
            }
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(manifest))
            wram = bytearray(0x20000)
            (dumps / "one.wram.bin").write_bytes(wram)
            _write_bmp(dumps / "one.fb.bmp")
            out_json = root / "atlas.json"
            proc = subprocess.run(
                [
                    sys.executable, str(TOOL),
                    "--manifest", str(manifest_path),
                    "--source-fixture", "fixture-a",
                    "--dump-dir", str(dumps),
                    "--out-json", str(out_json),
                    "--strict",
                ],
                check=False, capture_output=True, text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            report = json.loads(out_json.read_text())
            self.assertEqual(report["summary"]["declared"], 1)
            self.assertEqual([c["tag"] for c in report["captures"]], ["one"])


    def test_excludes_one_source_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            dumps = root / "dumps"
            dumps.mkdir()
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(_fixture_manifest([
                {"tag": "owned-elsewhere", "state_id": "GAMEPLAY", "source_fixture": "fixture-a"},
                {"tag": "owned-here", "state_id": "GAMEPLAY", "source_fixture": "fixture-b"},
            ])))
            _write_ok_capture(dumps, "owned-here")
            out_json = root / "atlas.json"
            proc = subprocess.run(
                [
                    sys.executable, str(TOOL),
                    "--manifest", str(manifest_path),
                    "--exclude-source-fixture", "fixture-a",
                    "--dump-dir", str(dumps),
                    "--out-json", str(out_json),
                    "--strict",
                ],
                check=False, capture_output=True, text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            report = json.loads(out_json.read_text())
            self.assertEqual([c["tag"] for c in report["captures"]], ["owned-here"])

    def test_repeated_fixture_exclusions_compose(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            dumps = root / "dumps"
            dumps.mkdir()
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(_fixture_manifest([
                {"tag": "a", "state_id": "GAMEPLAY", "source_fixture": "fixture-a"},
                {"tag": "b", "state_id": "GAMEPLAY", "source_fixture": "fixture-b"},
                {"tag": "c", "state_id": "GAMEPLAY", "source_fixture": "fixture-c"},
            ])))
            _write_ok_capture(dumps, "c")
            out_json = root / "atlas.json"
            proc = subprocess.run(
                [
                    sys.executable, str(TOOL),
                    "--manifest", str(manifest_path),
                    "--exclude-source-fixture", "fixture-a",
                    "--exclude-source-fixture", "fixture-b",
                    "--dump-dir", str(dumps),
                    "--out-json", str(out_json),
                    "--strict",
                ],
                check=False, capture_output=True, text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            report = json.loads(out_json.read_text())
            self.assertEqual([c["tag"] for c in report["captures"]], ["c"])

    def test_exclusion_keeps_unrelated_capture_strict(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            dumps = root / "dumps"
            dumps.mkdir()
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(_fixture_manifest([
                {"tag": "excluded", "state_id": "GAMEPLAY", "source_fixture": "fixture-a"},
                {"tag": "still-required", "state_id": "MAIN_MENU", "source_fixture": "fixture-b"},
            ])))
            proc = subprocess.run(
                [
                    sys.executable, str(TOOL),
                    "--manifest", str(manifest_path),
                    "--exclude-source-fixture", "fixture-a",
                    "--dump-dir", str(dumps),
                    "--strict",
                ],
                check=False, capture_output=True, text=True,
            )
            self.assertEqual(proc.returncode, 2)
            report = json.loads(proc.stdout)
            self.assertEqual([c["tag"] for c in report["captures"]], ["still-required"])
            self.assertEqual(report["captures"][0]["status"], "missing")

    def test_no_exclusion_preserves_normal_strict_behavior(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            dumps = root / "dumps"
            dumps.mkdir()
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(_fixture_manifest([
                {"tag": "required", "state_id": "GAMEPLAY", "source_fixture": "fixture-a"},
            ])))
            proc = subprocess.run(
                [
                    sys.executable, str(TOOL),
                    "--manifest", str(manifest_path),
                    "--dump-dir", str(dumps),
                    "--strict",
                ],
                check=False, capture_output=True, text=True,
            )
            self.assertEqual(proc.returncode, 2)
            report = json.loads(proc.stdout)
            self.assertEqual([c["tag"] for c in report["captures"]], ["required"])
            self.assertEqual(report["captures"][0]["status"], "missing")


if __name__ == "__main__":
    unittest.main()
