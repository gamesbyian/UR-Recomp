#!/usr/bin/env python3
"""Independently inspect a completed Windows tournament package QA receipt.

No guest/gameplay authority is invented here. The producer must first run a
real game through the existing packaged tournament route. This checker binds
the resulting source/ZIP nomination, archived QA harness identity, and three
post-reopen on-disk immutable artifacts to the same digest receipt. It does
not authenticate GitHub identity, verify codec/course semantics, or grant L5.
"""
from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path

CANDIDATE_KEYS = (
    "schema", "smoke_run_id", "source_commit", "inner_zip_sha256",
    "qa_harness_commit",
)
ARTIFACT_KEYS = (
    "schema", "source_commit", "inner_zip_sha256", "run_file",
    "run_sha256", "match_file", "match_sha256", "receipt_file",
    "receipt_sha256", "fresh_process_reopen",
)
SOURCE = re.compile(r"[0-9a-f]{40}\Z")
DIGEST = re.compile(r"[0-9a-f]{64}\Z")
RUN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*\.urrun\Z")
RECEIPT = re.compile(r"fixture-0\.urfixture\Z")
MAX_RECEIPT_BYTES = 4096
MAX_FILE_BYTES = 64 * 1024 * 1024


def fields(path: Path, exact_keys: tuple[str, ...]) -> dict[str, str]:
    if not path.is_file() or path.is_symlink() or path.stat().st_size > MAX_RECEIPT_BYTES:
        raise ValueError(f"missing, linked or oversized evidence receipt: {path.name}")
    payload = path.read_bytes()
    if not payload.endswith(b"\n") or b"\r" in payload or b"\0" in payload:
        raise ValueError(f"receipt is not canonical LF-delimited text: {path.name}")
    try:
        rows = payload.decode("ascii").splitlines()
    except UnicodeError as exc:
        raise ValueError("receipt must use canonical ASCII") from exc
    if len(rows) != len(exact_keys):
        raise ValueError("receipt has missing or unexpected fields")
    pairs = []
    for row in rows:
        if row.count("=") != 1:
            raise ValueError("receipt field must be exactly key=value")
        pairs.append(row.split("=", 1))
    if tuple(pair[0] for pair in pairs) != exact_keys:
        raise ValueError("receipt fields must be in canonical order without duplicates")
    if any(not pair[1] or pair[1] != pair[1].strip() for pair in pairs):
        raise ValueError("receipt value missing or noncanonical")
    return dict(pairs)


def sha256(path: Path) -> str:
    if not path.is_file() or path.is_symlink() or path.stat().st_size > MAX_FILE_BYTES:
        raise ValueError(f"missing, linked or oversized immutable artifact: {path.name}")
    h = hashlib.sha256()
    with path.open("rb") as reader:
        for block in iter(lambda: reader.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def verify(work: Path, candidate_path: Path,
           expected_source: str, expected_zip: str) -> dict[str, str]:
    if not SOURCE.fullmatch(expected_source) or not DIGEST.fullmatch(expected_zip):
        raise ValueError("independent source and portable ZIP pins must be canonical")
    # Resolve for consistent on-disk lookup, but inspect the caller's
    # original root first: Path.resolve() erases evidence of a symlink.
    if work.is_symlink() or not work.is_dir():
        raise ValueError("tournament work root is missing or linked")
    work = work.resolve(strict=True)
    candidate = fields(candidate_path, CANDIDATE_KEYS)
    receipt = fields(work / "tournament-artifacts.log", ARTIFACT_KEYS)
    if (candidate["schema"] != "ur-windows-qa-candidate/1"
            or receipt["schema"] != "ur-windows-tournament-artifacts/1"):
        raise ValueError("unsupported QA receipt schema")
    if (candidate["source_commit"] != expected_source
            or receipt["source_commit"] != expected_source
            or candidate["inner_zip_sha256"] != expected_zip
            or receipt["inner_zip_sha256"] != expected_zip):
        raise ValueError("QA receipts do not match the independently nominated candidate")
    if (not SOURCE.fullmatch(candidate["qa_harness_commit"])
            or not candidate["smoke_run_id"].isdecimal()
            or int(candidate["smoke_run_id"]) <= 0):
        raise ValueError("invalid producing smoke run or QA harness identity")
    if receipt["fresh_process_reopen"] != "passed":
        raise ValueError("actual separate-process reopen was not recorded as passed")
    if not RUN.fullmatch(receipt["run_file"]):
        raise ValueError("invalid canonical 2P run filename")
    if receipt["match_file"] != receipt["run_file"] + ".urmatch":
        raise ValueError("match sidecar does not name the recorded run")
    if not RECEIPT.fullmatch(receipt["receipt_file"]):
        raise ValueError("unexpected fixture-receipt filename")
    if any(not DIGEST.fullmatch(receipt[key])
           for key in ("run_sha256", "match_sha256", "receipt_sha256")):
        raise ValueError("receipt artifact checksums must be SHA-256")
    runs_root = work / "multiplayer-runs"
    tournament_root = work / "user data" / "local-tournaments"
    for folder in (work, runs_root, work / "user data", tournament_root):
        if folder.is_symlink() or not folder.is_dir():
            raise ValueError("tournament evidence root is missing or linked")
    runs = list(runs_root.glob("*.urrun"))
    matches = list(runs_root.glob("*.urmatch"))
    fixture_receipts = list(tournament_root.glob("*/fixtures/*.urfixture"))
    if (len(runs), len(matches), len(fixture_receipts)) != (1, 1, 1):
        raise ValueError("expected exactly one run, one match and one fixture receipt")
    run = runs_root / receipt["run_file"]
    match = runs_root / receipt["match_file"]
    fixture = fixture_receipts[0]
    if fixture.name != receipt["receipt_file"] or (
        fixture.parent.is_symlink() or fixture.parent.parent.is_symlink()
    ):
        raise ValueError("fixture-receipt path is not canonical")
    for path, key in ((run, "run_sha256"),
                      (match, "match_sha256"),
                      (fixture, "receipt_sha256")):
        if not path.stat().st_size or sha256(path) != receipt[key]:
            raise ValueError(f"on-disk artifact digest differs from receipt: {path.name}")
    return {
        "source_commit": expected_source,
        "inner_zip_sha256": expected_zip,
        "qa_harness_commit": candidate["qa_harness_commit"],
        "smoke_run_id": candidate["smoke_run_id"],
        "run_sha256": receipt["run_sha256"],
        "match_sha256": receipt["match_sha256"],
        "receipt_sha256": receipt["receipt_sha256"],
        "result": "read-only receipt consistency only, not physical or full schedule acceptance",
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--work", type=Path, required=True)
    p.add_argument("--candidate", type=Path, required=True)
    p.add_argument("--expected-source", required=True)
    p.add_argument("--expected-zip-sha256", required=True)
    args = p.parse_args()
    try:
        result = verify(args.work, args.candidate,
                        args.expected_source, args.expected_zip_sha256)
    except (OSError, ValueError) as exc:
        p.error(str(exc))
    print("UR_WINDOWS_TOURNAMENT_RECEIPT_VERIFIED "
          f"source={result['source_commit']} zip={result['inner_zip_sha256']}")
    print("UR_WINDOWS_TOURNAMENT_RECEIPT_SCOPE exact_artifact_integrity_only "
          "release_l4_l5_certified=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
