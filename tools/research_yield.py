#!/usr/bin/env python3
"""Scientific-yield report and escalation rules over the cumulative ledger.

Reads ``research/qa-cumulative-ledger:.github/qa-cumulative/ledger.json`` and
answers "what did each campaign actually discover, at what cost, and is the
next, larger run likely to change a decision?". It writes nothing to the
ledger and grants no credit; it is a derived view of signed records.

Measures, in decreasing order of decision value:

1. Feature-class discovery: first occurrence (run, seed, arm, frame) of each
   predefined source-field class and its cumulative case incidence.
2. Absence bounds: zero incidence in N independent cases bounds the per-case
   rate below 3/N at 95% (rule of three). More cases only tighten that bound;
   they do not make an unreachable class reachable.
3. Durability bounds: zero failures in N repeated trials bounds the per-trial
   failure rate below 3/N. This is what Windows/fault/native-2p repetitions
   buy; they are not new gameplay states.
4. Fingerprint novelty per case. When every varying checkpoint yields a new
   fingerprint for every case, the census merely restates the case count: it
   is reported as *non-saturating* and never used as a stopping signal.
5. Cost: runner-minutes per completed case where a ``runner_usage`` receipt
   exists (records before 2026-10-14 have none; they are reported as unknown).
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

SCHEMA = "ur-research-yield/1"
POSITIVE = ("completed_positive", "strict_divergence")
# A census whose novelty per case stays within this fraction of the number of
# varying checkpoints is measuring case count, not exploration progress.
NON_SATURATING_FRACTION = 0.98
RARE = 3


def rule_of_three(n: int) -> float | None:
    return None if n <= 0 else min(1.0, 3.0 / n)


def cases_to_bound(rate: float) -> int:
    """Independent zero-event cases needed for a 95% upper bound < rate."""
    return math.ceil(3.0 / rate)


def _frontier_rows(records: list[dict]) -> list[dict]:
    return [r for r in records if r.get("campaign") == "frontier"
            and r.get("origin") == "coordinator"
            and r.get("disposition") == "completed_positive"]


def _feature_counts(metrics: dict) -> tuple[dict, str]:
    if isinstance(metrics.get("full_trace_feature_counts"), dict):
        return metrics["full_trace_feature_counts"], metrics.get(
            "full_trace_probe_policy", "full-trace")
    return metrics.get("source_feature_counts") or {}, "three-checkpoint"


def frontier_yield(records: list[dict]) -> dict:
    rows = _frontier_rows(records)
    runs, features, observers = [], {}, {}
    total_cases = 0
    for row in rows:
        m = row.get("metrics", {})
        n = int(m.get("cases", 0))
        total_cases += n
        per_checkpoint = m.get("checkpoint_unique_fingerprints") or {}
        varying = sum(1 for v in per_checkpoint.values() if v > 1) or None
        novelty = m.get("exact_new_unique_fingerprints")
        per_case = None if novelty is None or n == 0 else round(novelty / n, 3)
        usage = row.get("runner_usage")
        counts, observer = _feature_counts(m)
        observers[observer] = observers.get(observer, 0) + n
        witnesses = (m.get("full_trace_source_feature_witnesses")
                     or m.get("source_feature_reproduction_seeds") or {})
        runs.append({
            "github_run_id": row["github_run_id"], "source_sha": row.get("source_sha"),
            "cases": n, "observer": observer,
            "exact_new_fingerprints": novelty, "new_fingerprints_per_case": per_case,
            "varying_checkpoints": varying,
            "runner_minutes": usage.get("total_runner_minutes") if usage else None,
            "runner_minutes_per_case": (round(usage["total_runner_minutes"] / n, 3)
                                        if usage and n else None),
        })
        for feature, count in counts.items():
            entry = features.setdefault(feature, {
                "cases_observed": 0, "cases_with_feature": 0, "first_occurrence": None,
                "observers": set()})
            entry["cases_observed"] += n
            entry["cases_with_feature"] += int(count)
            entry["observers"].add(observer)
            if count and entry["first_occurrence"] is None:
                witness = witnesses.get(feature) or {}
                entry["first_occurrence"] = {"github_run_id": row["github_run_id"],
                                             "seed": witness.get("seed"),
                                             "arm": witness.get("arm"),
                                             "first_frame": witness.get("first_frame")}
    feature_rows = {}
    for feature, entry in sorted(features.items()):
        n, k = entry["cases_observed"], entry["cases_with_feature"]
        feature_rows[feature] = {
            "cases_observed": n, "cases_with_feature": k,
            "incidence": round(k / n, 6) if n else None,
            "zero_incidence_95pct_upper_bound": rule_of_three(n) if k == 0 else None,
            "rare": 0 < k <= RARE, "ubiquitous": n > 0 and k == n,
            "first_occurrence": entry["first_occurrence"],
            "observers": sorted(entry["observers"]),
        }
    non_saturating = [r for r in runs if r["new_fingerprints_per_case"] is not None
                      and r["varying_checkpoints"]
                      and r["new_fingerprints_per_case"] >=
                      NON_SATURATING_FRACTION * r["varying_checkpoints"]]
    # Older rows lack per-checkpoint counts; ~2 new per case matches the
    # two diverging checkpoints of the same fixed fixture.
    # Pooled counts mix arm policies and observers. The latest contiguous
    # same-observer cohort is the only legitimate base for a rate estimate.
    cohort_rows = []
    for row, run in zip(reversed(rows), reversed(runs)):
        if cohort_rows and run["observer"] != runs[-1]["observer"]:
            break
        cohort_rows.append(row)
    cohort_features = {}
    for row in cohort_rows:
        m = row.get("metrics", {})
        counts, _ = _feature_counts(m)
        for feature, count in counts.items():
            entry = cohort_features.setdefault(feature, {"cases_observed": 0, "cases_with_feature": 0})
            entry["cases_observed"] += int(m.get("cases", 0))
            entry["cases_with_feature"] += int(count)
    return {
        "latest_cohort": {"observer": runs[-1]["observer"] if runs else None,
                          "github_run_ids": [r["github_run_id"] for r in reversed(cohort_rows)],
                          "features": cohort_features},
        "completed_runs": len(rows), "cases": total_cases,
        "cases_by_observer": observers, "runs": runs, "features": feature_rows,
        "fingerprint_census_non_saturating": bool(runs) and len(non_saturating) == sum(
            1 for r in runs if r["varying_checkpoints"]),
        "uninformative_features": sorted(f for f, r in feature_rows.items()
                                         if r["ubiquitous"] or r["cases_with_feature"] == 0),
        "rare_features": sorted(f for f, r in feature_rows.items() if r["rare"]),
    }


def durability_yield(records: list[dict]) -> dict:
    lanes = {}
    for row in records:
        lane = row.get("campaign")
        if lane in ("frontier",):
            continue
        entry = lanes.setdefault(lane, {"runs": 0, "positive_runs": 0, "failed_runs": 0,
                                        "strict_divergence_runs": 0, "cases": 0,
                                        "observations": 0, "runner_minutes": 0.0,
                                        "runs_with_usage": 0, "failure_reasons": []})
        entry["runs"] += 1
        disposition = row.get("disposition")
        m = row.get("metrics", {})
        if disposition in POSITIVE:
            entry["positive_runs"] += 1
            entry["strict_divergence_runs"] += disposition == "strict_divergence"
            entry["cases"] += int(m.get("cases", 0))
            entry["observations"] += int(m.get("observations", 0))
        else:
            entry["failed_runs"] += 1
            entry["failure_reasons"].append({
                "github_run_id": row.get("github_run_id"),
                "reason": m.get("reason"),
                "reusable_job_result": m.get("reusable_job_result")})
        if row.get("runner_usage"):
            entry["runs_with_usage"] += 1
            entry["runner_minutes"] += row["runner_usage"]["total_runner_minutes"]
    for lane, entry in lanes.items():
        entry["zero_failure_95pct_upper_bound_per_observation"] = (
            rule_of_three(entry["observations"])
            if entry["observations"] and lane != "original-native" else None)
        entry["runner_minutes"] = round(entry["runner_minutes"], 1)
    return lanes


def frontier_recommendation(report: dict, *, observer_changed: bool = False,
                            consumer_threshold: float | None = None,
                            target_feature: str | None = None,
                            needs_rate: bool = False) -> dict:
    """Explicit 100 / 1,000 / 10,000 escalation and stopping rules.

    * 100 cases: only to validate a changed observer, arm policy or plan.
    * 1,000 cases: only for a named target feature with a named downstream
      consumer threshold that the current evidence cannot yet decide, i.e.
      zero/rare incidence whose 95% bound still exceeds the threshold and that
      ~1,000 more cases would bring below it.
    * A rare (<=3) feature that already has a reproducible witness: the next
      step is reproducing that witness against the original oracle (owner
      lane), not volume. Volume is justified only if a consumer explicitly
      needs its *rate* (``needs_rate``): 1,000 cases, then 10,000 as ten
      1,000-case batches in a quiet window.
    * Never: to grow a non-saturating fingerprint census, or to search for a
      feature the source analysis says the fixture cannot produce. Pooled
      counts mix arm policies and observers; a rate estimate must come from
      one fixed cohort.
    """
    if observer_changed:
        return {"next": "100", "reason": "validate the changed observer/plan on real native cases first"}
    features = report.get("features", {})
    if target_feature is None:
        return {"next": "none", "reason": (
            "no named target feature and consumer threshold; fingerprint growth alone "
            + ("is non-saturating and " if report.get("fingerprint_census_non_saturating") else "")
            + "is not a reason to run")}
    row = features.get(target_feature)
    if row is None:
        return {"next": "none", "reason": f"{target_feature} is not a measured feature"}
    n, k = row["cases_observed"], row["cases_with_feature"]
    if k == 0 and consumer_threshold is None:
        return {"next": "none", "reason": "absence question needs a consumer threshold"}
    if k == 0:
        bound = rule_of_three(n)
        if bound is not None and bound <= consumer_threshold:
            return {"next": "none", "reason": (
                f"0/{n} already bounds {target_feature} below {bound:.4%} <= threshold")}
        need = cases_to_bound(consumer_threshold) - n
        size = "1000" if need <= 1000 else "10000"
        return {"next": size, "additional_cases_needed": need, "reason": (
            f"0/{n}: bound {bound if bound is None else round(bound, 6)} > threshold; "
            f"~{need} more zero-event cases needed; run as 1,000-case batches")}
    if k <= RARE:
        first = row.get("first_occurrence") or {}
        if not needs_rate:
            return {"next": "none", "action": "reproduce_witness", "witness": first, "reason": (
                f"{k}/{n} with witness seed {first.get('seed')} ({first.get('arm')}, frame "
                f"{first.get('first_frame')}): reproduce it against the original oracle "
                "before buying volume; volume cannot decide whether it is correct")}
        cohort = report.get("latest_cohort", {})
        latest = cohort.get("features", {}).get(target_feature, {})
        n, k = latest.get("cases_observed", n), latest.get("cases_with_feature", k)
        if n < 1000:
            return {"next": "1000", "reason": (
                f"{k}/{n} rare: estimate its rate and gather reproducible witnesses; "
                "first reproduce the existing witness against the original oracle")}
        return {"next": "10000", "reason": (
            f"{k}/{n} still rare after >=1,000 cases; only if a consumer needs the rate, "
            "as ten 1,000-case batches in a quiet window")}
    return {"next": "none", "reason": (
        f"{k}/{n} observed; more volume will not change the decision; hand the witnesses "
        "to the owning lane for reproduction")}


def build_report(ledger: dict) -> dict:
    records = ledger.get("records", [])
    frontier = frontier_yield(records)
    from qa_cumulative_ledger import series_status
    return {"schema": SCHEMA, "release_gate_credit": 0,
            "series": series_status(records),
            "ledger_records": len(records),
            "frontier": frontier, "durability": durability_yield(records),
            "frontier_default_recommendation": frontier_recommendation(frontier)}


def markdown(report: dict) -> str:
    f = report["frontier"]
    out = ["# Cumulative research yield", "",
           f"{report['ledger_records']} ledger records. Derived view; no release credit.", "",
           "## Frontier", "",
           f"{f['completed_runs']} completed runs, {f['cases']} real native cases.", "",
           "| Run | Cases | Observer | New fingerprints / case | Runner-min / case |",
           "| --- | ---: | --- | ---: | ---: |"]
    for r in f["runs"]:
        out.append(f"| {r['github_run_id']} | {r['cases']} | {r['observer']} | "
                   f"{r['new_fingerprints_per_case']} | {r['runner_minutes_per_case'] or 'unknown'} |")
    if f["fingerprint_census_non_saturating"]:
        out += ["", "**Fingerprint census is non-saturating:** every varying checkpoint produced "
                "a new fingerprint for essentially every case. Its growth restates the case "
                "count and is not evidence of exploration progress or a stopping signal."]
    out += ["", "| Feature class | With / observed | 95% bound if absent | First occurrence |",
            "| --- | ---: | ---: | --- |"]
    for name, r in f["features"].items():
        first = r["first_occurrence"]
        if not first:
            where = "never"
        elif first["seed"] is None:
            where = f"run {first['github_run_id']} (no witness recorded by that schema)"
        else:
            where = (f"run {first['github_run_id']} seed {first['seed']} {first['arm']} "
                     f"frame {first['first_frame']}")
        bound = r["zero_incidence_95pct_upper_bound"]
        out.append(f"| {name} | {r['cases_with_feature']} / {r['cases_observed']} | "
                   f"{'' if bound is None else f'< {bound:.4%}'} | {where} |")
    if report.get("series"):
        out += ["", "| Resumable series | Completed / target | Failed batches | Single binary | Checksum |",
                "| --- | ---: | --- | --- | --- |"]
        for s in report["series"]:
            out.append(f"| {s['id']} | {s['completed_cases']} / {s['target_cases']}"
                       f"{' (complete)' if s['complete'] else ''} | {s['failed_batches'] or '-'} | "
                       f"{s['single_binary_cohort']} | {s['series_sha256'][:16]} |")
    rec = report["frontier_default_recommendation"]
    out += ["", f"Default frontier recommendation: **{rec['next']}** — {rec['reason']}.", "",
            "## Repetition and comparator lanes", "",
            "| Lane | Positive / runs | Observations | Failure-rate bound (0 failures) | Runner-min (recorded) |",
            "| --- | ---: | ---: | ---: | ---: |"]
    for lane, r in sorted(report["durability"].items()):
        bound = r["zero_failure_95pct_upper_bound_per_observation"]
        out.append(f"| {lane} | {r['positive_runs']} / {r['runs']} | {r['observations']} | "
                   f"{'' if bound is None else f'< {bound:.4%}'} | "
                   f"{r['runner_minutes'] if r['runs_with_usage'] else 'unknown'} |")
    return "\n".join(out) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ledger", type=Path, required=True)
    ap.add_argument("--out-json", type=Path)
    ap.add_argument("--out-markdown", type=Path)
    ap.add_argument("--target-feature")
    ap.add_argument("--consumer-threshold", type=float)
    ap.add_argument("--observer-changed", action="store_true")
    ap.add_argument("--needs-rate", action="store_true")
    args = ap.parse_args()
    report = build_report(json.loads(args.ledger.read_text()))
    if args.target_feature or args.observer_changed:
        report["frontier_recommendation"] = frontier_recommendation(
            report["frontier"], observer_changed=args.observer_changed,
            consumer_threshold=args.consumer_threshold, target_feature=args.target_feature,
            needs_rate=args.needs_rate)
    text = markdown(report)
    if args.out_json:
        args.out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    if args.out_markdown:
        args.out_markdown.write_text(text)
    print(text)
    if "frontier_recommendation" in report:
        rec = report["frontier_recommendation"]
        print(f"Recommendation: {rec['next']} — {rec['reason']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
