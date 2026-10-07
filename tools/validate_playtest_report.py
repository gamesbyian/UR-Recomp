#!/usr/bin/env python3
"""Validate one UR-Recomp expert playtest report."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

SCHEMA = "ur-recomp-playtest-report-v1"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
ALLOWED_EXPERIENCE = {
    "high-skill",
    "pal-unirally",
    "collision-glitch",
    "multiplayer",
    "general-original",
}
ALLOWED_REGION = {"NTSC-U", "PAL"}
ALLOWED_EXECUTION = {"Authentic", "Modern"}
ALLOWED_VIEW = {"Original", "16:9"}
ALLOWED_GRAPHICS = {"Original", "Remastered", "Reimagined"}
ALLOWED_AREA = {
    "handling",
    "timing",
    "camera",
    "track-reading",
    "collision",
    "stunts",
    "progression",
    "persistence",
    "multiplayer",
    "rematch",
    "records",
    "presentation",
    "controls",
}
ALLOWED_REPRO = {"always", "often", "sometimes", "once", "not-reproduced"}
ALLOWED_SEVERITY = {"observation", "minor", "major", "release-blocker"}
ALLOWED_COMPARISON = {
    "none",
    "memory",
    "original-hardware",
    "emulator",
    "video",
    "timed-run",
}

REQUIRED_TOP = {
    "schema",
    "build_revision",
    "artifact_sha256",
    "tester_context",
    "environment",
    "finding",
}
REQUIRED_TESTER = {"experience"}
REQUIRED_ENVIRONMENT = {"region", "execution_mode", "view", "graphics"}
REQUIRED_FINDING = {
    "area",
    "summary",
    "reproducibility",
    "severity",
    "steps",
    "expected",
    "observed",
    "comparison_source",
}


def _require_exact_keys(obj: dict, required: set[str], optional: set[str], where: str) -> None:
    keys = set(obj)
    missing = sorted(required - keys)
    unknown = sorted(keys - required - optional)
    if missing:
        raise ValueError(f"{where}: missing fields: {', '.join(missing)}")
    if unknown:
        raise ValueError(f"{where}: unknown fields: {', '.join(unknown)}")


def _bounded_text(value: object, name: str, *, maximum: int, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{name}: must be a string")
    if value != value.strip():
        raise ValueError(f"{name}: leading/trailing whitespace is not canonical")
    if not allow_empty and not value:
        raise ValueError(f"{name}: must not be empty")
    if len(value) > maximum:
        raise ValueError(f"{name}: exceeds {maximum} characters")
    if any(ord(ch) < 0x20 and ch not in "\t" for ch in value):
        raise ValueError(f"{name}: contains control characters")
    return value


def _enum(value: object, allowed: set[str], name: str) -> str:
    text = _bounded_text(value, name, maximum=64)
    if text not in allowed:
        raise ValueError(f"{name}: unsupported value {text!r}")
    return text


def validate_report(report: object) -> dict:
    if not isinstance(report, dict):
        raise ValueError("report root must be an object")
    _require_exact_keys(report, REQUIRED_TOP, {"course", "notes"}, "report")

    if report["schema"] != SCHEMA:
        raise ValueError(f"report.schema: expected {SCHEMA}")
    _bounded_text(report["build_revision"], "report.build_revision", maximum=128)
    digest = _bounded_text(report["artifact_sha256"], "report.artifact_sha256", maximum=64)
    if not SHA256_RE.fullmatch(digest):
        raise ValueError("report.artifact_sha256: must be lowercase SHA-256")

    tester = report["tester_context"]
    if not isinstance(tester, dict):
        raise ValueError("report.tester_context: must be an object")
    _require_exact_keys(tester, REQUIRED_TESTER, {"comparison_familiarity"}, "report.tester_context")
    _enum(tester["experience"], ALLOWED_EXPERIENCE, "report.tester_context.experience")
    if "comparison_familiarity" in tester:
        _bounded_text(
            tester["comparison_familiarity"],
            "report.tester_context.comparison_familiarity",
            maximum=240,
            allow_empty=True,
        )

    environment = report["environment"]
    if not isinstance(environment, dict):
        raise ValueError("report.environment: must be an object")
    _require_exact_keys(environment, REQUIRED_ENVIRONMENT, set(), "report.environment")
    _enum(environment["region"], ALLOWED_REGION, "report.environment.region")
    _enum(environment["execution_mode"], ALLOWED_EXECUTION, "report.environment.execution_mode")
    _enum(environment["view"], ALLOWED_VIEW, "report.environment.view")
    _enum(environment["graphics"], ALLOWED_GRAPHICS, "report.environment.graphics")

    if "course" in report:
        _bounded_text(report["course"], "report.course", maximum=80, allow_empty=True)
    if "notes" in report:
        _bounded_text(report["notes"], "report.notes", maximum=1000, allow_empty=True)

    finding = report["finding"]
    if not isinstance(finding, dict):
        raise ValueError("report.finding: must be an object")
    _require_exact_keys(
        finding,
        REQUIRED_FINDING,
        {"frame_anchor", "input_anchor", "reference"},
        "report.finding",
    )
    _enum(finding["area"], ALLOWED_AREA, "report.finding.area")
    _bounded_text(finding["summary"], "report.finding.summary", maximum=160)
    _enum(finding["reproducibility"], ALLOWED_REPRO, "report.finding.reproducibility")
    _enum(finding["severity"], ALLOWED_SEVERITY, "report.finding.severity")
    _bounded_text(finding["steps"], "report.finding.steps", maximum=1200)
    _bounded_text(finding["expected"], "report.finding.expected", maximum=600)
    _bounded_text(finding["observed"], "report.finding.observed", maximum=600)
    _enum(finding["comparison_source"], ALLOWED_COMPARISON, "report.finding.comparison_source")
    for optional in ("frame_anchor", "input_anchor", "reference"):
        if optional in finding:
            _bounded_text(
                finding[optional],
                f"report.finding.{optional}",
                maximum=300,
                allow_empty=True,
            )

    return report


def load_report(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read playtest report: {exc}") from exc
    return validate_report(payload)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    try:
        report = load_report(args.report)
    except ValueError as exc:
        parser.error(str(exc))
    finding = report["finding"]
    print(
        "PLAYTEST_REPORT_VALID "
        f"area={finding['area']} "
        f"severity={finding['severity']} "
        f"reproducibility={finding['reproducibility']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
