#!/usr/bin/env python3
"""Build a compact UI atlas report from SNESRecomp state dumps.

Consumes the project UI capture manifest plus one or more dump directories.
No third-party packages are required.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def parse_int(value: str | int) -> int:
    if isinstance(value, int):
        return value
    return int(value, 0)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def bmp_dimensions(path: Path) -> tuple[int | None, int | None]:
    raw = path.read_bytes()[:26]
    if len(raw) < 26 or raw[:2] != b"BM":
        return None, None
    w = int.from_bytes(raw[18:22], "little", signed=True)
    h = int.from_bytes(raw[22:26], "little", signed=True)
    return abs(w), abs(h)


def load_wram(path: Path) -> bytes:
    raw = path.read_bytes()
    if len(raw) < 0x20000:
        raise ValueError(f"{path}: WRAM dump is only {len(raw)} bytes")
    return raw


def field_value(wram: bytes, spec: dict[str, Any]) -> int:
    offset = parse_int(spec["wram_offset"])
    width = int(spec.get("width", 1))
    if width not in (1, 2, 4):
        raise ValueError(f"unsupported field width {width}")
    end = offset + width
    if end > len(wram):
        raise ValueError(f"field at 0x{offset:X} width {width} exceeds WRAM dump")
    return int.from_bytes(wram[offset:end], "little")


def discover_file(tag: str, suffix: str, roots: list[Path]) -> Path | None:
    for root in roots:
        candidate = root / f"{tag}{suffix}"
        if candidate.is_file():
            return candidate
    return None


def analyze_capture(
    capture: dict[str, Any],
    fields: dict[str, dict[str, Any]],
    roots: list[Path],
) -> dict[str, Any]:
    tag = capture["tag"]
    result: dict[str, Any] = {
        "tag": tag,
        "state_id": capture["state_id"],
        "variant": capture.get("variant"),
        "source_fixture": capture.get("source_fixture"),
        "required": capture.get("required", True),
        "status": "missing",
        "expected": capture.get("expect", {}),
        "discover": capture.get("discover", []),
        "observed": {},
        "files": {},
        "mismatches": [],
    }

    wram_path = discover_file(tag, ".wram.bin", roots)
    bmp_path = discover_file(tag, ".fb.bmp", roots)
    info_path = discover_file(tag, ".info.json", roots)

    if wram_path:
        result["files"]["wram"] = str(wram_path)
    if bmp_path:
        result["files"]["framebuffer"] = str(bmp_path)
        width, height = bmp_dimensions(bmp_path)
        result["framebuffer"] = {
            "sha256": sha256(bmp_path),
            "size_bytes": bmp_path.stat().st_size,
            "width": width,
            "height": height,
        }
    if info_path:
        result["files"]["info"] = str(info_path)
        try:
            info = json.loads(info_path.read_text())
            result["frame"] = info.get("frame")
            result["dump_info"] = info
        except (json.JSONDecodeError, OSError) as exc:
            result["info_error"] = str(exc)

    if not wram_path:
        return result

    try:
        wram = load_wram(wram_path)
    except (OSError, ValueError) as exc:
        result["status"] = "invalid"
        result["error"] = str(exc)
        return result

    wanted_fields = set(capture.get("expect", {})) | set(capture.get("discover", []))
    # Always expose these cheap orientation fields when defined.
    wanted_fields |= {"current_menu", "selected_option", "menu_row", "menu_col", "in_race"}

    for name in sorted(wanted_fields):
        spec = fields.get(name)
        if spec is None:
            result["mismatches"].append(f"manifest references unknown field {name}")
            continue
        value = field_value(wram, spec)
        result["observed"][name] = f"0x{value:0{int(spec.get('width', 1))*2}X}"

    for name, expected in capture.get("expect", {}).items():
        observed = result["observed"].get(name)
        expected_value = parse_int(expected)
        spec = fields[name]
        expected_hex = f"0x{expected_value:0{int(spec.get('width', 1))*2}X}"
        if observed != expected_hex:
            result["mismatches"].append(
                f"{name}: expected {expected_hex}, observed {observed}"
            )

    result["status"] = "ok" if not result["mismatches"] else "mismatch"
    if bmp_path is None:
        result["mismatches"].append("framebuffer BMP missing")
        result["status"] = "partial" if result["status"] == "ok" else result["status"]
    return result


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# UI Atlas Capture Report",
        "",
        f"Manifest: `{report['manifest']}`",
        "",
        "| State | Variant | Tag | Required | Frame | Menu | Selected | In race | Framebuffer | Status |",
        "|---|---|---|---|---:|---:|---:|---:|---|---|",
    ]
    for item in report["captures"]:
        obs = item.get("observed", {})
        fb = item.get("framebuffer", {})
        fb_text = ""
        if fb:
            dims = ""
            if fb.get("width") and fb.get("height"):
                dims = f"{fb['width']}x{fb['height']} "
            fb_text = f"{dims}`{fb.get('sha256', '')[:12]}`"
        lines.append(
            "| {state} | {variant} | `{tag}` | {frame} | {menu} | {sel} | {race} | {fb} | {status} |".format(
                state=item["state_id"],
                variant=item.get("variant") or "",
                tag=item["tag"],
                required="yes" if item.get("required", True) else "no",
                frame=item.get("frame", ""),
                menu=obs.get("current_menu", ""),
                sel=obs.get("selected_option", ""),
                race=obs.get("in_race", ""),
                fb=fb_text,
                status=item["status"],
            )
        )
        for mismatch in item.get("mismatches", []):
            lines.append(f"|  |  |  |  |  |  |  |  | ↳ {mismatch} |  |")

    discoveries = []
    for item in report["captures"]:
        for field in item.get("discover", []):
            value = item.get("observed", {}).get(field)
            if value is not None:
                discoveries.append((item["state_id"], item["tag"], field, value))
    if discoveries:
        lines.extend(["", "## Discoveries", ""])
        for state, tag, field, value in discoveries:
            lines.append(f"- `{state}` / `{tag}`: {field} = `{value}`")

    lines.extend([
        "",
        "## Summary",
        "",
        f"- captures declared: {report['summary']['declared']}",
        f"- complete/ok: {report['summary']['ok']}",
        f"- partial: {report['summary']['partial']}",
        f"- mismatched: {report['summary']['mismatch']}",
        f"- missing: {report['summary']['missing']}",
        f"- invalid: {report['summary']['invalid']}",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, default=Path("analysis/ui-capture-manifest.json"))
    ap.add_argument("--dump-dir", action="append", type=Path, required=True,
                    help="Directory containing <tag>.wram.bin / <tag>.fb.bmp dumps; repeatable")
    ap.add_argument("--out-json", type=Path)
    ap.add_argument("--out-md", type=Path)
    ap.add_argument("--strict", action="store_true",
                    help="exit nonzero on missing, invalid, or mismatched captures")
    args = ap.parse_args()

    manifest = json.loads(args.manifest.read_text())
    fields = manifest["fields"]
    roots = args.dump_dir
    captures = [analyze_capture(c, fields, roots) for c in manifest["captures"]]
    counts = {k: sum(1 for c in captures if c["status"] == k)
              for k in ("ok", "partial", "mismatch", "missing", "invalid")}
    report = {
        "schema_version": 1,
        "manifest": str(args.manifest),
        "dump_dirs": [str(p) for p in roots],
        "captures": captures,
        "summary": {"declared": len(captures), **counts},
    }

    encoded = json.dumps(report, indent=2) + "\n"
    md = render_markdown(report)

    if args.out_json:
        args.out_json.parent.mkdir(parents=True, exist_ok=True)
        args.out_json.write_text(encoded)
    else:
        print(encoded, end="")

    if args.out_md:
        args.out_md.parent.mkdir(parents=True, exist_ok=True)
        args.out_md.write_text(md + "\n")

    if args.strict and any(
        c.get("required", True) and c["status"] in {"mismatch", "missing", "invalid"}
        for c in captures
    ):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
