#!/usr/bin/env python3
"""Run existing Windows bridge journeys concurrently without rewriting their scripts.

The owning GHA workflow is the sole source of each command. This bounded
pilot preserves all existing scenario outputs, relative evidence paths and
per-step assertions. It is NOT a release gate or an additional game oracle.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/baldosa-windows-native-bridge.yml"
STEPS = (
    "Execute actual Win32 two-player guest and native pause/resume",
    "Real stock 1P result and newly saved Records reopened by fresh native game",
    "Real named P1/P2 ordinary race through paired Records and fresh native process",
    "First controller-semantic native racer creation persists for exact fresh-game boot",
    "Native first-run nondefault Andrew stock rider and clean new-game SRAM",
    "Native named P1 explicitly creates independent P2 then both enter stock 2P",
    "Real pad-created P2 survives explicit interrupted-catalog recovery",
    "Native shared Quick Practice enters original source-qualified Dragster",
    "Native P1 gamepad-created P1 and P2 earn original 2P and both fresh Records",
    "Native first-racer creation through genuine earned 1P Records in three separate games",
    "Native controller selects existing P1 both directions across cold game processes",
)
STEP_RE = re.compile(r"^      - name: (.+)$")
OUT_RE = re.compile(r'--out "\$RUNNER_TEMP/(.*?)"')
EXE = ROOT / "baldosa/build-ur-win/UniracersSNESRecomp.exe"
FIXTURE = ROOT / "baldosa/build-ur-win/ur-baldosa-modern-profile-fixture.exe"


def extract_commands(source: str) -> list[str]:
    """Strictly extract and retain the *existing* YAML shell bodies.

    No newly written replacement guest probes are allowed. Reject missing,
    duplicate, non-bash or templated steps instead of silently reducing scope.
    """
    lines = source.splitlines()
    sections: dict[str, list[str]] = {}
    for index, line in enumerate(lines):
        match = STEP_RE.fullmatch(line)
        if match and match.group(1) in STEPS:
            name = match.group(1)
            if name in sections:
                raise ValueError("duplicate Windows journey step: " + name)
            end = next(
                (k for k in range(index + 1, len(lines))
                 if STEP_RE.fullmatch(lines[k]) or lines[k].startswith("      - uses:")),
                len(lines),
            )
            sections[name] = lines[index + 1:end]

    if set(sections) != set(STEPS):
        raise ValueError("missing existing Windows journey steps: "
                         + ", ".join(sorted(set(STEPS) - set(sections))))
    bodies: list[str] = []
    outputs: list[str] = []
    for name in STEPS:
        section = sections[name]
        if "        run: |" not in section:
            raise ValueError("missing YAML bash body for " + name)
        header = section[:section.index("        run: |")]
        # Preserve the only existing special step environment without
        # allowing future custom env configuration to silently vanish.
        if name == STEPS[0]:
            if header.count('          UR_BALDOSA_PRODUCT_INPUT_DIAGNOSTICS: "1"') != 1:
                raise ValueError("missing original real-input diagnostics env")
            if any(line.strip().startswith("if:") for line in header) is False:
                raise ValueError("missing serial fallback guard")
        elif any(line.strip() == "env:" for line in header):
            raise ValueError("new per-step environment requires review: " + name)
        body_lines = section[section.index("        run: |") + 1:]
        command = []
        for line in body_lines:
            if line.startswith("          "):
                command.append(line[10:])
            elif line.strip():
                break
            else:
                command.append("")
        script = "\n".join(command).rstrip() + "\n"
        if not script.startswith("set -euo pipefail\n") or not script.strip():
            raise ValueError("non-fail-closed original shell script: " + name)
        if "$" + "{{" in script:
            raise ValueError("unexpanded GHA template inside shell body")
        matches = OUT_RE.findall(script)
        if len(matches) != 1:
            raise ValueError("journey must own exactly one source output root: " + name)
        outputs.extend(matches)
        bodies.append(script)
    if len(outputs) != len(set(outputs)):
        raise ValueError("Windows journeys would collide on output roots")
    return bodies


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def find_git_bash(*, windows: bool | None = None,
                  program_files: str | None = None) -> str:
    """Match Actions' Windows Bash shell, not the WSL `bash.exe` PATH shim."""
    if windows is None:
        windows = os.name == "nt"
    if windows:
        prefix = program_files or os.environ.get("PROGRAMFILES") or "C:/Program Files"
        candidate = Path(prefix) / "Git" / "bin" / "bash.exe"
        if not candidate.is_file():
            raise RuntimeError("Windows acceptance requires installed Git Bash: "
                               + str(candidate))
        return str(candidate)
    return "bash"


