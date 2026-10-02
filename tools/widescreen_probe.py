#!/usr/bin/env python3
"""Create and validate read-only widescreen reconnaissance reports.

This tool implements the report contract in docs/WIDESCREEN-RECONNAISSANCE.md.
It does not launch an emulator or alter game/runtime behavior.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = ROOT / "analysis" / "widescreen-policy.yml"

_LIST_RE = re.compile(r"^  - (.+)$")
_ID_RE = re.compile(r"^  - id: (.+)$")
_MARGINS_RE = re.compile(r"^  source_pixel_margins: \[(.*)\]$")


def load_policy(path: Path) -> dict[str, Any]:
    """Read the small policy vocabulary without adding a YAML dependency."""
    lines = path.read_text(encoding="utf-8").splitlines()
    section: str | None = None
    margins: list[int] = []
    artifact_classes: list[str] = []
    aspect_policies: list[str] = []
    scenes: list[str] = []

    for line in lines:
        if line and not line.startswith(" "):
            key = line.split(":", 1)[0]
            section = key
            continue

        m = _MARGINS_RE.match(line)
        if m:
            margins = [int(part.strip(), 0) for part in m.group(1).split(",") if part.strip()]
            continue

        if section == "probe":
            stripped = line.strip()
            if stripped == "artifact_classes:":
                section = "probe_artifact_classes"
                continue
        elif section == "probe_artifact_classes":
            m = _LIST_RE.match(line)
            if m:
                artifact_classes.append(m.group(1).strip().strip('"'))
                continue
            if line.startswith("  ") and not line.startswith("    "):
                section = "probe"

        if section == "aspect_policies":
            m = _ID_RE.match(line)
            if m:
                aspect_policies.append(m.group(1).strip().strip('"'))
        elif section == "scenes":
            m = _ID_RE.match(line)
            if m:
                scenes.append(m.group(1).strip().strip('"'))

    if not margins:
        raise ValueError(f"{path}: source_pixel_margins not found")
    if not artifact_classes:
        raise ValueError(f"{path}: artifact_classes not found")
    if not aspect_policies:
        raise ValueError(f"{path}: aspect policies not found")
    if not scenes:
        raise ValueError(f"{path}: scenes not found")

    return {
        "source_pixel_margins": margins,
        "artifact_classes": artifact_classes,
        "aspect_policies": aspect_policies,
        "scenes": scenes,
    }


def new_report(
    policy: dict[str, Any],
    *,
    fixture: str,
    scene: str,
    aspect_policy: str,
    engine: str,
    revision: str,
    checkpoint_range: str,
    pixel_aspect: str,
    overscan_policy: str,
    layer_sprite_window_policy: str,
) -> dict[str, Any]:
    if scene not in policy["scenes"]:
        raise ValueError(f"unknown scene {scene!r}")
    if aspect_policy not in policy["aspect_policies"]:
        raise ValueError(f"unknown aspect policy {aspect_policy!r}")
    return {
        "schema_version": 1,
        "fixture": fixture,
        "scene": scene,
        "aspect_policy": aspect_policy,
        "runtime": {
            "engine": engine,
            "revision": revision,
        },
        "provenance": {
            "checkpoint_range": checkpoint_range,
            "pixel_aspect": pixel_aspect,
            "overscan_policy": overscan_policy,
            "layer_sprite_window_policy": layer_sprite_window_policy,
        },
        "runs": [
            {
                "margin": margin,
                "first_failure_frame": None,
                "class": "unknown",
                "surface": "unresolved",
                "evidence": [],
            }
            for margin in policy["source_pixel_margins"]
        ],
    }


def validate_report(report: dict[str, Any], policy: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    if report.get("schema_version") != 1:
        errors.append("schema_version must be 1")

    for key in ("fixture", "scene", "aspect_policy"):
        if not isinstance(report.get(key), str) or not report[key].strip():
            errors.append(f"{key} must be a non-empty string")

    if report.get("scene") not in policy["scenes"]:
        errors.append(f"scene {report.get('scene')!r} is not declared by widescreen policy")
    if report.get("aspect_policy") not in policy["aspect_policies"]:
        errors.append(
            f"aspect_policy {report.get('aspect_policy')!r} is not declared by widescreen policy"
        )

    runtime = report.get("runtime")
    if not isinstance(runtime, dict):
        errors.append("runtime must be an object")
    else:
        for key in ("engine", "revision"):
            if not isinstance(runtime.get(key), str) or not runtime[key].strip():
                errors.append(f"runtime.{key} must be a non-empty string")

    provenance = report.get("provenance")
    if not isinstance(provenance, dict):
        errors.append("provenance must be an object")
    else:
        for key in (
            "checkpoint_range",
            "pixel_aspect",
            "overscan_policy",
            "layer_sprite_window_policy",
        ):
            if not isinstance(provenance.get(key), str) or not provenance[key].strip():
                errors.append(f"provenance.{key} must be a non-empty string")

    runs = report.get("runs")
    if not isinstance(runs, list) or not runs:
        errors.append("runs must be a non-empty list")
        return errors

    seen: set[int] = set()
    for index, run in enumerate(runs):
        where = f"runs[{index}]"
        if not isinstance(run, dict):
            errors.append(f"{where} must be an object")
            continue

        margin = run.get("margin")
        if not isinstance(margin, int) or isinstance(margin, bool) or margin < 0:
            errors.append(f"{where}.margin must be a non-negative integer")
        else:
            if margin in seen:
                errors.append(f"{where}.margin duplicates margin {margin}")
            seen.add(margin)

        frame = run.get("first_failure_frame")
        if frame is not None and (
            not isinstance(frame, int) or isinstance(frame, bool) or frame < 0
        ):
            errors.append(f"{where}.first_failure_frame must be null or a non-negative integer")

        klass = run.get("class")
        if klass not in policy["artifact_classes"]:
            errors.append(f"{where}.class {klass!r} is not declared by widescreen policy")

        if not isinstance(run.get("surface"), str) or not run["surface"].strip():
            errors.append(f"{where}.surface must be a non-empty string")

        evidence = run.get("evidence")
        if not isinstance(evidence, list) or not all(
            isinstance(item, str) and item.strip() for item in evidence
        ):
            errors.append(f"{where}.evidence must be a list of non-empty strings")

    missing = [m for m in policy["source_pixel_margins"] if m not in seen]
    if missing:
        errors.append(
            "runs omit default source-pixel margins: " + ", ".join(str(m) for m in missing)
        )
    if 0 not in seen:
        errors.append("runs must include margin 0 as the matched 4:3 control")

    return errors


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    sub = ap.add_subparsers(dest="command", required=True)

    new = sub.add_parser("new", help="emit a policy-aligned reconnaissance report skeleton")
    new.add_argument("--fixture", required=True)
    new.add_argument("--scene", required=True)
    new.add_argument("--aspect-policy", required=True)
    new.add_argument("--engine", required=True)
    new.add_argument("--revision", required=True)
    new.add_argument("--checkpoint-range", required=True)
    new.add_argument("--pixel-aspect", required=True)
    new.add_argument("--overscan-policy", required=True)
    new.add_argument("--layer-sprite-window-policy", required=True)
    new.add_argument("--out", type=Path)

    validate = sub.add_parser("validate", help="validate an existing report")
    validate.add_argument("report", type=Path)

    args = ap.parse_args()
    policy = load_policy(args.policy)

    if args.command == "new":
        report = new_report(
            policy,
            fixture=args.fixture,
            scene=args.scene,
            aspect_policy=args.aspect_policy,
            engine=args.engine,
            revision=args.revision,
            checkpoint_range=args.checkpoint_range,
            pixel_aspect=args.pixel_aspect,
            overscan_policy=args.overscan_policy,
            layer_sprite_window_policy=args.layer_sprite_window_policy,
        )
        text = json.dumps(report, indent=2, sort_keys=True) + "\n"
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(text, encoding="utf-8")
        else:
            print(text, end="")
        return 0

    report = json.loads(args.report.read_text(encoding="utf-8"))
    errors = validate_report(report, policy)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(
        f"WIDESCREEN_PROBE_REPORT_VALID fixture={report['fixture']} "
        f"scene={report['scene']} runs={len(report['runs'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
