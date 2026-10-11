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
    "schema", "backend", "smoke_run_id", "source_commit", "inner_zip_sha256",
    "qa_harness_commit",
)
ARTIFACT_KEYS = (
    "schema", "backend", "source_commit", "inner_zip_sha256", "run_file",
    "run_sha256", "match_file", "match_sha256", "receipt_file",
    "receipt_sha256", "create_log_sha256", "reopen_log_sha256",
    "fresh_process_reopen",
)
SOURCE = re.compile(r"[0-9a-f]{40}\Z")
DIGEST = re.compile(r"[0-9a-f]{64}\Z")
RUN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*\.urrun\Z")
RECEIPT = re.compile(r"fixture-0\.urfixture\Z")
MAX_RECEIPT_BYTES = 4096
MAX_FILE_BYTES = 64 * 1024 * 1024
MAX_NATIVE_LOG_BYTES = 8 * 1024 * 1024
EXPECTED_CREATE_MARKERS = (
    "UR_LOCAL_MULTIPLAYER SESSION_READY",
    "UR_LOCAL_TOURNAMENT PANEL_OPENED page=setup",
    "UR_LOCAL_TOURNAMENT CREATED entrants=2 fixtures=1 courses=2 legs=1",
    "UR_LOCAL_TOURNAMENT ARMED fixture=0 course=course:01",
    "UR_LOCAL_TOURNAMENT CAPTURE_TAGGED",
    "UR_MULTIPLAYER_MATCH CAPTURED",
    "course=course:01 p1=join.alpha p2=join.bravo outcome=1",
    "UR_LOCAL_TOURNAMENT FIXTURE_COMMITTED",
    "UR_LOCAL_TOURNAMENT RESULT_NOTICE screen=F9 text=CHAMPION: MIKE",
)
EXPECTED_REOPEN_MARKERS = (
    "UR_LOCAL_TOURNAMENT SESSION_RESTORED",
    "UR_LOCAL_TOURNAMENT HISTORY completed=1 unavailable=0",
    "UR_LOCAL_TOURNAMENT PANEL_OPENED page=overview",
    "UR_LOCAL_TOURNAMENT_PANEL_ACCEPTANCE DONE mode=reopen step=2 armed=0",
)
FORBIDDEN_NATIVE_MARKERS = (
    "UR_LOCAL_TOURNAMENT FIXTURE_COMMIT_REJECTED",
    "UR_LOCAL_TOURNAMENT SESSION_RESTORE_REJECTED",
    "UR_LOCAL_TOURNAMENT_PANEL_ACCEPTANCE UNEXPECTED_PAGE",
)


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


def check_native_log(path: Path, expected: tuple[str, ...]) -> None:
    """Independently re-read bounded existing game logs; never print raw paths."""
    if (not path.is_file() or path.is_symlink()
            or path.stat().st_size > MAX_NATIVE_LOG_BYTES):
        raise ValueError(f"missing, linked or oversized packaged QA log: {path.name}")
    body = path.read_bytes().decode("utf-8", "replace")
    for marker in expected:
        if marker not in body:
            raise ValueError(f"native QA log lacks required event: {marker}")
    for forbidden in FORBIDDEN_NATIVE_MARKERS:
        if forbidden in body:
            raise ValueError(f"native QA log includes failed event: {forbidden}")
    if path.name == "tournament.log":
        for marker in ("UR_MULTIPLAYER_MATCH CAPTURED",
                       "UR_LOCAL_TOURNAMENT FIXTURE_COMMITTED"):
            if body.count(marker) != 1:
                raise ValueError(f"native QA log has duplicate/missing settled event: {marker}")


