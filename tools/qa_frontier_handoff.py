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
    owner_queue=[
        {"lane":"QA-01/07 original gameplay fidelity",
         "hypothesis":"Which novel native state bins diverge under authenticated original SNES inputs?",
         "next_proof":"Use one selected reproducible seed plus independent original USA observation; strict comparator stays unchanged."},
        {"lane":"QA-08/10 graphics and original PPU",
         "hypothesis":"Do sampled split/airborne racer states expose previously absent source-visible OBJ occlusion cases?",
         "next_proof":"Capture source reference PPU/OAM and compare final depth, not a hash-only frame."},
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
    lines+=["","## Decisions for the existing owners",""]
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
