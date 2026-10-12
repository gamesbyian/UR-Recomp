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


    # Validate the separately tamper-evident cumulative state sketch, if present.
    # Older historical ledger branches legitimately have no such record.
    if "frontier_coverage" in ledger:
        coverage.validate_record(ledger["frontier_coverage"])
    # Legacy HLL-only runs are never credited to the exact census.
    if "frontier_exact_coverage" in ledger:
        exact.validate_record(ledger["frontier_exact_coverage"])


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
              frontier_cases: int = 100) -> dict:
    validate_ledger(ledger)
    if (not SHA.fullmatch(source_sha) or minutes not in ALLOWED_MINUTES
            or windows_trials not in ALLOWED_WINDOWS_TRIALS
            or frontier_cases not in ALLOWED_FRONTIER_CASES
            or type(run_id) is not int or run_id <= 0):
        raise ValueError("invalid source, budget or exact workflow run identity")
    if any(row["github_run_id"] == run_id for row in ledger["records"]):
        raise ValueError("this coordinator run was already recorded")
    campaign = choose(ledger, selected)
    seq, seed = next_seed(ledger, campaign)
    body = {
        "schema": PLAN_SCHEMA,
        "campaign": campaign, "sequence": seq, "base_seed": seed,
        "source_sha": source_sha, "github_run_id": run_id,
        "minutes": minutes, "windows_trials": windows_trials,
        "frontier_cases": frontier_cases,
        "frontier_prior": frontier_strategy_prior(ledger),
        "ledger_before_sha256": digest(ledger),
        "release_gate_credit": 0,
    }
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


def outcome(plan: dict, producer: dict | None, job_result: str) -> tuple[str, dict]:
    campaign = plan["campaign"]
    if job_result != "success" or producer is None:
        return "incomplete_or_failed", {"reason": "original workflow or aggregate unavailable"}
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
        if type(metrics["semantic_bins_observed"]) is not int or metrics["semantic_bins_observed"]<0:
            raise ValueError("frontier provided no semantic-state discovery measurement")
    return status, metrics


def append(ledger: dict, plan: dict, producer: dict | None,
           job_result: str) -> tuple[dict, dict]:
    validate_ledger(ledger)
    validate_plan(plan)
    if digest(ledger) != plan["ledger_before_sha256"]:
        raise ValueError("ledger changed after seed reservation, do not silently overlap cases")
    expected = make_plan(ledger, selected=plan["campaign"],
                         source_sha=plan["source_sha"], minutes=plan["minutes"],
                         windows_trials=plan["windows_trials"],
                         frontier_cases=plan.get("frontier_cases",100),
                         run_id=plan["github_run_id"])
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
    plan.add_argument("--out", type=Path, required=True)
    plan.add_argument("--gha-output", type=Path, required=True)
    finish = sub.add_parser("append")
    finish.add_argument("--ledger", type=Path, required=True)
    finish.add_argument("--plan", type=Path, required=True)
    finish.add_argument("--aggregate", type=Path)
    finish.add_argument("--job-result", required=True)
    finish.add_argument("--out", type=Path, required=True)
    finish.add_argument("--receipt", type=Path, required=True)
    args = ap.parse_args()
    if args.mode == "plan":
        data = make_plan(read_json(args.ledger), selected=args.selected,
                         source_sha=args.source_sha, minutes=args.minutes,
                         windows_trials=args.windows_trials, run_id=args.run_id,
                         frontier_cases=args.frontier_cases)
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
    old = read_json(args.ledger)
    new, row = append(old, read_json(args.plan), producer, args.job_result)
    save(args.out, new)
    save(args.receipt, row)
    print(f"LEDGER {row['campaign']} {row['disposition']} "
          f"seed={row['base_seed']} run={row['github_run_id']}")
    return 0 if row["disposition"] in ("completed_positive", "strict_divergence") else 1


if __name__ == "__main__":
    raise SystemExit(main())