def run_one(index: int, script: str, work: Path, env: dict[str, str]) -> dict:
    name = STEPS[index]
    output = work / f"step-{index:02d}.log"
    summary = work / f"step-{index:02d}.md"
    invocation_env = dict(env)
    invocation_env["GITHUB_STEP_SUMMARY"] = str(summary)
    if index == 0:
        invocation_env["UR_BALDOSA_PRODUCT_INPUT_DIAGNOSTICS"] = "1"
    started = time.monotonic()
    try:
        with output.open("w", encoding="utf-8", errors="replace") as handle:
            completed = subprocess.run(
                [find_git_bash(), "--noprofile", "--norc", "-e", "-o", "pipefail", "-c", script],
                cwd=ROOT, env=invocation_env, stdout=handle,
                stderr=subprocess.STDOUT, check=False, timeout=900,
            )
        code = completed.returncode
        error = None
    except (OSError, subprocess.TimeoutExpired) as exc:
        code = 124
        error = type(exc).__name__
        with output.open("a", encoding="utf-8") as handle:
            handle.write("\n" + repr(exc) + "\n")
    seconds = round(time.monotonic() - started, 3)
    return {"name": name, "index": index, "exit_code": code,
            "elapsed_seconds": seconds, "error": error,
            "log": output.name, "summary": summary.name}


def run_overlapping_baseline(commands: list[str], work: Path,
                             env: dict[str, str]) -> list[dict]:
    """Overlap independent routes with baseline without racing its shared parent.

    Only two Records cases consume baseline SRAM (indices 1 and 2).
    The owning original pause producer creates the root with exist_ok=False;
    no descendant may start until this directory exists. No original test
    command, seed, byte, private output path or acceptance rule is changed.
    """
    outputs = [OUT_RE.findall(script)[0] for script in commands]
    parent_rel = outputs[0]
    if not all(output.startswith(parent_rel + "/") for output in outputs[1:]):
        raise ValueError("overlap requires a shared baseline output parent")
    if any("baseline/" in commands[index] for index in range(3, len(commands))):
        raise ValueError("independent Windows route gained a baseline seed dependency")
    parent = Path(env["RUNNER_TEMP"]) / parent_rel
    if parent.exists() or parent.is_symlink():
        raise ValueError("baseline output root already exists before live producer")
    expected_seed = (parent / "baseline" / "Modern Player Data With Spaces" /
                     "saves" / "save.srm")
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        baseline = executor.submit(run_one, 0, commands[0], work, env)
        started = time.monotonic()
        # Never let a child implicitly mkdir the shared parent before the
        # baseline's exclusive mkdir. The owner normally creates it at entry.
        while not parent.is_dir() and not baseline.done():
            if time.monotonic() - started > 30:
                raise RuntimeError("baseline did not create its exclusive output root")
            time.sleep(0.05)
        futures: dict[int, concurrent.futures.Future] = {}
        if parent.is_dir() and not parent.is_symlink():
            for index in range(3, len(commands)):
                futures[index] = executor.submit(run_one, index, commands[index], work, env)
        first = baseline.result()
        if first["exit_code"] == 0:
            # The original source producer, not this harness, must create
            # exactly the expected real USA baseline save before either
            # source-backed Records case may consume its bytes.
            if (not expected_seed.is_file() or expected_seed.is_symlink()
                    or expected_seed.stat().st_size != 8192):
                first = {**first, "exit_code": 1,
                         "error": "missing_exact_real_8192_byte_baseline_sram"}
            else:
                for index in (1, 2):
                    futures[index] = executor.submit(run_one, index, commands[index], work, env)
        return [first] + [futures[i].result() for i in sorted(futures)]


