# Daily progress and remaining-work estimation protocol

**Status:** proposed measurement operating contract, **not** an independently audited new completion score or a replacement release authority. **Prepared:** 2026-11-06. **Repository:** `gamesbyian/UR-Recomp`. **Snapshot reviewed:** current `main` at `770b2902549075a702afe1e3cc057b170d1ecf02`; frozen v2 source checkpoint `82111a8cbc690d729a16355d35fc35b3621200f3`. **Owner requirement:** a useful new estimate on any day, even after hundreds of merges since the last independent criterion audit. Never answer "too many commits since review, so no estimate."

**November 6 implementation checkpoint:** [PR #3219](https://github.com/gamesbyian/UR-Recomp/pull/3219) merged the operational first slice: source-linked per-agent entries, 25 bounded milestones across five active criteria, deterministic provisional engineering and relative-work output, tests and integration with the existing live reporter. All five installed shared-pool prompts were updated in-place with a low-overhead measurement handoff. **Still unimplemented:** full historical backfill, all-criteria milestone coverage, empirically calibrated task effort, and immutable dated daily snapshot publication. See [operational guide](daily/README.md). The original design below remains the long-term contract.

This is a *measurement specification and staged implementation plan*. The pilot implements source-linked partial-credit arithmetic; it does **not** claim calibrated delivery times, a complete current engineering estimate, or authoritative release approval. No real time data or owner approval should be inferred from the examples.

## 1. Four independent quantities, with an unambiguous answer every day

1. **Current engineering completion estimate** (`engineering_completion_estimate_percent`): the most plausible fraction of the fixed Windows-beta *deliverable* scope that has been genuinely implemented at the requested current `main` HEAD. Include defensible, nonbinary partial progress on unfinished criteria. Exclude CI/tooling as player-facing completion unless it directly satisfies an inventoried outcome. Label judgment, show range and sources. This estimate is **allowed and required** when a criterion audit is behind.
2. **Certified bounded criterion coverage** (`verified_coverage_percent`): compute from the unchanged 135-criterion, 4,500-unit `docs/progress/windows-beta-v2-inventory.json`; report its exact reviewed-source SHA and age. The last accepted number is a **historical measurement**, not guaranteed current minimum after later regressions.
3. **Remaining engineering effort** (`remaining_work_units`): expected unresolved effort, counted exactly once across criterion-specific implementation, shared blocker research/fixes, verification/review, and external acceptance work as defined by the current prior. Report realistic uncertainty. **Units are relative, NOT hours, days or probability-calibrated confidence.**
4. **Release acceptance** (`official_event_passes`, `official_release_gates`, `physical_hardware_status`, `owner_art_approval`): read only their authoritative ledgers and explicit evidence. Neither estimated completion nor a source test promotes these.

Additional, separate: `research_uncertainty_reduced`, `infrastructure_throughput`, `cycle_time`, `coverage_review_debt`, `unresolved_blocker_probability`. They help explain velocity; they are not automatic product-completion points.

**Default human headline:** "Engineering **X%** (range A–B), remaining **Y relative units** (planning range C–D), last bounded acceptance **V%** at SHA, USA **0/45**, formal Windows **0/12**" followed by **what physically changed, what was learned, and what caused numeric movement**. If exact HEAD source is inaccessible, cite last inspected HEAD, assign lower confidence and still produce a clearly qualified best-effort estimate from the available evidence. Never silently recycle old estimates as new ones.

## 2. Preserve the historical instruments and fix their blind spot

- **Do not modify** the 135 IDs, 45 event slots, original v2 weights, release ledger, baseline or historical audits merely to move a desired figure. `tools/atomic_progress_v2.py`, `tools/progress_interval_v2.py` and `tools/progress_receipt_ledger.py` remain formal source-bound acceptance instruments. Pending free-text receipts never earn formal credit. A physically accepted event still needs independent complete-event evidence. The 45 slots collectively supply 10% of frozen v2 scope, not 45 independent percent points.
- `tools/live_progress.py` currently emits `current_completion_estimate_percent: null` when there are unreviewed commits and exposes an uncalibrated `remaining_relative_work_units_prior_mean`. These values are useful for *formal audit debt* but **cannot serve as the engineering daily estimate**. The future daily evaluator must supplement, not spoof, these fields.
- The 2026-10-26 expert prior, `remaining-work-prior-v1.json`, includes task families, item overrides, four common prerequisites and 42 provisional-review obligations. `remaining-work-adjustments.json` supports evidenced changes to still-active item ranges. Its historical `ONE-03` higher estimate was properly retired when that criterion was independently admitted; keep that precedent.
- The previous owner-facing figures **56% formally bounded**, **~895.6 prior-only units**, **~62% judgment-based engineering** and **~830 engineering-adjusted units** are *different instruments*. **Do not connect them in a chart as if all numbers were generated by the same formula**. When migrating, rederive both endpoints using one newly frozen common method, or label a discontinuity.
- Formal score may stay constant while substantial intermediate work is completed. It may also increase from a retrospective audit without new engineering. Preserve both histories.

## 3. Source-linked incremental work ledger: record work while it happens

Implement a **small append-only evidence ledger** (proposed `docs/progress/daily/evidence/*.json` and materialized `docs/progress/daily/YYYY-MM-DD.json`, exact names subject to implementation review) and a standard, *brief* end-of-work handoff. No compulsory new PR per observation and no expensive CI solely for reporting.

Each qualified merged player-facing PR or accepted research outcome supplies, if relevant:

| Field | Purpose |
| --- | --- |
| `event_id`, `date_utc`, `main_sha`, `source_pr`, `work_id` | Stable identity, deduplication, exact provenance |
| `criterion_ids`, `shared_dependency_ids` | The specific fixed-scope obligations affected |
| `kind` | One of `player_implementation`, `verified_subtask`, `causal_discovery`, `negative_discovery`, `risk_reduction`, `acceptance`, `regression`, `rework`, `infrastructure`, `scope_change` |
| `outcome`, `source_receipts`, `limitations` | What worked, exact bounded evidence, and what did not |
| `remaining_before`, `remaining_after`, `unit_method_version` | Comparable forward-looking effort ranges; do not overwrite past beliefs |
| `confidence`, `assessed_by`, `independent_validation` | Provisional reasoning distinct from certified acceptance |
| `dependency_effects`, `shared_cost_id`, `affected_downstream_ids` | One-to-many blockers and anti-double-count rules |
| `time_data` (optional) | Measured active effort, CI queued/running, blocked/waiting, external wait, with source; missing is `null` |

A minimal handoff fits in 3–5 lines: work ID; affected criterion/subtask; observable change; *expected remaining-work change or "not measured"*; evidence link and next discriminator. A docs-only or CI-only PR with no credible causal closure must record **zero product completion**, however valuable its future throughput gain.

**Evidence inclusion:** ROM-free source/build tests, original emulator traces, GLB/PNG/PDF source-authenticated measurements, production Windows run, physical hardware witness, and independent reviewer notes remain separate grades. A passing synthetic test that detects a bug is meaningful but cannot be counted as a full product/hardware witness. Negative results can legitimately shrink uncertainty or rule out expensive branches without changing product coverage; the work saved must be justified, not assumed.

Avoid a permanent estimation agent or extra scheduled full-suite run. The existing five interchangeable shared-pool agents should attach these notes to their regular PR/issue handoffs. A daily aggregator reads them without blocking product work.

## 4. Represent partial engineering completion as real deliverables

For each **unfinished** fixed criterion with significant activity, decompose its *remaining work* into at most 3–7 meaningful, nonoverlapping milestones or acceptance-obligation components. Author milestones only when a specific source-independent outcome and a validating test can be named. Examples:

| Area | Intermediate outcome | What stays missing |
| --- | --- | --- |
| `ART-02` | Reusable authored five-parent, source-SHA-bound rig, exported pose assets and coherent wheel/frame pivots | Ground-truth original proportions, consistent full animation, integrated shipping model, approval |
| `ART-03/04/05` | 48 source-frame blue/red reference sequence, original printed multiview 2D landmarks, controlled saddle/fork mesh candidates | Validated exact silhouette/identity and owner signoff; no claiming recovered 1994 mesh |
| `WIDE-07` | Correct retained-history split-phase and negative HDMA termination tests | Complete actual moving-camera/tile parity across source and widened shipping viewport |
| `ONE-09/10`, `FID-01` | Source/native divergence located with reproducible causal test | Same-run complete race, result, progression, cold persistence and independent event acceptance |
| `QA-02..10` | Packaged source/hash-verified ROM-free ZIP and offline owner H01–H07 recorder | Physical two-pad/audio/4K/storage/recovery/soak/uncoached operator outcomes |

Each subtask has immutable `id`, parent criterion, a bounded deliverable, acceptance evidence, estimated work remaining by category and explicit dependencies. **Only source-verified delivered subtasks can earn engineering partial-credit.** A proposed research plan, PR in draft, discovered problem or model viewer alone may reduce some research uncertainty; it cannot count as final in-game art.

**Practical fractional score:** choose in advance `subtask_weight_units` for each parent criterion, summing to that criterion's fixed 45-unit or 10-unit weight. `complete` earns its exact subweight; `in_progress` earns zero until its next observable checkpoint is completed; unsupported or regressed evidence forfeits/discounts credit as explicitly recorded. The sum of already bounded-verified criteria plus delivered uncredited subtasks divided by 4,500 yields a reproducible *engineering progress candidate*. For shared tasks that cross many criteria, either allocate a stable portion to each affected subtask or report shared infrastructure readiness as a **separate axis**; never credit a shared prerequisite once for itself and again for each downstream event. **Independent event acceptance must not be awarded as a formal event by this fractional model.**

A second reviewer spot-checks the handful of largest or newest partial gains, not every merge. Where tasks are too poorly understood to decompose, retain a bounded qualitative estimate (e.g. 15–35% of *that* criterion's implementation complete), label lower confidence, and keep the audit trail. Avoid artificial single-decimal-point accuracy.

## 5. One comparable remaining-work model, updated prospectively

For each open **atomic subtask**, record three hypothetical **remaining** effort values `[optimistic, most_likely, pessimistic]` expressed in the existing relative-work units. This is a *forward-looking forecast*; time or sunk engineering effort already expended is not counted again. The current `remaining_work_forecast.py` uses `(low+mode+high)/3` as the per-job triangular mean, and deterministic per-job random streams for simulated percentiles. Preserve the interpretation and seeded reproducibility.

**Recompute from atomic remaining obligations:**

```text
Remaining = sum(open criterion subtasks)
          + sum(unresolved shared blockers ONCE)
          + remaining independent acceptance/review work
          + explicit external-dependent engineering preparation
          + expected bounded rework on already-completed but unqualified work
```

Never add full original item costs *and* the subtask breakdown for the same item. When decomposing, retire the original item forecast and replace it with the residual subtasks at the same time. Shared prerequisite dependencies must be DAG-linked, with 45 event verifications modeled as marginal event work *after* common parity, not 45 copies of the same common fix. An authentic source-to-native breakthrough should reduce the common-blocker remaining estimate **before** the first course is formally accepted, if independently reproduced.

Separate two reasons that remaining work changes:

- **Earned reduction:** a delivered subtask/accepted criterion/independently verified blocker has eliminated a specific remaining obligation. Do not relabel as another release gate.
- **Re-estimation:** a reproduced problem, new original reference, failed hypothesis, regression, or better scope information changes the effort estimate. Work may increase; call that **discovery**, not negative throughput. Record its previous and new [O,M,P], evidence, causal explanation and model version.

A source-authenticated original-art geometry measurement can lower future research uncertainty while leaving the work of generating a correct production model intact. A new owner likeness veto may raise remaining art work. Upstream CI and HP build improvements may increase feasible *iterations per day* but are **not work units earned** unless the estimate explicitly includes repeat validation labor and the cost change is measured.

**Suggested output decomposition:** implementation units; research/uncertainty units; independent review/qualification units; external/human validation preparation units; residual rework allowance. Report separate percentages for player functionality, final art, source fidelity and actual release qualification, without averaging acceptance gate counts into a fantasy release percentage.

## 6. Calibrate using actual completed work rather than PR counts

Create an immutable, at-least-20-completed-task calibration sample drawn from source-linked work across Windows, art, fidelity, UI and QA. Include representative successes **and** failed attempts; do not sample only green PRs. Capture:

- observable `opened_at`, `first_source_patch_at` if available, `ready_at`, `merged_at`, `first_verified_outcome_at`, `reworked_at` if any;
- CI execution and queue durations from actual workflow/job records, with hosted vs owner HP distinguished; avoid adding overlapping runs;
- actual timed agent/session effort **only if observed**, otherwise mark missing; GitHub PR wall-clock age is not agent labor time;
- task size/estimate at intake, current cumulative cost, estimate error, merge-to-acceptance latency, rework count, outcome and confidence;
- marked holidays/broken runner/external human wait as censored observations when appropriate.

Normalize to task families. Early on, compute rolling median actual delivery cycle time, bounded P20/P80, rework probability and effort-range calibration error. Avoid assuming five hourly agents produce five independent continuous worker-hours. The five-agent pool may collide, share CI and wait on source or owner validation. Estimate capacity from **observed independently earned subtask units per calendar day**, not merged commits or workflow jobs. Only translate relative work to calendar dates once enough same-family completed cases and waiting-time distributions exist; show the date's dependencies and sensitivity to human test/art approval and first-event parity. If the P80 is unconstrained, say so.

**Bias and stability test:** after each completed task compare its initial forecast with observed outcome and revise family priors only on documented samples. Prefer holdout/backtesting on past dated snapshots, never adjust last month's recorded assumptions in place so the forecast looks prescient.

## 7. Daily operator protocol, regardless of merge volume

Run once per local day or on demand. The cadence is a reporting convention, **not a mandatory extra hourly CI workflow**.

1. **Snapshot exact live HEAD**, current accepted inventory SHA, open PR/issue and relevant workflow results. Use `git rev-parse HEAD` or GitHub compare for exact provenance. If main advances during report, freeze one source SHA and state it; do not chase the moving head indefinitely.
2. **Collect changes since the previous daily snapshot** from already attached PR handoffs and evidence receipts. Identify affected outstanding criteria/subtasks and shared blockers. Classify `implementation`, `research`, `verification`, `regression`, `CI`, `documentation`, `retroactive` with bounded specific receipts; do not count all commits as production work.
3. **Update only affected subtask outcomes and residual [O,M,P] ranges.** Review the last daily work breakdown and unknowns; keep unchanged items at previous values. Where a new merged PR introduces product changes without available evidence, give a narrowly scoped provisional assessment and uncertainty; do **not refuse to estimate the whole project**.
4. **Recompute current engineering completion and total remaining work**, always using the same fixed scope and work-unit calibration version. Keep accepted score and release gates separately. Report changes by `earned`, `re-estimate`, `scope`, and `regression`.
5. **Produce a daily immutable snapshot**, anchored to `snapshot_main_sha`, prior snapshot, `inventory_sha`, estimation model version, assumptions, data quality and input provenance. If a later audit disputes a previous estimate, create an explicit `correction` on a new snapshot; retain the old one.
6. **Show a one-screen report first**, detail second. Daily change in completion (points), remaining effort units, movement by workstream, top three still-open dependencies, accepted USA events, physical Windows QA, and reasons for change. A newly discovered failure increasing effort is a valuable finding. Never promise a completion date without calibration.

**20-minute budget principle:** re-evaluate a bounded list of *materially affected requirements*, not every commit or all 135 criteria. If no short path exists, publish the best available current forecast and flag the relevant unresolved adjustment. The update must be possible even when 200 merges occur between formal audits.

### Required daily JSON (proposed v1 shape)

```json
{
  "schema": "ur-daily-engineering-estimate/1",
  "as_of_utc": "YYYY-MM-DDTHH:MM:SSZ",
  "snapshot_main_sha": "full-40-char-SHA",
  "prior_snapshot_sha": null,
  "frozen_criterion_contract": "32c62b80",
  "estimator_version": "daily-estimator-v1",
  "verified_reviewed_main_sha": "full-40-char-SHA",
  "verified_coverage_percent": 56.0,
  "engineering_completion_estimate_percent": null,
  "engineering_completion_range_percent": null,
  "remaining_relative_work_units": null,
  "remaining_work_range_units": null,
  "change_breakdown": {
    "earned_work_units": null,
    "re_estimated_work_units": null,
    "regression_work_units": null,
    "scope_change_units": 0
  },
  "release": {
    "accepted_usa_events": 0,
    "passed_windows_gates": 0
  },
  "changed_subtasks": [],
  "open_blockers": [],
  "source_receipts": [],
  "limitations": [
    "Example schema only; nulls indicate data to calculate, not current zeros"
  ]
}
```

On source-drift or absent measurements, the estimator should carry the historical formal score with `verified_reviewed_main_sha` but must **calculate the engineering estimate from the active subtask ledger**. Its result should be null only if the *entire project evidence record* is genuinely unavailable, not because a certification queue is longer than zero.

## 8. Calibration and trust rules

- **One immutable denominator per product scope**. Release quality, certified bounded criteria and engineering fractional progress are separate. Compare day-to-day *engineering estimates* only against snapshots computed using the **same estimator version**, or restate/backcast the previous snapshot under the new version and show method change explicitly.
- **No retroactive progress disguised as recent engineering.** Recovered old evidence is an acceptance correction, not today's implementation velocity.
- **No double counts.** Shared blockers, parent/subtask forecasts, overlapping accepted tests, duplicate PRs, multiple agent claims and repeated artifacts need unique IDs, contribution ownership and deterministic dedupe.
- **No falsely earned confidence.** A green CI test validates only its bounded assertion; one 3D source-shape IoU improvement is not recovered original art; Pages mobile reviewer work is not product runtime integration; speculative research does not equal shipped scope.
- **Conservative evidence model, useful estimate model.** Every day supply a concrete provisional estimate when enough source evidence exists, with ranges and assumptions; independent audit can run concurrently. The report should never stall merely because audit lags.
- **No fake precision.** Store exact machine arithmetic and provenance, display estimated product progress to ~1 percentage point and work units to roughly 5–10 units until family-level calibration supports finer resolution. The original 895.6 is a reproducible arithmetic output, not 0.1-unit real-world accuracy.
- **Regressions matter.** If latest tests invalidate a previously bounded claim, preserve historical audit record and explicitly record current regression risk or actual regression pending independent status amendment.
- **Owner-dependent approvals stay explicit:** final art likeness, actual human/controller/sound/4K Windows tests and real hardware faults cannot be inferred from hosted tests or visual inference.
- **No permanent new agent or cost explosion.** Implement in the existing Python standard-library toolchain, using already-owned GitHub Actions, stable shared work IDs and same review workflow.

## 9. Minimal implementation sequence, acceptance tests and stop rules

**P0: operational documentation and owner report.** Link this protocol in `docs/progress/README.md` and the five-agent shared board. Future reports must supply the two forward-looking estimates without waiting for full inventory certification. Does **not** modify the release ledger or add a scheduled workflow.

**P1: evidence and atomic-subtask schema.** Source-owned, append-only JSON; unique IDs, parent criterion contract, SHA links, orthogonal work kinds, no duplicate credit or negative unbounded efforts. Seed only materially active blockers: `ART-02/03/04/05`, `WIDE-07/09`, `FID-01`/`COMMON-PARITY`, physical QA. Tests: duplicate receipt rejection, no merge-count credit, source-hash mismatch rejection, draft vs merged distinctions, and nonshipping-art vs final-art distinction.

**P2: deterministic dual estimate calculator.** Preserve the frozen v2 inventory and existing expert-prior model while decomposing selected parent forecasts. Tests: all-open and all-complete bounds; completing a subtask decreases remaining units but awards only its assigned engineering partial weight; research result with no implementation credit may still revise [O,M,P]; source negative can raise work; a shared dependency finishes once; 45 FID events cannot gain formal admission; formally audited historical progress never changes from an engineering-only adjustment; repeat runs yield identical snapshots.

**P3: initial backward-compatible calibration and snapshots.** Independently curate 20+ real historical closed tasks and failed attempts. Set revision IDs; recalculate previous two daily snapshots with the *same* estimator and label estimates vs certification. Maintain one-line per-workstream movement and exact causal reasons. Tests: no fabricated labor hours, no date from uncalibrated units, no double-summed CI overlap.

**P4: low-overhead adoption.** Make the existing five-agent PR handoff template include the 3–5-line measurement fields, and run the fast estimator from the existing daily review or on demand. Only if useful should a CI summary be attached to the existing workflow; do not add 5×hourly reporting compute or another agent.

**Measurable success criteria:** (a) answering an update remains possible with 0, 5 or 500 unreviewed commits; (b) every reported day's percentage and remaining units trace to exact frozen source, model version and specific changed subtasks; (c) a zero-credit research PR does not inflate completion; (d) verified scope and physical/release gates never acquire unsupported credit; (e) backtesting finds and reduces systematic effort estimation bias; (f) daily report formation fits normal agent work and doesn't displace gameplay/art delivery.

## 10. Sources and adjacent authorities

- Frozen product inventory: [`windows-beta-v2-inventory.json`](windows-beta-v2-inventory.json); [atomic score](../../tools/atomic_progress_v2.py).
- Current formal source pointer: [`current-v2-review.json`](current-v2-review.json); [existing live reporter](../../tools/live_progress.py); [incremental candidate receipts](../../tools/progress_receipt_ledger.py).
- Expert effort priors and adjustments: [`remaining-work-prior-v1.json`](remaining-work-prior-v1.json), [`remaining-work-adjustments.json`](remaining-work-adjustments.json), [forecast tool](../../tools/remaining_work_forecast.py).
- Actual release authority: [`RELEASE-QUALITY-LEDGER.json`](../RELEASE-QUALITY-LEDGER.json); [original event census](../ORIGINAL-COURSE-EVENT-CENSUS.md); [physical Windows test plan](../WINDOWS-PLAYTEST-INSTRUCTIONS.md).
- Active shared-pool dispatch: [`HOURLY-AGENT-LINES.md`](../HOURLY-AGENT-LINES.md); [active queue](../WORK-QUEUE.md).
- Art evidence and limits: [HD racer reconstruction handoff](../HD-RACER-RECONSTRUCTION-DECISION-HANDOFF-20261103.md), [inverse graphics plan](../HD-RACER-INVERSE-GRAPHICS-PLAN.md), [unapproved canonical draft #2832](https://github.com/gamesbyian/UR-Recomp/pull/2832), [experimental stack #3124](https://github.com/gamesbyian/UR-Recomp/pull/3124).
- Compute and workflow integration: [collective qualification plan](../CI-COLLECTIVE-QUALIFICATION-INFRASTRUCTURE-PLAN-20261104.md) and [current implementation status](../CI-COLLECTIVE-QUALIFICATION-IMPLEMENTATION-STATUS.md).

**Do not treat this document as automatically introducing scope, implemented calculators, new release gates, a new scheduler or art approval.** It is the actionable contract for building useful day-by-day estimates from the real continuing work.
