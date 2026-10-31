#!/usr/bin/env python3
"""Seeded two-controller native gameplay endurance from the original 2P fixture.

Real compiled SNESRecomp guest; full-WRAM checkpoints; four fresh executions
per seed: treatment, repeat, P1-input ablation, P2-input ablation.
This is a deterministic input/durability oracle, NOT original/native parity,
full-course completion, physical pads, or a Baldosa Windows release witness.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from controller_input import load_controller_runs  # existing authoritative parser

SHA1 = re.compile(r"[a-f0-9]{40}\Z")
SHA256 = re.compile(r"[a-f0-9]{64}\Z")
SCHEMA = "ur-native-2p-input-endurance/1"
ROM_SHA = "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
SHARDS = (0, 1)
BUDGETS = (15, 60, 120)
FRAMES = tuple(range(1740, 3421, 120))
CONTROL_FILE = ROOT / "tests/input/two-player-first-race.input"
OBSERVATION_FILE = ROOT / "tests/input/two-player-first-race-observe.script"
BASE_CHECK = "two-player-both-post-1620"
FIRST_PROBE = "endurance-1740"
MASKS = (0x080, 0x040, 0x100, 0x180, 0x140, 0x080, 0x040)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def hash_object(value: dict) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def save(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def base_source() -> tuple[str, str]:
    raw_input = CONTROL_FILE.read_text(encoding="utf-8")
    raw_script = OBSERVATION_FILE.read_text(encoding="utf-8")
    # Review an observed source-owned fixed route, not a replacement 2P setup.
    controls = load_controller_runs(CONTROL_FILE)
    if not controls or max(c.end for c in controls) > 1630:
        raise ValueError("original 2P controller fixture changed its entry boundary")
    if "dump " + BASE_CHECK not in raw_script or not raw_script.rstrip().endswith("quit"):
        raise ValueError("source-owned 2P observation route changed")
    if any(line.strip().startswith(("press ", "reset", "until "))
           for line in raw_script.splitlines()):
        raise ValueError("expected stock 2P wait/dump-only observation script")
    return raw_input, raw_script


def input_plan(seed: int) -> tuple[list[tuple[int, int, int, int]], dict]:
    """Vary both player streams AFTER unchanged 2P game/menu setup."""
    rng = random.Random(seed)
    actions = [(1650, 60, 0x080, 0x040)]  # undeniable 2-seat stimulus
    distributions = {"p1_intervals": 1, "p2_intervals": 1, "p1_frames": 60, "p2_frames": 60}
    for start in range(1750, 3400, 42):
        p1 = rng.choice((0, *MASKS))
        p2 = rng.choice((0, *MASKS))
        duration = rng.randint(5, 35)
        # No overlap for either player's intervals; at least 7 idle frames.
        if not (p1 or p2):
            continue
        actions.append((start, duration, p1, p2))
        if p1:
            distributions["p1_intervals"] += 1
            distributions["p1_frames"] += duration
        if p2:
            distributions["p2_intervals"] += 1
            distributions["p2_frames"] += duration
    return actions, distributions


def render_input(prefix: str, actions: list[tuple[int, int, int, int]],
                 muted: str | None) -> str:
    if muted not in (None, "p1", "p2"):
        raise ValueError("unknown ablation")
    lines = [prefix.rstrip(), f"# seeded native 2P endurance / ablated={muted or 'none'}"]
    for start, duration, p1, p2 in actions:
        if muted == "p1":
            p1 = 0
        elif muted == "p2":
            p2 = 0
        if p1 or p2:
            lines.append(f"{start}:{duration}:{p1:03x}:{p2:03x}")
    return "\n".join(lines) + "\n"


def render_script(prefix: str) -> str:
    lines = prefix.splitlines()
    if lines[-1].strip() != "quit":
        raise ValueError("original two-player script must finish with quit")
    lines.pop()
    previous = 1620
    for frame in FRAMES:
        if frame <= previous:
            raise ValueError("nonmonotone canonical checkpoint sequence")
        lines.extend((f"wait {frame - previous}", f"dump endurance-{frame}"))
        previous = frame
    lines.append("quit")
    return "\n".join(lines) + "\n"


def identity(exe: Path, rom: Path, source_sha: str) -> dict:
    if not SHA1.fullmatch(source_sha):
        raise ValueError("missing exact 40-hex source revision")
    for path in (exe, rom):
        if not path.is_file() or path.is_symlink():
            raise ValueError("missing or symlinked exact candidate/ROM")
    if sha256(rom) != ROM_SHA:
        raise ValueError("unverified stock USA retail ROM")
    raw_input, raw_script = base_source()
    return {
        "source_commit": source_sha,
        "native_executable_sha256": sha256(exe),
        "rom_sha256": ROM_SHA,
        "stock_input_sha256": hashlib.sha256(raw_input.encode()).hexdigest(),
        "stock_script_sha256": hashlib.sha256(raw_script.encode()).hexdigest(),
    }


def observe(dumps: Path) -> dict[str, str]:
    names = (BASE_CHECK, *(f"endurance-{frame}" for frame in FRAMES))
    observed = {}
    for name in names:
        dump = dumps / (name + ".wram.bin")
        if not dump.is_file() or dump.is_symlink() or dump.stat().st_size != 131072:
            raise ValueError(f"missing/incomplete real 128-KiB WRAM checkpoint: {name}")
        observed[name] = sha256(dump)
    # 7E:0313 is source-observed racing state; prevent menu-only no-op trials.
    wram = (dumps / (BASE_CHECK + ".wram.bin")).read_bytes()
    if wram[0x0313] != 1:
        raise ValueError("source-owned 2P entry never reached active racing")
    return observed


def guest_command(exe: Path, rom: Path, config: Path, script: Path,
                  *, windows: bool) -> list[str]:
    args = [str(exe), str(rom), "--config", str(config), "--script", str(script)]
    return args if windows else ["xvfb-run", "-a", *args]


def execute(exe: Path, rom: Path, control: Path, script: Path,
            root: Path, timeout: int, *, runtime_log: Path | None = None,
            observe_result: bool = True) -> dict[str, str]:
    if root.exists():
        raise ValueError("refuse an existing/previously mutated process root")
    (root / "dumps").mkdir(parents=True)
    (root / "user-data").mkdir()  # real host refuses an absent explicit writable root
    config = root / "fast-real-guest.ini"
    # Stock native emulator frame pacing need not idle an endurance worker.
    # Direct local A/B smoke proved identical 128-KiB WRAM under this setting.
    config.write_text(
        "[General]\nDisableFrameDelay = 1\nSkipLauncher = 1\nAutosave = 0\n"
        "[Sound]\nEnableAudio = 0\n", encoding="ascii")
    env = dict(os.environ)
    env.update({
        "SDL_AUDIODRIVER": "dummy",
        "UR_EXECUTION_MODE": "authentic",
        "UR_RECOMP_USER_DATA_ROOT": str(root / "user-data"),
        "SNESRECOMP_USER_DATA_DIR": str(root / "user-data"),
        "SNESRECOMP_INPUT_FILE": str(control),
        "SNESRECOMP_DUMP_DIR": str(root / "dumps"),
    })
    # Reuse the exact native fixture and guest oracle on both OS families.
    # The HP uses its verified static SDL3 Windows offscreen driver; Linux
    # retains the long-standing xvfb-run path and unchanged guest behavior.
    windows = os.name == "nt"
    if windows:
        env["SDL_VIDEODRIVER"] = "offscreen"
    cmd = guest_command(exe, rom, config, script, windows=windows)
    try:
        done = subprocess.run(cmd, cwd=root, env=env, capture_output=True,
                              text=True, errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"real guest process timeout ({timeout}s)") from exc
    # Optional source/oracle diagnostic. The original shared endurance
    # producer's return value and behaviour remain unchanged when omitted.
    # Persist the raw script f=N completion receipts even on guest failure.
    if runtime_log is not None:
        if runtime_log.exists() or runtime_log.is_symlink():
            raise ValueError("refuse to overwrite prior native runtime transcript")
        runtime_log.write_text(done.stdout + "\n" + done.stderr, encoding="utf-8")
    if done.returncode != 0:
        raise RuntimeError(f"guest exited {done.returncode}; "
                           f"stdout/stderr tail={(done.stdout + done.stderr)[-900:]}")
    # Callers with their own dump schedule verify their own checkpoints.
    return observe(root / "dumps") if observe_result else {}


def trial(exe: Path, rom: Path, source_input: str, generated_script: str,
          root: Path, seed: int, timeout: int) -> dict:
    if root.exists():
        raise ValueError("trial root exists")
    root.mkdir(parents=True)
    actions, diversity = input_plan(seed)
    script = root / "route.script"
    script.write_text(generated_script, encoding="utf-8")
    input_files = {}
    inputs = {}
    for variant, muted in (("treatment", None), ("repeat", None),
                           ("mute-p1", "p1"), ("mute-p2", "p2")):
        path = root / (variant + ".input")
        path.write_text(render_input(source_input, actions, muted), encoding="utf-8")
        # Only the maintained production grammar defines legal rows/masks.
        load_controller_runs(path)
        input_files[variant] = path
        inputs[variant] = sha256(path)
    if inputs["treatment"] != inputs["repeat"]:
        raise ValueError("same-seed treatment changed between replicas")
    if len(set((inputs["treatment"], inputs["mute-p1"], inputs["mute-p2"]))) != 3:
        raise ValueError("counterfactuals did not alter independent seats")
    results = {}
    for variant in ("treatment", "repeat", "mute-p1", "mute-p2"):
        results[variant] = execute(exe, rom, input_files[variant], script,
                                   root / variant, timeout)
    a = results["treatment"]
    if a != results["repeat"]:
        first = next((name for name in a if a[name] != results["repeat"].get(name)), "?")
        raise ValueError(f"identical real 2P inputs produced different WRAM: {first}")
    for variant in ("mute-p1", "mute-p2"):
        b = results[variant]
        if b[BASE_CHECK] != a[BASE_CHECK]:
            raise ValueError(f"{variant}: pre-intervention source trace changed")
        if b[FIRST_PROBE] == a[FIRST_PROBE]:
            raise ValueError(f"{variant}: no guest-WRAM response to removed controller")
    return {
        "seed": seed, "input_sha256": inputs["treatment"],
        "script_sha256": sha256(script),
        "checkpoints_per_execution": len(a),
        "real_native_processes": 4,
        "two_seats_observably_active": True,
        "bit_exact_replay": True,
        "source_wram_hash_after_probe": a[FIRST_PROBE],
        **diversity,
    }


def run_shard(*, exe: Path, rom: Path, source_sha: str,
              shard: int, base_seed: int, minutes: int, max_cases: int,
              timeout: int, work: Path, wall_seconds: int | None = None) -> dict:
    if shard not in SHARDS or minutes not in BUDGETS or not 10 <= max_cases <= 5000:
        raise ValueError("unsafe cohort bounds")
    if type(base_seed) is not int or not 0 <= base_seed <= 100000000:
        raise ValueError("unsafe seed")
    if not 10 <= timeout <= 180:
        raise ValueError("unsafe individual native process deadline")
    if wall_seconds is not None and not 120 <= wall_seconds <= minutes * 60:
        raise ValueError("unsafe shortened unattended research budget")
    if work.exists():
        raise ValueError("refuse reused trial root")
    proof = identity(exe, rom, source_sha)
    prefix, script = base_source()
    generated_script = render_script(script)
    work.mkdir(parents=True)
    deadline = time.monotonic() + (wall_seconds if wall_seconds is not None else minutes * 60)
    start = time.monotonic()
    successes, failures = [], []
    seen_inputs = set()
    attempted = 0
    while attempted < max_cases and (attempted == 0 or time.monotonic() < deadline):
        remaining = deadline - time.monotonic()
        if wall_seconds is not None and attempted > 0 and remaining < 60:
            break
        # Only a shortened unattended budget changes timeout allocation.
        # A case runs four actual guests, so bound each one by the
        # remaining research horizon / 4. Linux's historical caller keeps
        # its identical fixed timeout and exact original fixture semantics.
        case_timeout = (timeout if wall_seconds is None else
                        max(10, min(timeout, int(max(0, remaining) / 4))))
        trial_index = attempted
        seed = base_seed + shard * 1000003 + trial_index
        path = work / f"trial-{trial_index:04d}"
        attempted += 1
        try:
            row = trial(exe, rom, prefix, generated_script, path, seed, case_timeout)
            if row["input_sha256"] in seen_inputs:
                raise ValueError("campaign created duplicate input stream")
            seen_inputs.add(row["input_sha256"])
            successes.append(row)
            shutil.rmtree(path)
        except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as exc:
            failures.append({"trial_index": trial_index, "seed": seed,
                             "kind": type(exc).__name__, "error": str(exc)[-700:]})
            if len(failures) >= 2:
                break
    elapsed = round(time.monotonic() - start, 3)
    stop = ("invariant_failure" if failures else
            "case_cap" if attempted == max_cases else "wall_budget")
    record = {
        "schema": SCHEMA, "identity": proof, "shard": shard,
        "base_seed": base_seed, "minutes_budget": minutes,
        "max_unique_cases": max_cases, "attempted_cases": attempted,
        "passed_cases": len(successes), "failed_cases": len(failures),
        "case_results": successes, "failures": failures,
        "total_real_native_processes": len(successes)*4,
        "elapsed_seconds": elapsed, "stop_reason": stop,
        "disposition": "completed_positive" if not failures and successes else "invariant_violation",
        "release_gate_credit": 0, "original_native_fidelity_accepted": False,
        "complete_two_player_result_accepted": False, "physical_gamepads_tested": False,
        "scope": ("One first-course ordinary native 2P input mutation and per-frame "
                  "guest WRAM determinism/control ablation. Not original/native "
                  "parity, a real pad, finished course or Windows shipping build."),
    }
    if wall_seconds is not None:
        record["wall_seconds_budget"] = wall_seconds
    record["receipt_sha256"] = hash_object(record)
    return record


def aggregate(results: Path, source_sha: str, minutes: int,
              max_cases: int, base_seed: int) -> dict:
    if not SHA1.fullmatch(source_sha) or minutes not in BUDGETS or not 10 <= max_cases <= 5000:
        raise ValueError("invalid target identity/bounds")
    valid, issues = [], []
    for shard in SHARDS:
        path = results / f"native-2p-endurance-{shard}" / "result.json"
        if not path.is_file():
            issues.append(f"shard {shard}: missing original result")
            continue
        try:
            row = json.loads(path.read_text(encoding="utf-8"))
            claimed = row.pop("receipt_sha256")
            if not isinstance(claimed, str) or not SHA256.fullmatch(claimed) or hash_object(row) != claimed:
                raise ValueError("tampered result receipt")
            fixed = {
                "schema": SCHEMA, "shard": shard, "base_seed": base_seed,
                "minutes_budget": minutes, "max_unique_cases": max_cases,
                "release_gate_credit": 0, "original_native_fidelity_accepted": False,
                "complete_two_player_result_accepted": False,
                "physical_gamepads_tested": False,
                "disposition": "completed_positive",
            }
            if any(type(row.get(k)) is not type(v) or row[k] != v for k,v in fixed.items()):
                raise ValueError("incorrect target or missing/false admission")
            identity_data = row["identity"]
            expected_identity = {"source_commit", "native_executable_sha256",
                                 "rom_sha256", "stock_input_sha256", "stock_script_sha256"}
            if (type(identity_data) is not dict or set(identity_data) != expected_identity
                    or identity_data["source_commit"] != source_sha
                    or identity_data["rom_sha256"] != ROM_SHA
                    or any(not SHA256.fullmatch(v) for k,v in identity_data.items()
                           if k != "source_commit")):
                raise ValueError("source/binary/ROM/controller fixture identity invalid")
            n = row["attempted_cases"]
            succeeded = row["passed_cases"]
            failed = row["failed_cases"]
            cases = row["case_results"]
            if (any(type(x) is not int for x in (n,succeeded,failed))
                    or not 1 <= n <= max_cases
                    or succeeded != n or failed != 0
                    or len(cases) != succeeded
                    or row["total_real_native_processes"] != 4*succeeded
                    or row["stop_reason"] not in ("wall_budget", "case_cap")
                    or row["elapsed_seconds"] < 0):
                raise ValueError("incomplete or implausible case population")
            if (len({v["seed"] for v in cases}) != succeeded or
                    len({v["input_sha256"] for v in cases}) != succeeded):
                raise ValueError("duplicate case seed/input not independent")
            if any(v["seed"] != base_seed + shard*1000003 + i or
                   v["real_native_processes"] != 4 or
                   v["bit_exact_replay"] is not True or
                   v["two_seats_observably_active"] is not True
                   for i,v in enumerate(cases)):
                raise ValueError("case stream is truncated or its stated property was false")
            row["receipt_sha256"] = claimed
            valid.append(row)
        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            issues.append(f"shard {shard}: {exc}")
    if len(valid) == 2 and valid[0]["identity"] != valid[1]["identity"]:
        issues.append("native executable/ROM/fixture differs between shards")
    if results.is_dir():
        extra = sorted(p.name for p in results.iterdir()
                       if p.name not in {f"native-2p-endurance-{s}" for s in SHARDS})
        if extra:
            issues.append(f"unexpected shard artifacts: {extra[:5]}")
    return {
        "schema": SCHEMA, "source_commit": source_sha,
        "requested_wall_minutes_per_shard": minutes,
        "requested_shards": len(SHARDS), "observed_shards": len(valid),
        "total_unique_cases": sum(v["passed_cases"] for v in valid),
        "total_real_native_processes": sum(v["total_real_native_processes"] for v in valid),
        "elapsed_seconds_by_shard": {str(v["shard"]): v["elapsed_seconds"] for v in valid},
        "shard_stop_reasons": {str(v["shard"]): v["stop_reason"] for v in valid},
        "issues": issues, "disposition": "completed_positive" if not issues else "incomplete_or_failed",
        "release_gate_credit": 0, "original_native_fidelity_accepted": False,
        "complete_two_player_result_accepted": False, "physical_gamepads_tested": False,
        "shards": valid,
    }


def summary(report: dict) -> str:
    lines = ["## Native 2P seeded endurance", "",
             f"**{report['disposition']}** | {report['total_unique_cases']} distinct "
             f"two-seat input streams | {report['total_real_native_processes']} real guest processes",
             f"Requested runtime: {report['requested_wall_minutes_per_shard']} minutes per shard. "
             "Actual wall time is reported below; the workload never sleeps to fill its budget.",
             "", "| Shard | Distinct streams | Native processes | Actual wall seconds | Stop |",
             "| --- | ---: | ---: | ---: | --- |"]
    for row in report["shards"]:
        lines.append(f"| {row['shard']} | {row['passed_cases']} | "
                     f"{row['total_real_native_processes']} | {row['elapsed_seconds']} | "
                     f"{row['stop_reason']} |")
    lines.extend(["", "**No original/native parity, completed-event, Windows product, "
                  "physical gamepad or release gate credit.**", ""])
    lines.extend(f"- {issue}" for issue in report["issues"])
    return "\n".join(lines) + "\n"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    modes = p.add_subparsers(dest="mode", required=True)
    run = modes.add_parser("run")
    for name in ("exe", "rom", "work", "out"):
        run.add_argument("--" + name.replace("_", "-"), type=Path, required=True)
    for name in ("source_sha","shard","base_seed","minutes","max_cases","timeout"):
        run.add_argument("--" + name.replace("_", "-"), required=True,
                         type=str if name=="source_sha" else int)
    run.add_argument("--wall-seconds", type=int, default=None,
                     help="Shorten scheduled runs within their nominal budget")
    agg = modes.add_parser("aggregate")
    for name in ("results","out","summary"):
        agg.add_argument("--"+name, type=Path, required=True)
    for name in ("source_sha","minutes","max_cases","base_seed"):
        agg.add_argument("--"+name.replace("_","-"), required=True,
                         type=str if name=="source_sha" else int)
    args = p.parse_args()
    if args.mode == "run":
        row = run_shard(
            exe=args.exe.resolve(), rom=args.rom.resolve(), source_sha=args.source_sha,
            shard=args.shard, base_seed=args.base_seed, minutes=args.minutes,
            max_cases=args.max_cases, timeout=args.timeout, work=args.work,
            wall_seconds=args.wall_seconds)
        save(args.out, row)
        print(f"shard={row['shard']} {row['disposition']} {row['passed_cases']} "
              f"unique input plans / {row['total_real_native_processes']} native processes")
        return 0 if row["disposition"] == "completed_positive" else 1
    report = aggregate(args.results, args.source_sha, args.minutes,
                       args.max_cases, args.base_seed)
    save(args.out, report)
    args.summary.write_text(summary(report), encoding="utf-8")
    return 0 if report["disposition"] == "completed_positive" else 1


if __name__ == "__main__":
    raise SystemExit(main())
