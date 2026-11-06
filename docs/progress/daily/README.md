# Daily agent measurements: operational pilot

**Status:** source-linked provisional engineering estimate and expected remaining relative-work model, not release acceptance. **One feed, five interchangeable agents.** This implements the first bounded subset of the [daily estimation protocol](../DAILY-ENGINEERING-PROGRESS-ESTIMATION-PLAN-20261106.md), without a new scheduler, extra full-suite CI or a required PR for each observation.

## Fast receipt creation (new)

Use the validated standard-library generator rather than hand-writing JSON:

```sh
python3 tools/record_agent_measurement.py \
  --id art-05-pivot-observation-unique-20261106 \
  --kind milestone \
  --work-id UR-ART-4K \
  --source-sha FULL_40_CHARACTER_SOURCE_MAIN_SHA \
  --pr https://github.com/gamesbyian/UR-Recomp/pull/3101 \
  --actor YOUR_AGENT_IDENTIFIER \
  --milestone ART-05-PIVOTS \
  --outcome "Observed five-part GLB pivot alignment with real artifact check" \
  --remaining "Original source animation and integrated game art remain missing" \
  --evidence https://github.com/gamesbyian/UR-Recomp/pull/3101 \
  --dry-run
```

Remove `--dry-run` after inspecting the result. The generator writes one validated `docs/progress/daily/entries/<event-id>.json` file and refuses overwriting an existing file. Use a *real* exact 40-hex source SHA, not the template above. For a zero-credit research finding use `--kind research` and omit `--milestone`. To change expected effort, add `--job-id`, `--from OPT LIKELY PESS`, `--to OPT LIKELY PESS`, `--reason-type earned|re_estimate|regression` and a concrete `--reason`; review the replacement range against the previous active range. Distinct reviewer follow-ups can use `--state reviewed --reviewer INDEPENDENT_REVIEWER` only when actual evidence review occurred. All five agents use the same mechanism within their normal PR and need no additional schedule.

**Expanded milestone allocation:** 50 atomic deliverables now span ART-02/03/04/05, ONE-09, DATA-10, WIDE-07/09, FID-01 and QA-04. They carry **no new automatic credits**; original source and physical evidence determine whether events are recorded. The provisional backfill remains three source events. Only register new immutable milestone allocations for other parent criteria after a genuine deliverable is defined; don't subdivide for the sake of displaying a bigger score.

## Do this after material work, inside your existing PR or handoff

1. Read [the frozen partial milestones](milestones-v1.json). If your product work delivered or invalidated one of them, add **one JSON event** to `entries/`, following the example below. If you just investigated the problem or improved infrastructure, use `kind: research` or `infrastructure` **without milestone fields**. Do not create an event for every inconsequential edit or docs formatting change.
2. Pin `source_main_sha` to the exact known *main commit that the result's source/build is based on*, not your draft PR head. The event file is admitted to reporting only when merged into the Git history being evaluated. The `source_pr` and `evidence` must point at actual source-specific review, test or original execution; a link alone does not certify its content. An event with source SHA not reachable from current main fails closed.
3. Describe what *observably* happened and what is **still missing**. For partial milestone work use `milestone_state: provisional` until a separate reviewer has checked the source-specific evidence and recorded `reviewed_by` distinct from `recorded_by`. If a finding is overturned add a later `withdrawn` event for the same milestone, never erase the earlier record. No ART owner approval, USA event or QA gate is implied.
4. If you can justify a remaining-work change, attach an optional **prospective** `effort_update` with the active job ID, its exact current `from` three-point range and new `to` range. Choose `reason_type: earned`, `re_estimate` or `regression`. The calculator rejects stale/overlapping edits, completed jobs, duplicate event IDs and malformed ranges. Do not translate test/CI speedup into eliminated product work without a concrete causal cost reduction.
5. Run `python3 tools/daily_measurement.py --format markdown` and `python3 tools/daily_measurement.py --format json` on the same checkout, plus targeted `python3 -m unittest tests.unit.test_daily_measurement` (normal project CI policy still applies). If a receipt has a bad source revision, correct its provenance, **not** the validation guard. Report the total and the specific delta in the existing PR/issue handoff.

**Short required handoff, even when no JSON event is warranted:** `WORK-ID | CRITERION or none | real result | partial milestone or no credit | expected remaining effort change or not measured | evidence | next missing discriminator`. A reviewer can turn a provisional entry into an independently reviewed entry using a later event. The five scheduled agents already read `AGENTS.md` and `docs/HOURLY-AGENT-LINES.md`; neither has a permanent estimator role.

### Example entry (fill in actual source-specific values)

