#!/usr/bin/env python3
"""Local provenance-safe index of existing CI receipt schemas.

Never ingests raw guest logs, filenames, controller inputs or user paths into
the database. Only caller-selected local receipts are processed; no network.
An indexed receipt is a *producer diagnostic*, never independent release QA.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
from pathlib import Path

SHA40 = re.compile(r"[0-9a-f]{40}\Z")
SHA64 = re.compile(r"[0-9a-f]{64}\Z")
SCHEMAS = ("UR-CI-UNIT-RESULT/1", "ur-win32-acceptance-fanout-aggregate/2")
DDL = """CREATE TABLE IF NOT EXISTS receipts (
    digest TEXT PRIMARY KEY,
    schema TEXT NOT NULL,
    source_sha TEXT NOT NULL,
    outcome TEXT NOT NULL,
    expected INTEGER,
    observed INTEGER NOT NULL,
    failures INTEGER NOT NULL,
    missing INTEGER NOT NULL,
    release_gate_credit INTEGER NOT NULL DEFAULT 0 CHECK(release_gate_credit = 0)
);
CREATE INDEX IF NOT EXISTS receipts_by_source ON receipts(source_sha, schema);
"""

def _require(value: bool, reason: str) -> None:
    if not value:
        raise ValueError(reason)

def project(receipt: object) -> dict:
    """Validate identity/outcome shape and return an intentionally narrow row."""
    _require(isinstance(receipt, dict), "receipt must be object")
    schema = receipt.get("schema")
    _require(schema in SCHEMAS, "unsupported receipt schema")
    _require(receipt.get("release_gate_credit", 0) == 0,
             "receipt attempted release-gate promotion")
    if schema == "UR-CI-UNIT-RESULT/1":
        _require(receipt.get("authority") == "diagnostic-only",
                 "unit receipt authority mismatch")
        source = receipt.get("source")
        _require(isinstance(source, dict), "unit source missing")
        sha = source.get("pr_head_sha") or source.get("GITHUB_SHA")
        _require(isinstance(sha, str) and bool(SHA40.fullmatch(sha)),
                 "unit source SHA not exact")
        outcome = receipt.get("outcome")
        _require(outcome in ("pass", "fail", "incomplete", "harness_error"),
                 "unit outcome invalid")
        shards = receipt.get("shards")
        _require(isinstance(shards, list) and 1 <= len(shards) <= 128,
                 "unit shards missing or invalid")
        _require(all(isinstance(row, dict) and row.get("outcome") in
                     ("pass", "fail", "incomplete", "harness_error", "not_run")
                     for row in shards), "invalid shard outcome")
        count = receipt.get("total_tests_observed")
        _require(type(count) is int and count >= 0, "invalid observed test count")
        missing = receipt.get("missing_evidence")
        _require(isinstance(missing, list) and
                 all(isinstance(x, str) for x in missing),
                 "invalid missing-evidence field")
        if outcome == "pass":
            _require(not missing and all(x["outcome"] == "pass" for x in shards),
                     "unit success contradicts shard evidence")
        failures = sum(x["outcome"] in ("fail", "harness_error") for x in shards)
        return {"schema": schema, "source_sha": sha, "outcome": outcome,
                "expected": len(shards), "observed": count, "failures": failures,
                "missing": len(missing), "release_gate_credit": 0}
    sha = receipt.get("source_sha")
    _require(isinstance(sha, str) and bool(SHA40.fullmatch(sha)),
             "Windows source SHA invalid")
    expected = receipt.get("expected_cases")
    observed = receipt.get("observed_cases")
    _require(expected == 13 and type(observed) is int and 0 <= observed <= 13,
             "Windows inventory invalid")
    issues = receipt.get("issues")
    failed = receipt.get("failed_cases", [])
    _require(isinstance(issues, list) and all(isinstance(x, str) for x in issues),
             "Windows aggregate issues invalid")
    _require(isinstance(failed, list) and all(isinstance(x, dict) and
             x.get("reason") in ("nonzero_exit", "missing_case") for x in failed),
             "Windows failed-case classification invalid")
    complete = receipt.get("transport_complete")
    _require(type(complete) is bool, "Windows transport status invalid")
    _require(not complete or (observed == 13 and not issues and not failed),
             "Windows transport success contradicts evidence")
    _require(receipt.get("independent_physical_qa") is False,
             "producer attempted independent physical acceptance")
    return {"schema": schema, "source_sha": sha,
            "outcome": "pass" if complete else "incomplete",
            "expected": expected, "observed": observed,
            "failures": len(failed), "missing": len(issues),
            "release_gate_credit": 0}

def ingest(db: Path, paths: list[Path]) -> dict:
    _require(len(paths) > 0, "no input receipts")
    rows = []
    for path in paths:
        _require(path.is_file() and not path.is_symlink(),
                 "input receipt missing or redirected")
        raw = path.read_bytes()
        _require(len(raw) <= 4_000_000, "receipt too large")
        value = json.loads(raw)
        row = project(value)
        row["digest"] = hashlib.sha256(raw).hexdigest()
        rows.append(row)
    # Validate everything before opening the database; no partial admission.
    db.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db) as con:
        con.executescript(DDL)
        con.executemany("""INSERT OR IGNORE INTO receipts
            (digest,schema,source_sha,outcome,expected,observed,failures,missing,release_gate_credit)
            VALUES (:digest,:schema,:source_sha,:outcome,:expected,:observed,:failures,:missing,:release_gate_credit)""", rows)
    return {"processed": len(rows), "unique_input_digests": len({r["digest"] for r in rows})}

def query(db: Path, source_sha: str, limit: int) -> list[dict]:
    _require(bool(SHA40.fullmatch(source_sha)), "invalid source SHA")
    _require(1 <= limit <= 100, "invalid result limit")
    _require(db.is_file() and not db.is_symlink(), "index missing")
    with sqlite3.connect(f"file:{db.resolve()}?mode=ro", uri=True) as con:
        con.row_factory = sqlite3.Row
        return [dict(row) for row in con.execute(
            """SELECT digest,schema,source_sha,outcome,expected,observed,failures,missing,
                      release_gate_credit FROM receipts
               WHERE source_sha=? ORDER BY schema,digest LIMIT ?""",
            (source_sha, limit))]

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    a = sub.add_parser("ingest")
    a.add_argument("--db", type=Path, required=True)
    a.add_argument("receipts", nargs="+", type=Path)
    b = sub.add_parser("query")
    b.add_argument("--db", type=Path, required=True)
    b.add_argument("--source-sha", required=True)
    b.add_argument("--limit", type=int, default=25)
    args = p.parse_args()
    result = (ingest(args.db, args.receipts) if args.command == "ingest"
              else query(args.db, args.source_sha, args.limit))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
