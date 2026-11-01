#!/usr/bin/env python3
"""Independently inspect an HP science Actions artifact and saved Actions run JSON.

Read-only, ROM-free inspection. The receipt is *hash sealed*, not a cryptographic
signature: independent guest execution, the claimed GitHub event and release
qualification cannot be established by an arbitrary ZIP or JSON alone.

Usage: python -m tools.hp_science_archive_audit --artifact windows-native-smoke.zip \
           --run-json actions-run.json
The run metadata must be fetched independently from GitHub's REST API. The
script never contacts GitHub or awards gameplay, physical-pad or release credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import stat
import sys
import zipfile

RUN_NAME = "HP unattended seeded 2P gameplay research"
RUN_PATH = ".github/workflows/owner-hp-seeded-2p-research.yml"
EXPECTED_REPO = "gamesbyian/UR-Recomp"
RECEIPT = "hp-seeded-2p-research-receipt.json"
BINDING = "windows-romfree-binary/binding.json"
EXECUTABLE = "windows-romfree-binary/UniracersSNESRecomp.exe"
SCHEMA = "ur-hp-windows-seeded-2p-research/1"
BINDING_SCHEMA = "ur-windows-smoke-romfree-pe-binding/1"
ROM_SHA = "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
MAX_ARCHIVE = 64 * 1024 * 1024
MAX_MEMBER = 128 * 1024 * 1024
MAX_TOTAL_UNCOMPRESSED = 256 * 1024 * 1024
MAX_JSON = 256 * 1024


class AuditError(ValueError):
    pass


def require(test: bool, reason: str) -> None:
    if not test:
        raise AuditError(reason)


def _strict_json(data: bytes) -> dict:
    require(len(data) <= MAX_JSON, "oversized metadata/receipt")
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "duplicate JSON field")
            result[key] = value
        return result
    def reject_constant(raw):
        raise AuditError("non-finite JSON constant: " + raw)
    try:
        result = json.loads(data.decode("utf-8"),
                            object_pairs_hook=unique_pairs,
                            parse_constant=reject_constant)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise AuditError("invalid JSON") from exc
    require(isinstance(result, dict), "expected JSON object")
    return result


def _hash_json(data: dict) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":"),
                                      ensure_ascii=True).encode("utf-8")).hexdigest()


def _safe_zip_members(z: zipfile.ZipFile) -> None:
    members = z.infolist()
    require(0 < len(members) <= 1000, "invalid archive entry count")
    seen = set()
    size = 0
    for entry in members:
        name = entry.filename
        require(name and "\\" not in name and not name.startswith("/")
                and all(p not in (".", "..") for p in name.split("/"))
                and not re.match(r"^[A-Za-z]:", name), "unsafe archive path")
        require(name not in seen, "duplicate archive member")
        seen.add(name)
        if entry.create_system == 3:
            mode = (entry.external_attr >> 16)
            require(not stat.S_ISLNK(mode), "archive symlink")
        require(entry.file_size <= MAX_MEMBER, "oversized archive member")
        size += entry.file_size
    require(size <= MAX_TOTAL_UNCOMPRESSED, "oversized expanded archive")
    for filename in (RECEIPT, BINDING, EXECUTABLE):
        require(filename in seen, "required archive member missing: " + filename)
    require(z.testzip() is None, "failed ZIP CRC check")


def _run_identity(run: dict) -> tuple[int, str, str]:
    require(type(run.get("id")) is int and run["id"] > 0, "invalid Actions run id")
    require(run.get("name") == RUN_NAME and run.get("path") == RUN_PATH,
            "wrong Actions workflow identity")
    require(run.get("event") in ("schedule", "workflow_dispatch"), "wrong Actions event")
    require(run.get("status") == "completed" and run.get("conclusion") == "success",
            "Actions run not completed successfully")
    require(run.get("head_branch") == "main", "not a main-branch Actions run")
    sha = run.get("head_sha")
    require(isinstance(sha, str) and HEX40.fullmatch(sha) is not None,
            "invalid Actions head SHA")
    repo = run.get("repository")
    if repo is not None:
        require(isinstance(repo, dict) and repo.get("full_name") == EXPECTED_REPO,
                "wrong Actions repository identity")
    require(run.get("html_url") ==
            f"https://github.com/{EXPECTED_REPO}/actions/runs/{run['id']}",
            "invalid Actions run URL")
    return run["id"], sha, run["event"]


def audit(artifact: Path, run: dict, *, fixture_sha256: tuple[str, str] | None = None) -> dict:
    """Validate retained evidence. Caller supplies independently fetched run JSON.

    fixture_sha256 optionally binds against independently verified canonical
    input/script text. A missing fixture is *reported*, not secretly assumed.
    """
    run_id, sha, event = _run_identity(run)
    require(artifact.is_file() and not artifact.is_symlink(), "missing/redirected archive")
    require(0 < artifact.stat().st_size <= MAX_ARCHIVE, "unexpected archive size")
    try:
        with zipfile.ZipFile(artifact) as z:
            _safe_zip_members(z)
            receipt = _strict_json(z.read(RECEIPT))
            binding = _strict_json(z.read(BINDING))
            with z.open(EXECUTABLE) as source:
                digest = hashlib.sha256()
                length = 0
                for block in iter(lambda: source.read(1 << 20), b""):
                    digest.update(block)
                    length += len(block)
            exe_sha = digest.hexdigest()
    except (OSError, zipfile.BadZipFile, RuntimeError) as exc:
        raise AuditError("invalid/unreadable artifact ZIP") from exc

    sig = receipt.get("receipt_sha256")
    require(isinstance(sig, str) and HEX64.fullmatch(sig) is not None,
            "missing/invalid receipt SHA-256")
    sealed = {k: v for k, v in receipt.items() if k != "receipt_sha256"}
    require(_hash_json(sealed) == sig, "receipt self-hash mismatch")
    require(receipt.get("schema") == SCHEMA and receipt.get("status") == "completed_positive",
            "not a completed-positive research receipt")
    require(receipt.get("run_id") == run_id and receipt.get("source_sha") == sha,
            "science receipt does not match Actions source and run")
    require(receipt.get("release_gate_credit") == 0
            and receipt.get("original_native_event_credit") == 0
            and receipt.get("physical_gamepads_tested") is False,
            "invalid science-only credit disclaimer")
    require(receipt.get("issues") == [], "research reports issues")
    workers = receipt.get("workers")
    accepted = receipt.get("accepted_cases")
    require(type(workers) is int and workers in (4, 8), "unsupported worker population")
    require(type(accepted) is int and accepted >= workers,
            "incomplete accepted cohort")
    require(type(receipt.get("attempted_cases")) is int
            and receipt["attempted_cases"] == accepted,
            "attempted/accepted mismatch")
    require(type(receipt.get("real_guest_processes")) is int
            and receipt["real_guest_processes"] == 4 * accepted,
            "incorrect four-way guest count")
    elapsed = receipt.get("elapsed_seconds")
    require(type(elapsed) in (float, int) and math.isfinite(elapsed) and elapsed > 0,
            "invalid research wall time")
    per_worker = receipt.get("per_worker")
    require(isinstance(per_worker, list) and len(per_worker) == workers,
            "missing worker summary")
    observed = set()
    count = 0
    for row in per_worker:
        require(isinstance(row, dict), "malformed worker row")
        index = row.get("worker")
        cases = row.get("case_count")
        seed = row.get("seed_first")
        duration = row.get("elapsed_seconds")
        require(type(index) is int and 0 <= index < workers and index not in observed,
                "invalid or duplicate worker index")
        observed.add(index)
        require(row.get("shard") == index % 2, "wrong worker shard")
        require(type(cases) is int and cases > 0, "missing worker cases")
        expected_seed = run_id % 10_000_000 + (index // 2) * 25_000_000 + (index % 2) * 1_000_003
        require(type(seed) is int and seed == expected_seed, "wrong worker seed namespace")
        require(type(duration) is float and math.isfinite(duration)
                and 0 <= duration <= elapsed + 0.002,
                "invalid per-worker wall time")
        count += cases
    require(count == accepted, "worker case totals disagree")

    identity = receipt.get("candidate_identity")
    require(isinstance(identity, dict) and identity.get("source_commit") == sha
            and identity.get("rom_sha256") == ROM_SHA,
            "research source/ROM identity mismatch")
    require(identity.get("native_executable_sha256") == exe_sha,
            "real executable differs from research witness")
    for key in ("stock_input_sha256", "stock_script_sha256"):
        require(isinstance(identity.get(key), str) and HEX64.fullmatch(identity[key]),
                "missing fixed input fixture identity")
    if fixture_sha256 is not None:
        require(len(fixture_sha256) == 2
                and (identity["stock_input_sha256"], identity["stock_script_sha256"]) == fixture_sha256,
                "fixture hashes do not match independently supplied source")

    require(binding.get("schema") == BINDING_SCHEMA
            and binding.get("source_commit") == sha
            and binding.get("executable_sha256") == exe_sha
            and type(binding.get("executable_bytes")) is int
            and binding["executable_bytes"] == length,
            "Windows ROM-free binary binding mismatch")
    require(binding.get("release_gate_credit") == 0
            and binding.get("physical_windows_accepted") is False
            and binding.get("rom_or_player_data_uploaded") is False
            and binding.get("original_zip_uploaded") is False,
            "invalid package evidence disclaimer")
    return {
        "schema": "ur-hp-science-archive-audit/1",
        "run_id": run_id, "source_sha": sha,
        "actions_event_from_supplied_metadata": event,
        "positive_receipt_verified": True,
        "archive_sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
        "science_receipt_sha256": sig,
        "executable_sha256": exe_sha,
        "workers": workers, "accepted_cases": accepted,
        "real_guest_processes": receipt["real_guest_processes"],
        "research_wall_seconds": elapsed,
        "accepted_cases_per_minute": round(60 * accepted / elapsed, 3),
        "fixture_source_rechecked": fixture_sha256 is not None,
        "limitations": [
            "The producer's SHA-256 seal is unkeyed, not a digital signature.",
            "GitHub event provenance depends on independently retrieved run metadata.",
            "No raw per-case guest traces exist in the uploaded summary receipt.",
            "Zero original/native-event, physical-gamepad, or release-gate credit.",
        ],
        "release_gate_credit": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", required=True, type=Path)
    parser.add_argument("--run-json", required=True, type=Path,
                        help="independently retrieved GitHub Actions run API JSON")
    parser.add_argument("--out", type=Path, help="optional read-only audit JSON output")
    args = parser.parse_args()
    try:
        run = _strict_json(args.run_json.read_bytes())
        # Import the canonical stock-route authority only when running inside
        # the source checkout, avoiding duplicate hand-entered fixture hashes.
        from tools import qa02_native_2p_seeded_endurance as native
        stock_input, stock_script = native.base_source()
        fixtures = (hashlib.sha256(stock_input.encode("utf-8")).hexdigest(),
                    hashlib.sha256(stock_script.encode("utf-8")).hexdigest())
        result = audit(args.artifact, run, fixture_sha256=fixtures)
    except (AuditError, OSError, ValueError) as exc:
        print("HP_SCIENCE_AUDIT=refused " + str(exc), file=sys.stderr)
        return 1
    output = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        if args.out.exists():
            print("HP_SCIENCE_AUDIT=refused output already exists", file=sys.stderr)
            return 1
        args.out.write_text(output, encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
