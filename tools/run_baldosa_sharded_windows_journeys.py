#!/usr/bin/env python3
"""ROM-free two-runner Win32 acceptance pilot using the existing eleven scripts.

No substitute guest, script, input or test oracle. This is independent
research transport, not QA-12/release acceptance. The default integrated
Windows PR workflow remains the authoritative full acceptance route.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

import bind_baldosa_candidate_receipt as binding
import run_baldosa_parallel_windows_journeys as original

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "UR-Recomp-Baldosa-Windows-x64-ROMLESS.zip"
EXPECTED = {
    "baseline-records": (0, 1, 2),
    "independent": tuple(range(3, 11)),
}
MANIFEST = (
    "UniracersSNESRecomp.exe",
    "ur-baldosa-modern-profile-fixture.exe",
    PREFIX,
)
SCHEMA = "ur-win32-two-runner-fanout-pilot/1"
SHA40 = re.compile(r"[0-9a-f]{40}")
SHA64 = re.compile(r"[0-9a-f]{64}")


def checksum(path: Path) -> str:
    return original.sha256_file(path)


def signed(data: dict) -> dict:
    unsigned = {k: v for k, v in data.items() if k != "receipt_sha256"}
    return {**unsigned, "receipt_sha256": hashlib.sha256(
        json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()}


def inspect_bundle(bundle: Path, source: str, work: Path) -> dict:
    if SHA40.fullmatch(source) is None:
        raise ValueError("source SHA must be exact 40 hex")
    if not bundle.is_dir() or bundle.is_symlink():
        raise ValueError("missing immutable candidate bundle directory")
    marker = bundle / "source-commit.txt"
    if marker.read_text(encoding="ascii").strip() != source:
        raise ValueError("candidate source revision mismatch")
    sums = bundle / "SHA256SUMS"
    rows = sums.read_text(encoding="ascii").splitlines()
    values = {}
    for row in rows:
        match = re.fullmatch(r"([0-9a-f]{64})\s+[*]?([A-Za-z0-9._-]+)", row.strip())
        if match is None or match.group(2) in values:
            raise ValueError("duplicate or malformed pinned SHA256SUMS")
        values[match.group(2)] = match.group(1)
    if set(values) != set(MANIFEST):
        raise ValueError("candidate bundle member mismatch")
    for name, digest in values.items():
        path = bundle / name
        if not path.is_file() or path.is_symlink() or checksum(path) != digest:
            raise ValueError("candidate SHA256 mismatch: " + name)
    # A source-pinned manifest/package identity check reused from shipping QA.
    sha_path = work / (PREFIX + ".sha256")
    sha_path.write_text(values[PREFIX] + "  " + PREFIX + "\n", encoding="ascii")
    candidate = binding.bind(
        bundle / "UniracersSNESRecomp.exe",
        bundle / PREFIX,
        sha_path,
        source,
    )
    if candidate["journey_and_packaged_executable_sha256"] != values[MANIFEST[0]]:
        raise ValueError("ZIP executable differs from the Windows process binary")
    if candidate["zip_sha256"] != values[PREFIX]:
        raise ValueError("ZIP binding differs from immutable candidate")
    return values


def run_case(index: int, scripts: list[str], work: Path, env: dict) -> dict:
    return original.run_one(index, scripts[index], work, env)


def run_shard(shard: str, bundle: Path, source: str,
              work: Path, output: Path, env: dict | None = None) -> dict:
    if shard not in EXPECTED:
        raise ValueError("unknown bounded Windows shard")
    env = dict(os.environ if env is None else env)
    if env.get("GITHUB_SHA") != source or "RUNNER_TEMP" not in env:
        raise ValueError("source or Windows runner environment mismatch")
    if not env.get("GITHUB_STEP_SUMMARY"):
        raise ValueError("missing separate Actions summary root")
    if work.exists():
        raise ValueError("refusing reused private work root")
    work.mkdir(parents=True, exist_ok=False)
    hashes = inspect_bundle(bundle, source, work)
    exe = original.EXE
    fixture = original.FIXTURE
    if (not exe.is_file() or not fixture.is_file()
            or checksum(exe) != hashes[MANIFEST[0]]
            or checksum(fixture) != hashes[MANIFEST[1]]):
        raise ValueError("consumer executable/fixture identity mismatch")
    scripts = original.extract_commands(original.WORKFLOW.read_text(encoding="utf-8"))
    indices = EXPECTED[shard]
    started = time.monotonic()
    records: list[dict] = []
    if shard == "baseline-records":
        baseline = run_case(0, scripts, work, env)
        records.append(baseline)
        seed = (Path(env["RUNNER_TEMP"]) / "UR Baldosa Win32 Pause Route" /
                "baseline" / "Modern Player Data With Spaces" / "saves" / "save.srm")
        if baseline["exit_code"] == 0 and seed.is_file() and not seed.is_symlink() and seed.stat().st_size == 8192:
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                records.extend(pool.map(
                    lambda i: run_case(i, scripts, work, env), (1, 2)
                ))
        else:
            # Never replace missing original SRAM with a synthetic seed.
            records[0] = {**baseline, "exit_code": 1,
                          "error": "failed_original_baseline_or_missing_8192_byte_sram"}
    else:
        # These eight original script bodies have no dependency on baseline
        # SRAM; their one shared root is private to this *separate* runner.
        if any("baseline/" in scripts[i] for i in indices):
            raise ValueError("independent Windows case acquired a baseline dependency")
        parent = Path(env["RUNNER_TEMP"]) / "UR Baldosa Win32 Pause Route"
        parent.mkdir(parents=True, exist_ok=False)
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            records.extend(pool.map(
                lambda i: run_case(i, scripts, work, env), indices
            ))
    records.sort(key=lambda row: row["index"])
    launcher = None
    if shard == "independent" and all(row["exit_code"] == 0 for row in records):
        # Same existing source-authoritative extracted Windows CMD probe, run
        # against the identical built ROMless ZIP and the real USA input.
        cmd = [
            sys.executable, "tools/verify_baldosa_windows_extracted_launcher.py",
            "--zip", str(bundle / PREFIX),
            "--rom", str(ROOT / "reference/roms/retail/Uniracers_USA.sfc"),
            "--out", str(work / "actual-extracted-launcher"),
            "--timeout", "80", "--expected-revision", source,
        ]
        with (work / "actual-extracted-launcher.log").open("w", encoding="utf-8") as fp:
            result = subprocess.run(cmd, cwd=ROOT, env=env, stdout=fp,
                                    stderr=subprocess.STDOUT, timeout=120, check=False)
        launcher = (result.returncode == 0)
    names = {row["index"] for row in records}
    missing = [i for i in indices if i not in names]
    good = not missing and all(row["exit_code"] == 0 for row in records)
    if shard == "independent":
        good = good and launcher is True
    report = signed({
        "schema": SCHEMA, "shard": shard, "source_sha": source,
        "exe_sha256": hashes[MANIFEST[0]],
        "fixture_sha256": hashes[MANIFEST[1]],
        "zip_sha256": hashes[PREFIX],
        "expected_cases": list(indices),
        "observed_cases": [row["index"] for row in records],
        "missing_cases": missing,
        "cases": [
            {"index": row["index"], "name": row["name"],
             "exit_code": row["exit_code"], "elapsed_seconds": row["elapsed_seconds"],
             "error": row["error"]}
            for row in records
        ],
        "launcher_verified": launcher,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "disposition": "produced_not_independently_adjudicated" if good else "incomplete_or_failed",
        "release_gate_credit": 0,
        "physical_hardware_verified": False,
    })
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = Path(env["GITHUB_STEP_SUMMARY"])
    with summary.open("a", encoding="utf-8") as fp:
        fp.write(f"\n### Experimental Windows fanout shard: {shard}\n\n")
        fp.write(f"Source {source}; executable {hashes[MANIFEST[0]]}; "
                 f"{len(records)}/{len(indices)} exact existing cases; "
                 f"elapsed {report['elapsed_seconds']}s; verdict {report['disposition']}. "
                 "Zero release QA credit.\n")
    for row in records:
        log = work / f"step-{row['index']:02d}.log"
        if log.is_file():
            log_text = log.read_text(encoding="utf-8", errors="replace")
            print(f"### Original Windows case {row['index']} "
                  f"{row['name']}: exit {row['exit_code']}", flush=True)
            print(log_text if row["exit_code"] else log_text[-2500:], flush=True)
    return report


def validate_shards(results: Path, source: str) -> dict:
    if not results.is_dir():
        raise ValueError("missing complete two-runner result directory")
    actual = sorted(p.name for p in results.iterdir())
    expected = sorted("fanout-win32-" + shard for shard in EXPECTED)
    if actual != expected:
        raise ValueError("missing/duplicate/unexpected Windows shard artifacts")
    reports = []
    hashes = set()
    indices = []
    for shard in EXPECTED:
        root = results / ("fanout-win32-" + shard)
        files = sorted(p.name for p in root.iterdir())
        if files != ["result.json"] or (root / "result.json").is_symlink():
            raise ValueError("unexpected Windows shard receipt contents")
        row = json.loads((root / "result.json").read_text(encoding="utf-8"))
        if signed(row) != row or row.get("schema") != SCHEMA:
            raise ValueError("invalid source-bound Windows receipt integrity")
        if row.get("shard") != shard or row.get("source_sha") != source:
            raise ValueError("mixed Windows shard source identities")
        if row.get("disposition") != "produced_not_independently_adjudicated" or (
                row.get("release_gate_credit") != 0
                or row.get("physical_hardware_verified") is not False):
            raise ValueError("incomplete shard or forged QA credit")
        if row.get("expected_cases") != list(EXPECTED[shard]) or (
                row.get("observed_cases") != list(EXPECTED[shard])
                or row.get("missing_cases") != []):
            raise ValueError("missing or duplicate original case population")
        cases = row.get("cases") or []
        if ([item.get("index") for item in cases] != list(EXPECTED[shard])
                or any(item.get("name") != original.STEPS[item["index"]]
                       or item.get("exit_code") != 0 for item in cases)):
            raise ValueError("original guest case identity or verdict mismatch")
        if row.get("launcher_verified") is not (shard == "independent") and (
                row.get("launcher_verified") is not None or shard == "independent"):
            raise ValueError("actual extracted CMD launcher not verified")
        sha = tuple(row.get(key) for key in
                    ("exe_sha256", "fixture_sha256", "zip_sha256"))
        if any(not isinstance(h, str) or not SHA64.fullmatch(h) for h in sha):
            raise ValueError("missing source-bound native build hashes")
        hashes.add(sha)
        indices.extend(row["observed_cases"])
        reports.append(row)
    if len(hashes) != 1 or sorted(indices) != list(range(len(original.STEPS))):
        raise ValueError("mixed native build or missing/duplicate Windows case")
    return signed({
        "schema": "ur-win32-two-runner-fanout-aggregate/1",
        "source_sha": source, "shards": list(EXPECTED),
        "executed_cases": len(indices), "expected_cases": len(original.STEPS),
        "exe_sha256": next(iter(hashes))[0], "fixture_sha256": next(iter(hashes))[1],
        "zip_sha256": next(iter(hashes))[2],
        "disposition": "produced_not_independently_adjudicated",
        "release_gate_credit": 0, "physical_hardware_verified": False,
        "shard_elapsed_seconds": {r["shard"]: r["elapsed_seconds"] for r in reports},
    })


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="operation", required=True)
    work = sub.add_parser("run")
    work.add_argument("--shard", choices=tuple(EXPECTED), required=True)
    work.add_argument("--bundle", type=Path, required=True)
    work.add_argument("--source-sha", required=True)
    work.add_argument("--work", type=Path, required=True)
    work.add_argument("--out", type=Path, required=True)
    agg = sub.add_parser("aggregate")
    agg.add_argument("--source-sha", required=True)
    agg.add_argument("--results", type=Path, required=True)
    agg.add_argument("--out", type=Path, required=True)
    agg.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    if args.operation == "run":
        report = run_shard(args.shard, args.bundle, args.source_sha, args.work, args.out)
        return 0 if report["disposition"] == "produced_not_independently_adjudicated" else 1
    result = validate_shards(args.results, args.source_sha)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    with args.summary.open("a", encoding="utf-8") as fp:
        fp.write("\n### Experimental two-runner Windows fanout\n\n"
                 f"All {result['executed_cases']} original scripts executed on "
                 "two source-identical Windows machines; one native producer build. "
                 "No independent release QA or physical hardware credit.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
