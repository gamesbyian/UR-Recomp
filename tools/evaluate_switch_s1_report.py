#!/usr/bin/env python3
"""Evaluate one or more on-device Switch S1 capability reports."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

HEADER = "UR-SWITCH-S1/1"
STYLE_PRO_CONTROLLER = 1 << 0
STYLE_HANDHELD = 1 << 1
STYLE_JOYCON = (1 << 2) | (1 << 3) | (1 << 4)
MODE_HANDHELD = 1 << 0
MODE_CONSOLE = 1 << 1

INT_KEYS = {
    "lifecycle_started",
    "clean_exit",
    "operation_mode",
    "operation_modes_seen",
    "display_ready",
    "audio_ready",
    "storage_writable",
    "input_seen",
    "controller_styles_seen",
    "background_events",
    "foreground_events",
    "suspend_resume_observed",
}


def parse_int(value: str) -> int:
    return int(value, 0)


def parse_report(path: Path) -> dict:
    lines = path.read_text().splitlines()
    if not lines or lines[0] != HEADER:
        raise ValueError(f"{path}: expected {HEADER}")
    out: dict[str, object] = {"source": str(path)}
    for line in lines[1:]:
        if not line or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key == "display_size":
            if "x" not in value:
                raise ValueError(f"{path}: malformed display_size")
            width, height = value.split("x", 1)
            out["display_width"] = int(width)
            out["display_height"] = int(height)
        elif key in INT_KEYS:
            out[key] = parse_int(value)
        else:
            out[key] = value
    return out


def merge_reports(reports: Iterable[dict]) -> dict:
    reports = list(reports)
    if not reports:
        raise ValueError("at least one S1 report is required")

    required_every_run = (
        "lifecycle_started",
        "clean_exit",
        "display_ready",
        "audio_ready",
        "storage_writable",
    )
    merged: dict[str, object] = {
        "report_count": len(reports),
        "sources": [report.get("source", "") for report in reports],
    }
    for key in required_every_run:
        merged[key] = int(all(int(report.get(key, 0)) == 1 for report in reports))

    merged["input_seen"] = int(any(int(report.get("input_seen", 0)) == 1 for report in reports))
    merged["operation_modes_seen"] = 0
    merged["controller_styles_seen"] = 0
    merged["background_events"] = 0
    merged["foreground_events"] = 0
    for report in reports:
        merged["operation_modes_seen"] |= int(report.get("operation_modes_seen", 0))
        merged["controller_styles_seen"] |= int(report.get("controller_styles_seen", 0))
        merged["background_events"] += int(report.get("background_events", 0))
        merged["foreground_events"] += int(report.get("foreground_events", 0))
    return merged


def evaluate(merged: dict) -> dict:
    modes = int(merged.get("operation_modes_seen", 0))
    styles = int(merged.get("controller_styles_seen", 0))
    checks = {
        "lifecycle_started": int(merged.get("lifecycle_started", 0)) == 1,
        "clean_exit": int(merged.get("clean_exit", 0)) == 1,
        "handheld_mode_observed": bool(modes & MODE_HANDHELD),
        "console_mode_observed": bool(modes & MODE_CONSOLE),
        "display_ready": int(merged.get("display_ready", 0)) == 1,
        "audio_ready": int(merged.get("audio_ready", 0)) == 1,
        "storage_writable": int(merged.get("storage_writable", 0)) == 1,
        "input_seen": int(merged.get("input_seen", 0)) == 1,
        "pro_controller_observed": bool(styles & STYLE_PRO_CONTROLLER),
        "handheld_controls_observed": bool(styles & STYLE_HANDHELD),
        "joycon_observed": bool(styles & STYLE_JOYCON),
        "background_event_observed": int(merged.get("background_events", 0)) > 0,
        "foreground_event_observed": int(merged.get("foreground_events", 0)) > 0,
    }
    return {
        "schema_version": 1,
        "gate": "S1",
        "passed": all(checks.values()),
        "checks": checks,
        "observed": merged,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reports", nargs="+", type=Path)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    result = evaluate(merge_reports(parse_report(path) for path in args.reports))
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    print(text, end="")
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text)
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
