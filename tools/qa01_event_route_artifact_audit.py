#!/usr/bin/env python3
"""Read-only exact supplied controller replay identity for QA-01/07.

The original 2014 SMV is the source. These are the actual *supplied* reference
and native event files generated for a completed historical USA event run.
They do not establish that each guest consumed every mask on the recorded
CPU/input phase. Source-original execution remains independently adjudicated.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

MAX_ROUTE_BYTES = 1_048_576
EVENT_ROW = re.compile(r"([0-9]+):([0-9]+):([0-9a-f]+)\Z")


def original_bytes(path: Path, label: str) -> bytes:
    if not path.is_file() or path.is_symlink():
        raise ValueError("missing, symlinked or non-file original " + label)
    raw = path.read_bytes()
    if not raw or len(raw) > MAX_ROUTE_BYTES:
        raise ValueError("empty or oversized original " + label)
    return raw


def events(path: Path, label: str) -> tuple[list[tuple[int, int, int]], str]:
    raw = original_bytes(path, label)
    if not raw.endswith(b"\n"):
        raise ValueError("original " + label + " has incomplete final input row")
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError as exc:
        raise ValueError("non-ASCII original " + label) from exc
    rows = []
    for line in text.splitlines():
        match = EVENT_ROW.fullmatch(line)
        if match is None:
            raise ValueError("malformed original " + label + " input event")
        start, duration, mask = (int(match[1]), int(match[2]), int(match[3], 16))
        if duration <= 0 or not 0 < mask <= 0x0FFF:
            raise ValueError("invalid original " + label + " duration/button mask")
        if rows and start < rows[-1][0]:
            raise ValueError("out-of-order original " + label + " input event")
        rows.append((start, duration, mask))
    if not rows:
        raise ValueError("missing original replay button events")
    return rows, hashlib.sha256(raw).hexdigest()


def audit(root: Path, report: dict, *, replay_dir: Path | None = None) -> dict:
    """Check source-event injections, script bytes and every selected dump.

    The source runner publishes its own calibrated frame shift. Never infer
    a new offset by aligning inputs after the fact.
    """
    case = report.get("name")
    if case not in {"zoom-zoo", "bowl", "switcher"}:
        raise ValueError("unsupported source-qualified USA event fixture")
    shift = report.get("native_frame_shift")
    if type(shift) is not int or not -1000 <= shift <= 1000:
        raise ValueError("invalid independently calibrated native frame shift")
    replay = replay_dir if replay_dir is not None else root / "work" / case / "replay"
    reference, ref_sha = events(replay / "ref.input", "Snes9x reference")
    native, native_sha = events(replay / "pinned-baldosa.input", "Baldosa native")
    if len(reference) != len(native) or any(
        (s + shift, duration, mask) != right
        for (s, duration, mask), right in zip(reference, native)
    ):
        raise ValueError("original/native supplied controller masks, order, duration or calibrated shift differ")
    script = original_bytes(replay / "complete.script", "shared replay script")
    sha = hashlib.sha256(script).hexdigest()
    if report.get("input_sha256") != sha:
        raise ValueError("original shared replay script bytes differ from producer input_sha256")
    try:
        lines = script.decode("ascii").splitlines()
    except UnicodeDecodeError as exc:
        raise ValueError("non-ASCII original shared replay script") from exc
    offsets = report.get("relative_sample_frames")
    if not isinstance(offsets, list) or not offsets or offsets[0] != 0:
        raise ValueError("missing sampled replay frame schedule")
    labels = ["dump race-entered", "dump result-onset", "dump result-stable"]
    labels += [f"dump scene-{frame:05d}" for frame in offsets[1:]]
    if case == "bowl":
        labels.append("dump result-tally")
    if any(lines.count(label) != 1 for label in labels):
        raise ValueError("source replay script omits or duplicates required guest dump observations")
    ref_sha_claim = report.get("reference_script_sha256")
    if ref_sha_claim == sha:
        reference_script = script
    else:
        if case != "switcher":
            raise ValueError("unexpected original-only replay script for non-Switcher event")
        reference_script = original_bytes(
            replay / "switcher-reference-penultimate.script",
            "source-only reference replay script",
        )
        if hashlib.sha256(reference_script).hexdigest() != ref_sha_claim:
            raise ValueError("original-only reference replay script SHA256 differs from producer")
        if any(reference_script.decode("ascii").splitlines().count(label) != 1
               for label in labels):
            raise ValueError("source-only original replay omitted required dump observation")
    return {
        "reference_input_sha256": ref_sha,
        "native_input_sha256": native_sha,
        "input_event_rows_per_guest": len(reference),
        "original_native_supplied_masks_and_durations_equal": True,
        "native_supplied_input_shift_exact": shift,
        "shared_replay_script_sha256": sha,
        "original_reference_script_sha256": hashlib.sha256(reference_script).hexdigest(),
        "guest_controller_consumption_proven": False,
        "release_credit": 0,
    }


def main() -> int:
    """Validate actual supplied controller route without emulating or editing gameplay."""
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--artifact-root", required=True, type=Path)
    p.add_argument("--producer-report", required=True, type=Path)
    p.add_argument("--replay-dir", type=Path,
                   help="explicit original replay directory for standalone Bowl archives")
    p.add_argument("--out", required=True, type=Path)
    args = p.parse_args()
    try:
        primary_bytes = args.producer_report.read_bytes()
        report = json.loads(primary_bytes)
        evidence = audit(args.artifact_root, report, replay_dir=args.replay_dir)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        p.exit(2, "QA01_INPUT_SOURCE_ARTIFACT_INVALID: " + str(exc) + "\n")
    result = {
        "schema": "ur-qa01-source-input-replay-artifact/1",
        "original_case": report["name"],
        "original_producer_sha256": hashlib.sha256(primary_bytes).hexdigest(),
        "route": evidence,
        "usa_event_admissions": 0,
        "scope": "supplied original/native controller files only; guest-consumed bus inputs NOT observed",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    print("Source-supplied event input identity verified; USA event admissions: 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
