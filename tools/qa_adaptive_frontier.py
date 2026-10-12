#!/usr/bin/env python3
"""QA research frontier: bounded, coverage-directed actual native 2P experiments.

One unchanged source-qualified historical 2P entry; the established guest runner
executes real compiled native code. Test-plan arms alter *only* legal post-entry
P1/P2 input masks. Coverage is advisory state-space novelty, NOT original-game
fidelity, event completion, graphics correctness or release acceptance.

Run: independent shards against one shared native candidate, with exact-count
aggregate and actionable retained minimal counterexample on first failure.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import re
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import qa02_native_2p_seeded_endurance as guest
from controller_input import load_controller_runs
from summarize_paired_player_slots import state

SCHEMA = "ur-research-frontier-2p/1"
PLAN_SCHEMA = "ur-research-frontier-plan/1"
ARMS = ("balanced", "p1-focus", "p2-focus", "alternating", "rotation")
FRAME_NAMES = ("endurance-1740", "endurance-2580", "endurance-3420")
COUNT_TO_SHARDS = {100: 4, 1000: 10, 10000: 40}
SOURCE = "existing original-fixture-qualified native 2P first-race route"
HEX40 = re.compile(r"^[a-f0-9]{40}$")
HEX64 = re.compile(r"^[a-f0-9]{64}$")
MAX_SEED = 99999999
MAX_CASES_PER_SHARD = 250
REPRO_ATTEMPTS = 12


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":")).encode("ascii")).hexdigest()


def save(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf8")


def read(path: Path) -> dict:
    result = json.loads(path.read_text(encoding="utf8"))
    if not isinstance(result, dict):
        raise ValueError("JSON object required")
    return result


def plan(source_sha: str, base_seed: int, count: int) -> dict:
    if (not HEX40.fullmatch(source_sha) or type(base_seed) is not int or
            not 0 <= base_seed <= MAX_SEED-1000003-count or
            count not in COUNT_TO_SHARDS):
        raise ValueError("invalid exact source, bounded population or distinct seed base")
    shards = COUNT_TO_SHARDS[count]
    per = count // shards
    if per > MAX_CASES_PER_SHARD:
        raise ValueError("unbounded shard workload")
    body = {
        "schema": PLAN_SCHEMA, "source_sha": source_sha,
        "base_seed": base_seed, "requested_cases": count, "shards": shards,
        "max_parallel": 4,
        "matrix": {"include": [{"shard": n, "first_index": n*per,
                                 "count": per} for n in range(shards)]},
        "fixture": SOURCE, "oracle": "compiled-native-2p-wram-observer",
        "disposition": "planned_not_executed", "release_gate_credit": 0,
        "original_native_parity": False, "complete_event_verified": False,
        "graphics_source_truth": False,
    }
    body["plan_sha256"] = digest(body)
    return body


def validate_plan(data: dict) -> None:
    if type(data) is not dict or data.get("schema") != PLAN_SCHEMA:
        raise ValueError("missing research plan")
    expected = plan(data.get("source_sha", ""),
                    data.get("base_seed"), data.get("requested_cases"))
    if data != expected:
        raise ValueError("altered or noncanonical frontier case allocation")


def assigned(plan_data: dict, shard: int) -> tuple[int, int]:
    validate_plan(plan_data)
    if type(shard) is not int or not 0 <= shard < plan_data["shards"]:
        raise ValueError("invalid allocated worker shard")
    item = plan_data["matrix"]["include"][shard]
    if item["shard"] != shard:
        raise ValueError("noncanonical matrix")
    return item["first_index"], item["count"]


def seed_for(plan_data: dict, shard: int, local_index: int) -> int:
    first, count = assigned(plan_data, shard)
    if type(local_index) is not int or not 0 <= local_index < count:
        raise ValueError("noncanonical case index")
    # Exact global identity independent of worker counts or execution order.
    return plan_data["base_seed"] + first + local_index


def select_arm(attempts: dict[str, int], gains: dict[str, int]) -> str:
    """Deterministic five-way local UCB, favouring observed new semantic bins.

    The policy chooses discovery, not an assertion of correctness or importance.
    """
    if set(attempts) != set(ARMS) or set(gains) != set(ARMS):
        raise ValueError("unknown coverage strategy")
    for arm in ARMS:
        if not attempts[arm]:
            return arm
    total = sum(attempts.values())
    return max(ARMS, key=lambda arm: (
        (gains[arm]+1)/(attempts[arm]+2) +
        0.5*math.sqrt(math.log(total+1)/attempts[arm]),
        -ARMS.index(arm),
    ))


def actions_for(seed: int, arm: str) -> tuple[list[tuple[int, int, int, int]], dict]:
    if arm not in ARMS:
        raise ValueError("unregistered research input strategy")
    actions, _ = guest.input_plan(seed)
    rng = random.Random(seed ^ 0xBEE5)
    amended = [actions[0]]  # preserve the proven real both-seat intervention
    for index, (frame, length, p1, p2) in enumerate(actions[1:]):
        if arm == "p1-focus" and index % 4 != 0:
            p2 = 0
        elif arm == "p2-focus" and index % 4 != 0:
            p1 = 0
        elif arm == "alternating":
            p1, p2 = (p1 or 0x080, 0) if index % 2 == 0 else (0, p2 or 0x040)
        elif arm == "rotation":
            p1 = rng.choice((0, 0x100, 0x140, 0x180))
            p2 = rng.choice((0, 0x100, 0x140, 0x180))
        if p1 or p2:
            amended.append((frame, length, p1, p2))
    if len(amended) < 8:
        raise ValueError("research mutation destroyed observed two-seat route")
    info = {"intervals": len(amended),
            "p1_intervals": sum(bool(a[2]) for a in amended),
            "p2_intervals": sum(bool(a[3]) for a in amended)}
    if min(info["p1_intervals"], info["p2_intervals"]) < 2:
        raise ValueError("research mutation eliminated one seat")
    return amended, info


def semantic_bins(dumps: Path) -> tuple[str, ...]:
    """Only a bounded set of source-referenced slot/camera/race-progress fields.

    Full 128-KiB WRAM hashes are deliberately NOT coverage: counters, scratch
    and unclassified space can create vast spurious novelty.
    """
    tokens = []
    for name in FRAME_NAMES:
        p = dumps / (name + ".wram.bin")
        if not p.is_file() or p.is_symlink() or p.stat().st_size != 131072:
            raise ValueError(f"missing 128-KiB source-qualified semantic sample {name}")
        d = state(p)
        slot1, slot2 = d["slot1"], d["slot2"]
        cam = d["camera_and_viewport"]["mode"]
        progress = d["race_progress"]
        normalized = {
            "checkpoint": name,
            "p1_xy": (slot1["x_pos"]//64, slot1["y_pos"]//32),
            "p2_xy": (slot2["x_pos"]//64, slot2["y_pos"]//32),
            "p1_velocity": (slot1["x_speed"]//64,slot1["y_speed"]//64),
            "p2_velocity": (slot2["x_speed"]//64,slot2["y_speed"]//64),
            "p1_air": slot1["air_effective"], "p2_air": slot2["air"],
            "p1_rotation": slot1["rotation_candidate"]//16,
            "p2_rotation": slot2["rotation_candidate"]//16,
            "split": cam["split_screen_active_raw"],
            "offscreen": (cam["player1_offscreen_raw"],cam["player2_offscreen_raw"]),
            "progress_p1": tuple(progress["player1"][k] for k in
                                  ("next_checkpoint","finish_gate","laps_remaining")),
            "progress_p2": tuple(progress["player2"][k] for k in
                                  ("next_checkpoint","finish_gate","laps_remaining")),
        }
        tokens.append(digest(normalized)[:24])
    return tuple(tokens)


def execute_once(*, exe: Path, rom: Path, source_input: str, script: Path,
                 root: Path, seed: int, arm: str, timeout: int) -> dict:
    actions, info = actions_for(seed, arm)
    generated = root.parent / f"case-{seed}.input"
    generated.write_text(guest.render_input(source_input, actions, None), encoding="utf8")
    load_controller_runs(generated)  # legal input grammar, unchanged stock prefix
    observed = guest.execute(exe, rom, generated, script, root, timeout)
    tokens = semantic_bins(root/"dumps")
    return {"seed": seed, "arm": arm, "input_sha256": guest.sha256(generated),
            "post_entry_wram_sha256": observed[guest.FIRST_PROBE],
            "tokens": list(tokens), "observation_count": len(observed), **info}


def fail_class(exc: BaseException) -> str:
    # Error type is useful for reproducible experiments; don't use volatile
    # stdout or runtime-dependent path strings as reproduction identity.
    return type(exc).__name__


def minimize_actions(*, predicate, actions: list, budget: int = REPRO_ATTEMPTS) -> dict:
    """Bounded ddmin for a known *reproducible* failing input sequence.

    The immutable source entry action is never removed; no mutating production
    code or altering an oracle. Caller must supply a real reproducibility probe.
    """
    if not actions or not 1 <= budget <= REPRO_ATTEMPTS:
        raise ValueError("invalid bounded reduction")
    kept = actions[1:]
    probes = 0
    granularity = 2
    while len(kept) >= 2 and probes < budget:
        size = max(1, math.ceil(len(kept)/granularity))
        reduced = False
        for i in range(0,len(kept),size):
            if probes >= budget:
                break
            candidate = kept[:i]+kept[i+size:]
            probes += 1
            if predicate([actions[0],*candidate]):
                kept=candidate
                granularity=max(2,granularity-1)
                reduced=True
                break
        if not reduced:
            if granularity >= len(kept):
                break
            granularity=min(len(kept),granularity*2)
    return {"actions": [actions[0],*kept], "probes": probes,
            "original_actions":len(actions),"remaining_actions":1+len(kept)}


def run_shard(*, plan_data: dict, shard: int, exe: Path, rom: Path,
              work: Path, out: Path, timeout: int = 120) -> dict:
    first, count = assigned(plan_data, shard)
    if not 30 <= timeout <= 180 or work.exists():
        raise ValueError("unsafe guest watchdog or reused isolated work root")
    identity = guest.identity(exe,rom,plan_data["source_sha"])
    source_input, source_script = guest.base_source()
    work.mkdir(parents=True)
    script = work/"source-route.script"
    script.write_text(guest.render_script(source_script),encoding="utf8")
    seen = set()
    attempts = dict.fromkeys(ARMS,0)
    gains = dict.fromkeys(ARMS,0)
    successful = []
    failure = None
    started = time.monotonic()
    for index in range(count):
        seed = seed_for(plan_data,shard,index)
        arm = select_arm(attempts,gains)
        root = work/f"native-{index:04d}"
        attempts[arm] += 1
        try:
            result = execute_once(exe=exe,rom=rom,source_input=source_input,
                                  script=script,root=root,seed=seed,arm=arm,
                                  timeout=timeout)
            unique = set(result["tokens"])-seen
            gains[arm] += len(unique)
            seen.update(result["tokens"])
            successful.append(result)
            shutil.rmtree(root)
            (work/f"case-{seed}.input").unlink()
        except (OSError,ValueError,RuntimeError) as exc:
            # Keep exact seed/arm and the isolated trial on the runner. Subsequent
            # handoff can regenerate the candidate input without storing ROM/WRAM.
            failure={"index":index,"seed":seed,"arm":arm,
                     "kind":fail_class(exc),"detail":str(exc)[-500:],
                     "repro_status":"not_yet_reproduced"}
            break
        if index % 10 == 0:
            save(out, _receipt(plan_data,shard,identity,attempts,gains,successful,
                               seen,failure,started,complete=False))
    result=_receipt(plan_data,shard,identity,attempts,gains,successful,
                    seen,failure,started,complete=failure is None)
    save(out,result)
    return result


def _receipt(plan_data,shard,identity,attempts,gains,successful,
             seen,failure,started,complete):
    result={
        "schema":SCHEMA,"plan_sha256":plan_data["plan_sha256"],
        "source_sha":plan_data["source_sha"],"shard":shard,
        "identity":identity,"requested_cases":assigned(plan_data,shard)[1],
        "attempted_cases":len(successful)+(failure is not None),
        "passed_cases":len(successful),"failures":[failure] if failure else [],
        "arm_attempts":dict(attempts),"arm_new_bins":dict(gains),
        "semantic_bins":sorted(seen),
        "case_results":list(successful),
        "elapsed_seconds":round(time.monotonic()-started,3),
        "disposition":"completed_observational" if complete else
                      ("producer_failure" if failure else "in_progress"),
        "release_gate_credit":0,
        "original_native_parity":False,"complete_event_verified":False,
        "graphics_source_truth":False,
    }
    result["receipt_sha256"]=digest(result)
    return result


def aggregate(plan_data: dict, root: Path) -> dict:
    validate_plan(plan_data)
    issues=[]
    records=[]
    global_seeds=set()
    global_inputs=set()
    global_tokens=set()
    first_identity=None
    arms={arm:{"attempted":0,"new_bins_local":0} for arm in ARMS}
    for shard in range(plan_data["shards"]):
        path=root/f"research-frontier-{shard}"/"result.json"
        try:
            row=read(path)
            sig=row.pop("receipt_sha256")
            if not isinstance(sig,str) or sig!=digest(row):
                raise ValueError("invalid/tampered original shard receipt")
            required={
                "schema":SCHEMA,"plan_sha256":plan_data["plan_sha256"],
                "source_sha":plan_data["source_sha"],"shard":shard,
                "requested_cases":assigned(plan_data,shard)[1],
                "disposition":"completed_observational","release_gate_credit":0,
                "original_native_parity":False,"complete_event_verified":False,
                "graphics_source_truth":False,
            }
            if any(type(row.get(k)) is not type(v) or row.get(k)!=v
                   for k,v in required.items()):
                raise ValueError("false completeness, release status or shard identity")
            ident=row["identity"]
            if (not isinstance(ident,dict) or
                    ident.get("source_commit")!=plan_data["source_sha"] or
                    ident.get("rom_sha256")!=guest.ROM_SHA or
                    not HEX64.fullmatch(str(ident.get("native_executable_sha256","")))):
                raise ValueError("missing exact native candidate and original ROM provenance")
            if first_identity is not None and ident!=first_identity:
                raise ValueError("shards used different native binary/source fixtures")
            first_identity=ident
            cases=row["case_results"]
            if (not isinstance(cases,list) or len(cases)!=assigned(plan_data,shard)[1]
                    or row["passed_cases"]!=len(cases) or
                    row["attempted_cases"]!=len(cases) or
                    row["failures"]!=[] or
                    set(row["arm_attempts"])!=set(ARMS) or
                    set(row["arm_new_bins"])!=set(ARMS) or
                    sum(row["arm_attempts"].values())!=len(cases)):
                raise ValueError("incomplete scientific population")
            shard_bins=set()
            seen_arms=dict.fromkeys(ARMS,0)
            for index, case in enumerate(cases):
                seed=seed_for(plan_data,shard,index)
                if (type(case) is not dict or case.get("seed")!=seed or
                        case.get("arm") not in ARMS or
                        not HEX64.fullmatch(str(case.get("input_sha256",""))) or
                        not HEX64.fullmatch(str(case.get("post_entry_wram_sha256",""))) or
                        not isinstance(case.get("tokens"),list) or
                        len(case["tokens"])!=len(FRAME_NAMES) or
                        any(not re.fullmatch(r"[a-f0-9]{24}",str(t)) for t in case["tokens"]) or
                        case.get("observation_count")!=len(guest.FRAMES)+1):
                    raise ValueError("case lacks source-authenticated native state evidence")
                seen_arms[case["arm"]]+=1
                if seed in global_seeds or case["input_sha256"] in global_inputs:
                    raise ValueError("duplicate native case across original shards")
                global_seeds.add(seed)
                global_inputs.add(case["input_sha256"])
                shard_bins.update(case["tokens"])
                global_tokens.update(case["tokens"])
            if seen_arms!=row["arm_attempts"] or set(row["semantic_bins"])!=shard_bins:
                raise ValueError("arm/captured semantic coverage count inconsistent")
            if any(type(v) is not int or v<0 or v>3*seen_arms[a]
                   for a,v in row["arm_new_bins"].items()):
                raise ValueError("impossible coverage claim")
            for a in ARMS:
                arms[a]["attempted"]+=seen_arms[a]
                arms[a]["new_bins_local"]+=row["arm_new_bins"][a]
            row["receipt_sha256"]=sig
            records.append({"shard":shard,"cases":len(cases),
                            "elapsed_seconds":row["elapsed_seconds"],
                            "receipt_sha256":sig,
                            "new_local_semantic_bins":len(shard_bins)})
        except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as exc:
            issues.append(f"shard {shard}: {str(exc)[:200]}")
    if root.is_dir():
        expected={f"research-frontier-{i}" for i in range(plan_data["shards"])}
        unexpected={p.name for p in root.iterdir()}-expected
        if unexpected:
            issues.append("unplanned producer artifacts: "+str(sorted(unexpected)[:8]))
    if len(records)!=plan_data["shards"] or len(global_seeds)!=plan_data["requested_cases"]:
        issues.append("requested native coverage count not reached")
    result={
        "schema":SCHEMA,"source_sha":plan_data["source_sha"],
        "plan_sha256":plan_data["plan_sha256"],
        "requested_cases":plan_data["requested_cases"],
        "completed_cases":len(global_seeds),"observed_shards":len(records),
        "native_processes":len(global_seeds),
        "semantic_bins_observed":len(global_tokens),
        "strategy_summary":arms,
        "reproduction_seeds_by_fingerprint":{
            token: seed
            for token,seed in _bounded_examples(plan_data,root).items()
        } if not issues else {},
        "shards":records,"issues":issues,
        "disposition":"completed_observational" if not issues else "incomplete_or_failed",
        "release_gate_credit":0,"original_native_parity":False,
        "complete_event_verified":False,"graphics_source_truth":False,
        "scope":"real native two-seat first-race semantic-state exploration only; not proof of SNES fidelity, scored completion or original PPU correctness",
    }
    result["receipt_sha256"]=digest(result)
    return result


def _bounded_examples(plan_data:dict,root:Path)->dict[str,int]:
    """Deterministic first-seed repro dictionary, 256 entries max, no WRAM/ROM."""
    examples={}
    for shard in range(plan_data["shards"]):
        row=read(root/f"research-frontier-{shard}"/"result.json")
        for case in row["case_results"]:
            for token in case["tokens"]:
                if token not in examples and len(examples)<256:
                    examples[token]=case["seed"]
    return examples


def summary(report:dict)->str:
    lines=["## Adaptive native 2P research frontier","",
           f"**{report['disposition']}**: {report['completed_cases']}/"
           f"{report['requested_cases']} distinct real compiled-native inputs, "
           f"{report['semantic_bins_observed']} observed source-field bins.","",
           "New bins are exploratory coverage only, never original-SNES correctness.",
           "No end-to-end event, renderer/4K, physical controller or release credit.","",
           "| Strategy | Executed cases | Novel local semantic bins |",
           "| --- | ---: | ---: |"]
    for arm,v in report["strategy_summary"].items():
        lines.append(f"| {arm} | {v['attempted']} | {v['new_bins_local']} |")
    lines+=["","First-capture seeds for unusual states are in the compact JSON artifact.",""]
    lines.extend("- "+s for s in report["issues"])
    return "\n".join(lines)+"\n"


def main()->int:
    ap=argparse.ArgumentParser(description=__doc__)
    cmds=ap.add_subparsers(dest="cmd",required=True)
    p=cmds.add_parser("plan")
    p.add_argument("--source-sha",required=True)
    p.add_argument("--base-seed",type=int,required=True)
    p.add_argument("--cases",type=int,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--gha-output",type=Path)
    r=cmds.add_parser("run")
    r.add_argument("--plan",type=Path,required=True)
    r.add_argument("--shard",type=int,required=True)
    r.add_argument("--exe",type=Path,required=True)
    r.add_argument("--rom",type=Path,required=True)
    r.add_argument("--work",type=Path,required=True)
    r.add_argument("--out",type=Path,required=True)
    r.add_argument("--timeout",type=int,default=120)
    a=cmds.add_parser("aggregate")
    a.add_argument("--plan",type=Path,required=True)
    a.add_argument("--results",type=Path,required=True)
    a.add_argument("--out",type=Path,required=True)
    a.add_argument("--summary",type=Path,required=True)
    args=ap.parse_args()
    if args.cmd=="plan":
        data=plan(args.source_sha,args.base_seed,args.cases)
        save(args.out,data)
        if args.gha_output:
            with args.gha_output.open("a") as f:
                f.write(f"matrix={json.dumps(data['matrix'],separators=(',',':'))}\n")
                f.write(f"plan_sha256={data['plan_sha256']}\n")
        print(f"PLANNED {data['requested_cases']} actual unique native 2P cases in "
              f"{data['shards']} reproducible, bounded worker shards")
        return 0
    if args.cmd=="run":
        result=run_shard(plan_data=read(args.plan),shard=args.shard,
                         exe=args.exe.resolve(),rom=args.rom.resolve(),
                         work=args.work,out=args.out,timeout=args.timeout)
        print(f"shard {args.shard}: {result['disposition']} "
              f"{result['passed_cases']}/{result['requested_cases']} real guest cases")
        return 0 if result["disposition"]=="completed_observational" else 1
    result=aggregate(read(args.plan),args.results)
    save(args.out,result)
    args.summary.write_text(summary(result),encoding="utf8")
    print(summary(result))
    return 0 if result["disposition"]=="completed_observational" else 1


if __name__=="__main__":
    raise SystemExit(main())
