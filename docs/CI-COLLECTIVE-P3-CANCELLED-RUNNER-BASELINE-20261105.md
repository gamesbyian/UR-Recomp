# P3 CI baseline: measured GitHub cancelled-job intervals (2026-11-05)

**Status:** bounded, read-only baseline for [collective qualification plan](CI-COLLECTIVE-QUALIFICATION-INFRASTRUCTURE-PLAN-20261104.md), **not** a P2/P3 success claim, new CI gate, product acceptance or permission to run PR code on the owner's HP.

**Exact selection:** all GitHub Actions runs **created** from `2026-10-29T08:14:05Z` through `2026-11-05T08:14:05Z` inclusive; repository `gamesbyian/UR-Recomp`. Read-only collection used the owner's already authenticated `gh api`, with no runner/cron changes. Run totals were independently read for each of six workflow IDs; **cancelled** run populations were exhaustively enumerated using the API's `status=cancelled` filter, avoiding the unfiltered 1,000-result pagination limit. The measurement read each cancelled run's `/actions/runs/{id}/jobs?per_page=100` response, rejected incomplete job inventories, excluded *and counted* inverted timestamp intervals, and summed `completed_at - started_at` for all **valid-timestamp started jobs within a cancelled run**, including jobs that had already succeeded when the workflow was cancelled. A separate column counts time only for jobs whose individual conclusion was `cancelled`. Values are a lower bound where job intervals were invalid.

## Five completely enumerated cancellation populations (sixth has zero)

| Workflow (Actions workflow ID) | Runs | Cancelled runs | Cancelled runs with valid started jobs | Valid started-job spans | Observed runner-min in cancelled runs | Job-interval min in individually cancelled jobs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Project tooling unit tests (`369800124`) | 1,180 | 308 | 248 | 382 | 295.02 | 294.43 |
| Repository hygiene (`374916710`) | 1,205 | 164 | 155 | 155 | 67.23 | 67.23 |
| Windows Visual Atlas PR validation (`393802512`) | 149 | 67 | 47 | 125 | 88.85 | 71.52 |
| QA-05/09 Windows candidate (`379623240`) | 142 | 36 | 34 | 34 | 111.15 | 111.15 |
| Windows native smoke (`374411662`) | 62 | 8 | 8 | 8 | 43.38 | 43.38 |
| HP seeded 2P research (`402410752`) | 72 | 0 | 0 | 0 | 0.00 | 0.00 |
| **Total, six selected workflows** | **2,810** | **583** | **492** | **704** | **605.63** | **587.71** |

All runner-minute columns are nonnegative measured job spans, rounded to two decimal places. The **17.92-minute** difference between total time in cancelled workflows and time in individually cancelled jobs includes completed or otherwise concluded jobs inside subsequently cancelled workflows. **It is not sound to call the 605.63 observed job-interval minutes waste, avoidable, active-runner time, or billable.** Neither Windows billing multipliers nor monetary cost are estimated. Parallel started jobs count as separate runner-minutes, as intended. A cancelled run with no valid started job contributes zero observed compute rather than a fictitious duration.

There are **91 cancelled workflows without a valid started-job span** in this census. This illustrates why raw cancellations and runner cost cannot be conflated: 583 workflow cancellations correspond to 492 with valid started jobs, containing 704 individually timed job spans.

**GitHub timestamp anomaly:** the 308 cancelled tooling runs contained **114 job intervals with `completed_at < started_at`**, excluded from both minute columns and from the 382 valid job count. The other four cancelled-workflow populations contained zero inverted intervals under the same collection; hygiene likewise contained zero. One identified example, job `127124818627`, was a **skipped** `draft-syntax` job recorded as started `2026-11-05T08:03:26Z` and completed one second *before* that at `08:03:25Z`. That example does not prove all 114 are skips, nor that the missing time would be material. The reported **605.63 job-interval minutes are conservative** under the valid-interval rule, and are not a measured billing or active-compute total. No started job lacked a completion timestamp in the fully fetched tooling/hygiene cancellations.

## Full seven-day outcome census

