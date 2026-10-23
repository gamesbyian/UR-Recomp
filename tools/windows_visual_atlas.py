#!/usr/bin/env python3
"""Windows Visual Atlas: ROM-free manifest validation, real-capture sharding and static assembly.

One atlas ID is one expected surface. A capture is admitted only from the
existing genuine Windows SDL readback driver and an exact matching receipt.
This tool never modifies host/gameplay/ROM bytes and never grants release QA.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "analysis/windows-visual-atlas.json"
WEB = ROOT / "tools/visual_atlas_web"
ART = ROOT / "media/showcase/2026-10-20/graphpaper-final/cards"
ID = re.compile(r"^URV-[A-Z]{2,3}-[0-9]{3}$")
WINDOW = re.compile(r"^([1-9][0-9]*)x([1-9][0-9]*)$")
SHARDS = ("frontend", "interaction", "motion", "authentic")
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_catalog(path: Path = CATALOG) -> dict:
    catalog = json.loads(path.read_text(encoding="utf-8"))
    if catalog.get("schema_version") != 1 or not isinstance(catalog.get("entries"), list):
        raise ValueError("Unknown atlas catalog schema")
    return catalog


def validate(catalog: dict, *, art_directory: Path = ART) -> list[dict]:
    # Import the actual driver route vocabulary so the atlas cannot silently
    # refer to renamed/imaginary fixture routes.
    try:
        from tools.qa_modern_visual_win32_capture_driver import ROUTES
    except ModuleNotFoundError:  # python tools/windows_visual_atlas.py
        from qa_modern_visual_win32_capture_driver import ROUTES
    # The two pre-existing inventories are authoritative for their own
    # original-game fixtures and independent visual acceptance cases.
    # Reject missing/stale crosswalk entries rather than silently claiming
    # coverage when a new source fixture is introduced.
    original = json.loads((ROOT / "analysis/ui-capture-manifest.json").read_text(encoding="utf-8"))
    modern_qa = json.loads((ROOT / "analysis/modern-visual-acceptance-matrix.json").read_text(encoding="utf-8"))
    canonical_original = {item["tag"]: item for item in original["captures"]}
    canonical_qa = {item["id"]: item for item in modern_qa["cases"]}
    seen_original: set[str] = set()
    seen_qa: set[str] = set()
    seen: set[str] = set()
    entries = catalog["entries"]
    if not entries:
        raise ValueError("Atlas cannot be empty")
    for entry in entries:
        key = entry.get("id", "")
        if not isinstance(key, str) or not ID.fullmatch(key) or key in seen:
            raise ValueError(f"Invalid or repeated atlas ID: {key!r}")
        seen.add(key)
        inventory = entry.get("source_inventory")
        if inventory is not None:
            path = inventory.get("path")
            if path == "analysis/ui-capture-manifest.json":
                tag = inventory.get("tag")
                source = canonical_original.get(tag)
                if not tag or tag in seen_original or source is None:
                    raise ValueError(f"{key}: missing, stale or repeated original UI crosswalk")
                if source["state_id"] != inventory.get("original_state") or (
                    source.get("source_fixture") != inventory.get("source_fixture")
                ) or source.get("variant") != inventory.get("variant"):
                    raise ValueError(f"{key}: original UI fixture identity drift")
                seen_original.add(tag)
            elif path == "analysis/modern-visual-acceptance-matrix.json":
                candidate = inventory.get("acceptance_case_id")
                if not candidate or candidate in seen_qa or candidate not in canonical_qa:
                    raise ValueError(f"{key}: missing, stale or repeated visual QA case")
                if entry["mode"] != canonical_qa[candidate]["mode"]:
                    raise ValueError(f"{key}: visual QA presentation drift")
                seen_qa.add(candidate)
            else:
                raise ValueError(f"{key}: unrecognized source inventory reference")
        for field in ("title", "mode", "family", "state", "display", "art"):
            if not isinstance(entry.get(field), str) or not entry[field].strip():
                raise ValueError(f"{key}: missing {field}")
        art = entry["art"]
        if not re.fullmatch(r"[a-z0-9_-]+", art):
            raise ValueError(f"{key}: invalid art identifier")
        if not (art_directory / (art + ".png")).is_file():
            raise ValueError(f"{key}: expected authentic promo plate missing: {art}")
        capture = entry.get("capture")
        if entry.get("kind") not in ("capturable", "planned"):
            raise ValueError(f"{key}: unknown kind")
        if bool(capture) != (entry["kind"] == "capturable"):
            raise ValueError(f"{key}: kind/capture mismatch")
        if capture:
            if capture.get("route") not in ROUTES:
                raise ValueError(f"{key}: capture route not supported by native driver")
            if capture.get("shard") not in SHARDS:
                raise ValueError(f"{key}: unknown job shard")
            match = WINDOW.fullmatch(str(capture.get("size", "")))
            if not match:
                raise ValueError(f"{key}: invalid capture size")
            w, h = map(int, match.groups())
            if not (320 <= w <= 3840 and 224 <= h <= 2160):
                raise ValueError(f"{key}: capture size out of safe driver bounds")
            if (capture["route"] == "authentic-stock") != (entry["mode"] == "authentic"):
                raise ValueError(f"{key}: execution mode mismatches real route")
    if seen_original != set(canonical_original):
        raise ValueError("Atlas original UI coverage drift: " + repr(sorted(set(canonical_original) - seen_original)[:10]))
    if seen_qa != set(canonical_qa):
        raise ValueError("Atlas independent visual QA coverage drift: " + repr(sorted(set(canonical_qa) - seen_qa)[:10]))
    return entries


def valid_receipt(entry: dict, root: Path, source: str, exe_digest: str | None) -> tuple[dict, str]:
    receipt_file = root / "readback-receipt.json"
    png = root / "actual-sdl-drawable.png"
    if not receipt_file.is_file() or not png.is_file() or receipt_file.is_symlink() or png.is_symlink():
        raise ValueError(f"{entry['id']}: incomplete native capture evidence")
    receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
    cap = entry["capture"]
    dimensions = [int(x) for x in cap["size"].split("x")]
    expected = {
        "source_sha": source,
        "native_semantic_route": cap["route"],
        "requested_window_size": dimensions,
        "actual_sdl_renderer_output": dimensions,
        "SDL_driver": "windows",
        "release_gate_credit": 0,
        "visual_approved": False,
        "hardware_approved": False,
    }
    for name, value in expected.items():
        if type(receipt.get(name)) is not type(value) or receipt.get(name) != value:
            raise ValueError(f"{entry['id']}: invalid native receipt {name}")
    digest = receipt.get("exe_sha256")
    if not isinstance(digest, str) or not re.fullmatch(r"[a-f0-9]{64}", digest):
        raise ValueError(f"{entry['id']}: executable provenance absent")
    if exe_digest and exe_digest != digest:
        raise ValueError("Atlas captures used different Windows executables")
    if sha256(png) != receipt.get("png_sha256") or not png.read_bytes().startswith(PNG_SIGNATURE):
        raise ValueError(f"{entry['id']}: captured PNG hash or signature mismatch")
    with png.open("rb") as file:
        file.seek(16)
        width, height = struct.unpack(">II", file.read(8))
    if [width, height] != dimensions:
        raise ValueError(f"{entry['id']}: PNG geometry differs from SDL readback")
    return receipt, digest


def build(catalog: dict, target: Path, captures: Path | None, source: str | None) -> dict:
    entries = validate(catalog)
    if target.exists():
        raise ValueError(f"Refusing to overwrite existing atlas site: {target}")
    target.mkdir(parents=True)
    (target / "assets").mkdir()
    (target / "images").mkdir()
    required_art = sorted({entry["art"] for entry in entries})
    for art in required_art:
        shutil.copyfile(ART / (art + ".png"), target / "assets" / (art + ".png"))
    for name in ("index.html", "atlas.css", "atlas.js"):
        shutil.copyfile(WEB / name, target / name)
    published = []
    exe_digest = None
    counts = {"captured": 0, "capture_failed": 0, "capture_pending": 0, "planned": 0}
    for entry in entries:
        case = dict(entry)
        case["status"] = "planned" if entry["kind"] == "planned" else "capture_pending"
        if captures and entry.get("capture"):
            case_root = captures / "captures" / entry["id"]
            failure = case_root / "capture-failure.json"
            receipt = case_root / "readback-receipt.json"
            if receipt.exists():
                if not source or not re.fullmatch(r"[0-9a-f]{40}", source):
                    raise ValueError("Exact 40-hex source SHA required when publishing captures")
                evidence, exe_digest = valid_receipt(entry, case_root, source, exe_digest)
                image_name = entry["id"] + ".png"
                shutil.copyfile(case_root / "actual-sdl-drawable.png", target / "images" / image_name)
                case["status"] = "captured"
                case["image"] = "images/" + image_name
                case["evidence"] = {
                    "source_sha": evidence["source_sha"],
                    "exe_sha256": evidence["exe_sha256"],
                    "png_sha256": evidence["png_sha256"],
                    "SDL_driver": evidence["SDL_driver"],
                    "capture_route": evidence["native_semantic_route"],
                    "output_pixels": evidence["actual_sdl_renderer_output"],
                    "actual_sdl_final_drawable": True,
                    "physical_screen_verified": False,
                    "release_accepted": False,
                }
            elif failure.exists():
                failure_data = json.loads(failure.read_text(encoding="utf-8"))
                if failure_data.get("id") != entry["id"]:
                    raise ValueError(f"{entry['id']}: unrelated failure marker")
                case["status"] = "capture_failed"
        counts[case["status"]] += 1
        published.append(case)
    data = {
        "schema_version": 1,
        "title": "Uniracers Windows Visual Atlas",
        "source_sha": source if exe_digest else None,
        "exe_sha256": exe_digest,
        "counts": counts,
        "entries": published,
        "provenance": "Only verified final SDL Windows captures are labelled captured. Other imagery is original graph-paper promotional art.",
    }
    (target / "atlas.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return data


def capture_shard(catalog: dict, *, shard: str, exe: Path, rom: Path,
                  target: Path, source: str, timeout: int, workers: int = 2) -> int:
    entries = validate(catalog)
    if shard not in SHARDS or not re.fullmatch(r"[0-9a-f]{40}", source):
        raise ValueError("Invalid shard or source SHA")
    if target.exists():
        raise ValueError("Capture output exists; refusing to overwrite evidence")
    target.mkdir(parents=True)
    matched = [x for x in entries if x.get("capture", {}).get("shard") == shard]
    if not matched:
        raise ValueError("No capture entries assigned to shard")
    if workers not in (1, 2):
        raise ValueError('Native process worker count must be 1 or 2')
    def run_case(entry: dict) -> dict:
        location = target / "captures" / entry["id"]
        location.parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            sys.executable, str(ROOT / "tools/qa_modern_visual_win32_capture_driver.py"),
            "--exe", str(exe.resolve()), "--rom", str(rom.resolve()),
            "--source-sha", source, "--route", entry["capture"]["route"],
            "--window-size", entry["capture"]["size"], "--video", "windows",
            "--timeout", str(timeout), "--out", str(location)
        ]
        # Each driver execution launches native Win32 in its own fresh user root.
        # A failing route does not invent pixels or stop unrelated routes.
        try:
            process = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout * 3)
            if process.returncode != 0:
                raise RuntimeError(f"capture driver exit {process.returncode}: " + (process.stdout + process.stderr)[-1500:])
            valid_receipt(entry, location, source, None)
            status = "captured"
        except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
            location.mkdir(parents=True, exist_ok=True)
            (location / "capture-failure.json").write_text(json.dumps({
                "id": entry["id"], "status": "failed", "reason": str(exc)[:1800]
            }, indent=2) + "\n", encoding="utf-8")
            status = "failed"
        return {"id": entry["id"], "result": status}
    # Bound resident native processes to at most two per Windows runner.
    # Each process owns independent screenshot, config and user-data paths.
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(run_case, matched))
    for result in results:
        print(result["id"], result["result"], flush=True)
    report = json.dumps({
        "shard": shard, "source_sha": source, "results": results,
        "captured": sum(r["result"] == "captured" for r in results),
        "failed": sum(r["result"] == "failed" for r in results),
        "release_gate_credit": 0,
    }, indent=2) + "\n"
    (target / "shard-summary.json").write_text(report, encoding="utf-8")
    # Publish a uniquely named summary inside the allowlisted artifact tree.
    (target / "captures" / f"atlas-shard-{shard}.json").write_text(report, encoding="utf-8")
    # A failed case is reviewable missingness, not a successful visual capture.
    # Never claim QA acceptance; preserve all available evidence.
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("validate")
    assemble = sub.add_parser("build")
    assemble.add_argument("--out", required=True, type=Path)
    assemble.add_argument("--captures", type=Path)
    assemble.add_argument("--source-sha")
    capture = sub.add_parser("capture-shard")
    capture.add_argument("--shard", choices=SHARDS, required=True)
    capture.add_argument("--exe", type=Path, required=True)
    capture.add_argument("--rom", type=Path, required=True)
    capture.add_argument("--out", required=True, type=Path)
    capture.add_argument("--source-sha", required=True)
    capture.add_argument("--timeout", type=int, default=100)
    capture.add_argument("--workers", type=int, choices=(1, 2), default=2)
    args = parser.parse_args()
    try:
        catalog = load_catalog()
        if args.action == "validate":
            print(f"Validated {len(validate(catalog))} unique Windows visual surfaces")
        elif args.action == "build":
            print(json.dumps(build(catalog, args.out, args.captures, args.source_sha)["counts"], indent=2))
        else:
            if not (5 <= args.timeout <= 180):
                raise ValueError("Capture timeout must be 5..180 seconds")
            return capture_shard(catalog, shard=args.shard, exe=args.exe, rom=args.rom,
                                 target=args.out, source=args.source_sha, timeout=args.timeout,
                                 workers=args.workers)
        return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print("WINDOWS_VISUAL_ATLAS_REJECTED:", exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
