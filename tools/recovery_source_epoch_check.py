#!/usr/bin/env python3
"""Offline, fail-closed Git-blob preflight for recovery candidate integration.

Observed blobs MUST come from an independent fresh GitHub read. This tool does
not fetch GitHub, apply patches, authenticate evidence, or grant QA credit.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

_SHA = re.compile(r"[0-9a-f]{40}\Z")


def _sha(value: object) -> bool:
    return type(value) is str and _SHA.fullmatch(value) is not None


def _path(value: object) -> bool:
    return (type(value) is str and value != "" and "\\" not in value and
            not value.startswith("/") and all(x not in ("", ".", "..") for x in value.split("/")) and
            not any(ord(c) < 32 or ord(c) == 127 for c in value))


def _sha_map(value: object, *, allow_missing: bool = False) -> dict[str, str | None]:
    if type(value) is not dict or not value:
        raise ValueError("missing or invalid Git blob map")
    if any(not _path(path) or not (_sha(sha) or (allow_missing and sha is None))
           for path, sha in value.items()):
        raise ValueError("invalid path or Git blob SHA")
    return value


def classify(candidate: dict, observed: dict) -> dict:
    """Classify exact bytes, not semantic equivalence or patch applicability."""
    if type(candidate) is not dict or type(observed) is not dict:
        raise ValueError("invalid recovery preflight envelope")
    if not _sha(candidate.get("source_main_sha")) or not _sha(observed.get("main_sha")):
        raise ValueError("missing exact Git main SHA")
    pre = _sha_map(candidate.get("preimage_blob_shas"), allow_missing=True)
    current = _sha_map(observed.get("blob_shas"), allow_missing=True)
    proposed = candidate.get("proposed_blob_shas", {})
    if type(proposed) is not dict or any(not _path(p) or not _sha(s) for p, s in proposed.items()):
        raise ValueError("invalid proposed Git blob map")
    if set(proposed) - set(pre):
        raise ValueError("proposed paths absent from preimage inventory")
    if set(pre) != set(current):
        raise ValueError("observed inventory must exactly cover candidate paths")
    rows = []
    for path in sorted(pre):
        before, now, after = pre[path], current[path], proposed.get(path)
        if before == now:
            state = "preimage-match"
        elif after is not None and after == now:
            state = "proposed-blob-present"
        else:
            state = "source-conflict"
        rows.append({"path": path, "status": state, "preimage_sha": before,
                     "observed_sha": now, "proposed_sha": after})
    states = {row["status"] for row in rows}
    status = ("applicable-preimages" if states == {"preimage-match"} else
              "already-proposed-blobs" if states == {"proposed-blob-present"} else
              "mixed-needs-review" if states <= {"preimage-match", "proposed-blob-present"} else
              "source-conflict")
    return {"schema": "ur-recovery-source-epoch/1", "status": status,
            "source_main_sha": candidate["source_main_sha"],
            "observed_main_sha": observed["main_sha"],
            "main_epoch_matches": candidate["source_main_sha"] == observed["main_sha"],
            "files": rows, "patch_tested": False, "release_gate_credit": False}


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--observed", type=Path, required=True)
    args = parser.parse_args()
    try:
        candidate = json.loads(args.candidate.read_text(encoding="utf-8"),
                               object_pairs_hook=_unique_pairs)
        observed = json.loads(args.observed.read_text(encoding="utf-8"),
                              object_pairs_hook=_unique_pairs)
        result = classify(candidate, observed)
    except (ValueError, OSError, UnicodeError) as exc:
        print(json.dumps({"status": "invalid-input", "reason": str(exc),
                          "release_gate_credit": False}, sort_keys=True))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] in ("applicable-preimages", "already-proposed-blobs") else 2


if __name__ == "__main__":
    raise SystemExit(main())
