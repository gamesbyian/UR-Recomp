#!/usr/bin/env python3
"""Bounded real-process C12 tournament-ownership stress; no package/QA gate credit."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import random
import re
import shutil
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_TEST = ROOT / "tests/unit/test_qa02_coordinator_create_race_process.py"
SOURCE_CPP = ROOT / "tests/native/qa02_coordinator_create_race_process.cpp"
SHA1 = re.compile(r"[0-9a-f]{40}\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
IDS = ("b" * 32, "c" * 32)


def checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def existing_test_sources() -> tuple[str, ...]:
    """Read the fixture's already owned compilation manifest, without importing tests."""
    syntax = ast.parse(SOURCE_TEST.read_text(encoding="utf-8"))
    for statement in syntax.body:
        if isinstance(statement, ast.Assign) and any(
            isinstance(name, ast.Name) and name.id == "SOURCES"
            for name in statement.targets
        ):
            value = ast.literal_eval(statement.value)
            if not isinstance(value, tuple) or not all(
                isinstance(name, str) and name.endswith(".cpp") and "/" not in name
                for name in value
            ):
                raise ValueError("C12 test source manifest is invalid")
            return value
    raise ValueError("C12 test has no canonical source manifest")


def build(executable: Path) -> None:
    if executable.exists() or executable.is_symlink():
        raise ValueError("refuse existing campaign executable")
    executable.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
        "-pedantic", "-pthread", "-I", str(ROOT / "native/product"),
        "-I", str(ROOT / "native/title"),
        *(str(ROOT / "native/product" / name) for name in existing_test_sources()),
        str(SOURCE_CPP), "-o", str(executable),
    ]
    subprocess.run(command, cwd=ROOT, check=True, timeout=240)
    if not executable.is_file():
        raise ValueError("C12 producer produced no executable")


def process_trial(executable: Path, root: Path, rng: random.Random) -> dict:
    root.mkdir(parents=False, exist_ok=False)
    barrier = root / "barrier"
    barrier.mkdir()
    order = list(IDS)
    rng.shuffle(order)
    children = []
    start = time.monotonic()
    result = {"order": ["b" if i == IDS[0] else "c" for i in order]}
    try:
        for identifier in order:
            children.append((identifier, subprocess.Popen(
                [str(executable), "contend", str(root), identifier],
                cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )))
        deadline = time.monotonic() + 10
        while not all((barrier / ("ready-" + identifier)).is_file() for identifier in IDS):
            if any(process.poll() is not None for _, process in children):
                raise RuntimeError("contender exited before synchronization")
            if time.monotonic() > deadline:
                raise TimeoutError("both contenders did not reach C12 barrier")
            time.sleep(0.01)
        # Both processes are waiting on the *same* file. Vary the release
        # micro-delay and launch order, without changing game/product inputs.
        time.sleep(rng.randint(0, 6) / 1000)
        (barrier / "go").touch()
        codes = {}
        for identifier, process in children:
            out, err = process.communicate(timeout=25)
            codes["b" if identifier == IDS[0] else "c"] = process.returncode
            if process.returncode not in (0, 6):
                raise RuntimeError(
                    f"contender {identifier[0]} rc={process.returncode} "
                    f"out={out[:400]!r} err={err[:400]!r}"
                )
            expected_marker = b"QA02_C12_CREATED" if process.returncode == 0 else b"QA02_C12_CONFLICT"
            if expected_marker not in out:
                raise RuntimeError(f"missing {expected_marker!r} on {identifier[0]}")
        result["return_codes"] = codes
        if sorted(codes.values()) != [0, 6]:
            raise RuntimeError(f"not exactly one active winner: {codes}")
        active = root / "local-tournaments/active.urtournament"
        if not active.is_file():
            raise RuntimeError("missing canonical tournament active pointer")
        before = checksum(active)
        for _ in range(2):
            verified = subprocess.run(
                [str(executable), "verify", str(root), IDS[0]],
                cwd=ROOT, capture_output=True, timeout=25,
            )
            if verified.returncode != 0 or b"QA02_C12_SINGLE_ACTIVE_NO_CREDIT" not in verified.stdout:
                raise RuntimeError(
                    f"fresh restore rejected rc={verified.returncode} "
                    f"out={verified.stdout[:400]!r} err={verified.stderr[:400]!r}"
                )
        if checksum(active) != before:
            raise RuntimeError("read-only restore modified active event bytes")
        result.update({"passed": True, "active_sha256": before})
    except (OSError, RuntimeError, TimeoutError, subprocess.TimeoutExpired) as exc:
        result.update({"passed": False, "error": str(exc)})
    finally:
        for _, child in children:
            if child.poll() is None:
                child.kill()
            child.communicate(timeout=10)
        result["elapsed_ms"] = int((time.monotonic() - start) * 1000)
    return result


