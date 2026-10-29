#!/usr/bin/env python3
"""Compare an actual UR native C++ test and Windows unit tests on two runners.

Diagnostic only; this does not grant a release, parity, or physical QA gate.
Emits no machine names, usernames, Wi-Fi IDs, IP addresses, or credentials.
"""
import argparse
import datetime
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
MODULES = (
    "tests.unit.test_check_windows_pe_timestamp",
    "tests.unit.test_windows_portable_binary",
    "tests.unit.test_assemble_baldosa_windows_candidate",
)

def probe(name, command, timeout):
    started = time.monotonic()
    try:
        completed = subprocess.run(
            command, cwd=ROOT, capture_output=True, text=True,
            errors="replace", timeout=timeout, check=False)
        return {
            "name": name, "seconds": round(time.monotonic() - started, 3),
            "status": "passed" if completed.returncode == 0 else "failed",
            "exitCode": completed.returncode,
            "outputTail": "\n".join(
                (completed.stdout + "\n" + completed.stderr).splitlines()[-12:]
            )[:2400]
        }
    except Exception as exc:
        return {
            "name": name, "seconds": round(time.monotonic() - started, 3),
            "status": "harness_error", "error": str(exc)[:400]
        }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", choices=("hp", "hosted"), required=True)
    args = parser.parse_args()
    if platform.system() != "Windows":
        parser.error("This benchmark requires Windows.")
    temp = Path(os.environ.get("RUNNER_TEMP", os.environ.get("TEMP", ".")))
    report_dir = temp / "ur-devnode-benchmark"
    report_dir.mkdir(parents=True, exist_ok=True)
    build = (Path("C:/DevNode/build-cache/ur-tour-benchmark")
             if args.target == "hp" else temp / "ur-tour-benchmark")
    source = ROOT / "tools" / "devnode_benchmark"
    report = {
        "schema": "ur-devnode-windows-benchmark-v1",
        "sourceSha": os.environ.get("GITHUB_SHA", ""),
        "runId": os.environ.get("GITHUB_RUN_ID", ""),
        "attempt": os.environ.get("GITHUB_RUN_ATTEMPT", ""),
        "timestampUtc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "target": args.target,
        "platform": platform.system(),
        "logicalProcessors": os.cpu_count(),
        "python": platform.python_version(),
        "cacheScope": "persistent" if args.target == "hp" else "ephemeral",
        "qaCredit": "none_diagnostic_only",
        "measurements": []
    }
    tests = [
        ("windows-unit-tests", [sys.executable, "-m", "unittest", "-q", *MODULES], 420),
        ("cmake-configure", ["cmake", "-S", str(source), "-B", str(build),
                              "-G", "Visual Studio 17 2022", "-A", "x64"], 240),
        ("native-cpp-build", ["cmake", "--build", str(build), "--config",
                               "Debug", "--parallel", "4"], 600),
        ("native-cpp-noop-rebuild", ["cmake", "--build", str(build), "--config",
                                      "Debug", "--parallel", "4"], 180),
    ]
    configured = False
    for name, command, timeout in tests:
        if name.startswith("native") and not configured:
            report["measurements"].append({
                "name": name, "status": "skipped", "reason": "configure did not pass"
            })
            continue
        measurement = probe(name, command, timeout)
        report["measurements"].append(measurement)
        print("{}: {} ({:.3f}s)".format(
            name, measurement["status"], measurement["seconds"]), flush=True)
        if measurement["status"] != "passed":
            print(measurement.get("outputTail", measurement.get("error", "")), flush=True)
        if name == "cmake-configure":
            configured = measurement["status"] == "passed"
        if name == "native-cpp-build" and measurement["status"] != "passed":
            configured = False

    if configured:
        exe = build / "Debug" / "ur_devnode_tour_test.exe"
        measurement = probe("native-cpp-regression", [str(exe)], 120)
        report["measurements"].append(measurement)
        print("{}: {} ({:.3f}s)".format(
            measurement["name"], measurement["status"], measurement["seconds"]), flush=True)
    report["status"] = ("passed" if len(report["measurements"]) == 5
                        and all(x["status"] == "passed" for x in report["measurements"])
                        else "failed")
    (report_dir / "report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        rows = [
            "### Windows benchmark: " + args.target,
            "Source: " + report["sourceSha"] + ". Result: **" +
            report["status"] + "**. No release or original/native QA credit.",
            "", "| Test | Status | Seconds |", "|:--|:--|--:|"
        ]
        for item in report["measurements"]:
            rows.append("| {} | {} | {} |".format(
                item["name"], item["status"], item.get("seconds", "n/a")))
        with open(summary, "a", encoding="utf-8") as stream:
            stream.write("\n".join(rows) + "\n")
    return 0 if report["status"] == "passed" else 1

if __name__ == "__main__":
    sys.exit(main())
