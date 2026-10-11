#!/usr/bin/env python3
"""Manual QA-02/03 production-store recovery cohort; no product/release credit.

Compiles the EXISTING native fault fixture once, then repeats five disjoint
fresh-process fault journeys on private roots. Case oracles are copied from
the established test_qa02_fixture_hardkill_process.py assertions, not invented
gameplay simulators. This does not emulate a played 2P match or power failure.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import random
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import qa02_c12_campaign as c12

SCHEMA = "ur-qa02-recovery-campaign/1"
SUITES = ("c09-orphan", "c14-c15-receipt", "qa03-midseries",
          "hardkill-owner", "c16-storage-outage")
SOURCE_TEST = ROOT / "tests/unit/test_qa02_fixture_hardkill_process.py"
SOURCE_CPP = ROOT / "tests/native/qa02_fixture_hardkill_process.cpp"
SHA1 = re.compile(r"[0-9a-f]{40}\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
INSTANCE = "a" * 32


class TrialError(RuntimeError):
    pass


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_hash(data: dict) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def save(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def existing_sources() -> tuple[str, ...]:
    """Validate the two original production fixture compilation manifests agree."""
    tree = ast.parse(SOURCE_TEST.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(name, ast.Name) and name.id == "SOURCES"
            for name in node.targets
        ):
            files = ast.literal_eval(node.value)
            expected = c12.existing_test_sources()
            if not isinstance(files, tuple) or files != expected or len(files) != len(set(files)):
                raise ValueError("C09/C14/C15 production source manifest disagrees with C12")
            return files
    raise ValueError("original fault fixture has no sources manifest")


def build(exe: Path) -> None:
    if exe.exists() or exe.is_symlink():
        raise ValueError("refuse to replace existing fault fixture")
    exe.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
           "-pedantic", "-pthread", "-I", str(ROOT / "native/product"),
           "-I", str(ROOT / "native/title"),
           *(str(ROOT / "native/product" / p) for p in existing_sources()),
           str(SOURCE_CPP), "-o", str(exe)]
    subprocess.run(cmd, cwd=ROOT, check=True, timeout=300)
    if not exe.is_file():
        raise ValueError("native producer not built")


def action(exe: Path, name: str, root: Path, expected: int = 0,
           marker: bytes | None = None) -> bytes:
    try:
        process = subprocess.run([str(exe), name, str(root)], cwd=ROOT,
                                 capture_output=True, timeout=25)
    except subprocess.TimeoutExpired as exc:
        raise TrialError(f"{name}: process timed out") from exc
    if process.returncode != expected:
        raise TrialError(f"{name}: exit {process.returncode}, expected {expected}; "
                         f"stdout={process.stdout[:180]!r} stderr={process.stderr[:180]!r}")
    if marker is not None and marker not in process.stdout:
        raise TrialError(f"{name}: missing {marker.decode('ascii')} assertion marker")
    return process.stdout


def count(root: Path, glob: str) -> int:
    return len(list(root.glob(glob)))


def require(condition: bool, label: str) -> None:
    if not condition:
        raise TrialError(label)


def barrier_wait(child: subprocess.Popen, path: Path) -> None:
    deadline = time.monotonic() + 12
    while not path.is_file():
        if child.poll() is not None:
            raise TrialError("owner exited before synchronized fault barrier")
        if time.monotonic() >= deadline:
            raise TrialError("owner did not reach synchronized fault barrier")
        time.sleep(0.01)


def wait_child(child: subprocess.Popen, expected: int, marker: bytes) -> None:
    try:
        out, err = child.communicate(timeout=25)
    except subprocess.TimeoutExpired as exc:
        raise TrialError("synchronized owner did not finish") from exc
    if child.returncode != expected or marker not in out:
        raise TrialError(f"owner outcome {child.returncode} expected {expected} "
                         f"marker={marker!r}, stdout={out[:180]!r} stderr={err[:180]!r}")


def suite_c09(exe: Path, root: Path, jitter: float) -> None:
    records = root / "multiplayer-runs"
    action(exe, "kill-c09", root, 79)
    require(count(records, "*.urrun") == 0, "orphan unexpectedly published run")
    require(count(records, "*.urmatch") == 1, "orphan sidecar not published")
    time.sleep(jitter)
    for _ in range(2):
        action(exe, "verify-c09", root, marker=b"QA02_C09_NO_RUN_NO_CREDIT")
    action(exe, "recover-c09", root, marker=b"QA02_C09_LATER_VALID_RETRY")
    require(count(records, "*.urrun") == 1, "valid C09 recovery missing run")
    require(count(records, "*.urmatch") == 2, "C09 orphan lost or wrong sidecar count")
    action(exe, "verify-c15", root)


def suite_receipt(exe: Path, root: Path, jitter: float) -> None:
    records = root / "multiplayer-runs"
    base = root / "local-tournaments" / INSTANCE
    receipt = base / "fixtures/fixture-0.urfixture"
    pending = base / "pending.urlaunch"
    action(exe, "kill-c14", root, 77)
    require(count(records, "*.urrun") == 1 and
            count(records, "*.urrun.urmatch") == 1,
            "C14 real completed record pair missing")
    require(not receipt.exists() and pending.is_file(),
            "C14 must remain uncredited with recoverable pending launch")
    time.sleep(jitter)
    for _ in range(2):
        action(exe, "verify-c14", root, marker=b"QA02_C14_ZERO_CREDIT")
    action(exe, "kill-c15", root, 78)
    require(count(records, "*.urrun") == 2 and
            count(records, "*.urrun.urmatch") == 2,
            "C15 record pair count incorrect")
    require(receipt.is_file() and pending.is_file(), "C15 receipt/pending missing")
    original, token = receipt.read_bytes(), pending.read_bytes()
    for _ in range(2):
        action(exe, "verify-c15", root, marker=b"QA02_C15_SINGLE_RECEIPT_SINGLE_AWARD")
        require(receipt.read_bytes() == original and pending.read_bytes() == token,
                "read-only restore mutated receipt or pending token")
    receipt.write_bytes(b"CORRUPTED-IMMUTABLE-RECEIPT")
    action(exe, "verify-corrupt", root, marker=b"QA02_CORRUPT_RECEIPT_REJECTED")
    require(receipt.read_bytes() == b"CORRUPTED-IMMUTABLE-RECEIPT",
            "corrupt receipt was silently rewritten")
    receipt.write_bytes(original)
    action(exe, "verify-c15", root, marker=b"QA02_C15_SINGLE_RECEIPT_SINGLE_AWARD")


def suite_midseries(exe: Path, root: Path, jitter: float) -> None:
    records = root / "multiplayer-runs"
    receipts = root / "local-tournaments" / INSTANCE / "fixtures"
    action(exe, "qa03-create-round-robin", root, marker=b"QA03_CREATED_UNPLAYED")
    action(exe, "qa03-cancel-next", root, marker=b"QA03_CANCELLED_WITHOUT_CREDIT")
    require(count(records, "*.urrun") == 0, "cancelled tournament minted a run")
    action(exe, "qa03-credit-next", root, marker=b"QA03_CREDITED_FIXTURE 0")
    time.sleep(jitter)
    action(exe, "qa03-kill-midseries", root, 82)
    require(count(records, "*.urrun") == 2 and
            count(receipts, "fixture-*.urfixture") == 1,
            "interrupted result was incorrectly credited")
    for index in range(1, 6):
        action(exe, "qa03-credit-next", root,
               marker=f"QA03_CREDITED_FIXTURE {index}".encode("ascii"))
    action(exe, "qa03-verify-round-robin-interrupted", root,
           marker=b"QA03_COMPLETED_RESTORED_STANDINGS_HISTORY_RECORDS")
    require(count(records, "*.urrun") == 7 and
            count(receipts, "fixture-*.urfixture") == 6,
            "six fixture credits must survive midseries death")
    action(exe, "qa03-replace-completed", root,
           marker=b"QA03_REPLACED_WITH_COMPLETED_HISTORY_PRESERVED")
    require(count(receipts, "fixture-*.urfixture") == 6,
            "replacement lost historical receipts")


def suite_hardkill(exe: Path, root: Path, jitter: float) -> None:
    owner = subprocess.Popen([str(exe), "owner-hold", str(root)], cwd=ROOT,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        barrier_wait(owner, root / "barrier/owner-live")
        require(owner.poll() is None, "owner died before enforced OS kill")
        time.sleep(jitter)
        owner.kill()  # Real SIGKILL/TerminateProcess, not fixture's graceful exit
        owner.communicate(timeout=10)
        require(owner.returncode != 0, "hard-killed owner returned success")
    finally:
        if owner.poll() is None:
            owner.kill()
            owner.communicate(timeout=10)
    records = root / "multiplayer-runs"
    require(count(records, "*.urrun") == 1, "hard-killed owner lost committed run")
    action(exe, "retry-owner-crash", root, marker=b"QA02_CRASH_RELEASED_AND_RETRIED")
    require(count(records, "*.urrun") == 2, "OS kill retry did not preserve both runs")
    action(exe, "verify-c15", root, marker=b"QA02_C15_SINGLE_RECEIPT_SINGLE_AWARD")


def suite_outage(exe: Path, root: Path, jitter: float) -> None:
    owner = subprocess.Popen([str(exe), "c16-receipt-storage-owner", str(root)],
                             cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        barrier_wait(owner, root / "barrier/receipt-offline")
        time.sleep(jitter)
        action(exe, "c16-outage-reader", root,
               marker=b"QA02_C16_FAIL_CLOSED_WHILE_OFFLINE")
        wait_child(owner, 0, b"QA02_C16_STORAGE_RECOVERED_ONCE")
    finally:
        if owner.poll() is None:
            owner.kill()
            owner.communicate(timeout=10)
    records = root / "multiplayer-runs"
    receipts = root / "local-tournaments" / INSTANCE / "fixtures"
    require(count(records, "*.urrun") == 1 and
            count(records, "*.urrun.urmatch") == 1 and
            count(receipts, "*.urfixture") == 1,
            "recovered C16 claimed wrong immutable pair/receipt count")
    action(exe, "verify-c15", root, marker=b"QA02_C15_SINGLE_RECEIPT_SINGLE_AWARD")


IMPLEMENTATIONS = dict(zip(SUITES, (suite_c09, suite_receipt, suite_midseries,
                                     suite_hardkill, suite_outage)))


def run_suite(*, exe: Path, source_sha: str, binary_sha256: str, suite: str,
              iterations: int, seed: int, work: Path) -> dict:
    if not SHA1.fullmatch(source_sha) or not SHA256.fullmatch(binary_sha256):
        raise ValueError("invalid exact revision or binary hash")
    if suite not in SUITES or iterations not in (10, 100, 500):
        raise ValueError("unknown suite or unbounded iteration count")
    if not exe.is_file() or digest(exe) != binary_sha256:
        raise ValueError("missing/stale shared production process fixture")
    if work.exists():
        raise ValueError("refuse nonempty fault campaign work root")
    work.mkdir(parents=True)
    rng = random.Random(seed)
    failed, attempted, start = [], 0, time.monotonic()
    try:
        for index in range(iterations):
            trial_root = work / f"trial-{index:05d}"
            trial_root.mkdir()
            attempted += 1
            try:
                # Every case gets a separate genuine user-data root and fresh
                # processes. Only the inter-process timing jitter varies.
                IMPLEMENTATIONS[suite](exe, trial_root, rng.randint(0, 8) / 1000)
                shutil.rmtree(trial_root)
            except Exception as exc:
                failed.append({"trial": index, "error": str(exc)[:420],
                               "kind": type(exc).__name__})
                # Retain the failure root only on the isolated runner.
                if len(failed) >= 3:
                    break
    except BaseException:
        # All completed attempts are written only on normal return; a killed
        # or timed-out shard has no valid receipt, so aggregate fails closed.
        raise
    result = {
        "schema": SCHEMA, "source_sha": source_sha,
        "binary_sha256": binary_sha256, "suite": suite,
        "seed": seed, "requested_iterations": iterations,
        "attempted_iterations": attempted,
        "passed_iterations": attempted - len(failed),
        "failed_iterations": len(failed),
        "disposition": ("completed_positive" if not failed and attempted == iterations
                        else "invariant_violation"),
        "failures": failed, "elapsed_ms": round((time.monotonic() - start) * 1000),
        "retained_failure_root_count": len(failed),
        "release_gate_credit": 0, "physical_hardware_covered": False,
        "actual_guest_gameplay_covered": False,
    }
    result["receipt_sha256"] = json_hash(result)
    return result


def aggregate(directory: Path, source_sha: str, binary_sha256: str,
              iterations: int, seed: int) -> dict:
    if not SHA1.fullmatch(source_sha) or not SHA256.fullmatch(binary_sha256):
        raise ValueError("invalid source/binary identity")
    if iterations not in (10, 100, 500):
        raise ValueError("unsupported iteration setting")
    rows, problems = [], []
    for index, suite in enumerate(SUITES):
        file = directory / f"qa02-recovery-{suite}" / "result.json"
        if not file.is_file():
            problems.append(f"{suite}: missing receipt")
            continue
        try:
            row = json.loads(file.read_text())
            claimed_hash = row.pop("receipt_sha256")
            if json_hash(row) != claimed_hash:
                raise ValueError("receipt integrity failure")
            expected = {"schema": SCHEMA, "source_sha": source_sha,
                        "binary_sha256": binary_sha256, "suite": suite,
                        "seed": seed + index * 1009,
                        "requested_iterations": iterations,
                        "release_gate_credit": 0,
                        "physical_hardware_covered": False,
                        "actual_guest_gameplay_covered": False}
            if any(row.get(key) != value for key, value in expected.items()):
                raise ValueError("cohort identity/release-credit mismatch")
            attempted = row["attempted_iterations"]
            passed = row["passed_iterations"]
            failed = row["failed_iterations"]
            if (any(type(k) is not int for k in (attempted, passed, failed))
                    or not 0 <= passed <= attempted <= iterations
                    or not 0 <= failed <= attempted
                    or passed + failed != attempted
                    or len(row["failures"]) != failed
                    or row["disposition"] not in ("completed_positive", "invariant_violation")
                    or (row["disposition"] == "completed_positive") !=
                       (failed == 0 and attempted == iterations)):
                raise ValueError("impossible case counts or disposition")
            row["receipt_sha256"] = claimed_hash
            rows.append(row)
            if row["disposition"] != "completed_positive":
                problems.append(f"{suite}: {failed} failed / {attempted} attempted")
        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            problems.append(f"{suite}: invalid receipt ({exc})")
    extras = [p.name for p in directory.iterdir()
              if p.name.startswith("qa02-recovery-") and
              p.name[len("qa02-recovery-"):] not in SUITES] if directory.is_dir() else []
    if extras:
        problems.append(f"unexpected cohort receipts: {sorted(extras)}")
    result = {
        "schema": SCHEMA, "source_sha": source_sha,
        "binary_sha256": binary_sha256,
        "requested_suite_count": len(SUITES),
        "completed_suite_count": len(rows),
        "requested_iterations": len(SUITES) * iterations,
        "observed_iterations": sum(r["attempted_iterations"] for r in rows),
        "passed_iterations": sum(r["passed_iterations"] for r in rows),
        "failed_iterations": sum(r["failed_iterations"] for r in rows),
        "disposition": "completed_positive" if not problems else "incomplete_or_failed",
        "issues": problems, "suites": rows,
        "release_gate_credit": 0, "physical_hardware_covered": False,
        "actual_guest_gameplay_covered": False,
        "scope": ("Exact original production store fixture, many genuine separate "
                  "process recoveries; not a shipped Windows ZIP, real guest-played "
                  "match, independent original oracle or power-loss proof."),
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="mode", required=True)
    b = subs.add_parser("build")
    b.add_argument("--exe", type=Path, required=True)
    run = subs.add_parser("run")
    run.add_argument("--exe", type=Path, required=True)
    run.add_argument("--source-sha", required=True)
    run.add_argument("--binary-sha", required=True)
    run.add_argument("--suite", choices=SUITES, required=True)
    run.add_argument("--iterations", type=int, required=True)
    run.add_argument("--seed", type=int, required=True)
    run.add_argument("--work", type=Path, required=True)
    run.add_argument("--out", type=Path, required=True)
    a = subs.add_parser("aggregate")
    a.add_argument("--results-dir", type=Path, required=True)
    a.add_argument("--source-sha", required=True)
    a.add_argument("--binary-sha", required=True)
    a.add_argument("--iterations", type=int, required=True)
    a.add_argument("--seed", type=int, required=True)
    a.add_argument("--out", type=Path, required=True)
    a.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    if args.mode == "build":
        build(args.exe)
        return 0
    if args.mode == "run":
        row = run_suite(exe=args.exe.resolve(), source_sha=args.source_sha,
                        binary_sha256=args.binary_sha, suite=args.suite,
                        iterations=args.iterations, seed=args.seed,
                        work=args.work)
        save(args.out, row)
        print(f"{row['suite']}: {row['disposition']} "
              f"{row['passed_iterations']}/{row['requested_iterations']} "
              f"failures={row['failed_iterations']}")
        return 0 if row["disposition"] == "completed_positive" else 1
    report = aggregate(args.results_dir, args.source_sha, args.binary_sha,
                       args.iterations, args.seed)
    save(args.out, report)
    rows = [
        "# QA-02/03 process recovery campaign",
        "",
        f"**{report['disposition']}**: {report['passed_iterations']}/"
        f"{report['requested_iterations']} trials passed; "
        f"{report['observed_iterations']} observed",
        "",
        f"Source: {report['source_sha']}, binary SHA-256: {report['binary_sha256']}",
        "",
        "| Scenario | Passed | Attempted | Outcome |",
        "| --- | ---: | ---: | --- |",
    ]
    for row in report["suites"]:
        rows.append(f"| {row['suite']} | {row['passed_iterations']} | "
                    f"{row['attempted_iterations']} | {row['disposition']} |")
    rows.extend(["", "**No release, Windows hardware or guest-gameplay credit.**", ""])
    rows.extend(f"- {issue}" for issue in report["issues"])
    args.summary.write_text("\n".join(rows) + "\n")
    return 0 if report["disposition"] == "completed_positive" else 1


if __name__ == "__main__":
    raise SystemExit(main())