| Workflow | Runs created in window | Status/conclusion distribution at read time |
| --- | ---: | --- |
| Project tooling unit tests | 1,180 | 789 success, 82 failure, **308 cancelled**, 1 in progress |
| Repository hygiene | 1,205 | 1,029 success, 10 failure, **164 cancelled**, 2 in progress |
| Windows Visual Atlas PR validation | 149 | 66 success, 67 cancelled, 16 failure |
| QA-05/09 Windows candidate | 142 | 63 success, 36 cancelled, 42 skipped, 1 failure |
| Windows native smoke | 62 | 52 success, 8 cancelled, 2 failure |
| HP seeded 2P research | 72 | 69 success, 3 failure |

The first two workflows exceeded GitHub's 1,000-result cap for unfiltered run lists. To resolve it, **separate `status`-filtered `total_count` queries were used**, rather than extrapolating the latest-1,000 sample: tooling **308 cancelled** (versus at least 289 in the truncated sample) and hygiene **164 cancelled** (versus at least 144). Each fully enumerated cancellation subset was below 1,000, so all affected job receipts could be read. These outcome counts are a snapshot of API state when read; the three in-progress runs may subsequently complete and change conclusion, so rerun the same time-bounded status census before relying on it for a future experiment.

## Timing precision: job intervals versus actual steps

The API's `job.started_at` can precede the first recorded step by a substantial interval. A directly inspected successful tooling job, `127490523824` in [run #42097281045](https://github.com/gamesbyian/UR-Recomp/actions/runs/42097281045), had job `started_at=2026-11-05T19:47:46Z` but its first `Set up job` step began at `19:54:08Z`: **a 382-second difference**. This observation is outside the frozen seven-day run census and serves as a timing-semantics control. Whether those seconds are queue time, API representation or a billable interval is unverified.

The first step-aware `tools/ci_cancelled_runner_census.py` collector emitted a **schema 2** receipt with both the original job-interval seconds and separately measured valid step-duration seconds, plus the job-to-first-step gap, missing step evidence and invalid interval counts. These additional fields require a **fresh collection**. They are **not retroactively available** from the historical v1 tally of 605.63 job-interval minutes. Both measures remain observational, not proof of cloud billing or recoverable CI capacity. An incomplete or anomalous step record is reported separately and never imputed as zero actual CPU usage.

For reproducibility, the manually invoked collector accepts the fixed UTC bounds and optionally writes JSON and Markdown:

```sh
python3 tools/ci_cancelled_runner_census.py \
  --start 2026-10-29T08:14:05Z \
  --end 2026-11-05T08:14:05Z \
  --json-out ci-cancelled-census.json \
  --markdown-out ci-cancelled-census.md
python3 -m unittest tests.unit.test_ci_cancelled_runner_census
```

**Authentication on Windows and other local hosts:** the collector uses a non-empty `GH_TOKEN` or `GITHUB_TOKEN` environment variable first. If neither is present, it reads the existing GitHub CLI credentials once through `gh auth token` without printing the token. If neither source works, it **fails before any API request** rather than silently falling back to the 60-request/hour anonymous limit. On the owner's HP workstation, GitHub CLI is installed but those two environment variables were absent when checked; this fallback makes the documented manual invocation workable with the existing authenticated CLI. The collector makes read-only GitHub requests; it does not schedule checks, execute PR code or dispatch runners. It bounds pagination, worker count and the calendar window and rejects duplicate/incomplete API source sets. To measure actual avoided compute, further pair a candidate with equivalent workloads and capture source, relevant cases, job steps, queueing and billed runner telemetry where available.

## Attempt-scoped job inventories: a newly verified GitHub API limitation

GitHub's [List jobs for a workflow run](https://docs.github.com/en/rest/actions/workflow-jobs) endpoint defaults to `filter=latest`: it returns only the most recent attempt's jobs. `filter=all` includes earlier attempts of the same workflow run. On a live, read-only recheck of the original **308 cancelled tooling workflows**, **one run had `run_attempt=2`**: run `41244488125`. Its latest-attempt jobs endpoint returned **two** job rows (cancelled `unit` and skipped `draft-syntax`); the all-attempt endpoint returned **four** (also the earlier successful unit job and skipped syntax job). No additional job-duration totals were inferred from this observation.

