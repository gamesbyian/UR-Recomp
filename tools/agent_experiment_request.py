#!/usr/bin/env python3
"""Strict, source-bound admission for a reusable, unprivileged GHA experiment.

An agent retries by pushing a new experiments/request.json on its dedicated
experiments/* branch. The branch's exact commit is the experiment source.
This validator never executes request-supplied shell or workflow expressions.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

SCHEMA = "ur-agent-experiment-request/1"
KINDS = frozenset(("qa01_zoo", "qa01_rf095_pcm", "windows_candidate"))
FIELDS = frozenset(("schema", "kind", "question", "expected", "owner", "attempt"))
HEX_SHA = re.compile(r"[0-9a-f]{40}\Z")
OWNER = re.compile(r"[A-Za-z0-9._-]{1,48}\Z")
EXPERIMENT_REF = re.compile(r"refs/heads/experiments/[A-Za-z0-9._/-]{1,128}\Z")


def no_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON field: " + key)
        result[key] = value
    return result


def reject_constant(value: str) -> None:
    raise ValueError("invalid non-finite JSON value: " + value)


def validate_request(raw: bytes, source_sha: str, ref: str) -> dict:
    if not HEX_SHA.fullmatch(source_sha):
        raise ValueError("exact 40-character source SHA required")
    if (not EXPERIMENT_REF.fullmatch(ref) or ".." in ref or "//" in ref
            or ref.endswith("/")):
        raise ValueError("request must execute on a dedicated experiments/* branch")
    if len(raw) > 4096 or not raw:
        raise ValueError("request must be nonempty and at most 4096 bytes")
    request = json.loads(raw, object_pairs_hook=no_duplicate_keys,
                         parse_constant=reject_constant)
    if not isinstance(request, dict) or set(request) != FIELDS:
        raise ValueError("request requires exactly: " + ", ".join(sorted(FIELDS)))
    if request["schema"] != SCHEMA or request["kind"] not in KINDS:
        raise ValueError("unknown experiment schema or kind")
    if not isinstance(request["owner"], str) or not OWNER.fullmatch(request["owner"]):
        raise ValueError("owner must be a short stable agent/workstream identifier")
    if type(request["attempt"]) is not int or not 1 <= request["attempt"] <= 10000:
        raise ValueError("attempt must be a positive bounded integer")
    for field in ("question", "expected"):
        value = request[field]
        if (not isinstance(value, str) or not 12 <= len(value) <= 500
                or any(ord(c) < 32 or ord(c) > 126 for c in value)):
            raise ValueError(field + " must be 12-500 printable ASCII characters")
    return {
        "schema": "ur-agent-experiment-receipt/1",
        "request": request,
        "request_sha256": hashlib.sha256(raw).hexdigest(),
        "source_sha": source_sha,
        "source_ref": ref,
        "qualification_status": "unreviewed_experiment",
        "usa_course_credit": 0,
        "release_gate_credit": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--ref", required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--gha-output", type=Path, required=True)
    args = parser.parse_args()
    if not args.request.is_file() or args.request.is_symlink():
        raise SystemExit("request must be a regular non-symlinked file")
    if args.receipt.exists() or args.receipt.is_symlink():
        raise SystemExit("refusing to overwrite an earlier experiment receipt")
    receipt = validate_request(args.request.read_bytes(),
                               args.source_sha, args.ref)
    args.receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n",
                            encoding="utf-8")
    with args.gha_output.open("a", encoding="utf-8") as out:
        out.write("kind=" + receipt["request"]["kind"] + "\n")
    print("EXPERIMENT_REQUEST_ACCEPTED kind=" + receipt["request"]["kind"]
          + " source=" + args.source_sha
          + " automatic_qualification=none")


if __name__ == "__main__":
    main()
