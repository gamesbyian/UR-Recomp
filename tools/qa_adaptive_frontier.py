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
import qa_frontier_coverage as coverage
import qa_frontier_exact as exact
from controller_input import load_controller_runs
from summarize_paired_player_slots import state

SCHEMA = "ur-research-frontier-2p/1"
PLAN_SCHEMA = "ur-research-frontier-plan/1"
ARMS = ("balanced", "p1-focus", "p2-focus", "alternating", "rotation")
FEATURES = (
    "both-air-raw",
    "both-moving-raw",
    "both-rotation-registers-change",
    "checkpoint-pointer-changes",
    "offscreen-register-nonzero",
    "opposing-x-motion-raw",
    "split-register-changes",
    "split-register-nonzero",
)
FRAME_NAMES = ("endurance-1740", "endurance-2580", "endurance-3420")
ALL_FRAME_NAMES = tuple(f"endurance-{frame}" for frame in guest.FRAMES)
TRACE_RAW_FIELDS = ("p1_air", "p2_air", "p1_offscreen", "p2_offscreen", "split")
TRACE_PROBE_POLICY = "full-existing-15-wram-frames-raw-fields-v1"
COUNT_TO_SHARDS = {100: 4, 1000: 10, 10000: 40}
SOURCE = "existing original-fixture-qualified native 2P first-race route"
HEX40 = re.compile(r"^[a-f0-9]{40}$")
HEX64 = re.compile(r"^[a-f0-9]{64}$")
MAX_SEED = 99999999
MAX_CASES_PER_SHARD = 250
REPRO_ATTEMPTS = 12
STRATEGY_POLICY = "fresh-five-arm-warmup-plus-decile-v1"
# The observers read only 128-KiB WRAM dumps. Runtime "turbo" skips PPU
# rendering on 15 of 16 frames: 12/12 local A/B cases (all arms, incl. the
# dual-air witness) were byte-identical at all 16 dumps and 22.7% faster
# (tools/qa_frontier_turbo_ab.py). Every 25th case's identical-input repeat runs fully rendered, so
# the existing byte-equality check continuously proves turbo-invariance of
# all observed WRAM. Framebuffer dumps from turbo cases are not evidence.
EXECUTION_POLICY = "wram-only-turbo-with-rendered-repeat-guard-v1"


def turbo_script(rendered: str) -> str:
    if not rendered.endswith("quit\n") or "turbo" in rendered:
        raise ValueError("expected one canonical rendered observation script")
    return "turbo on\n" + rendered


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



def normalized_prior(value: dict | None) -> dict:
    """Rolling *observed* strategy yield carried by the cumulative ledger.

    Prior counts are advisory for selection only, not fresh experiments.
    All statistics on the new run are counted from zero.
    """
    if value is None or value=={}:
        return {arm:{"attempted":0,"new_bins_local":0} for arm in ARMS}
    if not isinstance(value,dict) or set(value)!=set(ARMS):
        raise ValueError("malformed frontier prior strategies")
    for arm,row in value.items():
        if (type(row) is not dict or set(row)!={"attempted","new_bins_local"} or
                type(row["attempted"]) is not int or
                type(row["new_bins_local"]) is not int or
                not 0<=row["attempted"]<=1000000 or
                not 0<=row["new_bins_local"]<=3*row["attempted"]):
            raise ValueError(f"invalid prior for {arm}")
    return {arm:dict(value[arm]) for arm in ARMS}


def plan(source_sha: str, base_seed: int, count: int,
         strategy_prior: dict | None = None) -> dict:
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
        "strategy_prior": normalized_prior(strategy_prior),
        "strategy_policy": STRATEGY_POLICY,
        "trace_probe_policy": TRACE_PROBE_POLICY,
        "execution_policy": EXECUTION_POLICY,
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
                    data.get("base_seed"), data.get("requested_cases"),
                    data.get("strategy_prior"))
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


