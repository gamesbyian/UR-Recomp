#!/usr/bin/env python3
"""Check the preserved H27 compact/wide Windows SDL receipt bundle.

This only connects already-existing P7 nearest-neighbour grid admission with
independent PNG/P7/log receipt consistency. Neither a hosted log nor a digest
proves the producer really ran the claimed binary, current source, or physical
GPU. Never award source authenticity, art approval or release gate credit.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import tempfile
import zipfile

from qa06_sdl_source_grid_audit import audit_pair
from verify_menu_source_art_bundle import read_png_rgba

GEOMETRIES = ((1024, 768), (1280, 720))
MAX_ZIP = 16 * 1024 * 1024
MAX_TOTAL = 10 * 1024 * 1024


def _paths(width: int, height: int) -> dict[str, str]:
    prefix = f"ur-modern-win32-visual-{width}x{height}/"
    return {
        "receipt": prefix + "readback-receipt.json",
        "png": prefix + "actual-sdl-drawable.png",
        "p7": prefix + "probe_first/actual-sdl-drawable.pam",
        "log": prefix + "probe_first/native-process.log",
    }


def _capture(line: str, width: int, height: int) -> bool:
    tokens = line.split()
    if not tokens or tokens[0] != "UR_MODERN_VISUAL_SDL_CAPTURE":
        return False
    fields: dict[str, str] = {}
    for token in tokens[1:]:
        key, sep, value = token.partition("=")
        if not sep or not key or not value or key in fields:
            return False
        fields[key] = value
    return fields == {
        "status": "saved",
        "draw": "40",
        "guest_frame": "40",
        "output": f"{width}x{height}",
        "source": "SDL_RenderReadPixels",
        "backend": "sdl3",
    }


def audit_receipt_bundle(archive: Path) -> dict[str, object]:
    """Admit exactly the two archived H27 receipt/P7/PNG/log records."""
    if not archive.is_file() or archive.stat().st_size > MAX_ZIP:
        raise ValueError("absent or oversized historical H27 ZIP")
    needed = {name for w, h in GEOMETRIES for name in _paths(w, h).values()}
    archive_digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    with zipfile.ZipFile(archive) as zipped:
        entries = zipped.infolist()
        if (len(entries) != len(needed) or
                {i.filename for i in entries} != needed or
                len({i.filename for i in entries}) != len(entries) or
                any(i.is_dir() or i.flag_bits & 1 for i in entries) or
                sum(i.file_size for i in entries) > MAX_TOTAL):
            raise ValueError("unsafe, incomplete or oversized H27 bundle")
        records = {}
        for w, h in GEOMETRIES:
            paths = _paths(w, h)
            raw = {kind: zipped.read(name) for kind, name in paths.items()}
            try:
                receipt = json.loads(raw["receipt"])
            except (UnicodeError, ValueError) as exc:
                raise ValueError("invalid original H27 receipt JSON") from exc
            if (type(receipt) is not dict or
                    receipt.get("actual_sdl_renderer_output") != [w, h] or
                    receipt.get("execution_mode") != "modern" or
                    receipt.get("SDL_driver") != "windows" or
                    receipt.get("native_process_exit") != 0 or
                    receipt.get("observed_in_draw") != 40 or
                    receipt.get("source_bound_by_independent_rebuild") is not False or
                    receipt.get("visual_approved") is not False or
                    receipt.get("hardware_approved") is not False or
                    type(receipt.get("release_gate_credit")) is not int or
                    receipt["release_gate_credit"] != 0 or
                    not re.fullmatch(r"[0-9a-f]{40}", str(receipt.get("source_sha"))) or
                    not re.fullmatch(r"[0-9a-f]{64}", str(receipt.get("exe_sha256")))):
                raise ValueError("unsupported H27 receipt or preapproved claim")
            for kind, key in (("png", "png_sha256"), ("p7", "p7_sha256"),
                              ("log", "native_process_log_sha256")):
                if (not isinstance(receipt.get(key), str) or
                        hashlib.sha256(raw[kind]).hexdigest() != receipt[key]):
                    raise ValueError(f"{w}x{h}: {kind} digest mismatch")
            try:
                lines = raw["log"].decode("utf-8").splitlines()
            except UnicodeError as exc:
                raise ValueError("non-UTF8 native process log") from exc
            captures = [line for line in lines if
                        "UR_MODERN_VISUAL_SDL_CAPTURE" in line]
            if len(captures) != 1 or not _capture(captures[0], w, h):
                raise ValueError("missing or spoofed native SDL capture event")
            records[(w, h)] = (raw, receipt)
    if (records[GEOMETRIES[0]][1]["source_sha"] !=
            records[GEOMETRIES[1]][1]["source_sha"] or
            records[GEOMETRIES[0]][1]["exe_sha256"] !=
            records[GEOMETRIES[1]][1]["exe_sha256"]):
        raise ValueError("compact/wide receipts differ in binary/source identity")

    with tempfile.TemporaryDirectory() as td:
        surfaces = []
        for w, h in GEOMETRIES:
            raw, _receipt = records[(w, h)]
            p7, png = Path(td) / f"{w}x{h}.pam", Path(td) / f"{w}x{h}.png"
            p7.write_bytes(raw["p7"])
            png.write_bytes(raw["png"])
            header = (f"P7\nWIDTH {w}\nHEIGHT {h}\nDEPTH 4\n"
                      "MAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n").encode()
            if (not raw["p7"].startswith(header) or
                    len(raw["p7"]) != len(header) + w * h * 4 or
                    read_png_rgba(png, w, h) != raw["p7"][len(header):]):
                raise ValueError("native P7 and converted PNG disagree")
            surfaces.append(p7)
        grid = audit_pair(*surfaces)
    return {
        "schema": "qa06-h27-sdl-receipt-grid/1",
        "archive_sha256": archive_digest,
        "compact_wide_grid_sha256": grid["source_grid_sha256"],
        "checked_surfaces": ["1024x768", "1280x720"],
        "compact_wide_grid_identical": True,
        "source_bound_by_independent_rebuild": False,
        "actual_native_execution_independently_proven": False,
        "physical_device_approved": False,
        "visual_approved": False,
        "release_gate_credit": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    args = parser.parse_args()
    print(json.dumps(audit_receipt_bundle(args.archive), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
