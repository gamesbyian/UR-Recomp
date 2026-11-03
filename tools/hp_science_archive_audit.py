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
import io
import os
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


def _pe_timestamp_neutral_sha256(data: bytes) -> str | None:
    """Exploratory PE identity with only the four COFF timestamp bytes masked.

    This is NOT a replacement for the fully bound executable SHA-256.
    Invalid, non-PE or ambiguous headers return no comparable fingerprint.
    """
    if len(data) < 0x40 or data[:2] != b"MZ":
        return None
    pe = int.from_bytes(data[0x3c:0x40], "little")
    if pe < 0x40 or pe + 12 > len(data) or data[pe:pe + 4] != b"PE\0\0":
        return None
    digest = hashlib.sha256()
    digest.update(data[:pe + 8])
    digest.update(b"\0" * 4)
    digest.update(data[pe + 12:])
    return digest.hexdigest()


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
    # Read one bounded snapshot through a single descriptor. Its identity and
    # archive SHA-256 now describe exactly the same bytes audited by ZipFile,
    # even if the path is replaced immediately after the read completes.
    require(not artifact.is_symlink(), "redirected archive")
    try:
        flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(artifact, flags)
        with os.fdopen(fd, "rb") as source:
            info = os.fstat(source.fileno())
            require(stat.S_ISREG(info.st_mode) and 0 < info.st_size <= MAX_ARCHIVE,
                    "unexpected archive type/size")
            snapshot = source.read(MAX_ARCHIVE + 1)
        require(0 < len(snapshot) <= MAX_ARCHIVE, "archive exceeds bounded snapshot")
        with zipfile.ZipFile(io.BytesIO(snapshot)) as z:
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
            # Only read small executables again for optional comparison.
            # The original byte-exact, source-bound binding remains mandatory.
            pe_neutral = (_pe_timestamp_neutral_sha256(z.read(EXECUTABLE))
                          if length <= 16 * 1024 * 1024 else None)
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
    # Historical 4/8-worker receipts did not declare an explicit cohort wall
    # horizon. Keep them auditable without inventing a value. Once a producer
    # does declare one, enforce the only two authorized populations and the
    # independently fetched Actions event's manual-only widening boundary.
    horizon = receipt.get("wall_seconds_budget")
    if "wall_seconds_budget" in receipt:
        require(type(horizon) is int and horizon in (360, 600),
                "unsupported science cohort wall budget")
        require(horizon != 600 or event == "workflow_dispatch",
                "extended cohort wall budget is not a manual dispatch")
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
    first_seeds = {}
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
        first_seeds[index] = seed
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
        "archive_sha256": hashlib.sha256(snapshot).hexdigest(),
        "science_receipt_sha256": sig,
        "executable_sha256": exe_sha,
        # Cross-run comparison only: the full PE digest above is authoritative.
        "pe_coff_timestamp_neutral_executable_sha256": pe_neutral,
        "worker_first_seeds": [first_seeds[i] for i in sorted(first_seeds)],
        "stock_input_sha256": identity["stock_input_sha256"],
        "stock_script_sha256": identity["stock_script_sha256"],
        "workers": workers, "accepted_cases": accepted,
        "real_guest_processes": receipt["real_guest_processes"],
        "research_wall_seconds": elapsed,
        "declared_cohort_wall_seconds_budget": horizon,
        "accepted_cases_per_minute": round(60 * accepted / elapsed, 3),
        "fixture_source_rechecked": fixture_sha256 is not None,
        "limitations": [
            "The producer's SHA-256 seal is unkeyed, not a digital signature.",
            "GitHub event provenance depends on independently retrieved run metadata.",
            "No raw per-case guest traces exist in the uploaded summary receipt.",
            "PE timestamp-neutral fingerprint masks only four COFF header bytes, "
            "not source differences or gameplay behavior; full binary SHA-256 "
            "remains the independently bound executable identity.",
            "Only first worker seeds are retained; not all generated input plans.",
            "Zero original/native-event, physical-gamepad, or release-gate credit.",
        ],
        "release_gate_credit": 0,
    }