**Interpretation:** The original 605.63 GitHub job-interval-minute baseline and later 494.22 step-minute snapshot use the GitHub API's default **latest-attempt** population. They do not describe all earlier reruns. The collector now explicitly requests and records `--attempts latest` (default, for historical comparison) or `--attempts all` (an alternate, separately labelled full-attempt census). These populations must not be interchanged in a savings comparison. The run-count snapshot still counts each workflow-run ID once, irrespective of the number of attempts. A newer all-attempt census must read every returned job and publish independent totals rather than guessing added minutes from the observed extra jobs.

The updated schema 3 parser also accepts offset-qualified and fractional-second GitHub job/step timestamps while maintaining **strict UTC Z search-window bounds**. GitHub's official job REST schema demonstrates offset-bearing step timestamps. Each fetched job carrying a `run_id` is checked against the requested run; mismatched job ownership is rejected.

## Follow-up schema-v2 recorded-step measurement (separate November 5 read)

The same frozen `created_at` interval was queried again on November 5, after the collector acquired step-level timing fields. This was an **independent later API snapshot** using read-only authenticated GitHub queries, with complete status-filtered cancelled-run and per-run job inventories. It is **not** a retroactive modification to the original 583-cancellation v1 snapshot.

| Workflow | Cancelled workflows in later snapshot | Valid job intervals | Jobs with valid step evidence | GitHub job-interval minutes | Sum of valid recorded step minutes | Job-start to first-timed-step gap minutes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Project tooling | 308 | 382 | 197 | 295.02 | 234.02 | 2.75 |
| Repository hygiene | 164 | 155 | 106 | 67.23 | 31.60 | 1.45 |
| Windows Visual Atlas | 66 | 125 | 112 | 88.85 | 78.55 | 1.73 |
| QA-05/09 Windows candidate | 36 | 34 | 30 | 111.15 | 107.08 | 0.48 |
| Windows native smoke | 8 | 8 | 8 | 43.38 | 42.97 | 0.13 |
| HP seeded research | 0 | 0 | 0 | 0 | 0 | 0 |
| **Total** | **582** | **704** | **453** | **605.63** | **494.22** | **6.54** |

The Visual Atlas cancelled-run count was **66 in this later read**, versus **67 in the original frozen snapshot**; the observed job-interval sum remained 88.85 minutes. No particular reason for that one-run reclassification has been established. Preserve both readings and their collection times instead of silently rewriting historical outcomes.

The **111.41-minute arithmetic difference** between job intervals and recorded step durations is not a measure of saved time. Only 453 of 704 jobs with valid GitHub job intervals had usable timed steps. Missing step data, reporting semantics, zero-length steps and inter-step gaps all affect completeness. The 6.54 minutes of job-to-first-step gap was computed only for jobs with a valid first step; it is **not a full explanation** of the 111.41-minute difference. Summing step spans is likewise **not guaranteed billable or active CPU time**, and may include setup/post-processing steps. Invalid/inverted job and step timestamps were excluded from their respective totals; missing observations must never be imputed as zero execution.

For prioritization, the larger observed cancelled **step-duration** buckets were: tooling `unit` 216.47 minutes, QA-05/09 `windows-candidate / windows` 107.08 minutes, Visual Atlas `experimental-real-model-export` 48.27 minutes, Windows native `windows` 42.97 minutes, and repository `hygiene` 31.60 minutes. These are targets for *measurement*, not permission to skip required checks. Keep comparison cohorts source-matched and preserve exact acceptance conditions and `cancel-in-progress` safeguards until an actual, separately qualified P2 experiment proves a benefit.

