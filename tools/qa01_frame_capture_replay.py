#!/usr/bin/env python3
"""Stage actual original/native script-dump frames for QA01 unmasked auditing.

This is a read-only hardlink bridge, not an emulator, guest input attestation,
or a same-instruction-clock assertion. Both genuine logs must independently
acknowledge each requested frame at its own declared guest frame clock.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
import time
from pathlib import Path

import qa01_frame_fingerprint as fingerprint
import qa01_verify_frame_capture as independent


def acknowledgments(log: Path, prefix: str, width: int, guest: str) -> dict[int, int]:
    fingerprint.must(log.is_file() and not log.is_symlink(),
                     "missing authentic guest log: " + str(log))
    data = log.read_text(encoding="utf-8", errors="replace")
    # Parse full source-emitted dump records. stdout/stderr line ordering
    # is not an opcode ordering or CPU/SPC timeline.
    fingerprint.must(guest in ("original", "native"), "unknown QA01 guest log format")
    # Every *candidate* dump line must have a genuine success receipt. Original
    # snesref emits "fb=256x224 RGB565 sram=8192 ppuw=N"; native Baldosa
    # emits "ok". Accept neither "failed" nor incomplete lines as an ACK.
    pattern = re.compile(r"^script f=(\d+) dump " + re.escape(prefix) +
                         r"(\d{" + str(width) + r"})([^\r\n]*)$", re.MULTILINE)
    found: dict[int, int] = {}
    for match in pattern.finditer(data):
        relative = int(match.group(2))
        fingerprint.must(relative not in found,
                         "duplicate original/native frame acknowledgment: " + str(relative))
        suffix = match.group(3)
        if guest == "original":
            success = bool(re.fullmatch(
                r" fb=\d+x\d+ [A-Za-z0-9]+ sram=8192 ppuw=\d+", suffix))
        else:
            success = suffix == " ok"
        fingerprint.must(success, "missing successful " + guest +
                         " frame dump acknowledgment: " + str(relative))
        found[relative] = int(match.group(1))
    return found


def stage(guest_root: Path, log: Path, dest: Path, *, prefix: str,
          width: int, start: int, end: int, origin: int, guest: str) -> int:
    fingerprint.must(guest_root.is_dir() and not guest_root.is_symlink(),
                     "missing/symlinked guest memory dump root")
    captured = acknowledgments(log, prefix, width, guest)
    required = set(range(start, end + 1))
    # Genuine source logs may contain additional sparse checkpoints outside
    # the requested continuous interval; never infer a missing inside frame.
    fingerprint.must(required.issubset(captured),
                     "missing actual guest frame acknowledgments: " +
                     str(sorted(required - set(captured))[:8]))
    dest.mkdir()
    for relative in range(start, end + 1):
        host = captured[relative]
        fingerprint.must(host == origin + relative,
                         "guest actual host frame mismatches declared independent clock")
        tag = prefix + f"{relative:0{width}d}"
        for kind, length in (("wram", fingerprint.WRAM),
                             ("sram", fingerprint.SRAM)):
            source = guest_root / f"{tag}.{kind}.bin"
            # Size-only preflight avoids reading every 128KiB image TWICE.
            # fingerprint.audit below actually reopens, hashes and compares
            # every source byte. Never skip that forensic byte-level read.
            fingerprint.must(source.is_file() and not source.is_symlink() and
                             source.stat().st_size == length,
                             "missing/symlinked/truncated actual guest memory: " +
                             str(source))
            os.link(source, fingerprint.snapshot_path(dest, host, kind))
    return len(required)


def audit_replay(*, original_root: Path, native_root: Path,
                 original_log: Path, native_log: Path, identity: dict,
                 start: int, end: int, prefix: str, width: int,
                 report: Path, retained: Path, review: Path,
                 max_retained: int = 200) -> dict:
    fingerprint.validate_identity(identity)
    fingerprint.must(original_root.resolve() != native_root.resolve(),
                     "original/native capture roots must be distinct")
    fingerprint.must(type(width) is int and 1 <= width <= 8 and
                     type(prefix) is str and re.fullmatch(r"[A-Za-z0-9_-]+", prefix),
                     "invalid source dump tag format")
    fingerprint.must(type(start) is int and type(end) is int and
                     0 <= start <= end and end-start < 20000,
                     "invalid bounded guest frame window")
    fingerprint.must(len({str(p.resolve()) for p in (report, retained, review)}) == 3
                     and all(not p.exists() for p in (report, retained, review)),
                     "forensic output paths must be distinct and new")
    t0 = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="qa01-frame-stage-") as directory:
        root = Path(directory)
        original, native = root / "original", root / "native"
        n_orig = stage(original_root, original_log, original,
                       prefix=prefix, width=width, start=start, end=end,
                       origin=identity["original_frame_origin"], guest="original")
        n_nat = stage(native_root, native_log, native,
                      prefix=prefix, width=width, start=start, end=end,
                      origin=identity["native_frame_origin"], guest="native")
        staged = time.perf_counter()
        # A bounded window at or under the explicit retention budget
        # preserves *every* actual original/native raw pair, including equal
        # interior frames. Large races still retain differences + boundaries
        # (and fail closed if that exceeds their explicit cap).
        retain_all = (end - start + 1) <= max_retained
        result = fingerprint.audit(identity, original, native, start, end,
                                   retained=retained, max_retained=max_retained,
                                   retain_all_raw=retain_all)
        audited = time.perf_counter()
    verdict = independent.verify(result, retained)
    verified = time.perf_counter()
    report.parent.mkdir(parents=True, exist_ok=True)
    review.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    review.write_text(json.dumps(verdict, sort_keys=True, indent=2) + "\n")
    return {
        "schema": "ur-qa01-source-acknowledged-frame-replay/1",
        "window": {"start": start, "end": end, "count": end-start+1},
        "original_guest_acknowledged_frames": n_orig,
        "native_guest_acknowledged_frames": n_nat,
        "bytes_read_for_paired_full_memory_comparison":
            (end-start+1)*2*(fingerprint.WRAM + fingerprint.SRAM),
        "retained_full_raw_image_bytes": sum(p.stat().st_size for p in retained.iterdir()),
        "all_observed_raw_frames_independently_reopened":
            verdict["digest_only_equal_frames_not_independently_reopened"] == 0,
        "stage_seconds": round(staged-t0, 6),
        "hash_compare_and_retain_seconds": round(audited-staged, 6),
        "independent_reverify_seconds": round(verified-audited, 6),
        "execution_overhead_measured": False,
        "same_guest_inputs_actually_consumed_proven": False,
        "accepted_USA_events": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("original-root", "native-root", "original-log", "native-log",
                 "identity", "report", "retained", "review", "metrics"):
        parser.add_argument("--"+name, type=Path, required=True)
    parser.add_argument("--start", type=int, required=True)
    parser.add_argument("--end", type=int, required=True)
    parser.add_argument("--tag-prefix", default="qa01-frame-")
    parser.add_argument("--tag-width", type=int, default=6)
    parser.add_argument("--max-retained", type=int, default=200)
    args = parser.parse_args()
    metrics = audit_replay(
        original_root=args.original_root, native_root=args.native_root,
        original_log=args.original_log, native_log=args.native_log,
        identity=json.loads(args.identity.read_text()), start=args.start, end=args.end,
        prefix=args.tag_prefix, width=args.tag_width,
        report=args.report, retained=args.retained, review=args.review,
        max_retained=args.max_retained)
    fingerprint.must(not args.metrics.exists(), "refusing overwrite of QA01 metrics")
    args.metrics.parent.mkdir(parents=True, exist_ok=True)
    args.metrics.write_text(json.dumps(metrics, sort_keys=True, indent=2) + "\n")
    print("QA01 source-acknowledged frame audit: bounded, zero USA event credit")


if __name__ == "__main__":
    main()