def sha256(path: Path) -> str:
    if not path.is_file() or path.is_symlink() or path.stat().st_size > MAX_FILE_BYTES:
        raise ValueError(f"missing, linked or oversized immutable artifact: {path.name}")
    h = hashlib.sha256()
    with path.open("rb") as reader:
        for block in iter(lambda: reader.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def fnv_hex(data: bytes) -> str:
    """The existing v1 run/match trailer checksum, not a new file format."""
    value = 14695981039346656037
    for byte in data:
        value = ((value ^ byte) * 1099511628211) & 0xffffffffffffffff
    return f"{value:016x}"


def canonical_rows(path: Path, maximum: int) -> list[str]:
    if (not path.is_file() or path.is_symlink()
            or not 0 < path.stat().st_size <= maximum):
        raise ValueError("saved two-player artifact absent, linked or oversized")
    raw = path.read_bytes()
    if not raw.endswith(b"\n") or b"\r" in raw or b"\0" in raw:
        raise ValueError("saved two-player artifact has noncanonical LF framing")
    try:
        return raw.decode("ascii").splitlines()
    except UnicodeError as exc:
        raise ValueError("saved two-player artifact must be ASCII") from exc


def checked_checksum(rows: list[str]) -> str:
    if (len(rows) < 2 or not re.fullmatch(r"checksum [0-9a-f]{16}", rows[-1])):
        raise ValueError("saved artifact lacks canonical v1 checksum trailer")
    encoded = ("\n".join(rows[:-1]) + "\n").encode("ascii")
    expected = fnv_hex(encoded)
    if rows[-1] != "checksum " + expected:
        raise ValueError("saved artifact v1 internal checksum mismatch")
    return expected


def inspect_two_player_pair(run: Path, match: Path) -> dict[str, str]:
    """Narrow independent admission of the one stock P1-win/no-time event.

    The repository's native C++ codecs remain authoritative for full record
    parsing. This second reader checks only the known packaged QA scenario
    and is deliberately not a replacement general-purpose decoder.
    """
    rr = canonical_rows(run, MAX_FILE_BYTES)
    side = canonical_rows(match, 4096)
    run_checksum = checked_checksum(rr)
    checked_checksum(side)
    if (len(rr) < 12 or rr[0] != "URRUN 1" or rr[-2] != "END"
            or len(side) != 13 or side[0] != "UR-MULTIPLAYER-MATCH/1"):
        raise ValueError("stock 2P run/match has unexpected v1 structure")

    scalars = (
        "game ", "rom_sha256 ", "build_compat ", "course ", "mode ",
        "elapsed_ticks60 ", "frame_count ", "terminal_digest ",
    )
    if any(not rr[i + 1].startswith(key) or len(rr[i + 1]) <= len(key)
           for i, key in enumerate(scalars)):
        raise ValueError("stock 2P run scalar provenance incomplete")
    run_fields = {
        key.rstrip(): rr[i + 1][len(key):]
        for i, key in enumerate(scalars)
    }
    if (run_fields["course"] != "course:01"
            or run_fields["mode"] != "race-2p"
            or not re.fullmatch(r"[0-9a-fA-F]{64}", run_fields["rom_sha256"])):
        raise ValueError("stock 2P run has unexpected ROM/course/mode provenance")
    if not re.fullmatch(r"[0-9]+", run_fields["frame_count"]):
        raise ValueError("stock 2P run has invalid frame count")
    frames = int(run_fields["frame_count"])
    if not 0 < frames < 2**64:
        raise ValueError("stock 2P run has invalid frame count")
    if not re.fullmatch(r"[0-9]+", run_fields["elapsed_ticks60"]):
        raise ValueError("stock 2P run has invalid timing")
    ticks = int(run_fields["elapsed_ticks60"])
    if not 0 < ticks < 2**64:
        raise ValueError("stock 2P run has invalid timing")

    saw_p1 = saw_p2 = False
    previous_end = 0
    for line in rr[9:-2]:
        values = line.split(" ")
        if len(values) != 5 or values[0] != "input":
            raise ValueError("stock 2P run contains unexpected split or input shape")
        if not (re.fullmatch(r"[0-9]+", values[1])
                and re.fullmatch(r"[0-9]+", values[2])
                and re.fullmatch(r"[0-9a-fA-F]+", values[3])
                and re.fullmatch(r"[0-9a-fA-F]+", values[4])):
            raise ValueError("stock 2P run has malformed mapped input")
        start, duration = int(values[1]), int(values[2])
        p1, p2 = int(values[3], 16), int(values[4], 16)
        if (duration <= 0 or start < previous_end or start + duration > frames
                or p1 > 0xfff or p2 > 0xfff or not (p1 or p2)):
            raise ValueError("stock 2P run has invalid input span or mask")
        previous_end = start + duration
        saw_p1 |= bool(p1)
        saw_p2 |= bool(p2)
    if not (saw_p1 and saw_p2):
        raise ValueError("stock 2P run is missing either captured input lane")

    keys = (
        "run_checksum ", "course ", "outcome ", "p1_result ", "p2_result ",
        "p1_profile ", "p1_name ", "p1_rider ",
        "p2_profile ", "p2_name ", "p2_rider ",
    )
    if any(not side[i + 1].startswith(key) or len(side[i + 1]) <= len(key)
           for i, key in enumerate(keys)):
        raise ValueError("stock 2P sidecar has malformed v1 fields")
    m = {key.rstrip(): side[i + 1][len(key):] for i, key in enumerate(keys)}
    # These are the exact identities seeded by the existing packaged
    # join.alpha/join.bravo acceptance, never inferred from arbitrary names.
    identity = (
        ("p1_profile", "join.alpha"), ("p2_profile", "join.bravo"),
        ("p1_name", "MIKE"), ("p2_name", "ANDREW"),
    )
    for field, expected in identity:
        try:
            actual = bytes.fromhex(m[field]).decode("ascii")
        except (ValueError, UnicodeError) as exc:
            raise ValueError("stock 2P sidecar identity is not hex-encoded") from exc
        if actual != expected:
            raise ValueError("stock 2P sidecar has unexpected participant identity")
    if (m["run_checksum"] != run_checksum
            or m["course"] != run_fields["course"]
            or m["outcome"] != "p1"
            or m["p1_rider"] != "0" or m["p2_rider"] != "1"
            or not re.fullmatch(r"[0-9]+", m["p1_result"])
            or m["p2_result"] != "60000"):
        raise ValueError("stock 2P sidecar is not bound to the expected result")
    hundredths = int(m["p1_result"])
    if not 0 < hundredths < 60000 or ticks != (hundredths * 60 + 50) // 100:
        raise ValueError("stock 2P run timing differs from settled winner")
    return {"course": m["course"], "winner": "join.alpha",
            "run_artifact_checksum": run_checksum, "elapsed_ticks60": str(ticks)}


def verify(work: Path, candidate_path: Path,
           expected_source: str, expected_zip: str,
           *, expected_harness: str | None = None,
           expected_smoke_run: str | None = None) -> dict[str, str]:
    if not SOURCE.fullmatch(expected_source) or not DIGEST.fullmatch(expected_zip):
        raise ValueError("independent source and portable ZIP pins must be canonical")
    if expected_harness is not None and not SOURCE.fullmatch(expected_harness):
        raise ValueError("expected QA harness SHA must be 40 lowercase hex")
    if expected_smoke_run is not None and (
        not expected_smoke_run.isdecimal() or int(expected_smoke_run) <= 0
    ):
        raise ValueError("expected smoke run ID must be a positive decimal integer")
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
    # This is the SNESRecomp portable package, not the provisional Baldosa ZIP.
    if candidate["backend"] != "snesrecomp" or receipt["backend"] != "snesrecomp":
        raise ValueError("QA backend does not match the SNESRecomp producer")
    if (candidate["source_commit"] != expected_source
            or receipt["source_commit"] != expected_source
            or candidate["inner_zip_sha256"] != expected_zip
            or receipt["inner_zip_sha256"] != expected_zip):
        raise ValueError("QA receipts do not match the independently nominated candidate")
    if (not SOURCE.fullmatch(candidate["qa_harness_commit"])
            or not candidate["smoke_run_id"].isdecimal()
            or int(candidate["smoke_run_id"]) <= 0):
        raise ValueError("invalid producing smoke run or QA harness identity")
    if (expected_harness is not None
            and candidate["qa_harness_commit"] != expected_harness):
        raise ValueError("candidate QA harness SHA differs from running checkout")
    if (expected_smoke_run is not None
            and candidate["smoke_run_id"] != expected_smoke_run):
        raise ValueError("candidate smoke run differs from selected run")
    if receipt["fresh_process_reopen"] != "passed":
        raise ValueError("actual separate-process reopen was not recorded as passed")
    if not RUN.fullmatch(receipt["run_file"]):
        raise ValueError("invalid canonical 2P run filename")
    if receipt["match_file"] != receipt["run_file"] + ".urmatch":
        raise ValueError("match sidecar does not name the recorded run")
    if not RECEIPT.fullmatch(receipt["receipt_file"]):
        raise ValueError("unexpected fixture-receipt filename")
    if any(not DIGEST.fullmatch(receipt[key])
           for key in ("run_sha256", "match_sha256", "receipt_sha256",
                       "create_log_sha256", "reopen_log_sha256")):
        raise ValueError("receipt artifact checksums must be SHA-256")
    runs_root = work / "multiplayer-runs"
    tournament_root = work / "user data" / "local-tournaments"
    for folder in (work, runs_root, work / "user data", tournament_root):
        if folder.is_symlink() or not folder.is_dir():
            raise ValueError("tournament evidence root is missing or linked")
    runs = list(runs_root.glob("*.urrun"))
    matches = list(runs_root.glob("*.urmatch"))
    fixture_receipts = list(tournament_root.rglob("*.urfixture"))
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
    # Hashes prove bytes did not change, not that the two saved files
    # describe one genuine P1-win result. Independently inspect the narrow
    # v1 pair contract without altering the canonical C++ codecs or game.
    bound_pair = inspect_two_player_pair(run, match)
    # The producer asserted both launcher processes were successful, but a
    # bounded second read must independently see the event route, actual
    # stock-result notice and fresh process restore/history markers.
    for logfile, field, expected in (
        (work / "tournament.log", "create_log_sha256", EXPECTED_CREATE_MARKERS),
        (work / "reopen.log", "reopen_log_sha256", EXPECTED_REOPEN_MARKERS),
    ):
        check_native_log(logfile, expected)
        if sha256(logfile) != receipt[field]:
            raise ValueError(f"post-reopen native transcript digest differs: {logfile.name}")
    return {
        "source_commit": expected_source,
        "inner_zip_sha256": expected_zip,
        "qa_harness_commit": candidate["qa_harness_commit"],
        "smoke_run_id": candidate["smoke_run_id"],
        "backend": "snesrecomp",
        "run_sha256": receipt["run_sha256"],
        "paired_course": bound_pair["course"],
        "paired_winner": bound_pair["winner"],
        "paired_ticks60": bound_pair["elapsed_ticks60"],
        "match_sha256": receipt["match_sha256"],
        "receipt_sha256": receipt["receipt_sha256"],
        "create_log_sha256": receipt["create_log_sha256"],
        "reopen_log_sha256": receipt["reopen_log_sha256"],
        "result": "read-only receipt consistency only, not physical or full schedule acceptance",
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--work", type=Path, required=True)
    p.add_argument("--candidate", type=Path, required=True)
    p.add_argument("--expected-source", required=True)
    p.add_argument("--expected-zip-sha256", required=True)
    p.add_argument("--expected-harness-sha", help="current checkout git SHA")
    p.add_argument("--expected-smoke-run-id", help="workflow-selected smoke run")
    args = p.parse_args()
    try:
        result = verify(
            args.work, args.candidate,
            args.expected_source, args.expected_zip_sha256,
            expected_harness=args.expected_harness_sha,
            expected_smoke_run=args.expected_smoke_run_id,
        )
    except (OSError, ValueError) as exc:
        p.error(str(exc))
    print("UR_WINDOWS_TOURNAMENT_RECEIPT_VERIFIED "
          f"source={result['source_commit']} zip={result['inner_zip_sha256']}")
    print("UR_WINDOWS_TOURNAMENT_RECEIPT_SCOPE exact_artifact_integrity_only "
          "release_l4_l5_certified=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
