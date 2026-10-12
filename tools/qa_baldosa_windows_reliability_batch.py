#!/usr/bin/env python3
"""Manual Windows Baldosa shared-build guest/launcher reliability cohort.

Run existing real Win32 producers unmodified with fresh roots. Research-level
repeatability only: not original/native event parity, complete product journeys,
a physical-controller test, or release certification.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHA1 = re.compile(r"[0-9a-f]{40}\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
SUITES = ("guest", "launcher")
SHARDS = tuple(f"{suite}-{i}" for suite in SUITES for i in range(2))
# 60 Windows native guest repeats took ~150 minutes at prior measured pace.
# Bound at 60 per shard to retain headroom under the 240-minute job timeout.
TRIAL_POPULATIONS = (1, 3, 10, 30, 60)
SCHEMA = "ur-baldosa-win32-reliability-batch/1"
ROM_SHA = "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
GUEST_FLAGS = (
    "per_frame_wram_crc_identical",
    "modern_lifecycle_abi_exercised",
    "native_modern_user_data_root_isolation",
    "native_corrupt_selected_profile_fails_closed",
    "native_invalid_explicit_root_fails_closed",
    "physical_sdl_event_pump_exercised",
    "native_same_boundary_restart_restored",
    "native_delayed_guest_restart_restored",
)
LAUNCHER_FLAGS = (
    "verified_rom_used_temporarily", "rom_not_in_archive",
    "missing_rom_rejected_before_user_data",
    "wrong_rom_rejected_before_user_data",
    "package_local_and_relative_root_rejected",
    "external_junction_to_package_rejected",
    "real_extracted_launcher_accepted",
    "exact_native_profile_refusal_code_and_guidance",
    "rejected_profile_save_unchanged", "native_root_drawn",
    "canonical_8192_byte_save_outside_package",
    "published_zip_unchanged",
)


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def hash_object(data: dict) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def save(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def validate_producer(suite: str, report: dict, identity: dict) -> None:
    """Validate only independently known claims, not a self-produced pass flag."""
    if type(report) is not dict:
        raise ValueError("producer did not return a JSON object")
    if suite == "guest":
        for key in GUEST_FLAGS:
            if report.get(key) is not True:
                raise ValueError(f"native guest failed a required original observer: {key}")
        expected = {
            "classification": "windows_native_pause_and_named_profile_smoke_only",
            "rom_sha256": ROM_SHA,
            "exe_sha256": identity["exe_sha256"],
            "script_sha256": identity["script_sha256"],
            "video_driver": "windows",
            "guest_frames": 2473,
            "course_complete_credit": 0,
            "modern_frontend_connected": False,
            "packaged_windows_product": False,
            "physical_gamepad_hardware_tested": False,
        }
        for key, value in expected.items():
            if type(report.get(key)) is not type(value) or report[key] != value:
                raise ValueError(f"invalid source-authenticated guest report property {key}")
        for key in ("native_real_named_modern_profile_boot",
                    "native_existing_modern_profile_fresh_process",
                    "native_two_named_profile_isolation",
                    "modern_root_race_entry_p1", "modern_root_race_entry_p2"):
            if not isinstance(report.get(key), dict) or not report[key]:
                raise ValueError(f"missing actual native witness: {key}")
    else:
        for key in LAUNCHER_FLAGS:
            if report.get(key) is not True:
                raise ValueError(f"actual CMD launcher did not demonstrate {key}")
        if report.get("archive_sha256") != identity["archive_sha256"]:
            raise ValueError("launcher report tested another ZIP")
        # No producer is authorized to mint QA release credit in this cohort.
        if "release_gate_credit" in report or "qa01_accepted_courses" in report:
            raise ValueError("launcher report contains unexpected release assertion")


def identity_for(exe: Path, fixture: Path, archive: Path,
                 rom: Path, script: Path, source_sha: str) -> dict:
    if not SHA1.fullmatch(source_sha):
        raise ValueError("must pin an exact source commit")
    sources = dict(exe_sha256=exe, fixture_sha256=fixture,
                   archive_sha256=archive, rom_sha256=rom,
                   script_sha256=script)
    for key, path in sources.items():
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"missing/symlinked input: {key}")
    result = {key: sha(path) for key, path in sources.items()}
    result["source_commit"] = source_sha
    if result["rom_sha256"] != ROM_SHA:
        raise ValueError("only original, hash-pinned USA ROM is permitted")
    return result


def run_one(suite: str, exe: Path, fixture: Path, archive: Path, rom: Path,
            script: Path, root: Path, identity: dict) -> None:
    if root.exists():
        raise ValueError("refuse existing per-trial data root")
    if suite == "guest":
        cmd = [
            sys.executable, str(ROOT / "tools/baldosa_windows_native_pause_route.py"),
            "--exe", str(exe), "--profile-fixture", str(fixture),
            "--rom", str(rom), "--script", str(script),
            "--out", str(root), "--video", "windows",
            "--expected-frames", "2473", "--timeout", "95",
        ]
        report_path = root / "report.json"
        timeout = 2100
    else:
        cmd = [
            sys.executable, str(ROOT / "tools/verify_baldosa_windows_extracted_launcher.py"),
            "--zip", str(archive), "--rom", str(rom),
            "--out", str(root), "--timeout", "80",
        ]
        report_path = root / "launcher-acceptance.json"
        timeout = 500
    finished = subprocess.run(cmd, cwd=ROOT, capture_output=True,
                              text=True, errors="replace", timeout=timeout)
    if finished.returncode:
        excerpt = (finished.stdout + "\n" + finished.stderr)[-600:]
        raise RuntimeError(f"{suite} real Win32 producer exit={finished.returncode}; {excerpt}")
    if not report_path.is_file() or report_path.is_symlink():
        raise RuntimeError(f"{suite} claimed success without actual guest/launcher report")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    validate_producer(suite, report, identity)


def run_shard(*, source_sha: str, shard: str, trials: int,
              exe: Path, fixture: Path, archive: Path, rom: Path,
              script: Path, work: Path) -> dict:
    if shard not in SHARDS or trials not in TRIAL_POPULATIONS:
        raise ValueError("unsupported Windows shard or trial population")
    identity = identity_for(exe, fixture, archive, rom, script, source_sha)
    if work.exists():
        raise ValueError("cannot reuse an earlier trial work root")
    work.mkdir(parents=True)
    suite = shard.rsplit("-", 1)[0]
    failures = []
    attempted = 0
    start = time.monotonic()
    for index in range(trials):
        attempted += 1
        test_root = work / f"trial-{index:03d}"
        try:
            run_one(suite, exe, fixture, archive, rom, script, test_root, identity)
            shutil.rmtree(test_root)
        except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired,
                json.JSONDecodeError) as exc:
            failures.append({"iteration": index, "error_class": type(exc).__name__,
                             "error": str(exc)[-700:]})
            # Stopping early retains rather than destroys failure roots on
            # the ephemeral runner. Only compact receipts are uploaded.
            if len(failures) >= 2:
                break
    report = {
        "schema": SCHEMA, "identity": identity, "shard": shard,
        "suite": suite, "expected_trials": trials,
        "attempted_trials": attempted,
        "passed_trials": attempted - len(failures),
        "failed_trials": len(failures), "failures": failures,
        "disposition": ("completed_positive" if attempted == trials and not failures
                        else "invariant_violation"),
        "elapsed_ms": int((time.monotonic() - start) * 1000),
        "release_gate_credit": 0, "physical_hardware_witness": False,
        "independent_original_native_oracle": False,
        "integrated_complete_1p_2p_event_certified": False,
    }
    report["receipt_sha256"] = hash_object(report)
    return report


def aggregate(root: Path, source_sha: str, trials: int) -> dict:
    if not SHA1.fullmatch(source_sha) or trials not in TRIAL_POPULATIONS:
        raise ValueError("invalid expected campaign population")
    observed = []
    issues = []
    identities = []
    for shard in SHARDS:
        path = root / f"qa-win32-batch-{shard}" / "result.json"
        if not path.is_file():
            issues.append(f"{shard}: missing case result")
            continue
        try:
            report = json.loads(path.read_text(encoding="utf-8"))
            content = dict(report)
            digest = content.pop("receipt_sha256", None)
            if not isinstance(digest, str) or not SHA256.fullmatch(digest) or hash_object(content) != digest:
                raise ValueError("altered or unbound receipt hash")
            identity = content.get("identity")
            if not isinstance(identity, dict) or identity.get("source_commit") != source_sha:
                raise ValueError("source revision identity changed")
            if set(identity) != {"exe_sha256", "fixture_sha256", "archive_sha256",
                                 "rom_sha256", "script_sha256", "source_commit"}:
                raise ValueError("missing expected binary/ROM/script digests")
            if any(not SHA256.fullmatch(identity[name]) for name in identity
                   if name != "source_commit") or identity["rom_sha256"] != ROM_SHA:
                raise ValueError("invalid original ROM/binary/script hash")
            expected = {
                "schema": SCHEMA, "shard": shard, "suite": shard.rsplit("-", 1)[0],
                "expected_trials": trials, "release_gate_credit": 0,
                "physical_hardware_witness": False,
                "independent_original_native_oracle": False,
                "integrated_complete_1p_2p_event_certified": False,
            }
            if any(type(content.get(key)) is not type(value) or content.get(key) != value
                   for key, value in expected.items()):
                raise ValueError("invalid cohort identity or fake release credit")
            a, p, f = (content.get(k) for k in
                       ("attempted_trials", "passed_trials", "failed_trials"))
            if (any(type(x) is not int for x in (a, p, f))
                    or not 0 <= p <= a <= trials or p + f != a
                    or len(content["failures"]) != f
                    or (content["disposition"] == "completed_positive") !=
                       (a == trials and f == 0)
                    or content["disposition"] not in ("completed_positive", "invariant_violation")):
                raise ValueError("inconsistent scenario population or disposition")
            observed.append(content)
            identities.append(identity)
            if content["disposition"] != "completed_positive":
                issues.append(f"{shard}: {f} / {a} trials failed")
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            issues.append(f"{shard}: invalid case result ({exc})")
    if identities and any(x != identities[0] for x in identities[1:]):
        issues.append("case shards did not use exact identical source/binary/ROM inputs")
    if root.is_dir():
        expected_dirs = {f"qa-win32-batch-{shard}" for shard in SHARDS}
        unexpected = sorted(p.name for p in root.iterdir() if p.name not in expected_dirs)
        if unexpected:
            issues.append(f"unexpected result directories: {unexpected[:10]}")
    return {
        "schema": SCHEMA, "source_commit": source_sha, "requested_shards": len(SHARDS),
        "observed_shards": len(observed), "requested_trials": len(SHARDS)*trials,
        "attempted_trials": sum(x["attempted_trials"] for x in observed),
        "passed_trials": sum(x["passed_trials"] for x in observed),
        "failed_trials": sum(x["failed_trials"] for x in observed),
        "disposition": "completed_positive" if not issues else "incomplete_or_failed",
        "input_identity": identities[0] if identities else None,
        "issues": issues, "shards": observed,
        "release_gate_credit": 0, "physical_hardware_witness": False,
        "independent_original_native_oracle": False,
        "integrated_complete_1p_2p_event_certified": False,
        "scope": ("Original pinned Windows Baldosa native bridge, real 1P/2P "
                  "startup/input/pause/profiles and actual extracted ROMless CMD "
                  "launcher; neither complete-event equivalence nor integrated "
                  "Windows release certification."),
    }


def summary(data: dict) -> str:
    lines = ["## Baldosa Windows shared-binary reliability batch", "",
             f"**{data['disposition']}**: {data['passed_trials']}/"
             f"{data['requested_trials']} repeated complete producer invocations",
             "",
             f"Source SHA: \u0060{data['source_commit']}\u0060", "",
             "| Scenario shard | Repetitions | Passed | Outcome |",
             "| --- | ---: | ---: | --- |"]
    for row in data["shards"]:
        lines.append(f"| {row['shard']} | {row['attempted_trials']}/"
                     f"{row['expected_trials']} | {row['passed_trials']} | "
                     f"{row['disposition']} |")
    lines.extend(["", "No QA-01, complete Windows 1P/2P event or physical hardware credit.", ""])
    lines.extend(f"- {item}" for item in data["issues"])
    return "\n".join(lines) + "\n"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    modes = p.add_subparsers(dest="mode", required=True)
    r = modes.add_parser("run")
    r.add_argument("--source-sha", required=True)
    r.add_argument("--shard", choices=SHARDS, required=True)
    r.add_argument("--trials", type=int, required=True)
    for name in ("exe", "fixture", "archive", "rom", "script", "work", "out"):
        r.add_argument(f"--{name}", type=Path, required=True)
    a = modes.add_parser("aggregate")
    a.add_argument("--source-sha", required=True)
    a.add_argument("--trials", type=int, required=True)
    a.add_argument("--results", type=Path, required=True)
    a.add_argument("--out", type=Path, required=True)
    a.add_argument("--summary", type=Path, required=True)
    args = p.parse_args()
    if args.mode == "run":
        row = run_shard(
            source_sha=args.source_sha, shard=args.shard, trials=args.trials,
            exe=args.exe, fixture=args.fixture, archive=args.archive, rom=args.rom,
            script=args.script, work=args.work)
        save(args.out, row)
        print(f"{row['shard']}: {row['disposition']}, "
              f"{row['passed_trials']}/{row['expected_trials']} passes")
        return 0 if row["disposition"] == "completed_positive" else 1
    report = aggregate(args.results, args.source_sha, args.trials)
    save(args.out, report)
    args.summary.write_text(summary(report), encoding="utf-8")
    return 0 if report["disposition"] == "completed_positive" else 1


if __name__ == "__main__":
    raise SystemExit(main())
