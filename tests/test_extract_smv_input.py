#!/usr/bin/env python3
"""ROM-free regression tests for tools/extract_smv_input.py."""

from __future__ import annotations

import gzip
import json
import struct
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "extract_smv_input.py"


def make_v1(path: Path) -> tuple[bytes, list[int]]:
    sram = bytes((i * 17 + 3) & 0xFF for i in range(0x20000))
    packed = gzip.compress(sram, mtime=0)

    # Four controller samples (header frame_count is sample_count - 1).
    # Raw Snes9x bits: B, Right+R, reset marker, A+Left+L.
    samples = [0x8000, 0x0110, 0xFFFF, 0x02A0]
    save_off = 32
    ctrl_off = save_off + len(packed)

    hdr = bytearray(32)
    hdr[0:4] = b"SMV\x1a"
    struct.pack_into("<I", hdr, 4, 1)
    struct.pack_into("<I", hdr, 8, 0x12345678)
    struct.pack_into("<I", hdr, 12, 7)
    struct.pack_into("<I", hdr, 16, len(samples) - 1)
    hdr[20] = 0x01
    hdr[21] = 0x01  # reset anchored, NTSC
    hdr[22] = 0x00
    hdr[23] = 0x00
    struct.pack_into("<I", hdr, 24, save_off)
    struct.pack_into("<I", hdr, 28, ctrl_off)

    body = bytes(hdr) + packed + b"".join(struct.pack("<H", x) for x in samples)
    path.write_bytes(body)
    return sram, samples


def run_case(movie: Path, expected_sram: bytes, container: str | None) -> None:
    with tempfile.TemporaryDirectory() as td:
        out = Path(td)
        inp = out / "input.txt"
        srm = out / "save.srm"
        meta = out / "meta.json"
        subprocess.run(
            [
                sys.executable,
                str(TOOL),
                str(movie),
                "--input-out", str(inp),
                "--sram-out", str(srm),
                "--sram-size", "8192",
                "--json-out", str(meta),
            ],
            check=True,
        )
        lines = [
            x for x in inp.read_text().splitlines()
            if x and not x.startswith("#")
        ]
        assert lines == [
            "0:1:001",   # B
            "1:1:880",   # Right+R
            "3:1:540",   # A+Left+L
        ], lines
        assert srm.read_bytes() == expected_sram[:8192]
        m = json.loads(meta.read_text())
        assert m["version"] == 1
        assert m["sample_count"] == 4
        assert m["reset_anchored"] is True
        assert m["reset_markers"] == [2]
        assert m["embedded_sram_size"] == 0x20000
        assert m["emitted_sram_size"] == 8192
        assert m["event_runs"] == 3
        assert m["container"] == container


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        raw = td / "movie.smv"
        sram, _ = make_v1(raw)
        run_case(raw, sram, None)

        wrapped = td / "movie-download.smv"
        with zipfile.ZipFile(wrapped, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("nested/test.smv", raw.read_bytes())
        run_case(wrapped, sram, "zip")

    print("PASS: SMV extractor raw/zip input, reset SRAM and joypad translation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
