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


def load_memory(path: Path, source: str) -> bytes:
    raw = path.read_bytes()
    if source == "wram" and len(raw) < 0x20000:
        raise ValueError(f"{path}: WRAM dump is only {len(raw)} bytes")
    if not raw:
        raise ValueError(f"{path}: {source.upper()} dump is empty")
    return raw


def field_value(memory: bytes, spec: dict[str, Any]) -> int:
    source = spec.get("source", "wram")
    if source not in {"wram", "sram"}:
        raise ValueError(f"unsupported field source {source!r}")
    offset_key = f"{source}_offset"
    if offset_key not in spec:
        raise ValueError(f"field source {source!r} requires {offset_key}")
    offset = parse_int(spec[offset_key])
    width = int(spec.get("width", 1))
    if width not in (1, 2, 4):
        raise ValueError(f"unsupported field width {width}")
    end = offset + width
    if end > len(memory):
        raise ValueError(
            f"field at 0x{offset:X} width {width} exceeds {source.upper()} dump"
        )
    return int.from_bytes(memory[offset:end], "little")


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
    sram_path = discover_file(tag, ".sram.bin", roots)
    bmp_path = discover_file(tag, ".fb.bmp", roots)
    info_path = discover_file(tag, ".info.json", roots)

    if wram_path:
        result["files"]["wram"] = str(wram_path)
    if sram_path:
        result["files"]["sram"] = str(sram_path)
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
        memories = {"wram": load_memory(wram_path, "wram")}
        if sram_path:
            memories["sram"] = load_memory(sram_path, "sram")
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
        source = spec.get("source", "wram")
        memory = memories.get(source)
        if memory is None:
            result["mismatches"].append(
                f"{name}: {source.upper()} dump missing for requested field"
            )
            continue
        try:
            value = field_value(memory, spec)
        except ValueError as exc:
            result["mismatches"].append(f"{name}: {exc}")
            continue
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



