#!/usr/bin/env python3
"""Preserve exact original QA artifact-wrapper bytes, without new Windows QA."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path

SOURCE = "11501a15dea38fa912335cfc63103ce3a7208001"
ZIP_SHA = "5605aaf2ab1773b35385601564ee320ef065ce9bde091117b1e8e5a4661ed1f7"
RUN = 38813101482
OWNER_ID = 12009612842  # Owner ZIP retained separately by existing job.
QA_IDS = frozenset({12010371123, 12010675093, 12010555537, 12010495750,
                   12010421091, 12009069728, 12010750002, 12010640197,
                   12010490843})
DIGEST = re.compile(r"[0-9a-f]{64}\Z")
MAX_WRAPPER = 12 * 1024 * 1024


def require(valid: bool, reason: str) -> None:
    if not valid:
        raise ValueError("QA_RETENTION_INVALID: " + reason)


def pins(report: dict) -> list[tuple[int, str]]:
    require(report.get("schema") == "qa-exact-main-38813101482-independent-cross-artifact/1",
            "independent QA report schema drift")
    require(report.get("workflow_run") == RUN, "original run drift")
    candidate = report.get("candidate", {})
    require(candidate.get("source_commit") == SOURCE and
            candidate.get("portable_zip_sha256") == ZIP_SHA,
            "nominated source/ZIP not original")
    assertions = report.get("assertions", {})
    require(assertions.get("full_qa_gate_witnesses") == 0 and
            assertions.get("strict_original_native_usa_events_accepted") == 0,
            "cannot archive as certified release evidence")
    originals = report.get("outer_artifacts")
    require(isinstance(originals, list) and len(originals) == 10,
            "original wrapper population changed")
    result: dict[int, str] = {}
    for item in originals:
        require(isinstance(item, list) and len(item) == 2 and
                isinstance(item[0], int) and not isinstance(item[0], bool) and
                isinstance(item[1], str) and DIGEST.fullmatch(item[1]) is not None,
                "malformed independent wrapper receipt")
        require(item[0] not in result, "duplicate original artifact ID")
        result[item[0]] = item[1]
    require(set(result) == QA_IDS | {OWNER_ID},
            "unexpected original artifact identity")
    return sorted((key, result[key]) for key in QA_IDS)


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_wrappers(directory: Path, entries: list[tuple[int, str]]) -> dict:
    require(directory.is_dir() and not directory.is_symlink(), "root missing")
    names = {f"{key}.zip" for key, _ in entries}
    found = list(directory.iterdir())
    require(len(found) == len(names) and {p.name for p in found} == names,
            "missing/extra original ZIP wrappers")
    for artifact_id, wanted in entries:
        path = directory / f"{artifact_id}.zip"
        require(path.is_file() and not path.is_symlink() and
                0 < path.stat().st_size <= MAX_WRAPPER, "unsafe wrapper")
        require(digest(path) == wanted, "SHA-256 original wrapper changed")
        with zipfile.ZipFile(path) as z:
            infos = z.infolist()
            require(infos and len(infos) <= 1000,
                    "invalid/beyond-bounded original wrapper")
            for item in infos:
                parts = Path(item.filename).parts
                require(not item.filename.startswith("/") and ".." not in parts,
                        "unsafe original wrapper member")
            require(z.testzip() is None, "original wrapper CRC mismatch")
    return {
        "schema": "ur-retained-original-windows-QA-wrappers/1",
        "original_run": RUN,
        "source_commit": SOURCE,
        "candidate_zip_sha256": ZIP_SHA,
        "original_qa_wrapper_sha256": [[i, hash_] for i, hash_ in entries],
        "new_windows_executable_compiled": False,
        "release_gate_credit": 0,
        "physical_hardware_verified": False,
        "github_release_created": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qa-report", required=True, type=Path)
    parser.add_argument("--emit-index", type=Path)
    parser.add_argument("--verify-dir", type=Path)
    args = parser.parse_args()
    require((args.emit_index is None) != (args.verify_dir is None),
            "select exactly one operation")
    manifest = json.loads(args.qa_report.read_text(encoding="utf-8"))
    original = pins(manifest)
    if args.emit_index is not None:
        require(not args.emit_index.exists(), "refuse index overwrite")
        args.emit_index.write_text("".join(f"{i} {v}\n" for i,v in original),
                                  encoding="ascii")
        return
    result = verify_wrappers(args.verify_dir, original)
    path = args.verify_dir / "ORIGINAL-WRAPPER-RETENTION.json"
    require(not path.exists(), "refuse prior attestation overwrite")
    path.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