The full evidence, individual job-name breakdown and limitations were also recorded in [P3 discussion](https://github.com/gamesbyian/UR-Recomp/pull/3156#issuecomment-6670947983). This report establishes the observational baseline and nothing about individual-source acceptance, Windows PE/ZIP identity, HP PR-code authorization or measured recoverable compute.

## P3 source-methodology correction: schema 4 (qualification pending)

An independent source inspection of P3 head `ff3553f8a1b1853cdc6948b1a97aa4b144e62c1b` identified three incomplete-evidence cases that were not covered by the earlier green hosted tests. The proposed schema **4** correction and new synthetic negatives make the manual collector refuse or separately count them:

1. A job with `completed_at` but **no `started_at`** now increments a distinct `missing_starts` counter rather than disappearing into the unstarted-job category. Both timestamps absent still mean no started interval was observed; it is never proof of zero actual resource use.
2. A step whose timestamps fall outside the parent job or overlap an earlier accepted step is now counted as an invalid step interval and **excluded** from the sum of valid step durations. One-sided step timestamps are also counted as incomplete evidence. The first-step gap only uses valid retained steps.
3. After reading every selected cancelled run's job inventory, the source again fetches the complete bounded cancelled workflow-run population and compares run IDs, attempts, head SHAs, created times and conclusions. Any change aborts, even when the run-count total stays constant. This reduces, but does not eliminate, the nontransactional GitHub REST snapshot race.

The source changes are **not** a retroactive remeasurement. Retain the original **605.63 observed GitHub job-interval minutes** and the later **494.22 recorded-step minutes** as their own historical source populations and earlier counting rules. A future schema-4 collector result must be labelled with its **new retrieval date**, attempt policy, schema, exact fixed UTC window, missing/invalid evidence counters and tested source SHA. A changed step total after excluding out-of-job or overlapping intervals is a *methodology correction*, not a measured resource saving.

Independent follow-up review of the corrected exact PR SHA and the usual complete hosted unit/hygiene checks remain required before merging this collector. This does not relax P1 whole-tree trust, Windows/native packaging acceptance or HP unmerged-code restrictions.
## Reproducibility and decision rules

1. Obtain each workflow's exact seven-day `total_count`. For large workflows, separately read `GET /repos/gamesbyian/UR-Recomp/actions/workflows/{workflow_id}/runs?created=2026-10-29T08:14:05Z..2026-11-05T08:14:05Z&status=cancelled&per_page=100&page=N`, advancing pages until the filtered `total_count` is retrieved. Read additional `status=success`, `failure`, `skipped`, `in_progress`, etc. counts to reconcile outcome totals; do not treat an unfiltered 1,000-row sample as complete.
2. For each `conclusion=cancelled` run, read `GET /repos/gamesbyian/UR-Recomp/actions/runs/{run_id}/jobs?per_page=100`, reject incomplete pagination, and count but **exclude** missing/reversed timestamp intervals. Include every valid timed started job regardless of its own conclusion. Record cancelled-*job* time separately from total started time in cancelled-*workflow* runs. Do not impute missing time, including from skipped jobs with reversed timestamps.
3. Compare only source-compatible candidate campaigns with identical test intent, actual executed-case identities, hosted OS, all relevant acceptance checks, exact source/PE/package envelopes and measured queue delays. **Do not** claim that cancellation totals would be eliminated by batching, or skip required ready-state tests.
4. Preserve the existing protective `cancel-in-progress` rules until matched evidence proves an alternative saves runner-minutes without letting obsolete source consume a scarce runner. The Visual Atlas expensive model-export job already waits for ready PRs; Windows candidate validation also gates its full hosted Windows job on ready state.
5. P1 source verification is still under review in [PR #3146](https://github.com/gamesbyian/UR-Recomp/pull/3146), specifically whole-composite tree membership and file-mode integrity. Do not promote shared builds or install the five-agent prompt addendum from this observational baseline.

**Prior sample reconciliation:** the existing read-only [CI runtime report run #41983549429](https://github.com/gamesbyian/UR-Recomp/actions/runs/41983549429) covered 300 most recent runs across roughly 12 hours, with `window_census_complete=false`. The exact-window numbers here use separately enumerated workflow IDs and are not extrapolated from that sample. The sample is useful for step-level bottleneck analysis but does not replace the seven-day baseline above.

**Next P3 measurement:** before any claimed savings, compare a genuinely useful, P1-verified P2 collective candidate against the actual same-case conventional Windows checks with source/PE/ZIP identities and started runner-minute measurements. Re-run an identical frozen-window query to track settled conclusions for the three still-in-progress runs. A per-job reason audit should distinguish never-started cancellations, requested cancellations and successful jobs before cancellation; there is no evidence yet that all 605.63 observed minutes can be eliminated. In the absence of compatible candidates, retain this measured baseline without inventing a benchmark.
