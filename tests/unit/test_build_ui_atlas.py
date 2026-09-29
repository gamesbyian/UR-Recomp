import json
import subprocess
import sys
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


def test_build_ui_atlas_reports_state_and_discovery(tmp_path: Path) -> None:
    dumps = tmp_path / "dumps"
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
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest))

    wram = bytearray(0x20000)
    wram[0x009F] = 0xAA
    wram[0x009B] = 0x04
    (dumps / "options.wram.bin").write_bytes(wram)
    _write_bmp(dumps / "options.fb.bmp")
    (dumps / "options.info.json").write_text(json.dumps({"frame": 123}))

    out_json = tmp_path / "atlas.json"
    out_md = tmp_path / "atlas.md"
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
    assert proc.returncode == 0, proc.stderr

    report = json.loads(out_json.read_text())
    capture = report["captures"][0]
    assert capture["status"] == "ok"
    assert capture["frame"] == 123
    assert capture["observed"]["current_menu"] == "0xAA"
    assert capture["observed"]["selected_option"] == "0x04"
    assert capture["framebuffer"]["width"] == 256
    assert capture["framebuffer"]["height"] == 224
    assert len(capture["framebuffer"]["sha256"]) == 64

    md = out_md.read_text()
    assert "OPTIONS_MENU" in md
    assert "current_menu = `0xAA`" in md


def test_build_ui_atlas_strict_rejects_mismatch(tmp_path: Path) -> None:
    dumps = tmp_path / "dumps"
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
    manifest_path = tmp_path / "manifest.json"
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
    assert proc.returncode == 2
    report = json.loads(proc.stdout)
    assert report["captures"][0]["status"] == "mismatch"