def run_shard(*, executable: Path, source_sha: str, binary_sha256: str,
              trials: int, shard: int, seed: int, work: Path) -> dict:
    if not SHA1.fullmatch(source_sha) or not SHA256.fullmatch(binary_sha256):
        raise ValueError("unbound source or binary digest")
    if not executable.is_file() or checksum(executable) != binary_sha256:
        raise ValueError("stale, missing or corrupted compiled C12 fixture")
    if trials < 1 or trials > 2000 or shard not in range(4):
        raise ValueError("trial count or shard is out of bounds")
    work.mkdir(parents=False, exist_ok=False)
    rng = random.Random(seed)
    attempts = []
    failures = 0
    for index in range(trials):
        root = work / f"trial-{index:05d}"
        current = process_trial(executable, root, rng)
        current["index"] = index
        attempts.append(current)
        if current["passed"]:
            shutil.rmtree(root)  # only newly-created private trial roots
        else:
            failures += 1
            if failures == 5:
                break  # avoid spending thousands of runner-minutes on a systemic break
    return {
        "schema": "ur-qa02-c12-campaign-shard/1",
        "source_commit": source_sha,
        "binary_sha256": binary_sha256,
        "shard": shard,
        "seed": seed,
        "requested_trials": trials,
        "attempted_trials": len(attempts),
        "passed_trials": sum(1 for row in attempts if row["passed"]),
        "failed_trials": failures,
        "disposition": "observed_failure" if failures else (
            "completed_positive" if len(attempts) == trials else "incomplete"),
        "failures": [row for row in attempts if not row["passed"]],
        "elapsed_ms": sum(row["elapsed_ms"] for row in attempts),
        "release_gate_credit": 0,
        "process_death_or_power_loss_claim": False,
    }


def aggregate(results_dir: Path, source_sha: str, binary_sha256: str,
              trials: int, seed: int) -> dict:
    if not SHA1.fullmatch(source_sha) or not SHA256.fullmatch(binary_sha256):
        raise ValueError("invalid input provenance")
    members, missing, defects = [], [], []
    for shard in range(4):
        path = results_dir / f"qa02-c12-shard-{shard}/result.json"
        if not path.is_file():
            missing.append(shard)
            continue
        try:
            row = json.loads(path.read_text(encoding="utf-8"))
            if (
                row.get("schema") != "ur-qa02-c12-campaign-shard/1"
                or row.get("source_commit") != source_sha
                or row.get("binary_sha256") != binary_sha256
                or row.get("shard") != shard
                or row.get("seed") != seed + shard * 1000003
                or row.get("requested_trials") != trials
                or row.get("attempted_trials") != row.get("passed_trials", 0) + row.get("failed_trials", 0)
                or row.get("attempted_trials", 0) > trials
                or row.get("release_gate_credit") != 0
            ):
                defects.append(f"shard-{shard}: manifest/provenance/count mismatch")
                continue
            if row.get("disposition") == "completed_positive" and (
                row.get("failed_trials") != 0 or row.get("attempted_trials") != trials
            ):
                defects.append(f"shard-{shard}: false completed_positive")
                continue
            members.append(row)
        except (OSError, ValueError, TypeError) as exc:
            defects.append(f"shard-{shard}: unreadable evidence: {exc}")
    negative = [m["shard"] for m in members if m["failed_trials"]]
    if defects:
        disposition = "evidence_invalid"
    elif negative:
        disposition = "observed_failure"
    elif missing or len(members) < 4:
        disposition = "incomplete"
    elif all(m["disposition"] == "completed_positive" for m in members):
        disposition = "completed_positive"
    else:
        disposition = "incomplete"
    return {
        "schema": "ur-qa02-c12-campaign-aggregate/1",
        "source_commit": source_sha,
        "binary_sha256": binary_sha256,
        "requested_trials": 4 * trials,
        "observed_trials": sum(m["attempted_trials"] for m in members),
        "passed_trials": sum(m["passed_trials"] for m in members),
        "failed_trials": sum(m["failed_trials"] for m in members),
        "missing_shards": missing,
        "invalid_shards": defects,
        "failing_shards": negative,
        "disposition": disposition,
        "release_gate_credit": 0,
        "scope": "Native production coordinator C12 OS-process CAS races only; no complete game, packaged Windows, disk-power-loss or user-device witness.",
    }


