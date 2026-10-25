#!/usr/bin/env python3
"""Manual two-job fan-out of exact original Windows bridge journeys; no QA credit."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
import re
import time
from pathlib import Path

import run_baldosa_parallel_windows_journeys as bridge

SCHEMA = "ur-win32-acceptance-fanout/2"
GROUPS = {"seed-dependent": (0, 1, 2), "independent": tuple(range(3, 13))}
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def candidate_identity(source_sha, exe, fixture, archive):
    require(bool(HEX40.fullmatch(source_sha)), "invalid source SHA")
    for path in (exe, fixture, archive):
        require(path.is_file() and not path.is_symlink(), "missing candidate input " + str(path))
    return {"source_sha": source_sha, "exe_sha256": bridge.sha256_file(exe),
            "fixture_sha256": bridge.sha256_file(fixture),
            "zip_sha256": bridge.sha256_file(archive)}


def attest_private_case_files(rows, work):
    """Bind private original script outputs without publishing their contents.

    Full guest logs stay on the ephemeral Windows runner. The artifact exposes
    only the SHA-256, size and fixed filename, so a later separately authorized
    read can detect whether the original bytes differ from the producer claim.
    A digest is not a signature and cannot, by itself, independently verify
    that the guest actually executed its claimed journey.
    """
    for row in rows:
        index = row["index"]
        for label, suffix in (("log", ".log"), ("summary", ".md")):
            expected = f"step-{index:02d}{suffix}"
            require(row.get(label) == expected,
                    "original script output name changed")
            path = work / expected
            # The existing original bridge permits an absent optional .md
            # summary; only the subprocess's combined .log is mandatory.
            require(not path.is_symlink(), "redirected original Windows " + label)
            if label == "summary" and not path.exists():
                row["summary_sha256"] = None
                row["summary_bytes"] = 0
                continue
            require(path.is_file(), "missing original Windows " + label)
            data = path.read_bytes()
            row[label + "_sha256"] = hashlib.sha256(data).hexdigest()
            row[label + "_bytes"] = len(data)
    return rows


def validate_receipt(receipt, group, source_sha):
    require(isinstance(receipt, dict) and receipt.get("schema") == SCHEMA, "wrong receipt schema")
    require(group in GROUPS and receipt.get("group") == group, "wrong group")
    who = receipt.get("candidate_identity")
    require(isinstance(who, dict) and set(who) ==
            {"source_sha", "exe_sha256", "fixture_sha256", "zip_sha256"},
            "missing candidate identity")
    require(who["source_sha"] == source_sha and bool(HEX40.fullmatch(source_sha)),
            "source identity changed")
    require(all(isinstance(who[k], str) and bool(HEX64.fullmatch(who[k]))
                for k in ("exe_sha256", "fixture_sha256", "zip_sha256")),
            "invalid binary/ZIP digests")
    stamp = receipt.get("receipt_sha256")
    unsigned = {k: v for k, v in receipt.items() if k != "receipt_sha256"}
    require(isinstance(stamp, str) and bool(HEX64.fullmatch(stamp))
            and digest(unsigned) == stamp, "altered receipt")
    expected = GROUPS[group]
    require(receipt.get("expected_indices") == list(expected), "case inventory changed")
    rows = receipt.get("cases")
    require(isinstance(rows, list) and len(rows) == len(expected),
            "missing / duplicated original cases")
    for idx, row in zip(expected, rows):
        require(isinstance(row, dict) and row.get("index") == idx
                and row.get("name") == bridge.STEPS[idx], "original case identity changed")
        require(type(row.get("exit_code")) is int, "invalid original step exit code")
        require(type(row.get("elapsed_seconds")) in (float, int)
                and row["elapsed_seconds"] >= 0, "invalid measured step time")
        for label, ext in (("log", ".log"), ("summary", ".md")):
            require(row.get(label) == f"step-{idx:02d}{ext}",
                    "changed original private Windows output label")
            value = row.get(label + "_sha256")
            require((value is None and label == "summary" and
                     row.get("summary_bytes") == 0)
                    or (type(value) is str and bool(HEX64.fullmatch(value))),
                    "missing original output SHA256")
            require(type(row.get(label + "_bytes")) is int
                    and 0 <= row[label + "_bytes"] < 50_000_000,
                    "invalid private original output size")
    require(receipt.get("release_gate_credit") == 0
            and receipt.get("independent_physical_qa") is False,
            "producer attempted QA promotion")
    require(receipt.get("all_passed") is
            all(row["exit_code"] == 0 for row in rows), "contradictory success marker")
    return who


def run_group(group, source_sha, archive, work, env=None, workers=2):
    require(group in GROUPS and workers in (1, 2), "invalid group/parallelism")
    env = dict(os.environ if env is None else env)
    require(env.get("GITHUB_SHA") == source_sha, "not the checked-out source")
    require(bool(env.get("RUNNER_TEMP") and env.get("GITHUB_STEP_SUMMARY")),
            "not a pinned Actions run")
    require(not work.exists() and not work.is_symlink(), "work root already used")
    who = candidate_identity(source_sha, bridge.EXE, bridge.FIXTURE, archive)
    commands = bridge.extract_commands(bridge.WORKFLOW.read_text(encoding="utf-8"))
    bridge.independent_priority_indices(len(commands))
    require(len(commands) == 13, "missing original Windows journeys")
    work.mkdir(parents=True)
    started = time.monotonic()
    if group == "seed-dependent":
        first = bridge.run_one(0, commands[0], work, env)
        rows = [first]
        seed = (Path(env["RUNNER_TEMP"]) / "UR Baldosa Win32 Pause Route" /
                "baseline" / "Modern Player Data With Spaces" / "saves" / "save.srm")
        if first["exit_code"] == 0 and seed.is_file() and not seed.is_symlink() and seed.stat().st_size == 8192:
            rows.extend(bridge.run_one(i, commands[i], work, env) for i in (1, 2))
    else:
        for idx in GROUPS[group]:
            require("baseline/" not in commands[idx],
                    "supposedly independent journey depends on SRAM baseline")
        paths = [bridge.OUT_RE.findall(script) for script in commands]
        require(all(len(x) == 1 for x in paths)
                and all(x[0].startswith(paths[0][0] + "/") for x in paths[1:]),
                "original script roots changed")
        parent = Path(env["RUNNER_TEMP"]) / paths[0][0]
        require(not parent.exists() and not parent.is_symlink(), "work parent already used")
        parent.mkdir(parents=True)
        indices = [i for i in bridge.INDEPENDENT_PRIORITY if i in GROUPS[group]]
        with ThreadPoolExecutor(max_workers=workers) as pool:
            rows = list(pool.map(lambda i: bridge.run_one(i, commands[i], work, env), indices))
    require(candidate_identity(source_sha, bridge.EXE, bridge.FIXTURE, archive) == who,
            "candidate changed during original scripts")
    rows.sort(key=lambda row: row["index"])
    attest_private_case_files(rows, work)
    report = {
        "schema": SCHEMA, "group": group, "candidate_identity": who,
        "expected_indices": list(GROUPS[group]), "cases": rows,
        "all_passed": len(rows) == len(GROUPS[group]) and all(row["exit_code"] == 0 for row in rows),
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "release_gate_credit": 0, "independent_physical_qa": False,
    }
    report["receipt_sha256"] = digest(report)
    (work / "result.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    return report


def summarize_case_failures(group, rows):
    """Public, bounded failure identifiers only; never private guest logs."""
    expected = GROUPS[group]
    by_index = {row["index"]: row for row in rows}
    return [
        {"group": group, "index": index, "name": bridge.STEPS[index],
         "reason": "missing_case" if index not in by_index else "nonzero_exit",
         "exit_code": None if index not in by_index else by_index[index]["exit_code"]}
        for index in expected
        if index not in by_index or by_index[index]["exit_code"] != 0
    ]


def aggregate(root, source_sha):
    problems, cases, identities, failures = [], [], [], []
    for group in GROUPS:
        path = root / ("windows-fanout-" + group) / "result.json"
        try:
            require(path.is_file() and not path.is_symlink(), "missing group receipt")
            row = json.loads(path.read_text(encoding="utf-8"))
            identities.append(validate_receipt(row, group, source_sha))
            cases.extend(row["cases"])
            failures.extend(summarize_case_failures(group, row["cases"]))
            if not row["all_passed"]:
                problems.append(group + ": " + str(len(summarize_case_failures(group, row["cases"]))) +
                                " failed/missing original Windows journeys")
        except (OSError, ValueError, TypeError, KeyError) as error:
            problems.append(group + ": " + str(error))
    if len(identities) == 2 and identities[0] != identities[1]:
        problems.append("different source/EXE/fixture/ZIP identities across groups")
    indices = [row["index"] for row in cases]
    if sorted(indices) != list(range(13)):
        problems.append("original thirteen-journey inventory incomplete or duplicated")
    return {
        "schema": "ur-win32-acceptance-fanout-aggregate/2",
        "source_sha": source_sha, "candidate_identity": identities[0] if identities else None,
        "cases": sorted(({"index": row["index"], "exit_code": row["exit_code"],
                          "elapsed_seconds": row["elapsed_seconds"],
                          "log_sha256": row["log_sha256"],
                          "log_bytes": row["log_bytes"],
                          "summary_sha256": row["summary_sha256"],
                          "summary_bytes": row["summary_bytes"]} for row in cases),
                        key=lambda x: x["index"]),
        "observed_cases": len(indices), "expected_cases": 13,
        "failed_cases": sorted(failures, key=lambda x: x["index"]),
        "transport_complete": not problems, "issues": problems,
        "release_gate_credit": 0, "independent_physical_qa": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="mode", required=True)
    run = commands.add_parser("run")
    run.add_argument("--group", choices=tuple(GROUPS), required=True)
    run.add_argument("--source-sha", required=True)
    run.add_argument("--archive", type=Path, required=True)
    run.add_argument("--work", type=Path, required=True)
    agg = commands.add_parser("aggregate")
    agg.add_argument("--source-sha", required=True)
    agg.add_argument("--results", type=Path, required=True)
    agg.add_argument("--out", type=Path, required=True)
    agg.add_argument("--summary", type=Path)
    args = parser.parse_args()
    if args.mode == "run":
        result = run_group(args.group, args.source_sha, args.archive, args.work)
        print("original Windows journeys:", len(result["cases"]), "passed:", result["all_passed"])
        return 0 if result["all_passed"] else 1
    result = aggregate(args.results, args.source_sha)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    if args.summary:
        with args.summary.open("a", encoding="utf-8") as output:
            output.write("\n### Windows fan-out pilot\n\n")
            output.write("Original journeys: %s/13\n\n" % result["observed_cases"])
            output.write("Transport complete: %s. Release credit: 0.\n" % result["transport_complete"])
            for problem in result["issues"]:
                output.write("\n- " + problem)
            if result["failed_cases"]:
                output.write("\n\nFailed source journeys (index, step, exit):\n")
                for row in result["failed_cases"]:
                    output.write("\n- %02d %s: %s (%s)" %
                                 (row["index"], row["name"], row["reason"],
                                  row["exit_code"]))
    return 0 if result["transport_complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