```json
{
  "schema": "ur-agent-work-measurement/1",
  "event_id": "art-02-source-fit-first-holdout-unique-20261106",
  "recorded_at": "2026-11-06T22:10:00Z",
  "source_main_sha": "0000000000000000000000000000000000000000",
  "source_pr": "https://github.com/gamesbyian/UR-Recomp/pull/3101",
  "kind": "milestone",
  "work_id": "UR-ART-4K",
  "recorded_by": "actual-author-identifier",
  "milestone_id": "ART-02-SOURCE-POSE-FIT",
  "milestone_state": "provisional",
  "outcome": "Exactly what source-integrated result can be reopened and reproduced",
  "remaining": "One still-missing authentic source/Windows/owner discriminator",
  "evidence": ["https://github.com/gamesbyian/UR-Recomp/pull/3101"]
}
```

This is a **template only**, not an achieved completion claim. The zero SHA must be replaced with a reachable actual main SHA. Filename is descriptive, not an authority. Do not place templates in `entries/` where they would be interpreted as real measurements.

For a non-credit research finding: change `kind` to `research`, omit `milestone_id` and `milestone_state`, and keep the evidence and remaining discriminator. For a separate reviewer acceptance: use the same milestone with a new unique event ID, later timestamp, `milestone_state: reviewed`, and a genuinely distinct `reviewed_by`.

### Optional effort revision

```json
{
  "effort_update": {
    "job_id": "ART-02",
    "from": [6, 20, 70],
    "to": [5, 18, 60],
    "reason_type": "earned",
    "reason": "Actual previously unfinished model-authoring task has been eliminated by reproducible integrated source results."
  }
}
```

The example is an *illustration*, not an approved effort deduction. `from` must equal the active frozen prior or prior verified change. Effort changes are **replacements**, never additive claims on top of a full parent item; shared tasks (`COMMON-*`) are modeled once. The prospective expected delta is the change in the arithmetic mean of the three values. Optional per-event `effort_update` is absent by default, leaving the prior untouched.

## Read the report correctly

```sh
python3 tools/daily_measurement.py --format markdown
python3 tools/daily_measurement.py --format json
python3 tools/live_progress.py --format json
```

The report binds its milestone-allocation methodology to an explicit SHA-256 fingerprint, so a new set of weights or criteria cannot silently masquerade as an unchanged historical estimator. Compare two daily percentages only when their `milestone_allocation_sha256` values match, or re-evaluate both snapshots with the same new allocation and report the methodological discontinuity.

The daily calculator produces an **engineering partial-work instrument**, not a replacement for a human's comprehensive source judgment until substantially more historical evidence has been entered. It starts from the *last frozen certified criterion inventory*; reviewed milestones add their exact fixed subweight and provisional milestones add half as a transparent planning point, with the full 0–100% provisional-subweight interval reported separately. Milestone sums are bounded by their original parent 45 units or 10 USA-event units, and credited parents are never counted twice. Provisional calibration **is a modelling convention**, not a statistically measured completion probability.

The forecast separately starts at the original prior for all unfinished criterion jobs, residual independent review and one-time shared blockers, then replaces per-job remaining cost only when an evidence-linked revision exists. It deliberately never subtracts arbitrary "units completed" from effort because product coverage units and engineering effort units are different quantities. A milestone can increase engineering coverage while remaining cost stays unchanged; that's a legitimate initial observation pending justified cost reassessment.

Existing v2 **formal** acceptance, physical H01–H07, owner art approval, 45 USA event passes and 12 Windows release gates remain unchanged. **No source/PR/agent can self-approve those through this ledger.**

## Evidence quality, chronology and limits

- The first three entries are **explicitly provisional historical backfills**, not new November 6 work or independent release proofs. Their job is to exercise the complete record-to-report loop. The rollout is **not** a comprehensive historical calibration; the displayed engineering percentage will start below previous informal ~62% judgment until other historical subtasks are source-reviewed and added. Never compare these two methodologies as a single continuous series without a methodological bridge/backcast.
- Reports are deterministic across the same inventory/model/events. Input files travel with source and remain diffable. A dated snapshot can be stored later once the instrument has enough coverage; do not create a second competing completion dashboard.
- For very large unknowns (original CPU parity, missing 1994 model/camera or physical owner sessions), forecast intervals remain judgmental, not measured labor-hours. CI queue time, runner memory, source proof and player acceptance are distinct axes.
- Avoid measurement bureaucracy: one relevant event per independently meaningful outcome, and bundle it with work already in flight. Agents can submit a no-credit handoff when evidence is inconclusive.

## What this pilot does not implement

Historical full-scope backfill; automated merged-PR semantic review; active agent-hours accounting; empirical calendar calibration; physical QA; and permanent subtask coverage for every open criterion. These are follow-ups under the already merged daily plan, not excuses to suppress an estimate. Prioritize evidence on large unfinished ART/WIDE/FID obligations before decomposing all 135 criteria.
