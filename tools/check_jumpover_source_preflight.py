#!/usr/bin/env python3
"""Verify the pinned Jumpover source preflight against original SMVs and Lua.

Static provenance only: this does not replay a movie or admit a native fixture.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class EvidenceError(ValueError):
    """Source evidence is missing, malformed, or inconsistent."""


def require(label: str, actual: object, expected: object) -> None:
    if actual != expected:
        raise EvidenceError(f"{label}: expected {expected!r}, got {actual!r}")


def blob_sha1(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def input_runs(samples: list[int]) -> list[dict]:
    result: list[dict] = []
    for frame, mask in enumerate(samples):
        if result and result[-1]["mask"] == f"{mask:04x}":
            result[-1]["duration"] += 1
        else:
            result.append({"start": frame, "duration": 1, "mask": f"{mask:04x}"})
    return result


def source_bytes(root: Path, rel: str) -> bytes:
    path = Path(rel)
    if path.is_absolute() or ".." in path.parts:
        raise EvidenceError(f"source path escapes repository: {rel}")
    full = (root / path).resolve()
    if not full.is_relative_to(root.resolve()):
        raise EvidenceError(f"source path escapes repository: {rel}")
    try:
        return full.read_bytes()
    except OSError as exc:
        raise EvidenceError(f"cannot read {rel}: {exc}") from exc


def unique_routes(rows: object, label: str) -> dict:
    if not isinstance(rows, list) or len(rows) != 2:
        raise EvidenceError(f"{label}: expected exactly two routes")
    result = {row.get("route"): row for row in rows if isinstance(row, dict)}
    if set(result) != {"left", "right"} or len(result) != len(rows):
        raise EvidenceError(f"{label}: expected one left and one right route")
    return result


def verify_preflight(root: Path, evidence: dict) -> dict:
    """Fail closed on changed source blobs, input streams, anchors, or scripts."""
    require("schema_version", evidence.get("schema_version"), 1)
    require("kind", evidence.get("kind"), "static-source-preflight")
    movies = unique_routes(evidence.get("movies"), "movies")
    scripts = unique_routes(evidence.get("historical_scripts"), "historical_scripts")

    # Reuse the project's SMV/freeze authority rather than a second parser.
    from extract_smv_freeze import summarize_movie
    from probe_jumpover_fallthrough import controller_samples

    checked: list[dict] = []
    for route in ("left", "right"):
        movie = movies[route]
        rel = movie["path"]
        raw = source_bytes(root, rel)
        require(f"{route} SMV blob", blob_sha1(raw), movie["git_blob_sha1"])
        require(f"{route} SMV size", len(raw), movie["size_bytes"])
        try:
            summary, _ = summarize_movie(root / rel, rel)
            samples = controller_samples(raw)
        except (ValueError, struct.error, OSError) as exc:
            raise EvidenceError(f"{route} invalid SMV: {exc}") from exc
        for field in (
            "smv_version", "uid", "frame_count_header", "controller_mask",
            "movie_options", "reset_anchored", "savestate_offset", "controller_data_offset",
        ):
            require(f"{route} {field}", summary[field], movie[field])
        require(f"{route} controller count", len(samples), movie["controller_samples"])
        require(f"{route} raw input runs", input_runs(samples), movie["raw_input_runs"])
        require(f"{route} reset markers", [i for i, v in enumerate(samples) if v == 0xffff], movie["reset_markers"])
        require(f"{route} port types", list(raw[0x24:0x26]), movie["port_types"])
        require(f"{route} trailing bytes", len(raw) - summary["controller_data_offset"] - 2 * len(samples), movie["trailing_bytes"])
        anchor = movie["embedded_anchor"]
        require(f"{route} freeze SHA256", summary["freeze_sha256"], anchor["freeze_sha256"])
        require(f"{route} WRAM SHA256", summary["wram_sha256"], anchor["wram_sha256"])
        if summary["cpu_registers"] is None:
            raise EvidenceError(f"{route} missing CPU registers")
        require(f"{route} anchor PC", summary["cpu_registers"]["pb_pc"], anchor["cpu_pb_pc"])

        script = scripts[route]
        lua = source_bytes(root, script["path"])
        require(f"{route} Lua blob", blob_sha1(lua), script["git_blob_sha1"])
        text = lua.decode("utf-8")
        match = re.search(r"for\s+i\s*=\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s+do", text)
        if match is None:
            raise EvidenceError(f"{route} Lua missing X sweep")
        sweep = script["x_sweep"]
        require(f"{route} X sweep", tuple(map(int, match.groups())), (sweep["start"], sweep["stop"], sweep["step"]))
        for marker in ("savestate.create(11)", "savestate.load(startSS)", "memory.writeword(RAM.uniXPos, xPos)", "uniXPos = 0x7e0411"):
            if marker not in text:
                raise EvidenceError(f"{route} Lua missing {marker}")
        success = script["reported_successful_x"]
        if not re.search(rf"\b{success}{'l' if route == 'left' else 'r'}\b", text):
            raise EvidenceError(f"{route} Lua missing reported successful X {success}")
        checked.append({"route": route, "controller_samples": len(samples), "freeze_sha256": summary["freeze_sha256"]})
    return {"status": "PASS", "kind": "static-source-preflight", "routes": checked, "native_admitted": False}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--evidence", type=Path, default=Path("analysis/generated/jumpover-fallthrough-source-preflight.json"))
    args = ap.parse_args(argv)
    try:
        doc = json.loads((args.root / args.evidence).read_text(encoding="utf-8"))
        result = verify_preflight(args.root, doc)
    except (EvidenceError, OSError, ValueError, KeyError, UnicodeError) as exc:
        print(f"JUMPOVER_SOURCE_PREFLIGHT FAIL: {exc}", file=sys.stderr)
        return 2
    print("JUMPOVER_SOURCE_PREFLIGHT " + json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
