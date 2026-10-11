#!/usr/bin/env python3
"""Validate offline HD-art/scaler trial provenance and emit a compact candidate report.

This is NOT an art-acceptance validator. It validates input/output identity and
experiment bookkeeping; only the existing Racer-HD/native review approves art.
No network, GPU, model weights, ROM, or third-party runtime is needed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

SCHEMA = "UR-HD-UPSCALE-TRIALS/1"
PNG_SIG = b"\x89PNG\r\n\x1a\n"
DECISIONS = {"unreviewed", "rejected", "needs_refinement", "candidate_for_hd_review"}
KINDS = {"art_4x", "display_reference"}
ASSETS = {"racer_pose", "environment", "frontend", "typography", "full_frame"}


class TrialError(ValueError):
    pass


def ensure(test: bool, message: str):
    if not test:
        raise TrialError(message)


def asset_path(base: Path, value: str) -> Path:
    ensure(isinstance(value, str) and value and not Path(value).is_absolute(),
           "asset path must be a nonempty relative path")
    ensure(all(part not in (".", "..") for part in Path(value).parts),
           "asset path contains traversal")
    target = (base / value).resolve()
    ensure(target.is_relative_to(base.resolve()), "asset escapes manifest directory")
    ensure(target.is_file(), f"missing asset: {value}")
    return target


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def png_meta(path: Path) -> tuple[int, int, int]:
    with path.open("rb") as stream:
        header = stream.read(29)
    ensure(header[:8] == PNG_SIG and header[12:16] == b"IHDR"
           and struct.unpack(">I", header[8:12])[0] == 13,
           f"not a valid PNG IHDR: {path.name}")
    w, h, depth, color_type = struct.unpack(">IIBB", header[16:26])
    ensure(0 < w <= 32768 and 0 < h <= 32768 and depth in (1, 2, 4, 8, 16)
           and color_type in (0, 2, 3, 4, 6), "invalid PNG dimensions/type")
    return w, h, color_type


def check_identity(base: Path, record: dict, label: str):
    ensure(isinstance(record, dict), f"{label} must be an object")
    path = asset_path(base, record.get("path"))
    claimed = record.get("sha256")
    ensure(isinstance(claimed, str) and len(claimed) == 64
           and all(c in "0123456789abcdef" for c in claimed),
           f"{label} must have a lowercase 64-character SHA-256")
    measured = digest(path)
    ensure(measured == claimed, f"{label} SHA-256 mismatch: {record['path']}")
    return path, png_meta(path)


def nonempty(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate(manifest: Path) -> dict:
    base = manifest.resolve().parent
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    ensure(isinstance(payload, dict) and payload.get("schema") == SCHEMA, "unsupported schema")
    source = payload.get("source")
    ensure(isinstance(source, dict), "missing source")
    ensure(source.get("asset_kind") in ASSETS, "unknown source asset kind")
    ensure(nonempty(source.get("semantic_id")), "source semantic_id required")
    provenance = source.get("provenance")
    ensure(isinstance(provenance, dict)
           and nonempty(provenance.get("capture_or_extraction"))
           and nonempty(provenance.get("rom_or_source_identity")),
           "source extraction/capture and ROM/source identity required")
    _, (sw, sh, _) = check_identity(base, source, "source")
    trials = payload.get("candidates")
    ensure(isinstance(trials, list) and len(trials) > 0, "nonempty candidates array required")
    seen = set()
    counts = {status: 0 for status in sorted(DECISIONS)}
    methods = set()
    report_candidates = []
    for i, trial in enumerate(trials):
        label = f"candidates[{i}]"
        ensure(isinstance(trial, dict), f"{label} must be object")
        ident = trial.get("id")
        ensure(nonempty(ident) and ident not in seen, f"{label}: unique id required")
        seen.add(ident)
        kind = trial.get("kind")
        ensure(kind in KINDS, f"{label}: invalid kind")
        status = trial.get("decision")
        ensure(status in DECISIONS, f"{label}: invalid decision (no automatic approvals)")
        method = trial.get("method")
        ensure(isinstance(method, dict)
               and nonempty(method.get("name"))
               and nonempty(method.get("revision_or_model_id"))
               and isinstance(method.get("settings"), dict),
               f"{label}: exact method name, revision/model, settings required")
        methods.add(method["name"])
        if method.get("generative") is True:
            generation = trial.get("generation")
            ensure(isinstance(generation, dict)
                   and nonempty(generation.get("prompt_or_prompt_sha256"))
                   and nonempty(generation.get("provider"))
                   and nonempty(generation.get("request_id"))
                   and nonempty(generation.get("model_version")),
                   f"{label}: generative request provenance incomplete")
        if status != "unreviewed":
            ensure(nonempty(trial.get("review_reason")), f"{label}: review reason required")
        _, (ow, oh, _) = check_identity(base, trial.get("output"), label)
        if kind == "art_4x":
            ensure((ow, oh) == (4 * sw, 4 * sh),
                   f"{label}: art_4x output must be exactly four times source dimensions")
            ensure(source["asset_kind"] != "full_frame" or nonempty(trial.get("scene_policy")),
                   f"{label}: full-frame art needs an explicit scene policy")
        else:
            ensure(isinstance(trial.get("display_policy"), dict)
                   and trial["display_policy"].get("pixel_aspect") in ("raw_1_1", "snes_7_6", "square_output")
                   and nonempty(trial["display_policy"].get("view"))
                   and nonempty(trial["display_policy"].get("treatment")),
                   f"{label}: display pixel aspect, view and treatment must be explicit")
        counts[status] += 1
        report_candidates.append({"id": ident, "kind": kind,
                                  "decision": status, "method": method["name"],
                                  "output_sha256": trial["output"]["sha256"]})
    return {"schema": "UR-HD-UPSCALE-TRIAL-REPORT/1",
            "source_semantic_id": source["semantic_id"],
            "source_sha256": source["sha256"],
            "source_dimensions": [sw, sh],
            "candidate_count": len(report_candidates),
            "counts": counts,
            "methods": sorted(methods),
            "shipping_approvals": 0,
            "note": "No candidate is shipping-approved by this evidence-only validator.",
            "candidates": report_candidates}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("manifest", type=Path)
    p.add_argument("--report", type=Path)
    args = p.parse_args()
    try:
        report = validate(args.manifest)
    except (TrialError, OSError, json.JSONDecodeError, TypeError, KeyError) as exc:
        p.exit(2, f"invalid upscale trial: {exc}\n")
    value = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(value, encoding="utf-8")
    print(value, end="")


if __name__ == "__main__":
    main()
