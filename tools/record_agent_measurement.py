#!/usr/bin/env python3
"""Produce one validated per-task measurement file, without overwriting anyone's work.

No GitHub/network/CI dispatch. Use within the task's existing branch/PR.
Records remain provisional unless independently reviewed.
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools.daily_measurement import (EVENTS, INVENTORY, PRIOR, ADJUSTMENTS, MILESTONES,
                                     job_ranges, load, validate_milestones, validate_entry)

def make_entry(args, milestones, jobs):
    if args.kind == "milestone" and not args.milestone:
        raise ValueError("Milestone events require --milestone")
    if args.kind != "milestone" and args.milestone:
        raise ValueError("Only milestone events can specify --milestone")
    if args.state == "reviewed" and not args.reviewer:
        raise ValueError("Reviewed state requires a different --reviewer")
    if args.reviewer and args.state != "reviewed":
        raise ValueError("--reviewer only valid for independently reviewed milestone")
    if args.kind != "milestone" and args.state:
        raise ValueError("--state requires milestone kind")
    if args.to and not args.from_range:
        raise ValueError("--to requires --from")
    if args.from_range and not args.to:
        raise ValueError("--from requires --to")
    if bool(args.job_id) != bool(args.to):
        raise ValueError("--job-id required exactly when --from and --to are present")
    e = {
        "schema":"ur-agent-work-measurement/1", "event_id":args.id,
        "recorded_at":args.when, "source_main_sha":args.source_sha,
        "source_pr":args.pr, "kind":args.kind, "work_id":args.work_id,
        "recorded_by":args.actor, "outcome":args.outcome,
        "remaining":args.remaining, "evidence":args.evidence,
    }
    if args.milestone:
        e["milestone_id"] = args.milestone
        e["milestone_state"] = args.state or "provisional"
        if args.reviewer:
            e["reviewed_by"] = args.reviewer
    if args.to:
        e["effort_update"] = {
            "job_id":args.job_id, "from":[float(x) for x in args.from_range],
            "to":[float(x) for x in args.to], "reason_type":args.reason_type,
            "reason":args.reason,
        }
    validate_entry(e, milestones, jobs)
    return e

def parser():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--id", required=True, help="Stable unique slug; do not reuse")
    p.add_argument("--kind", required=True, choices=("milestone","effort_revision","research",
        "risk_reduction","regression","infrastructure","acceptance"))
    p.add_argument("--work-id", required=True)
    p.add_argument("--source-sha", required=True, help="Exact ancestry-reachable main SHA")
    p.add_argument("--pr", required=True, help="Actual GitHub source PR URL")
    p.add_argument("--actor", required=True, help="Contributor identifier")
    p.add_argument("--outcome", required=True, help="Reproduced result, not desired outcome")
    p.add_argument("--remaining", required=True, help="One concrete missing discriminator")
    p.add_argument("--evidence", action="append", required=True, help="Repeat for distinct source URLs")
    p.add_argument("--milestone", help="Frozen milestone ID from milestones-v1.json")
    p.add_argument("--state", choices=("provisional","reviewed","withdrawn"),
                   help="Defaults to provisional for milestone")
    p.add_argument("--reviewer", help="Distinct independent reviewer when state reviewed")
    p.add_argument("--job-id", help="Active remaining-work job to revise")
    p.add_argument("--from", dest="from_range", nargs=3, type=float,
                   metavar=("OPT","LIKELY","PESS"))
    p.add_argument("--to", nargs=3, type=float, metavar=("OPT","LIKELY","PESS"))
    p.add_argument("--reason-type", choices=("earned","re_estimate","regression"),
                   default="re_estimate")
    p.add_argument("--reason", help="Why the evidenced change affects remaining effort")
    p.add_argument("--when", default=None, help="Override UTC timestamp, YYYY-MM-DDTHH:MM:SSZ")
    p.add_argument("--output-dir",type=Path,default=EVENTS)
    p.add_argument("--dry-run", action="store_true")
    return p

def main():
    p=parser()
    args=p.parse_args()
    args.when = args.when or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    milestones=validate_milestones(load(MILESTONES),load(INVENTORY))
    jobs=job_ranges(load(PRIOR),load(INVENTORY),load(ADJUSTMENTS))
    try:
        e=make_entry(args,milestones,jobs)
    except ValueError as exc:
        p.error(str(exc))
    data=json.dumps(e,indent=2,ensure_ascii=False)+"\n"
    dest=args.output_dir/(args.id+".json")
    if args.dry_run:
        print(data,end="")
        print("DRY RUN: no file created",file=sys.stderr)
        return
    args.output_dir.mkdir(parents=True,exist_ok=True)
    try:
        with dest.open("x",encoding="utf-8") as f:
            f.write(data)
    except FileExistsError:
        p.error("Refusing to overwrite existing task measurement: "+str(dest))
    print(str(dest))

if __name__=="__main__":
    main()
