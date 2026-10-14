#!/usr/bin/env python3
"""Append-only, source-bound research coverage ledger for bounded CI campaigns.

Only the serialized coordinator is authorized to commit the ledger branch.
A planned run reserves one deterministic *non-overlapping* seed window;
the terminal step records success OR failure, preserving attempted coverage
without ever converting research evidence into gameplay or release credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import qa_frontier_coverage as coverage
import qa_frontier_exact as exact
import research_admission as admission

SCHEMA = "ur-cumulative-campaign-ledger/1"
PLAN_SCHEMA = "ur-cumulative-campaign-plan/1"
CAMPAIGNS = ("native-2p", "windows", "fault-recovery",
             "graphics", "performance", "original-native", "frontier")
SOURCES = {
    "native-2p": ("ur-native-2p-input-endurance/1", "source_commit",
                  "total_unique_cases", "total_real_native_processes"),
    "windows": ("ur-baldosa-win32-reliability-batch/1", "source_commit",
                "passed_trials", "attempted_trials"),
    "fault-recovery": ("ur-qa02-seeded-fault-endurance/1", "source_sha",
                       "completed_unique_timing_batches",
                       "completed_real_fault_process_journeys"),
    "graphics": ("ur-cumulative-graphics/1", "source_sha",
                 "unique_seeded_frame_sweeps", "measured_frame_checks"),
    "performance": ("ur-cumulative-performance/1", "source_sha",
                    "completed_processes", "sampled_process_seconds"),
    "original-native": ("ur-qa01-event-campaign/1", "source_sha",
                        "selected_cases", "completed"),
    "frontier": ("ur-research-frontier-2p/1", "source_sha",
                 "completed_cases", "native_processes"),
}
SHA = re.compile(r"^[a-f0-9]{40}$")
SHA256 = re.compile(r"^[a-f0-9]{64}$")
# Exactly one reserved 12k seed window per run; the 3k native input plans,
# 2 independent shards, and original fault 1009-multiple case seeds remain
# distinguishable. Never reinterpret already consumed failed seeds as fresh.
WINDOW = 12000
BASE = 50000000
MAX_SEQUENCE = 4083
ALLOWED_WINDOWS_TRIALS = (1, 3, 10, 30, 60)
ALLOWED_MINUTES = (15, 60, 120)
ALLOWED_FRONTIER_CASES = (100, 1000, 10000)
# Resumable frontier series: one fixed-design experiment split into
# independently verified batches, each an ordinary record with its own fresh
# seed window. Only completed_positive batches count toward the target.
SERIES_TARGETS = (1000, 10000)
SERIES_MODES = ("none", "new", "continue")


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":")).encode("utf8")).hexdigest()


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf8"))
    if type(value) is not dict:
        raise ValueError("expected an object")
    return value


def save(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf8")


def validate_ledger(ledger: dict) -> None:
    if type(ledger) is not dict or ledger.get("schema") != SCHEMA:
        raise ValueError("invalid ledger schema")
    if type(ledger.get("records")) is not list:
        raise ValueError("ledger lacks append-only run records")
    seen = set()
    for row in ledger["records"]:
        if (type(row) is not dict or row.get("campaign") not in CAMPAIGNS
                or row.get("origin") not in ("adopted", "coordinator")
                or not SHA.fullmatch(str(row.get("source_sha", "")))
                or type(row.get("github_run_id")) is not int
                or row["github_run_id"] <= 0
                or row.get("disposition") not in ("completed_positive",
                                                 "strict_divergence",
                                                 "incomplete_or_failed",
                                                 "producer_failure")):
            raise ValueError("invalid historical/proposed campaign record")
        key = (row["campaign"], row["github_run_id"])
        if key in seen:
            raise ValueError("duplicate campaign run in append-only ledger")
        seen.add(key)
        if row["origin"] == "coordinator":
            h = row.get("record_sha256")
            content = {k: v for k, v in row.items() if k != "record_sha256"}
            if not isinstance(h, str) or not SHA256.fullmatch(h) or digest(content) != h:
                raise ValueError("mutated coordinator record signature")
            if "producer_digest" in row and not SHA256.fullmatch(str(row["producer_digest"])):
                raise ValueError("invalid scheduling producer digest")
            if "runner_usage" in row:
                admission.validate_usage(row["runner_usage"])


    validate_series(ledger["records"])

    # Validate the separately tamper-evident cumulative state sketch, if present.
    # Older historical ledger branches legitimately have no such record.
    if "frontier_coverage" in ledger:
        coverage.validate_record(ledger["frontier_coverage"])
    # Legacy HLL-only runs are never credited to the exact census.
    if "frontier_exact_coverage" in ledger:
        exact.validate_record(ledger["frontier_exact_coverage"])


def validate_series(records: list[dict]) -> None:
    """Series rows must be internally consistent and strictly sequential."""
    series: dict[str, list[dict]] = {}
    for row in records:
        if "series" not in row:
            continue
        s = row["series"]
        if (row.get("campaign") != "frontier" or row.get("origin") != "coordinator"
                or type(s) is not dict
                or set(s) != {"id", "target_cases", "index", "frontier_prior", "producer_digest"}
                or s["target_cases"] not in SERIES_TARGETS
                or type(s["index"]) is not int or s["index"] < 0
                or not isinstance(s["id"], str)
                or not SHA256.fullmatch(str(s["producer_digest"]))):
            raise ValueError("malformed frontier series batch")
        series.setdefault(s["id"], []).append(row)
    for sid, rows in series.items():
        first = rows[0]["series"]
        if sid != f"frontier-series-{rows[0]['github_run_id']}":
            raise ValueError("series id must name its opening run")
        completed = 0
        for index, row in enumerate(rows):
            s = row["series"]
            if (s["index"] != index or s["target_cases"] != first["target_cases"]
                    or s["frontier_prior"] != first["frontier_prior"]
                    or s["producer_digest"] != first["producer_digest"]):
                raise ValueError("series batch order, target, prior or producer changed")
            if completed >= first["target_cases"]:
                raise ValueError("batch appended to an already complete series")
            if row["disposition"] == "completed_positive":
                completed += int(row.get("metrics", {}).get("cases", 0))
        if completed > first["target_cases"]:
            raise ValueError("series overshoots its target")


def series_status(records: list[dict]) -> list[dict]:
    """Per-series progress; incomplete batches are listed, never counted."""
    out: dict[str, dict] = {}
    for row in records:
        s = row.get("series")
        if not s:
            continue
        entry = out.setdefault(s["id"], {
            "id": s["id"], "target_cases": s["target_cases"], "completed_cases": 0,
            "completed_batches": [], "failed_batches": [], "native_executables": [],
            "producer_digest": s["producer_digest"]})
        m = row.get("metrics", {})
        if row["disposition"] == "completed_positive":
            entry["completed_cases"] += int(m.get("cases", 0))
            entry["completed_batches"].append(row["record_sha256"])
            exe = m.get("native_executable_sha256")
            if exe and exe not in entry["native_executables"]:
                entry["native_executables"].append(exe)
        else:
            entry["failed_batches"].append(row["github_run_id"])
    for entry in out.values():
        entry["complete"] = entry["completed_cases"] >= entry["target_cases"]
        entry["remaining_cases"] = max(0, entry["target_cases"] - entry["completed_cases"])
        # Aggregate checksum over the ordered completed batch signatures.
        entry["series_sha256"] = digest(entry["completed_batches"])
        entry["single_binary_cohort"] = len(entry["native_executables"]) <= 1
    return list(out.values())


def _series_for_plan(ledger: dict, *, mode: str, target: int, cases: int, run_id: int,
                     prior: dict, producer_digest: str | None) -> dict | None:
    if mode == "none":
        return None
    if mode not in SERIES_MODES:
        raise ValueError("unknown series mode")
    if producer_digest is None:
        raise ValueError("a series pins its producer digest")
    if mode == "new":
        if target not in SERIES_TARGETS or cases >= target:
            raise ValueError("a new series needs a 1,000/10,000 target larger than its batch")
        return {"id": f"frontier-series-{run_id}", "target_cases": target, "index": 0,
                "frontier_prior": prior, "producer_digest": producer_digest}
    open_series = [s for s in series_status(ledger["records"]) if not s["complete"]]
    if not open_series:
        raise ValueError("no open frontier series to continue")
    current = open_series[-1]
    rows = [r for r in ledger["records"] if r.get("series", {}).get("id") == current["id"]]
    first = rows[0]["series"]
    if producer_digest != first["producer_digest"]:
        raise ValueError("frontier producer changed since the series opened; "
                         "close it and open a new series rather than mixing observers")
    if cases > current["remaining_cases"]:
        raise ValueError("batch larger than the series' remaining cases")
    return {"id": current["id"], "target_cases": first["target_cases"], "index": len(rows),
            "frontier_prior": first["frontier_prior"], "producer_digest": producer_digest}


def next_seed(ledger: dict, campaign: str) -> tuple[int, int]:
    prior = [r for r in ledger["records"] if r["campaign"] == campaign
             and r["origin"] == "coordinator"]
    sequence = len(prior)
    if sequence > MAX_SEQUENCE:
        raise ValueError("8-digit non-overlapping seed space exhausted; rotate namespace explicitly")
    return sequence, BASE + sequence * WINDOW


def choose(ledger: dict, selected: str) -> str:
    if selected in CAMPAIGNS:
        return selected
    if selected != "auto":
        raise ValueError("unknown campaign")
    previous = [r for r in ledger["records"] if r["origin"] == "coordinator"]
    return CAMPAIGNS[len(previous) % len(CAMPAIGNS)]



def frontier_strategy_prior(ledger: dict) -> dict:
    """Bounded six-recent-run adaptive learning from actual completed receipts.

    These are *prior* local novelty counts; never billed as fresh test cases.
    """
    from qa_adaptive_frontier import ARMS, normalized_prior
    total={arm:{"attempted":0,"new_bins_local":0} for arm in ARMS}
    recent=[row for row in ledger["records"]
            if row["campaign"]=="frontier" and
               row["origin"]=="coordinator" and
               row["disposition"]=="completed_positive"][-6:]
    for row in recent:
        observations=normalized_prior(row.get("metrics",{}).get("strategy_summary"))
        for arm in ARMS:
            for key in ("attempted","new_bins_local"):
                total[arm][key]+=observations[arm][key]
    return normalized_prior(total)


def make_plan(ledger: dict, *, selected: str, source_sha: str,
              minutes: int, windows_trials: int, run_id: int,
              frontier_cases: int = 100, producer_digest: str | None = None,
              series: str = "none", series_target: int = 0) -> dict:
    validate_ledger(ledger)
    if (not SHA.fullmatch(source_sha) or minutes not in ALLOWED_MINUTES
            or windows_trials not in ALLOWED_WINDOWS_TRIALS
            or frontier_cases not in ALLOWED_FRONTIER_CASES
            or type(run_id) is not int or run_id <= 0):
        raise ValueError("invalid source, budget or exact workflow run identity")
    if any(row["github_run_id"] == run_id for row in ledger["records"]):
        raise ValueError("this coordinator run was already recorded")
    campaign = choose(ledger, selected)
    if series != "none" and campaign != "frontier":
        raise ValueError("resumable series are defined for the frontier only")
    seq, seed = next_seed(ledger, campaign)
    prior = frontier_strategy_prior(ledger)
    series_body = _series_for_plan(ledger, mode=series, target=series_target,
                                   cases=frontier_cases, run_id=run_id, prior=prior,
                                   producer_digest=producer_digest)
    if series_body is not None:
        # The arm allocation is pinned for the whole series: batches form one
        # fixed-design experiment rather than a drifting adaptive mixture.
        prior = series_body["frontier_prior"]
    body = {
        "schema": PLAN_SCHEMA,
        "campaign": campaign, "sequence": seq, "base_seed": seed,
        "source_sha": source_sha, "github_run_id": run_id,
        "minutes": minutes, "windows_trials": windows_trials,
        "frontier_cases": frontier_cases,
        "frontier_prior": prior,
        "ledger_before_sha256": digest(ledger),
        "release_gate_credit": 0,
    }
    if producer_digest is not None:
        # Scheduling heuristic only (see research_admission.auto_lane); it is
        # not part of seed allocation or scientific identity.
        if not SHA256.fullmatch(producer_digest):
            raise ValueError("invalid producer digest")
        body["producer_digest"] = producer_digest
    if series_body is not None:
        body["series"] = series_body
    body["plan_sha256"] = digest(body)
    return body


def validate_plan(plan: dict) -> None:
    if type(plan) is not dict:
        raise ValueError("missing plan")
    key = plan.get("plan_sha256")
    unsigned = {k: v for k, v in plan.items() if k != "plan_sha256"}
    if (plan.get("schema") != PLAN_SCHEMA or not isinstance(key, str)
            or not SHA256.fullmatch(key) or digest(unsigned) != key
            or plan.get("campaign") not in CAMPAIGNS
            or not SHA.fullmatch(str(plan.get("source_sha", "")))):
        raise ValueError("tampered or incomplete campaign plan")


def _diagnostic(plan: dict, producer: dict | None) -> dict:
    """Bounded, uncredited description of an aggregate from a failed run.

    A red reusable job may still deliver a source-bound aggregate holding valid
    per-case observations (e.g. two strict divergences and one producer
    error). Retain what it says for triage; never count it as completed work.
    """
    if producer is None:
        return {}
    schema, source_key, _, _ = SOURCES[plan["campaign"]]
    out = {"aggregate_sha256": digest(producer),
           "aggregate_bound_to_plan": (producer.get("schema") == schema
                                       and producer.get(source_key) == plan["source_sha"])}
    if not out["aggregate_bound_to_plan"]:
        return out
    if type(producer.get("disposition")) is str:
        out["producer_disposition"] = producer["disposition"][:60]
    if type(producer.get("counts")) is dict:
        out["case_counts"] = {str(k)[:40]: v for k, v in list(producer["counts"].items())[:8]
                              if type(v) is int}
    if type(producer.get("results")) is list:
        out["case_dispositions"] = [
            {"case": str(r.get("case"))[:40], "disposition": str(r.get("disposition"))[:40],
             "reason": str(r.get("reason") or "")[:200]}
            for r in producer["results"][:16] if type(r) is dict]
    if type(producer.get("issues")) is list:
        out["issues"] = [str(i)[:200] for i in producer["issues"][:5]]
    return out


def outcome(plan: dict, producer: dict | None, job_result: str) -> tuple[str, dict]:
    campaign = plan["campaign"]
    # Previous original/native receipts conflated a red reusable workflow
    # (plan/build/cases/aggregate may each be responsible) with a green child
    # whose expected aggregate was unavailable. Preserve exactly the observed
    # outer coordinator status, not a guessed inner root cause.
    if campaign == "original-native":
        if job_result != "success":
            return "incomplete_or_failed", {
                "reason": "original/native reusable workflow did not succeed",
                "reusable_job_result": job_result,
                "aggregate_present": producer is not None,
                "first_failed_child_step_verified": False,
                **({"diagnostic": _diagnostic(plan, producer)} if producer is not None else {}),
            }
        if producer is None:
            return "incomplete_or_failed", {
                "reason": "original/native aggregate missing after successful reusable workflow",
                "reusable_job_result": "success",
                "aggregate_present": False,
                "first_failed_child_step_verified": False,
            }
    elif job_result != "success" or producer is None:
        # Record the observed reusable-job result: an operator cancellation
        # and a producer failure are different operational facts.
        return "incomplete_or_failed", {
            "reason": "original workflow or aggregate unavailable",
            "reusable_job_result": str(job_result)[:40],
            "aggregate_present": producer is not None,
            **({"diagnostic": _diagnostic(plan, producer)} if producer is not None else {}),
        }
    schema, source_key, cases_key, unit_key = SOURCES[campaign]
    if producer.get("schema") != schema or producer.get(source_key) != plan["source_sha"]:
        raise ValueError("aggregate is not bound to the exact planned source/producer schema")
    if producer.get("release_gate_credit", producer.get("release_admissions", None)) != 0:
        raise ValueError("research attempted release gate credit")
    if producer.get("disposition") == "completed_positive" or (
            campaign == "frontier" and producer.get("disposition") == "completed_observational"):
        status = "completed_positive"
    elif campaign == "original-native" and producer.get("transport_complete") is True:
        counts = producer.get("counts")
        if not isinstance(counts, dict) or counts.get("producer_error") != 0 or counts.get("missing_evidence") != 0:
            return "incomplete_or_failed", {"reason": "original/native case missing/producer error"}
        status = "strict_divergence" if counts.get("strict_divergence", 0) > 0 else "completed_positive"
    else:
        return "incomplete_or_failed", {"reason": "source producer reported partial/negative results"}
    n = producer.get(cases_key)
    processes = producer.get(unit_key)
    if any(type(v) is not int or v < 0 for v in (n, processes)):
        raise ValueError("aggregate has no grounded nonnegative workload counts")
    if (campaign == "native-2p" and
            (n < 1 or processes != 4*n or producer.get("observed_shards") != 2)):
        raise ValueError("native input case/process counts are not complete")
    if (campaign == "windows" and
            (n != 4*plan["windows_trials"] or processes != n or producer.get("observed_shards") != 4)):
        raise ValueError("Windows cohort did not execute the exact planned population")
    if (campaign == "fault-recovery" and
            (n < 5 or processes != 10*n or producer.get("observed_suites") != 5)):
        raise ValueError("production fault trial counts are inconsistent")
    if campaign == "frontier":
        from qa_adaptive_frontier import plan as frontier_plan
        expected=frontier_plan(plan["source_sha"],plan["base_seed"],plan["frontier_cases"],
                               plan["frontier_prior"])
        if (n != plan["frontier_cases"] or processes != n+3*(
                expected["shards"]*((n//expected["shards"]+24)//25))
                or producer.get("observed_shards")!=expected["shards"]
                or producer.get("plan_sha256")!=expected["plan_sha256"]
                or producer.get("release_gate_credit")!=0
                or producer.get("original_native_parity") is not False
                or producer.get("complete_event_verified") is not False):
            raise ValueError("frontier input/oracle identity or case/ablation population not complete")
    if campaign == "original-native":
        if n < 1 or processes > n or producer.get("release_admissions") != 0:
            raise ValueError("original comparator completeness is inconsistent")
    if campaign in ("graphics", "performance") and n < 1:
        raise ValueError("no actual inspected frames/processes")
    if producer.get("issues") not in (None, []):
        raise ValueError("aggregate contains unresolved evidence issues")
    metrics={"cases": n, "observations": processes,
             "aggregate_sha256": digest(producer)}
    if campaign == "frontier":
        summary=producer.get("strategy_summary")
        if (not isinstance(summary,dict) or
                set(summary)!={"balanced","p1-focus","p2-focus","alternating","rotation"}):
            raise ValueError("frontier strategy/novelty evidence absent")
        if any(type(row) is not dict or
               any(type(row.get(key)) is not int or row[key]<0
                   for key in ("attempted","new_bins_local")) or
               row["new_bins_local"]>3*row["attempted"]
               for row in summary.values()):
            raise ValueError("frontier contains impossible semantic novelty metrics")
        if sum(row["attempted"] for row in summary.values())!=n:
            raise ValueError("frontier strategy cases do not sum to observed real inputs")
        from qa_adaptive_frontier import guest
        ident = producer.get("identity")
        required_identity = {
            "source_commit", "native_executable_sha256", "rom_sha256",
            "stock_input_sha256", "stock_script_sha256",
        }
        if (type(ident) is not dict or set(ident) != required_identity
                or ident.get("source_commit") != plan["source_sha"]
                or ident.get("rom_sha256") != guest.ROM_SHA
                or any(not SHA256.fullmatch(str(ident.get(key, "")))
                       for key in required_identity - {"source_commit"})):
            raise ValueError("frontier lacks original ROM, fixture or compiled-native exact provenance")
        metrics["native_executable_sha256"] = ident["native_executable_sha256"]
        metrics["original_rom_sha256"] = ident["rom_sha256"]
        metrics["stock_input_sha256"] = ident["stock_input_sha256"]
        metrics["stock_script_sha256"] = ident["stock_script_sha256"]
        metrics["frontier_source_plan_sha256"] = producer["plan_sha256"]
        from qa_adaptive_frontier import FRAME_NAMES
        per_checkpoint = producer.get("checkpoint_unique_fingerprints")
        if (type(per_checkpoint) is not dict or
                set(per_checkpoint) != set(FRAME_NAMES) or
                any(type(v) is not int or not 1 <= v <= n
                    for v in per_checkpoint.values()) or
                sum(per_checkpoint.values()) <
                    producer.get("semantic_bins_observed", n * 3 + 1)):
            raise ValueError("frontier source checkpoint-specific census is missing or inconsistent")
        metrics["checkpoint_unique_fingerprints"] = per_checkpoint
        metrics["semantic_bins_observed"]=producer.get("semantic_bins_observed")
        metrics["strategy_summary"]=summary
        from qa_adaptive_frontier import FEATURES
        feature_counts=producer.get("source_feature_counts")
        feature_repros=producer.get("source_feature_reproduction_seeds")
        if (type(feature_counts) is not dict or set(feature_counts)!=set(FEATURES)
                or type(feature_repros) is not dict
                or any(type(v) is not int or not 0<=v<=n
                       for v in feature_counts.values())
                or set(feature_repros)!={key for key,v in feature_counts.items() if v}):
            raise ValueError("missing or impossible source-observed development-category population")
        for feature,w in feature_repros.items():
            if (type(w) is not dict
                    or w.get("arm") not in summary
                    or type(w.get("seed")) is not int
                    or not plan["base_seed"]<=w["seed"]<plan["base_seed"]+n):
                raise ValueError("unbound source feature reproduction seed or strategy")
        metrics["source_feature_counts"]=feature_counts
        from qa_adaptive_frontier import TRACE_PROBE_POLICY, TRACE_RAW_FIELDS, ALL_FRAME_NAMES, guest as native_guest
        traced=producer.get("full_trace_feature_counts")
        by_arm=producer.get("full_trace_feature_counts_by_arm")
        first_frames=producer.get("full_trace_first_detection_frame_counts")
        only=producer.get("full_trace_only_feature_counts")
        repros=producer.get("full_trace_source_feature_witnesses")
        only_repros=producer.get("full_trace_only_feature_witnesses")
        raw=producer.get("full_trace_raw_field_values")
        if (producer.get("full_trace_probe_policy")!=TRACE_PROBE_POLICY or
                producer.get("full_trace_checkpoint_count")!=len(ALL_FRAME_NAMES) or
                type(traced) is not dict or set(traced)!=set(FEATURES) or
                type(by_arm) is not dict or set(by_arm)!=set(summary) or
                type(first_frames) is not dict or set(first_frames)!=set(FEATURES) or
                type(only) is not dict or set(only)!=set(FEATURES) or
                type(repros) is not dict or
                set(repros)!={k for k,v in traced.items() if v} or
                type(only_repros) is not dict or
                set(only_repros)!={k for k,v in only.items() if v} or
                type(raw) is not dict or set(raw)!=set(TRACE_RAW_FIELDS)):
            raise ValueError("missing or inconsistent all-checkpoint native WRAM source probe")
        for arm,counts in by_arm.items():
            if (type(counts) is not dict or set(counts)!=set(FEATURES)
                    or any(type(v) is not int or not 0<=v<=summary[arm]["attempted"]
                           for v in counts.values())):
                raise ValueError("unbound source feature arm-specific observation counts")
        for feature,histogram in first_frames.items():
            if (type(histogram) is not dict or
                    any(not str(k).isdigit() or int(k) not in native_guest.FRAMES
                            or str(int(k))!=k or type(v) is not int or v<=0
                            for k,v in histogram.items())):
                raise ValueError("invalid native first-detection frame histogram")
        for feature in FEATURES:
            old,new,only_count=feature_counts[feature],traced[feature],only[feature]
            if (type(new) is not int or type(only_count) is not int or
                    not 0<=old<=new<=n or only_count!=new-old
                    or sum(by_arm[arm][feature] for arm in summary)!=new
                    or sum(first_frames[feature].values())!=new):
                raise ValueError("full-trace observation contradicts canonical sparse source counts")
            for witness in (repros[feature],only_repros[feature]) if only_count else (
                    (repros[feature],) if new else ()):
                if (type(witness) is not dict or
                        set(witness)!={"seed","arm","shard","first_frame"} or
                        type(witness["seed"]) is not int or
                        not plan["base_seed"]<=witness["seed"]<plan["base_seed"]+n or
                        witness["arm"] not in summary or
                        type(witness["shard"]) is not int or
                        not 0<=witness["shard"]<expected["shards"] or
                        witness["first_frame"] not in native_guest.FRAMES):
                    raise ValueError("unbound all-checkpoint source feature witness")
        for field,values in raw.items():
            if (type(values) is not list or not 1<=len(values)<=256 or
                    values!=sorted(set(values)) or
                    any(type(v) is not int or not 0<=v<=255 for v in values)):
                raise ValueError("invalid recorded native raw-register byte population")
        if ((traced["split-register-changes"] and len(raw["split"])<2) or
                (traced["split-register-nonzero"] and not any(raw["split"])) or
                (traced["offscreen-register-nonzero"] and
                 not (any(raw["p1_offscreen"]) or any(raw["p2_offscreen"]))) or
                (traced["both-air-raw"] and
                 not (any(raw["p1_air"]) and any(raw["p2_air"])))):
            raise ValueError("aggregate native register values contradict claimed source features")
        metrics["full_trace_probe_policy"]=TRACE_PROBE_POLICY
        metrics["full_trace_checkpoint_count"]=len(ALL_FRAME_NAMES)
        metrics["full_trace_feature_counts"]=traced
        metrics["full_trace_feature_counts_by_arm"]=by_arm
        metrics["full_trace_first_detection_frame_counts"]=first_frames
        metrics["full_trace_only_feature_counts"]=only
        metrics["full_trace_raw_field_values"]=raw
        metrics["full_trace_source_feature_witnesses"]=repros
        metrics["full_trace_only_feature_witnesses"]=only_repros
        if type(metrics["semantic_bins_observed"]) is not int or metrics["semantic_bins_observed"]<0:
            raise ValueError("frontier provided no semantic-state discovery measurement")
    return status, metrics


def _series_args(plan: dict) -> dict:
    s = plan.get("series")
    if not s:
        return {}
    return {"series": "new" if s["index"] == 0 else "continue",
            "series_target": s["target_cases"]}


def append(ledger: dict, plan: dict, producer: dict | None,
           job_result: str, usage: dict | None = None) -> tuple[dict, dict]:
    validate_ledger(ledger)
    validate_plan(plan)
    if digest(ledger) != plan["ledger_before_sha256"]:
        raise ValueError("ledger changed after seed reservation, do not silently overlap cases")
    expected = make_plan(ledger, selected=plan["campaign"],
                         source_sha=plan["source_sha"], minutes=plan["minutes"],
                         windows_trials=plan["windows_trials"],
                         frontier_cases=plan.get("frontier_cases",100),
                         run_id=plan["github_run_id"],
                         producer_digest=plan.get("producer_digest"),
                         **_series_args(plan))
    if expected != plan:
        raise ValueError("stale or forged campaign reservation")
    frontier_state = None
    frontier_exact_state = None
    try:
        state, metrics = outcome(plan, producer, job_result)
        if state == "completed_positive" and plan["campaign"] == "frontier":
            # Update real semantic-state coverage only after the original
            # source-bound experiment has passed its exact-count assertions.
            observed = coverage.observed_report(producer)
            frontier_state, new_metrics = coverage.make_record(
                ledger.get("frontier_coverage"), observed, plan["frontier_cases"])
            metrics.update(new_metrics)
            from qa_adaptive_frontier import COUNT_TO_SHARDS
            exact_observed = exact.observed_report(
                producer, plan["base_seed"], plan["frontier_cases"],
                COUNT_TO_SHARDS[plan["frontier_cases"]])
            frontier_exact_state, exact_metrics = exact.make_record(
                ledger.get("frontier_exact_coverage"), exact_observed,
                plan["github_run_id"], plan["frontier_cases"])
            metrics.update(exact_metrics)
    except (ValueError, KeyError, TypeError) as exc:
        # A malformed/contradictory source receipt is a red research outcome.
        # It still consumes the reserved seed and is retained in the ledger.
        state = "incomplete_or_failed"
        metrics = {"reason": "producer evidence rejected: " + str(exc)[:400]}
    record = {
        "campaign": plan["campaign"], "origin": "coordinator",
        "sequence": plan["sequence"], "base_seed": plan["base_seed"],
        "source_sha": plan["source_sha"], "github_run_id": plan["github_run_id"],
        "minutes": plan["minutes"], "windows_trials": plan["windows_trials"],
        "frontier_cases": plan.get("frontier_cases",100),
        "disposition": state, "metrics": metrics,
        "release_gate_credit": 0,
    }
    if "producer_digest" in plan:
        record["producer_digest"] = plan["producer_digest"]
    if "series" in plan:
        record["series"] = plan["series"]
    if usage is not None:
        # Operational cost, measured from the run's own jobs: lets yield be
        # expressed per runner-hour. Malformed usage is dropped, never fatal.
        try:
            admission.validate_usage(usage)
            record["runner_usage"] = usage
        except ValueError:
            record["runner_usage_rejected"] = True
    record["record_sha256"] = digest(record)
    new = {**ledger, "records": [*ledger["records"], record]}
    if frontier_state is not None and frontier_exact_state is not None:
        new["frontier_coverage"] = frontier_state
        new["frontier_exact_coverage"] = frontier_exact_state
    validate_ledger(new)
    return new, record


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="mode", required=True)
    plan = sub.add_parser("plan")
    plan.add_argument("--ledger", type=Path, required=True)
    plan.add_argument("--selected", choices=(*CAMPAIGNS, "auto"), required=True)
    plan.add_argument("--source-sha", required=True)
    plan.add_argument("--minutes", type=int, required=True)
    plan.add_argument("--windows-trials", type=int, required=True)
    plan.add_argument("--frontier-cases", type=int, default=100)
    plan.add_argument("--run-id", type=int, required=True)
    plan.add_argument("--producer-digest")
    plan.add_argument("--series", choices=SERIES_MODES, default="none")
    plan.add_argument("--series-target", type=int, default=0)
    plan.add_argument("--out", type=Path, required=True)
    plan.add_argument("--gha-output", type=Path, required=True)
    finish = sub.add_parser("append")
    finish.add_argument("--ledger", type=Path, required=True)
    finish.add_argument("--plan", type=Path, required=True)
    finish.add_argument("--aggregate", type=Path)
    finish.add_argument("--job-result", required=True)
    finish.add_argument("--out", type=Path, required=True)
    finish.add_argument("--receipt", type=Path, required=True)
    finish.add_argument("--usage", type=Path)
    args = ap.parse_args()
    if args.mode == "plan":
        data = make_plan(read_json(args.ledger), selected=args.selected,
                         source_sha=args.source_sha, minutes=args.minutes,
                         windows_trials=args.windows_trials, run_id=args.run_id,
                         frontier_cases=args.frontier_cases,
                         producer_digest=args.producer_digest or None,
                         series=args.series, series_target=args.series_target)
        save(args.out, data)
        with args.gha_output.open("a", encoding="utf8") as out:
            for key in ("campaign", "base_seed", "minutes", "windows_trials", "frontier_cases", "frontier_prior", "plan_sha256"):
                value=json.dumps(data[key],sort_keys=True,separators=(",",":")) if key=="frontier_prior" else data[key]
                out.write(f"{key}={value}\n")
        print(f"RESERVED {data['campaign']} sequence={data['sequence']} "
              f"seed_window_start={data['base_seed']} on exact source={data['source_sha']}")
        return 0
    producer = None
    if args.aggregate is not None and args.aggregate.is_file():
        producer = read_json(args.aggregate)
    usage = None
    if args.usage is not None and args.usage.is_file():
        try:
            usage = read_json(args.usage)
        except (ValueError, OSError):
            usage = {"schema": "unreadable"}
    old = read_json(args.ledger)
    new, row = append(old, read_json(args.plan), producer, args.job_result, usage)
    save(args.out, new)
    save(args.receipt, row)
    print(f"LEDGER {row['campaign']} {row['disposition']} "
          f"seed={row['base_seed']} run={row['github_run_id']}")
    return 0 if row["disposition"] in ("completed_positive", "strict_divergence") else 1


if __name__ == "__main__":
    raise SystemExit(main())
