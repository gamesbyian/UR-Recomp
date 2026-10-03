#!/usr/bin/env python3
"""Create and validate read-only widescreen reconnaissance reports.

This tool implements the report contract in docs/WIDESCREEN-RECONNAISSANCE.md.
It does not launch an emulator or alter game/runtime behavior.
"""
from __future__ import annotations

import argparse
import json
import re
from fractions import Fraction
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = ROOT / "analysis" / "widescreen-policy.yml"

_MARGINS_RE = re.compile(r"^  source_pixel_margins: \[(.*)\]$")


def load_policy(path: Path) -> dict[str, Any]:
    """Read the small policy vocabulary without adding a YAML dependency."""
    lines = path.read_text(encoding="utf-8").splitlines()
    section: str | None = None
    margins: list[int] = []
    materializer_granularity_pixels: int | None = None
    validated_capacity_margin_pixels: int | None = None
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
            if stripped.startswith("materializer_granularity_pixels:"):
                materializer_granularity_pixels = int(stripped.split(":", 1)[1].strip(), 0)
                continue
            if stripped.startswith("validated_capacity_margin_pixels:"):
                validated_capacity_margin_pixels = int(stripped.split(":", 1)[1].strip(), 0)
                continue
            if stripped == "artifact_classes:":
                section = "probe_artifact_classes"
                continue
        elif section == "probe_artifact_classes":
            stripped = line.strip()
            if stripped.startswith("- "):
                artifact_classes.append(stripped[2:].strip().strip('"'))
                continue
            if line.startswith("  ") and not line.startswith("    "):
                section = "probe"

        if section == "aspect_policies":
            stripped = line.strip()
            if stripped.startswith("- id: "):
                aspect_policies.append(stripped[len("- id: "):].strip().strip('"'))
        elif section == "scenes":
            stripped = line.strip()
            if stripped.startswith("- id: "):
                scenes.append(stripped[len("- id: "):].strip().strip('"'))

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
        "materializer_granularity_pixels": materializer_granularity_pixels,
        "validated_capacity_margin_pixels": validated_capacity_margin_pixels,
        "artifact_classes": artifact_classes,
        "aspect_policies": aspect_policies,
        "scenes": scenes,
    }


def parse_ratio(value: str) -> Fraction:
    """Parse a positive ratio written as A:B, A/B or an integer."""
    raw = value.strip()
    if not raw:
        raise ValueError("ratio must not be empty")
    if ":" in raw:
        parts = raw.split(":")
    elif "/" in raw:
        parts = raw.split("/")
    else:
        parts = [raw, "1"]
    if len(parts) != 2:
        raise ValueError(f"invalid ratio {value!r}")
    try:
        ratio = Fraction(int(parts[0].strip()), int(parts[1].strip()))
    except (ValueError, ZeroDivisionError) as exc:
        raise ValueError(f"invalid ratio {value!r}") from exc
    if ratio <= 0:
        raise ValueError(f"ratio must be positive: {value!r}")
    return ratio


def _fraction_payload(value: Fraction) -> dict[str, int | float]:
    return {
        "numerator": value.numerator,
        "denominator": value.denominator,
        "decimal": float(value),
    }


def _ceil_fraction_to_multiple(value: Fraction, multiple: int) -> int:
    if multiple <= 0:
        raise ValueError("granularity must be positive")
    if value <= 0:
        return 0
    units = (value.numerator + value.denominator * multiple - 1) // (
        value.denominator * multiple
    )
    return units * multiple


def derive_symmetric_margin(
    *,
    base_logical_width: int,
    logical_height: int,
    target_aspect: Fraction,
    pixel_aspect: Fraction,
    granularity: int = 8,
    capacity_margin: int | None = None,
) -> dict[str, Any]:
    """Derive logical widening from display geometry without magic source widths.

    pixel_aspect is display-width/display-height for one logical source pixel.
    logical_height is the active height after the selected overscan policy.
    """
    if base_logical_width <= 0 or logical_height <= 0:
        raise ValueError("logical dimensions must be positive")
    if target_aspect <= 0 or pixel_aspect <= 0:
        raise ValueError("aspects must be positive")
    if granularity <= 0:
        raise ValueError("granularity must be positive")
    if capacity_margin is not None and capacity_margin < 0:
        raise ValueError("capacity margin must be non-negative")

    required_width = Fraction(logical_height) * target_aspect / pixel_aspect
    exact_margin = (required_width - base_logical_width) / 2
    if exact_margin < 0:
        exact_margin = Fraction(0)
    materializer_margin = _ceil_fraction_to_multiple(exact_margin, granularity)
    materialized_width = base_logical_width + materializer_margin * 2
    achieved_aspect = (
        Fraction(materialized_width) * pixel_aspect / Fraction(logical_height)
    )

    out: dict[str, Any] = {
        "schema_version": 1,
        "base_logical_width": base_logical_width,
        "logical_height": logical_height,
        "target_aspect": _fraction_payload(target_aspect),
        "pixel_aspect": _fraction_payload(pixel_aspect),
        "required_logical_width": _fraction_payload(required_width),
        "symmetric_margin_exact": _fraction_payload(exact_margin),
        "materializer_granularity_pixels": granularity,
        "materializer_margin_pixels": materializer_margin,
        "materialized_logical_width": materialized_width,
        "materialized_display_aspect": _fraction_payload(achieved_aspect),
    }
    if capacity_margin is not None:
        out["validated_capacity_margin_pixels"] = capacity_margin
        out["capacity_sufficient"] = materializer_margin <= capacity_margin
    return out


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

    derive = sub.add_parser(
        "derive-margin",
        help="derive logical per-side widening from aspect/PAR/active-height policy",
    )
    derive.add_argument("--base-width", type=int, default=256)
    derive.add_argument("--logical-height", type=int, required=True)
    derive.add_argument("--target-aspect", default="16:9")
    derive.add_argument("--pixel-aspect", required=True)
    derive.add_argument("--granularity", type=int)
    derive.add_argument("--capacity-margin", type=int)
    derive.add_argument("--out", type=Path)

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

    if args.command == "derive-margin":
        result = derive_symmetric_margin(
            base_logical_width=args.base_width,
            logical_height=args.logical_height,
            target_aspect=parse_ratio(args.target_aspect),
            pixel_aspect=parse_ratio(args.pixel_aspect),
            granularity=(
                args.granularity
                if args.granularity is not None
                else policy.get("materializer_granularity_pixels") or 8
            ),
            capacity_margin=(
                args.capacity_margin
                if args.capacity_margin is not None
                else policy.get("validated_capacity_margin_pixels")
            ),
        )
        payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(payload, encoding="utf-8")
        else:
            print(payload, end="")
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
