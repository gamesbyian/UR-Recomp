#!/usr/bin/env python3
"""Fail-closed byte audit of a retained Windows Modern title-attract artifact.

Independent of the Windows producer: inspect exact ZIP members, do not
extract, normalize text newlines or reconstruct any missing frames. This
checks archive integrity, not visual approval, original parity or hardware.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

P6 = re.compile(rb"\AP6\n(\d+) (\d+)\n255\n")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
STAGES = ("original-demo", "restored-title", "root")


def _digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def audit_title_archive(path: Path) -> dict:
    with zipfile.ZipFile(path) as archive:
        entries = archive.namelist()
        if len(entries) != len(set(entries)):
            raise ValueError("duplicate archive members")
        names = set(entries)
        roots = sorted({
            name.removesuffix("/native-attract-receipt.json")
            for name in entries if name.endswith("/native-attract-receipt.json")
        })
        if not roots:
            raise ValueError("no native original-attract receipts")
        results = []
        binaries = set()
        counted = 0
        for folder in roots:
            receipt = json.loads(archive.read(folder + "/native-attract-receipt.json"))
            if receipt.get("schema_version") != 1:
                raise ValueError("unsupported native original-attract receipt")
            sha = receipt.get("candidate_executable_sha256")
            if not isinstance(sha, str) or not SHA256.fullmatch(sha):
                raise ValueError("invalid exact native candidate digest")
            binaries.add(sha)
            if receipt.get("final_sdl_capture") is not False or receipt.get("release_gate_credit") != 0:
                raise ValueError("native pixels improperly promoted to final SDL/release")
            logpath = folder + "/native-attract.log"
            if logpath not in names:
                raise ValueError("missing retained process log: " + folder)
            log = archive.read(logpath)
            if _digest(log) != receipt.get("log_sha256"):
                raise ValueError("retained native log byte SHA256 mismatch: " + folder)
            photos = receipt.get("native_stock_demo_and_wake_presentations", [])
            if not isinstance(photos, list):
                raise ValueError("native photograph receipt is not a list")
            preview = receipt.get("scripted_host_preview_only") is True
            if preview != bool(photos):
                raise ValueError("missing preview images or unexpected source-only images")
            if preview and {p.get("stage") for p in photos} != set(STAGES):
                raise ValueError("not all three original-demo/wake native stages retained")
            if len(photos) != (3 if preview else 0):
                raise ValueError("repeated/missing original visual stages")
            modern = 256 if receipt.get("drawable_aspect") == "4:3" else 342
            observed = []
            for photo in photos:
                stage = photo["stage"]
                name = folder + "/presented/" + photo["file"]
                if photo["file"] != "native-" + stage + ".ppm" or name not in names:
                    raise ValueError("actual native visual evidence absent: " + name)
                raw = archive.read(name)
                match = P6.match(raw)
                if not match:
                    raise ValueError("invalid original native P6 image")
                width, height = int(match[1]), int(match[2])
                target = 256 if stage == "original-demo" else modern
                if (width, height) != (target, 224) or len(raw) != match.end() + width * height * 3:
                    raise ValueError("native original/demo/Modern geometry invalid")
                if _digest(raw) != photo.get("sha256") or width != photo.get("width") or height != photo.get("height"):
                    raise ValueError("retained original native image SHA256/receipt mismatch")
                counted += 1
                observed.append({"stage": stage, "frame": photo.get("guest_frame"),
                                 "size": [width, height], "sha256": _digest(raw)})
            results.append({
                "folder": folder, "wake_route": receipt.get("native_wake_route"),
                "aspect": receipt.get("drawable_aspect"), "recovery": receipt.get("real_guest_main_recovery_verified"),
                "log_sha256": _digest(log), "presented_images": observed,
            })
        if len(binaries) != 1:
            raise ValueError("mixed native executable candidates in title archive")
        return {
            "schema_version": 1,
            "archive_sha256": _digest(path.read_bytes()),
            "scenario_count": len(results),
            "native_presented_images_verified": counted,
            "same_candidate_executable_receipt_sha256": next(iter(binaries)),
            "scenarios": results,
            "original_gameplay_parity_approved": False,
            "final_sdl_capture_approved": False,
            "physical_hardware_approved": False,
            "release_gate_credit": 0,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    try:
        result = audit_title_archive(args.archive.resolve(strict=True))
    except (OSError, ValueError, zipfile.BadZipFile, KeyError, TypeError,
            json.JSONDecodeError) as exc:
        print("MODERN_TITLE_ARTIFACT_AUDIT_REJECTED: " + str(exc))
        return 1
    if args.out:
        args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"MODERN_TITLE_ARTIFACT_AUDIT_OK scenarios={result['scenario_count']} images={result['native_presented_images_verified']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