def forced_fresh_arm(index: int, shard: int) -> str | None:
    """Guaranteed fresh 5-way control coverage, regardless of historical prior.

    Every shard tests all five input strategies in its first five cases.
    Every tenth subsequent case is also a deterministic rotating exploration
    trial. This prevents an older high-reward prior from starving legal arms.
    The other cases retain the original adaptive UCB policy.
    """
    if (type(index) is not int or not 0 <= index < MAX_CASES_PER_SHARD
            or type(shard) is not int or not 0 <= shard < 40):
        raise ValueError("invalid deterministic fresh exploration coordinate")
    if index < len(ARMS):
        return ARMS[(index + shard) % len(ARMS)]
    if (index + 1) % 10 == 0:
        return ARMS[(((index + 1)//10) - 1 + shard) % len(ARMS)]
    return None


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


def normalized_token(path: Path, name: str) -> str:
    """The census's 96-bit normalized fingerprint of one 128-KiB WRAM sample.

    ``name`` is the checkpoint label hashed into the identity. Shared by the
    native census and the original-emulator cross-check so both sides use one
    definition.
    """
    d = state(path)
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
    return digest(normalized)[:24]


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
        tokens.append(normalized_token(p, name))
    return tuple(tokens)


def _feature_labels(observed: list[dict]) -> tuple[str,...]:
    """Raw WRAM-feature observer shared without changing the legacy 3-frame census."""
    if not observed:
        raise ValueError("no authenticated native WRAM observations")
    found=set()
    if any(
        row["slot1"]["air_effective"] and row["slot2"]["air"]
        for row in observed
    ):
        found.add("both-air-raw")
    if any(
        (row["slot1"]["x_speed"] or row["slot1"]["y_speed"]) and
        (row["slot2"]["x_speed"] or row["slot2"]["y_speed"])
        for row in observed
    ):
        found.add("both-moving-raw")
    if any(row["slot1"]["x_speed"]*row["slot2"]["x_speed"] < 0
           for row in observed):
        found.add("opposing-x-motion-raw")
    if (len({row["slot1"]["rotation_candidate"] for row in observed}) > 1
            and len({row["slot2"]["rotation_candidate"] for row in observed}) > 1):
        found.add("both-rotation-registers-change")
    modes=[row["camera_and_viewport"]["mode"] for row in observed]
    if len({row["split_screen_active_raw"] for row in modes}) > 1:
        found.add("split-register-changes")
    if any(row["split_screen_active_raw"] for row in modes):
        found.add("split-register-nonzero")
    if any(row["player1_offscreen_raw"] or row["player2_offscreen_raw"]
           for row in modes):
        found.add("offscreen-register-nonzero")
    progress=[row["race_progress"] for row in observed]
    keys=("next_checkpoint","finish_gate","laps_remaining")
    if any(
        tuple(row[player][key] for player in ("player1","player2") for key in keys)
        != tuple(progress[0][player][key] for player in ("player1","player2") for key in keys)
        for row in progress[1:]
    ):
        found.add("checkpoint-pointer-changes")
    if not found.issubset(FEATURES):
        raise ValueError("source feature vocabulary unexpectedly changed")
    return tuple(sorted(found))


def source_features(dumps: Path) -> tuple[str, ...]:
    """Retain the historical three-frame raw-field feature definitions, unchanged."""
    observed=[]
    for name in FRAME_NAMES:
        path=dumps/(name+".wram.bin")
        if not path.is_file() or path.is_symlink() or path.stat().st_size != 131072:
            raise ValueError(f"missing true 128KiB semantic feature source snapshot {name}")
        observed.append(state(path))
    return _feature_labels(observed)


def _raw_trace_fields(row: dict) -> dict[str,int]:
    mode=row["camera_and_viewport"]["mode"]
    return {
        "p1_air":row["slot1"]["air_effective"],
        "p2_air":row["slot2"]["air"],
        "p1_offscreen":mode["player1_offscreen_raw"],
        "p2_offscreen":mode["player2_offscreen_raw"],
        "split":mode["split_screen_active_raw"],
    }


def probe_all_checkpoints(dumps: Path) -> dict:
    """Diagnose raw source fields at all 15 ALREADY-DUMPED WRAM frames.

    Keep the original 3-frame fingerprint extraction epoch unchanged.
    This additional source-observed diagnostic is NOT a new emulator execution
    or evidence of original SNES correctness or visible sprite occlusion.
    """
    snapshots=[]
    for name in ALL_FRAME_NAMES:
        p=dumps/(name+".wram.bin")
        if not p.is_file() or p.is_symlink() or p.stat().st_size != 131072:
            raise ValueError(f"missing full-trace 128KiB original native dump {name}")
        snapshots.append(state(p))
    values={key:set() for key in TRACE_RAW_FIELDS}
    first={}
    for i,snapshot in enumerate(snapshots):
        for key,value in _raw_trace_fields(snapshot).items():
            if type(value) is not int or not 0<=value<=255:
                raise ValueError("raw source register out of byte range")
            values[key].add(value)
        for feature in _feature_labels(snapshots[:i+1]):
            first.setdefault(feature,guest.FRAMES[i])
    return {
        "features":list(_feature_labels(snapshots)),
        "first_frames":first,
        "raw_values":{key:sorted(values[key]) for key in TRACE_RAW_FIELDS},
    }


def execute_once(*, exe: Path, rom: Path, source_input: str, script: Path,
                 root: Path, seed: int, arm: str, timeout: int) -> dict:
    actions, info = actions_for(seed, arm)
    generated = root.parent / f"case-{seed}.input"
    generated.write_text(guest.render_input(source_input, actions, None), encoding="utf8")
    load_controller_runs(generated)  # legal input grammar, unchanged stock prefix
    observed = guest.execute(exe, rom, generated, script, root, timeout)
    tokens = semantic_bins(root/"dumps")
    features = source_features(root/"dumps")
    full_trace = probe_all_checkpoints(root/"dumps")
    if not set(features).issubset(full_trace["features"]):
        raise ValueError("full native WRAM trace contradicts sampled source categories")
    return {"seed": seed, "arm": arm, "input_sha256": guest.sha256(generated),
            "post_entry_wram_sha256": observed[guest.FIRST_PROBE],
            "tokens": list(tokens), "features": list(features),
            "full_trace": full_trace,
            "observation_count": len(observed), **info}



def verify_sample(*,exe: Path, rom: Path, source_input: str, script: Path,
                  root: Path, seed: int, arm: str, timeout: int,
                  rendered_script: Path | None = None) -> None:
    """Strict replay/seat-ablation witness, on every 25th tested case.

    These are real additional native processes; the source fixture's active
    race and pre-intervention state are still checked by guest.execute().
    When ``rendered_script`` is given, the identical-input repeat runs with
    full rendering, so equality also proves the turbo case's WRAM unchanged.
    """
    actions,_=actions_for(seed,arm)
    baseline=guest.observe(root/"dumps")
    treatment=root.parent/f"case-{seed}.input"
    repeat=guest.execute(exe,rom,treatment,rendered_script or script,
                         root.parent/f"verify-repeat-{seed}",timeout)
    if baseline!=repeat:
        raise ValueError("same actual 2P input produced changed full-WRAM checkpoints")
    for muted in ("p1","p2"):
        input_path=root.parent/f"verify-{muted}-{seed}.input"
        input_path.write_text(
            guest.render_input(source_input,actions,muted),encoding="utf8")
        load_controller_runs(input_path)
        probe_dir=root.parent/f"verify-{muted}-{seed}"
        alt=guest.execute(exe,rom,input_path,script,probe_dir,timeout)
        if alt[guest.BASE_CHECK]!=baseline[guest.BASE_CHECK]:
            raise ValueError(f"independent {muted} removal changed original pre-stimulus race")
        if alt[guest.FIRST_PROBE]==baseline[guest.FIRST_PROBE]:
            raise ValueError(f"independent {muted} removal caused no post-stimulus native change")
    for suffix in (f"verify-repeat-{seed}",f"verify-p1-{seed}",f"verify-p2-{seed}"):
        shutil.rmtree(root.parent/suffix)
    for muted in ("p1","p2"):
        (root.parent/f"verify-{muted}-{seed}.input").unlink()



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
    rendered = work/"source-route-rendered.script"
    rendered.write_text(guest.render_script(source_script),encoding="utf8")
    script = work/"source-route.script"
    script.write_text(turbo_script(guest.render_script(source_script)),encoding="utf8")
    seen = set()
    attempts = dict.fromkeys(ARMS,0)
    gains = dict.fromkeys(ARMS,0)
    successful = []
    failure = None
    started = time.monotonic()
    for index in range(count):
        seed = seed_for(plan_data,shard,index)
        prior=plan_data["strategy_prior"]
        selection_attempts={a:attempts[a]+prior[a]["attempted"] for a in ARMS}
        selection_gains={a:gains[a]+prior[a]["new_bins_local"] for a in ARMS}
        arm = forced_fresh_arm(index, shard) or select_arm(selection_attempts,selection_gains)
        root = work/f"native-{index:04d}"
        attempts[arm] += 1
        try:
            result = execute_once(exe=exe,rom=rom,source_input=source_input,
                                  script=script,root=root,seed=seed,arm=arm,
                                  timeout=timeout)
            if index % 25 == 0:
                verify_sample(exe=exe,rom=rom,source_input=source_input,
                              script=script,root=root,seed=seed,arm=arm,
                              timeout=timeout,rendered_script=rendered)
            result["verified_ablation"] = index % 25 == 0
            result["real_native_processes"] = 4 if index % 25 == 0 else 1
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
        "real_native_processes":sum(row["real_native_processes"] for row in successful),
        "metamorphic_verified_cases":sum(bool(row["verified_ablation"]) for row in successful),
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
    checkpoint_tokens={name:set() for name in FRAME_NAMES}
    global_witness={}
    first_identity=None
    arms={arm:{"attempted":0,"new_bins_local":0} for arm in ARMS}
    feature_counts=dict.fromkeys(FEATURES,0)
    feature_repros={}
    trace_counts=dict.fromkeys(FEATURES,0)
    trace_by_arm={arm:dict.fromkeys(FEATURES,0) for arm in ARMS}
    trace_first_frame_histograms={feature:{} for feature in FEATURES}
    trace_new_counts=dict.fromkeys(FEATURES,0)
    trace_repros={}
    trace_only_repros={}
    trace_values={name:set() for name in TRACE_RAW_FIELDS}
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
                    sum(row["arm_attempts"].values())!=len(cases) or
                    row.get("real_native_processes")!=len(cases)+3*((len(cases)+24)//25) or
                    row.get("metamorphic_verified_cases")!=(len(cases)+24)//25):
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
                        case.get("observation_count")!=len(guest.FRAMES)+1 or
                        type(case.get("features")) is not list or
                        case["features"] != sorted(set(case["features"])) or
                        any(feature not in FEATURES for feature in case["features"]) or
                        case.get("verified_ablation") is not (index%25==0) or
                        case.get("real_native_processes")!=(4 if index%25==0 else 1)):
                    raise ValueError("case lacks source-authenticated native state evidence")
                required_arm = forced_fresh_arm(index, shard)
                if required_arm is not None and case["arm"] != required_arm:
                    raise ValueError("source strategy policy violated fresh-shard exploration")
                seen_arms[case["arm"]]+=1
                if seed in global_seeds or case["input_sha256"] in global_inputs:
                    raise ValueError("duplicate native case across original shards")
                trace=case.get("full_trace")
                if (type(trace) is not dict or set(trace)!={"features","first_frames","raw_values"}
                        or type(trace["features"]) is not list
                        or trace["features"]!=sorted(set(trace["features"]))
                        or any(feature not in FEATURES for feature in trace["features"])
                        or not set(case["features"]).issubset(trace["features"])
                        or type(trace["first_frames"]) is not dict
                        or set(trace["first_frames"])!=set(trace["features"])
                        or any(type(frame) is not int or frame not in guest.FRAMES
                               for frame in trace["first_frames"].values())
                        or type(trace["raw_values"]) is not dict
                        or set(trace["raw_values"])!=set(TRACE_RAW_FIELDS)
                        or any(type(v) is not list or not 1<=len(v)<=len(guest.FRAMES)
                               or v!=sorted(set(v))
                               or any(type(x) is not int or not 0<=x<=255 for x in v)
                               for v in trace["raw_values"].values())):
                    raise ValueError("incomplete or fabricated full source trace observations")
                raw=trace["raw_values"]
                if (("split-register-changes" in trace["features"]) != (len(raw["split"])>1)
                        or ("split-register-nonzero" in trace["features"]) !=
                           any(raw["split"])
                        or ("offscreen-register-nonzero" in trace["features"]) !=
                           (any(raw["p1_offscreen"]) or any(raw["p2_offscreen"]))
                        or ("both-air-raw" in trace["features"] and
                            (not any(raw["p1_air"]) or not any(raw["p2_air"])))):
                    raise ValueError("full source trace raw bytes contradict feature labels")
                for feature in trace["features"]:
                    trace_counts[feature]+=1
                    trace_by_arm[case["arm"]][feature]+=1
                    frame=str(trace["first_frames"][feature])
                    frame_hist=trace_first_frame_histograms[feature]
                    frame_hist[frame]=frame_hist.get(frame,0)+1
                    trace_repros.setdefault(feature,{
                        "seed":seed,"arm":case["arm"],"shard":shard,
                        "first_frame":trace["first_frames"][feature]})
                    if feature not in case["features"]:
                        trace_new_counts[feature]+=1
                        trace_only_repros.setdefault(feature,{
                            "seed":seed,"arm":case["arm"],"shard":shard,
                            "first_frame":trace["first_frames"][feature]})
                for name,values in raw.items():
                    trace_values[name].update(values)
                global_seeds.add(seed)
                global_inputs.add(case["input_sha256"])
                for feature in case["features"]:
                    feature_counts[feature]+=1
                    if feature not in feature_repros:
                        feature_repros[feature]={
                            "seed":seed,"arm":case["arm"],"shard":shard}
                shard_bins.update(case["tokens"])
                global_tokens.update(case["tokens"])
                for frame_name,token in zip(FRAME_NAMES,case["tokens"]):
                    checkpoint_tokens[frame_name].add(token)
                    global_witness.setdefault(token,(seed,case["arm"],shard))
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
                            "processes":row["real_native_processes"],
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
        "native_processes":sum(1+3*(i%25==0) for i in range(plan_data["requested_cases"])) if not issues else sum(r.get("processes",0) for r in records),
        "metamorphic_verified_cases":sum((n+24)//25 for n in (assigned(plan_data,s)[1] for s in range(plan_data["shards"]))) if not issues else 0,
        "identity":first_identity if not issues else None,
        "semantic_bins_observed":len(global_tokens),
        "checkpoint_unique_fingerprints":{
            name:len(checkpoint_tokens[name]) for name in FRAME_NAMES
        } if not issues else {},
        "source_feature_counts":feature_counts,
        "source_feature_reproduction_seeds":feature_repros if not issues else {},
        "full_trace_probe_policy":TRACE_PROBE_POLICY,
        "full_trace_checkpoint_count":len(ALL_FRAME_NAMES),
        "full_trace_feature_counts":trace_counts if not issues else {},
        "full_trace_feature_counts_by_arm":trace_by_arm if not issues else {},
        "full_trace_first_detection_frame_counts":trace_first_frame_histograms if not issues else {},
        "full_trace_only_feature_counts":trace_new_counts if not issues else {},
        "full_trace_source_feature_witnesses":trace_repros if not issues else {},
        "full_trace_only_feature_witnesses":trace_only_repros if not issues else {},
        "full_trace_raw_field_values":{
            name:sorted(trace_values[name]) for name in TRACE_RAW_FIELDS
        } if not issues else {},
        "semantic_epoch": coverage.EPOCH,
        "semantic_hll_b64": coverage.encode(coverage.observe(global_tokens)) if not issues else coverage.encode(coverage.empty()),
        "semantic_exact_witnesses_b64": exact.encode_run(global_witness) if not issues else exact.encode_run({}),
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


def _bounded_examples(plan_data:dict,root:Path)->dict[str,dict]:
    """Bounded, shard/strategy-stratified reproducible native witnesses.

    The previous first-256 insertion order selected almost exclusively shard
    zero, so even successful large campaigns handed out misleadingly narrow
    reproduction examples. First cover every actually observed (shard, arm)
    cohort, then round-robin fill by case index across shards. These samples
    are *advisory reproducible witnesses*, not necessarily the earliest source
    sighting; that stronger claim belongs to the exact cumulative ledger.
    """
    rows=[read(root/f"research-frontier-{shard}"/"result.json")
          for shard in range(plan_data["shards"])]
    examples={}

    def include(case:dict,shard:int)->bool:
        for token in case["tokens"]:
            if token not in examples:
                examples[token]={"seed":case["seed"],"arm":case["arm"],
                                 "shard":shard}
                return True
        return False

    # At 40 shards * five arms this uses <=200 of 256 witness slots.
    for shard,row in enumerate(rows):
        seen_arms=set()
        for case in row["case_results"]:
            arm=case["arm"]
            if arm not in seen_arms and include(case,shard):
                seen_arms.add(arm)
            if len(seen_arms)==len(ARMS):
                break

    # Remaining slots cover more temporal/input variation across all shards,
    # not a monotonically filled prefix of the first shard's seeds.
    count=max((len(row["case_results"]) for row in rows),default=0)
    for index in range(count):
        for shard,row in enumerate(rows):
            if len(examples)>=256:
                return examples
            if index<len(row["case_results"]):
                include(row["case_results"][index],shard)
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
    lines+=["","### Actual source-slot feature categories", "",
            "| Raw-observed category | Native input cases |",
            "| --- | ---: |"]
    for name,count in sorted(report["source_feature_counts"].items(),key=lambda row:(row[1],row[0])):
        lines.append(f"| {name} | {count} |")
    lines+=["","Exact seed/arm witnesses for source-slot categories are in the compact JSON artifact.",
            "Source register flags, unlike independent SNES PPU pixel evidence, are not final visual truth.",""]
    lines.extend("- "+s for s in report["issues"])
    return "\n".join(lines)+"\n"


def main()->int:
    ap=argparse.ArgumentParser(description=__doc__)
    cmds=ap.add_subparsers(dest="cmd",required=True)
    p=cmds.add_parser("plan")
    p.add_argument("--source-sha",required=True)
    p.add_argument("--base-seed",type=int,required=True)
    p.add_argument("--cases",type=int,required=True)
    p.add_argument("--strategy-prior-json",default="{}")
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
    repro=cmds.add_parser("repro")
    repro.add_argument("--plan",type=Path,required=True)
    repro.add_argument("--seed",type=int,required=True)
    repro.add_argument("--arm",choices=ARMS,required=True)
    repro.add_argument("--exe",type=Path,required=True)
    repro.add_argument("--rom",type=Path,required=True)
    repro.add_argument("--work",type=Path,required=True)
    repro.add_argument("--out",type=Path,required=True)
    a=cmds.add_parser("aggregate")
    a.add_argument("--plan",type=Path,required=True)
    a.add_argument("--results",type=Path,required=True)
    a.add_argument("--out",type=Path,required=True)
    a.add_argument("--summary",type=Path,required=True)
    args=ap.parse_args()
    if args.cmd=="plan":
        data=plan(args.source_sha,args.base_seed,args.cases,
                  json.loads(args.strategy_prior_json))
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
    if args.cmd=="repro":
        plan_data=read(args.plan)
        validate_plan(plan_data)
        if not plan_data["base_seed"]<=args.seed<plan_data["base_seed"]+plan_data["requested_cases"]:
            raise ValueError("reproducer seed not within exact source-bound planned population")
        proof=guest.identity(args.exe.resolve(),args.rom.resolve(),plan_data["source_sha"])
        if args.work.exists():
            raise ValueError("refuse reused external reproduction root")
        args.work.mkdir(parents=True)
        original_input,original_script=guest.base_source()
        script=args.work/"route.script"
        script.write_text(guest.render_script(original_script),encoding="utf8")
        witness=execute_once(exe=args.exe.resolve(),rom=args.rom.resolve(),
                             source_input=original_input,script=script,
                             root=args.work/"repro",seed=args.seed,arm=args.arm,timeout=120)
        witness.update(identity=proof,plan_sha256=plan_data["plan_sha256"],
                       original_native_parity=False,release_gate_credit=0,
                       disposition="observed_native_not_original_parity")
        save(args.out,witness)
        print(f"Real native semantic repro seed={args.seed} arm={args.arm} "
              f"bins={','.join(witness['tokens'])}")
        return 0
    result=aggregate(read(args.plan),args.results)
    save(args.out,result)
    args.summary.write_text(summary(result),encoding="utf8")
    print(summary(result))
    return 0 if result["disposition"]=="completed_observational" else 1


if __name__=="__main__":
    raise SystemExit(main())
