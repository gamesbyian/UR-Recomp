#!/usr/bin/env python3
"""Receipt for the manual Modern native/Windows campaign; no release adjudication."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from assemble_windows_package import verify_archive_checksum

_STATES = {"success", "failure", "cancelled", "skipped"}
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_SHA1 = re.compile(r"[0-9a-f]{40}\Z")
_SUITES = ("native", "shared", "onboarding", "ui", "windows")


def make_receipt(
    *,
    source_sha: str,
    run_id: str,
    states: dict[str, str],
    include_windows: bool,
    native_sha256: str = "",
    windows_zip: Path | None = None,
    windows_checksum: Path | None = None,
) -> dict:
    if not _SHA1.fullmatch(source_sha):
        raise ValueError("source identity must be an exact 40-hex commit")
    if not run_id.isdecimal() or not run_id:
        raise ValueError("missing numeric GitHub Actions run ID")
    if set(states) != set(_SUITES) or any(s not in _STATES for s in states.values()):
        raise ValueError("incomplete or invalid suite-result population")
    if not include_windows and states["windows"] != "skipped":
        raise ValueError("opted-out Windows suite reported an unexpected result")
    if states["native"] == "success" and not _SHA256.fullmatch(native_sha256):
        raise ValueError("successful canonical native build lacks its SHA-256")
    if native_sha256 and not _SHA256.fullmatch(native_sha256):
        raise ValueError("malformed native candidate digest")
    if states["windows"] == "success":
        if not windows_zip or not windows_checksum:
            raise ValueError("successful Windows suite is missing its portable ZIP evidence")
        windows_digest = verify_archive_checksum(windows_zip, windows_checksum)
    else:
        windows_digest = None

    required = [states[s] for s in ("native", "shared", "onboarding", "ui")]
    if include_windows:
        required.append(states["windows"])
    if "failure" in required:
        disposition = "suite_failure"
    elif all(v == "success" for v in required):
        disposition = "component_suites_passed"
    else:
        disposition = "incomplete"

    return {
        "schema": "ur-modern-candidate-campaign/1",
        "source_commit": source_sha,
        "github_run_id": run_id,
        "run_url": f"https://github.com/gamesbyian/UR-Recomp/actions/runs/{run_id}",
        "suites": states,
        "windows_requested": include_windows,
        "candidate": {
            "linux_native_build_archive_sha256": native_sha256 or None,
            "windows_portable_zip_sha256": windows_digest,
            "linux_native_backend": "legacy-snesrecomp-product",
            "windows_backend": "legacy-snesrecomp-product" if include_windows else None,
            "distinct_builds": True,
        },
        "disposition": disposition,
        "qa01_accepted_courses": 0,
        "release_gate_credit": 0,
        "physical_hardware_witness": False,
        "boundary": "Existing component suites only; no Baldosa/native original-event, physically witnessed hardware, or full-release acceptance.",
    }


def render_summary(report: dict) -> str:
    lines = [
        "## Manual Modern candidate campaign",
        "",
        f"Source: \`{report['source_commit']}\` · run \`{report['github_run_id']}\`",
        "",
        f"Disposition: **{report['disposition']}** (no independent release credit)",
        "",
        "| Existing suite | Job outcome |",
        "| --- | --- |",
    ]
    for name in _SUITES:
        lines.append(f"| {name} | {report['suites'].get(name, 'unknown')} |")
    lines += [
        "",
        f"Linux candidate archive SHA-256: \`{report['candidate'].get('linux_native_build_archive_sha256') or 'missing'}\`",
        "",
        f"Windows portable ZIP SHA-256: \`{report['candidate'].get('windows_portable_zip_sha256') or 'not available'}\`",
        "",
        "Linux and Windows are **distinct legacy-backend builds** from the same source commit.",
        "This campaign does not independently qualify Baldosa, original/native complete events,",
        "fresh real-player 1P/2P journeys, or physical Windows/hardware release gates.",
        "",
    ]
    if report.get("error"):
        lines += [f"Evidence contract failure: \`{report['error']}\`", ""]
    return "\n".join(lines)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-sha", required=True)
    p.add_argument("--run-id", required=True)
    for name in _SUITES:
        p.add_argument(f"--{name}", required=True, choices=sorted(_STATES))
    p.add_argument("--include-windows", required=True, choices=("true", "false"))
    p.add_argument("--native-sha256", default="")
    p.add_argument("--windows-zip", type=Path)
    p.add_argument("--windows-checksum", type=Path)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--summary", type=Path, required=True)
    args = p.parse_args()

    states = {name: getattr(args, name) for name in _SUITES}
    try:
        report = make_receipt(
            source_sha=args.source_sha,
            run_id=args.run_id,
            states=states,
            include_windows=args.include_windows == "true",
            native_sha256=args.native_sha256,
            windows_zip=args.windows_zip,
            windows_checksum=args.windows_checksum,
        )
        result = 0
    except (ValueError, OSError) as exc:
        report = {
            "schema": "ur-modern-candidate-campaign/1",
            "source_commit": args.source_sha,
            "github_run_id": args.run_id,
            "suites": states,
            "windows_requested": args.include_windows == "true",
            "candidate": {},
            "disposition": "evidence_invalid",
            "error": str(exc),
            "release_gate_credit": 0,
            "physical_hardware_witness": False,
        }
        result = 2
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with args.summary.open("a", encoding="utf-8") as handle:
        handle.write(render_summary(report))
    print(json.dumps({"disposition": report["disposition"], "suites": states}, sort_keys=True))
    return result


if __name__ == "__main__":
    raise SystemExit(main())