def compare_audited_runs(left: dict, right: dict) -> dict:
    """Observational comparison of two independently audited positive runs.

    This NEVER grants binary reuse, executable QA, or release acceptance.
    Call audit() on each raw ZIP and independent Actions JSON first.
    """
    for candidate in (left, right):
        require(isinstance(candidate, dict)
                and candidate.get("schema") == "ur-hp-science-archive-audit/1"
                and candidate.get("positive_receipt_verified") is True
                and candidate.get("release_gate_credit") == 0,
                "comparison requires two positive audit receipts")
    require(left["run_id"] != right["run_id"], "comparison requires distinct runs")
    one = left["worker_first_seeds"]
    two = right["worker_first_seeds"]
    require(isinstance(one, list) and isinstance(two, list)
            and all(type(x) is int for x in one + two)
            and len(set(one)) == len(one) and len(set(two)) == len(two),
            "invalid comparison seed populations")
    a, b = (left.get("pe_coff_timestamp_neutral_executable_sha256"),
            right.get("pe_coff_timestamp_neutral_executable_sha256"))
    normalized_equal = (isinstance(a, str) and HEX64.fullmatch(a) is not None
                        and isinstance(b, str) and HEX64.fullmatch(b) is not None
                        and a == b)
    exact_equal = left["executable_sha256"] == right["executable_sha256"]
    return {
        "schema": "ur-hp-science-cross-run-comparison/1",
        "run_ids": [left["run_id"], right["run_id"]],
        "same_source_commit": left["source_sha"] == right["source_sha"],
        "same_stock_fixture_hashes": (
            left["stock_input_sha256"], left["stock_script_sha256"]) == (
            right["stock_input_sha256"], right["stock_script_sha256"]),
        "same_full_executable_sha256": exact_equal,
        "same_pe_coff_timestamp_neutral_executable_sha256": normalized_equal,
        "distinct_first_worker_seeds_total": len(set(one + two)),
        "first_worker_seed_collisions": sorted(set(one).intersection(two)),
        "new_first_worker_seeds_in_second_run": len(set(two) - set(one)),
        "binary_comparison": (
            "exact_binary_bytes_equal" if exact_equal
            else "equal_except_pe_coff_timestamp" if normalized_equal
            else "different_or_unavailable"),
        "safe_to_skip_build_or_product_qa": False,
        "limitations": [
            "Both inputs must already have passed independent source-bound ZIP/Actions audits.",
            "First worker seeds are not the complete input-plan census.",
            "Equal PE bytes with a masked four-byte timestamp do not prove source, "
            "toolchain, portable package or release equivalence.",
            "No Windows QA, original/native comparison, physical gamepad or release gate credit.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", required=True, type=Path)
    parser.add_argument("--run-json", required=True, type=Path,
                        help="independently retrieved GitHub Actions run API JSON")
    parser.add_argument("--out", type=Path, help="optional read-only audit JSON output")
    parser.add_argument("--compare-artifact", type=Path,
                        help="second ROM-free archive for independent audited comparison")
    parser.add_argument("--compare-run-json", type=Path,
                        help="independently fetched GitHub Actions JSON for second archive")
    args = parser.parse_args()
    if (args.compare_artifact is None) != (args.compare_run_json is None):
        parser.error("--compare-artifact and --compare-run-json must both be supplied")
    try:
        run = _strict_json(args.run_json.read_bytes())
        # Import the canonical stock-route authority only when running inside
        # the source checkout, avoiding duplicate hand-entered fixture hashes.
        from tools import qa02_native_2p_seeded_endurance as native
        stock_input, stock_script = native.base_source()
        fixtures = (hashlib.sha256(stock_input.encode("utf-8")).hexdigest(),
                    hashlib.sha256(stock_script.encode("utf-8")).hexdigest())
        result = audit(args.artifact, run, fixture_sha256=fixtures)
        if args.compare_artifact is not None:
            other_run = _strict_json(args.compare_run_json.read_bytes())
            other = audit(args.compare_artifact, other_run, fixture_sha256=fixtures)
            result = {
                "first_run": result,
                "second_run": other,
                "comparison": compare_audited_runs(result, other),
            }
    except (AuditError, OSError, ValueError) as exc:
        print("HP_SCIENCE_AUDIT=refused " + str(exc), file=sys.stderr)
        return 1
    output = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        # Atomic publication: never follow a symlink, truncate a competing
        # writer's file or publish a partially written report.
        from tools.art.no_replace_report import publish_text_once
        try:
            publish_text_once(args.out, output)
        except OSError as exc:
            print("HP_SCIENCE_AUDIT=refused output publication: " +
                  type(exc).__name__, file=sys.stderr)
            return 1
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