def run_all(*, workers: int, work: Path, source: str | None = None,
            env: dict[str, str] | None = None, overlap_baseline: bool = False) -> dict:
    if workers not in (2, 3):
        raise ValueError("only 2/3 bounded Windows pilot workers")
    if overlap_baseline and workers != 3:
        raise ValueError("baseline overlap requires three bounded workers")
    source = source if source is not None else WORKFLOW.read_text(encoding="utf-8")
    commands = extract_commands(source)
    env = dict(env if env is not None else os.environ)
    for required in ("GITHUB_SHA", "GITHUB_STEP_SUMMARY", "RUNNER_TEMP"):
        if not env.get(required):
            raise ValueError("missing exact Actions environment: " + required)
    if not re.fullmatch(r"[0-9a-f]{40}", env["GITHUB_SHA"]):
        raise ValueError("missing pinned 40-hex Actions commit")
    if not EXE.is_file() or not FIXTURE.is_file():
        raise ValueError("cannot run without built genuine Windows guest and fixture")
    exe_hash = sha256_file(EXE)
    fixture_hash = sha256_file(FIXTURE)
    work.mkdir(parents=True, exist_ok=False)
    start = time.monotonic()
    # Baseline writes the canonical SRAM seed consumed by BOTH real 1P and 2P
    # probe scripts. Do not parallelize or synthesize this dependency.
    if overlap_baseline:
        results = run_overlapping_baseline(commands, work, env)
    else:
        results = [run_one(0, commands[0], work, env)]
        if results[0]["exit_code"] == 0:
            with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
                results.extend(executor.map(
                    lambda pair: run_one(pair[0], pair[1], work, env),
                    enumerate(commands[1:], start=1),
                ))
    results.sort(key=lambda result: result["index"])
    summary_path = Path(env["GITHUB_STEP_SUMMARY"])
    with summary_path.open("a", encoding="utf-8") as summary:
        summary.write("\n### Parallel Windows journey pilot\n\n")
        summary.write(f"Source: {env['GITHUB_SHA']}  \n")
        summary.write(f"Workers: {workers} (baseline serialized)  \n")
        summary.write(f"Native EXE SHA256: {exe_hash}  \n")
        summary.write(f"Fixture SHA256: {fixture_hash}\n\n")
        summary.write("| Existing test | Result | Seconds |\n|---|---|---:|\n")
        for row in results:
            summary.write(f"| {row['name']} | "
                          f"{'pass' if row['exit_code'] == 0 else 'FAIL'} | "
                          f"{row['elapsed_seconds']:.1f} |\n")
            step_summary = work / row["summary"]
            if step_summary.exists():
                summary.write("\n" + step_summary.read_text(encoding="utf-8") + "\n")
    for row in results:
        data = (work / row["log"]).read_text(encoding="utf-8", errors="replace")
        print(f"### {row['index'] + 1}/{len(STEPS)} {row['name']}: exit "
              f"{row['exit_code']} in {row['elapsed_seconds']:.1f}s", flush=True)
        # Full failure diagnostics; successful verbose guest frame traces are
        # bounded to avoid opaque multi-megabyte CI logs.
        print(data if row["exit_code"] else data[-3000:], flush=True)
    observed = {row["index"] for row in results}
    missing = [name for index, name in enumerate(STEPS) if index not in observed]
    identity_changed = sha256_file(EXE) != exe_hash or sha256_file(FIXTURE) != fixture_hash
    if identity_changed:
        print("ERROR: native Windows candidate changed during parallel execution",
              file=sys.stderr)
    result = {
        "schema": "ur-baldosa-parallel-windows-journeys/1",
        "source_sha": env["GITHUB_SHA"], "exe_sha256": exe_hash,
        "fixture_sha256": fixture_hash,
        "workers": workers, "overlap_baseline": overlap_baseline,
        "expected_cases": len(STEPS),
        "executed_cases": len(results),
        "missing_cases": missing, "identity_changed": identity_changed,
        "elapsed_seconds": round(time.monotonic() - start, 3),
        "cases": results, "release_gate_credit": 0,
    }
    (work / "pilot-result.json").write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, choices=(2, 3), default=2)
    parser.add_argument("--overlap-baseline", action="store_true")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = run_all(workers=args.workers, work=args.out,
                     overlap_baseline=args.overlap_baseline)
    if (report["executed_cases"] != report["expected_cases"] or
            report["missing_cases"] or report["identity_changed"] or
            any(row["exit_code"] for row in report["cases"])):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