def select_captures(
    captures: list[dict[str, Any]],
    include_source_fixtures: list[str] | None = None,
    exclude_source_fixtures: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Select manifest captures by workflow-owned source fixtures."""
    selected = list(captures)
    if include_source_fixtures:
        wanted = set(include_source_fixtures)
        selected = [c for c in selected if c.get("source_fixture") in wanted]
    if exclude_source_fixtures:
        excluded = set(exclude_source_fixtures)
        selected = [c for c in selected if c.get("source_fixture") not in excluded]
    return selected


def discover_unclassified_captures(
    declared_tags: set[str],
    fields: dict[str, dict[str, Any]],
    roots: list[Path],
) -> list[dict[str, Any]]:
    """Surface dump tags that exist on disk but are not yet in the capture manifest."""
    tags: set[str] = set()
    for root in roots:
        if not root.is_dir():
            continue
        for bmp in root.glob("*.fb.bmp"):
            tags.add(bmp.name[:-len(".fb.bmp")])
        for wram in root.glob("*.wram.bin"):
            tags.add(wram.name[:-len(".wram.bin")])

    out = []
    for tag in sorted(tags - declared_tags):
        synthetic = {
            "tag": tag,
            "state_id": "UNCLASSIFIED",
            "variant": "raw-evidence",
            "required": False,
            "discover": [
                name for name in (
                    "current_menu", "selected_option", "menu_row", "menu_col", "in_race"
                ) if name in fields
            ],
        }
        item = analyze_capture(synthetic, fields, roots)
        item["classification_status"] = "unclassified"
        out.append(item)
    return out

def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# UI Atlas Capture Report",
        "",
        f"Manifest: `{report['manifest']}`",
        "",
        "| State | Variant | Tag | Required | Frame | Menu | Selected | In race | Visual leads | Blockers | Framebuffer | Status |",
        "|---|---|---|---|---:|---:|---:|---:|---:|---|---|---|",
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
            "| {state} | {variant} | `{tag}` | {required} | {frame} | {menu} | {sel} | {race} | {refs} | {blockers} | {fb} | {status} |".format(
                state=item["state_id"],
                variant=item.get("variant") or "",
                tag=item["tag"],
                required="yes" if item.get("required", True) else "no",
                frame=item.get("frame", ""),
                menu=obs.get("current_menu", ""),
                sel=obs.get("selected_option", ""),
                race=obs.get("in_race", ""),
                refs=len(item.get("visual_references", [])),
                blockers=", ".join(item.get("blockers", [])),
                fb=fb_text,
                status=item["status"],
            )
        )
        for mismatch in item.get("mismatches", []):
            lines.append(f"|  |  |  |  |  |  |  |  |  |  | ↳ {mismatch} |  |")

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
        f"- unclassified raw captures: {report['summary'].get('unclassified', 0)}",
        f"- total atlas cards: {report['summary'].get('total_cards', report['summary']['declared'])}",
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
    ap.add_argument("--reference-index", type=Path,
                    help="Optional analysis/ui-reference-index.json")
    ap.add_argument("--transition-contract", type=Path,
                    help="Optional analysis/ui-transition-contract.json")
    ap.add_argument("--include-unclassified", action="store_true",
                    help="include dump tags not declared in the capture manifest as UNCLASSIFIED cards")
    ap.add_argument("--source-fixture", action="append",
                    help="only include captures owned by this source_fixture; repeatable")
    ap.add_argument("--exclude-source-fixture", action="append",
                    help="exclude captures owned by this source_fixture; repeatable")
    ap.add_argument("--out-json", type=Path)
    ap.add_argument("--out-md", type=Path)
    ap.add_argument("--strict", action="store_true",
                    help="exit nonzero on missing, invalid, or mismatched captures")
    args = ap.parse_args()

    manifest = json.loads(args.manifest.read_text())
    fields = manifest["fields"]
    roots = args.dump_dir
    selected_captures = select_captures(
        manifest["captures"],
        include_source_fixtures=args.source_fixture,
        exclude_source_fixtures=args.exclude_source_fixture,
    )
    captures = [analyze_capture(c, fields, roots) for c in selected_captures]
    if args.include_unclassified:
        declared_tags = {c["tag"] for c in manifest["captures"]}
        captures.extend(discover_unclassified_captures(declared_tags, fields, roots))

    refs_by_state: dict[str, list[dict[str, Any]]] = {}
    if args.reference_index:
        reference_index = json.loads(args.reference_index.read_text())
        for entry in reference_index.get("entries", []):
            refs_by_state.setdefault(entry["state_id"], []).extend(
                entry.get("references", [])
            )

    blockers_by_state: dict[str, set[str]] = {}
    capability_dependencies: dict[str, Any] = {}
    if args.transition_contract:
        transition_contract = json.loads(args.transition_contract.read_text())
        capability_dependencies = transition_contract.get("capability_dependencies", {})
        incoming: dict[str, list[dict[str, Any]]] = {}
        for edge in transition_contract.get("edges", []):
            incoming.setdefault(edge["to"], []).append(edge)
        for state, edges in incoming.items():
            open_blocked = [
                e for e in edges
                if e.get("blocked_by")
                and capability_dependencies.get(e["blocked_by"], {}).get("status") != "complete"
            ]
            unblocked = [
                e for e in edges
                if not e.get("blocked_by")
                or capability_dependencies.get(e.get("blocked_by"), {}).get("status") == "complete"
            ]
            if edges and open_blocked and not unblocked:
                blockers_by_state[state] = {e["blocked_by"] for e in open_blocked}

    for item in captures:
        state = item["state_id"]
        item["visual_references"] = refs_by_state.get(state, [])
        item["blockers"] = sorted(blockers_by_state.get(state, set()))
    counts = {k: sum(1 for c in captures if c["status"] == k)
              for k in ("ok", "partial", "mismatch", "missing", "invalid")}
    report = {
        "schema_version": 1,
        "manifest": str(args.manifest),
        "dump_dirs": [str(p) for p in roots],
        "captures": captures,
        "summary": {
            "declared": len(selected_captures),
            "unclassified": sum(1 for c in captures if c.get("classification_status") == "unclassified"),
            "total_cards": len(captures),
            "states_with_visual_references": len(refs_by_state),
            "open_capability_dependencies": sum(
                1 for dep in capability_dependencies.values()
                if dep.get("status") != "complete"
            ),
            **counts,
        },
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
        c.get("required", True) and c["status"] in {"partial", "mismatch", "missing", "invalid"}
        for c in captures
    ):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
