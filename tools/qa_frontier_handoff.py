#!/usr/bin/env python3
"""Read-only frontier finding/handoff packets for existing owning development lanes.

Use source-owned aggregate evidence; don't auto-create speculative defects,
approve PPU pixels, overwrite release QA, or alter another lane's gameplay.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import qa_adaptive_frontier as frontier

SCHEMA="ur-research-frontier-handoff/1"


def report(plan_data:dict, observed:dict)->dict:
    frontier.validate_plan(plan_data)
    unsigned={k:v for k,v in observed.items() if k!="receipt_sha256"}
    if (observed.get("schema")!=frontier.SCHEMA or
        observed.get("source_sha")!=plan_data["source_sha"] or
        observed.get("plan_sha256")!=plan_data["plan_sha256"] or
        observed.get("receipt_sha256")!=frontier.digest(unsigned) or
        observed.get("release_gate_credit")!=0 or
        observed.get("original_native_parity") is not False):
        raise ValueError("untrusted or unbound native source observations")
    successful=observed.get("disposition")=="completed_observational"
    if successful:
        if (observed.get("completed_cases")!=plan_data["requested_cases"]
            or observed.get("issues")!=[] or
            observed.get("observed_shards")!=plan_data["shards"]):
            raise ValueError("a partial frontier cohort cannot be a successful handoff")
    elif observed.get("disposition")!="incomplete_or_failed":
        raise ValueError("unrecognized source experiment disposition")
    ranking=[]
    for arm,row in observed.get("strategy_summary",{}).items():
        if arm not in frontier.ARMS or type(row) is not dict:
            raise ValueError("unexpected coverage policy")
        n,g=row.get("attempted"),row.get("new_bins_local")
        if any(type(x) is not int or x<0 for x in (n,g)) or g>3*n:
            raise ValueError("impossible evidence-weighted strategy claims")
        ranking.append({"arm":arm,"cases":n,"local_bins":g,
                        "discovery_per_case":round(g/n,4) if n else 0})
    ranking.sort(key=lambda item:(-item["discovery_per_case"],-item["cases"],item["arm"]))
    examples=observed.get("reproduction_seeds_by_fingerprint",{})
    if not isinstance(examples,dict) or len(examples)>256:
        raise ValueError("unbounded or missing source-state examples")
    witnesses=[]
    for fingerprint,case in sorted(examples.items())[:24]:
        if (not isinstance(fingerprint,str) or len(fingerprint)!=24 or
                not isinstance(case,dict) or case.get("arm") not in frontier.ARMS or
                type(case.get("seed")) is not int or
                not plan_data["base_seed"]<=case["seed"]<
                    plan_data["base_seed"]+plan_data["requested_cases"]):
            raise ValueError("invalid purported native state reproduction")
        witnesses.append({"fingerprint":fingerprint,
                          "seed":case["seed"],"arm":case["arm"],"shard":case.get("shard")})
    # Do not rank arbitrary hashes alphabetically when a real observed
    # source-slot category has an exact, finite-grammar reproduction seed.
    source_counts=observed.get("source_feature_counts",{})
    source_repros=observed.get("source_feature_reproduction_seeds",{})
    if successful and (
        type(source_counts) is not dict or
        set(source_counts)!=set(frontier.FEATURES) or
        type(source_repros) is not dict
    ):
        raise ValueError("missing bounded source-slot discovery categories")
    category_witnesses=[]
    for feature,n in sorted(source_counts.items(),key=lambda x:(x[1],x[0])):
        if (feature not in frontier.FEATURES or type(n) is not int
                or not 0<=n<=observed.get("completed_cases",0)):
            raise ValueError("invented native source-slot category count")
        if n==0:
            if feature in source_repros:
                raise ValueError("unsupported source slot witness for zero observed cases")
            continue
        w=source_repros.get(feature)
        if (type(w) is not dict or w.get("arm") not in frontier.ARMS
                or type(w.get("seed")) is not int
                or not plan_data["base_seed"]<=w["seed"]<
                       plan_data["base_seed"]+plan_data["requested_cases"]
                or type(w.get("shard")) is not int
                or not 0<=w["shard"]<plan_data["shards"]):
            raise ValueError("source category missing exact original-input reproducer")
        category_witnesses.append({"feature":feature,"cases":n,
                                   "seed":w["seed"],"arm":w["arm"],
                                   "shard":w["shard"]})
    if set(source_repros)-set(source_counts):
        raise ValueError("extra non-source native category witness")
    # A separately epoch-marked fifteen-frame diagnostic can surface a
    # previously unsampled raw source predicate. Do not silently merge its
    # case count into the established three-frame corpus.
    dense_counts=observed.get("dense_feature_counts",{})
    dense_repros=observed.get("dense_feature_reproduction_seeds",{})
    dense_witnesses=[]
    if dense_counts:
        if (observed.get("dense_observer_epoch")!=frontier.DENSE_EPOCH or
                type(dense_counts) is not dict or
                set(dense_counts)!=set(frontier.FEATURES) or
                type(dense_repros) is not dict or
                set(dense_repros)!={key for key,n in dense_counts.items() if n}):
            raise ValueError("unbound fifteen-frame source-feature handoff")
        for feature,n in sorted(dense_counts.items(),key=lambda item:(item[1],item[0])):
            if (type(n) is not int or
                    not source_counts[feature]<=n<=observed["completed_cases"]):
                raise ValueError("dense feature count less than historical three-frame evidence")
            if n==0:
                continue
            w=dense_repros[feature]
            if (type(w) is not dict or w.get("arm") not in frontier.ARMS or
                    type(w.get("seed")) is not int or
                    not plan_data["base_seed"]<=w["seed"]<
                      plan_data["base_seed"]+plan_data["requested_cases"] or
                    type(w.get("shard")) is not int or
                    not 0<=w["shard"]<plan_data["shards"] or
                    w.get("first_frame") not in frontier.DENSE_FRAME_NAMES):
                raise ValueError("invalid first fifteen-frame diagnostic reproduction")
            dense_witnesses.append({
                "feature":feature,"cases":n,"historical_three_frame_cases":source_counts[feature],
                "newly_visible_at_dense_cadence":source_counts[feature]==0,
                "seed":w["seed"],"arm":w["arm"],"shard":w["shard"],
                "first_frame":w["first_frame"]})
    def first_matching(*features):
        return next((w for w in category_witnesses
                     if w["feature"] in features),None)
    dense_graphics_hint=next((
        w for w in dense_witnesses
        if w["newly_visible_at_dense_cadence"] and w["feature"] in (
            "both-air-raw","offscreen-register-nonzero","split-register-changes")),
        None)
    graphics_hint=first_matching("both-air-raw","offscreen-register-nonzero",
                                 "split-register-changes","split-register-nonzero")
    gameplay_hint=first_matching("checkpoint-pointer-changes",
                                 "opposing-x-motion-raw",
                                 "both-rotation-registers-change")
    def dense_hint_text():
        if not dense_graphics_hint:
            return ""
        w=dense_graphics_hint
        return (f" New 15-frame raw-register observation: {w['feature']} at "
                f"{w['first_frame']}, seed {w['seed']}, arm {w['arm']}, "
                f"shard {w['shard']}; validate original source semantics.")
    def hint_text(hint):
        return (f" Candidate source-state reproduction: seed {hint['seed']},"
                f" arm {hint['arm']}, observed category {hint['feature']}."
                if hint else " No special source-slot category nominated yet.")
    owner_queue=[
        {"lane":"QA-01/07 original gameplay fidelity",
         "hypothesis":"Which novel native state bins diverge under authenticated original SNES inputs?",
         "next_proof":"Use one selected reproducible seed plus independent original USA observation; strict comparator stays unchanged."+hint_text(gameplay_hint)},
        {"lane":"QA-08/10 graphics and original PPU",
         "hypothesis":"Do sampled split/airborne racer states expose previously absent source-visible OBJ occlusion cases?",
         "next_proof":"Capture source reference PPU/OAM and compare final depth, not a hash-only frame."+hint_text(graphics_hint)+dense_hint_text()},
        {"lane":"Modern Windows product / independent QA",
         "hypothesis":"Which actually played native transitions now expose missing 2P result and Records publication paths?",
         "next_proof":"Single exact native Windows candidate, complete result, fresh-process Records acceptance."},
    ] if successful else [
        {"lane":"Owned native gameplay + independent CI QA",
         "hypothesis":"Which exact shard/seed/first failed step caused an incomplete native producer?",
         "next_proof":"Reproduce the logged first failing script with original source and binary; classify infra versus game before code changes."}
    ]
    return {
        "schema":SCHEMA,"source_sha":plan_data["source_sha"],
        "plan_sha256":plan_data["plan_sha256"],
        "aggregate_sha256":observed["receipt_sha256"],
        "evidence_disposition":observed["disposition"],
        "independently_adjudicated_original_fidelity":False,
        "release_gate_credit":0,
        "completed_real_native_cases":observed.get("completed_cases",0),
        "observed_semantic_bins":observed.get("semantic_bins_observed",0),
        "strategies_ranked_by_within_shard_coverage":ranking,
        "reproducers":witnesses,
        "source_feature_reproducers":category_witnesses,
        "dense_feature_reproducers":dense_witnesses,
        "owning_lanes":owner_queue,
        "recommendation":("Review and qualify a small selection of unusual observed states with their "
                          "independent original source, rather than automatically generating 10k release passes."
                          if successful else
                          "Repair or independently reproduce first missing or negative source observation; "
                          "never fill the missing population with synthetic evidence."),
    }


def markdown(data:dict)->str:
    lines=["# UR-Recomp adaptive frontier: development handoff","",
           f"Source revision: \`{data['source_sha']}\`",
           f"Exact aggregate receipt: \`{data['aggregate_sha256']}\`",
           f"Outcome: **{data['evidence_disposition']}**; "
           f"{data['completed_real_native_cases']} actual native input cases; "
           f"{data['observed_semantic_bins']} exploratory semantic-state bins.","",
           "**Zero independent original/native or shipping release credit.**","",
           "## Exploration strategies","",
           "| Legal input strategy | Cases | Local new source-field bins / case |",
           "| --- | ---: | ---: |"]
    for row in data["strategies_ranked_by_within_shard_coverage"]:
        lines.append(f"| {row['arm']} | {row['cases']} | {row['discovery_per_case']} |")
    lines+=["","## Reproducible observed-state candidates (not confirmed defects)",""]
    for row in data["reproducers"][:12]:
        lines.append(f"- \`{row['fingerprint']}\`: seed **{row['seed']}**, "
                     f"arm \`{row['arm']}\`. Recreate by invoking "
                     "\`python3 tools/qa_adaptive_frontier.py repro --plan PLAN "
                     f"--seed {row['seed']} --arm {row['arm']} --exe EXACT_EXE "
                     "--rom VERIFIED_USA_ROM --work NEW_PRIVATE_ROOT --out repro.json\`.")
    lines+=["","## Source-observed categories worth an independent source-oracle check","",
            "| Raw WRAM-derived category | Real native inputs | Exact repro seed | Arm |",
            "| --- | ---: | ---: | --- |"]
    for row in data["source_feature_reproducers"]:
        lines.append(f"| {row['feature']} | {row['cases']} | {row['seed']} | {row['arm']} |")
    lines+=["","**These are sampled native register observations, not independent original SNES or PPU truth.**",
            "","## Decisions for the existing owners",""]
    for owner in data["owning_lanes"]:
        lines.append(f"- **{owner['lane']}:** {owner['hypothesis']} "
                     f"Next: {owner['next_proof']}")
    lines+=["",data["recommendation"],"",
            "No commits to gameplay, original oracles, graphics acceptance or release ledger "
            "are authorized by this generated research packet.",""]
    return "\n".join(lines)


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--plan",type=Path,required=True)
    p.add_argument("--aggregate",type=Path,required=True)
    p.add_argument("--out-json",type=Path,required=True)
    p.add_argument("--out-markdown",type=Path,required=True)
    args=p.parse_args()
    value=report(frontier.read(args.plan),frontier.read(args.aggregate))
    frontier.save(args.out_json,value)
    args.out_markdown.parent.mkdir(parents=True,exist_ok=True)
    args.out_markdown.write_text(markdown(value),encoding="utf8")
    print(f"FRONTIER_HANDOFF {value['evidence_disposition']} "
          f"{len(value['reproducers'])} exact source-bound state candidates")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