def write_report(path: Path, data: dict, summary: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with summary.open("a", encoding="utf-8") as output:
        output.write(
            f"## QA-02 C12 process-race campaign\n\n"
            f"Disposition: **{data['disposition']}**; completed/target "
            f"{data.get('observed_trials',data.get('attempted_trials',0))}/"
            f"{data.get('requested_trials',0)}; passed "
            f"{data.get('passed_trials',0)}; failed {data.get('failed_trials',0)}.\n\n"
            f"Source: \`{data['source_commit']}\`; binary SHA-256 "
            f"\`{data['binary_sha256']}\`.\n\n"
            "Only production coordinator's native OS-process C12 atomic ownership is exercised. "
            "**Release credit: 0; no physical hardware, Windows ZIP or power-loss claim.**\n\n"
        )
        if data.get("missing_shards") or data.get("invalid_shards") or data.get("failing_shards"):
            output.write("Missing: " + str(data.get("missing_shards", [])) + "; "
                         "invalid: " + str(data.get("invalid_shards", [])) + "; "
                         "failing: " + str(data.get("failing_shards", [])) + "\n\n")


def cli() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="command", required=True)
    b = sub.add_parser("build")
    b.add_argument("--executable", type=Path, required=True)
    s = sub.add_parser("run")
    s.add_argument("--executable", type=Path, required=True)
    s.add_argument("--source-sha", required=True)
    s.add_argument("--binary-sha256", required=True)
    s.add_argument("--trials", type=int, required=True)
    s.add_argument("--shard", type=int, required=True)
    s.add_argument("--seed", type=int, required=True)
    s.add_argument("--work", type=Path, required=True)
    s.add_argument("--out", type=Path, required=True)
    s.add_argument("--summary", type=Path, required=True)
    a = sub.add_parser("aggregate")
    a.add_argument("--results-dir", type=Path, required=True)
    a.add_argument("--source-sha", required=True)
    a.add_argument("--binary-sha256", required=True)
    a.add_argument("--trials", type=int, required=True)
    a.add_argument("--seed", type=int, required=True)
    a.add_argument("--out", type=Path, required=True)
    a.add_argument("--summary", type=Path, required=True)
    args = ap.parse_args()
    if args.command == "build":
        build(args.executable)
        print(checksum(args.executable))
        return 0
    if args.command == "run":
        report = run_shard(
            executable=args.executable, source_sha=args.source_sha,
            binary_sha256=args.binary_sha256, trials=args.trials,
            shard=args.shard, seed=args.seed, work=args.work,
        )
    else:
        report = aggregate(
            args.results_dir, args.source_sha, args.binary_sha256,
            args.trials, args.seed,
        )
    write_report(args.out, report, args.summary)
    print(json.dumps({k: report[k] for k in ("disposition", "requested_trials", "passed_trials", "failed_trials")}, sort_keys=True))
    return 0 if report["disposition"] == "completed_positive" else 1


if __name__ == "__main__":
    raise SystemExit(cli())
