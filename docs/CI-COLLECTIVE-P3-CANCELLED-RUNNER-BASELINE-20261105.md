# P3 CI baseline: measured cancelled-job compute (2026-11-05)

**Status:** bounded, read-only baseline for [collective qualification plan](CI-COLLECTIVE-QUALIFICATION-INFRASTRUCTURE-PLAN-20261104.md), **not** a P2/P3 success claim, new CI gate, product acceptance or permission to run PR code on the owner's HP.

**Exact selection:** all GitHub Actions runs **created** from `2026-10-29T08:14:05Z` through `2026-11-05T08:14:05Z` inclusive; repository `gamesbyian/UR-Recomp`. Read-only collection used the owner's already authenticated `gh api`, with no runner/cron changes. All run listings for the three job-timed workflows below were paginated completely. The measurement read each cancelled run's `/actions/runs/{id}/jobs?per_page=100` response, rejected incomplete or inverted job timing, and summed `completed_at - started_at` for **every started job within a cancelled run**, including jobs that had already succeeded when the overall run was cancelled. A separate column counts time only for jobs whose individual conclusion was `cancelled`.

## Three fully enumerated high-cost workflows

| Workflow (Actions workflow ID) | Runs | Cancelled runs | Cancelled runs with at least one started job | Started jobs inside cancelled runs | Runner-min in cancelled runs | Runner-min in jobs concluded cancelled |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Windows Visual Atlas PR validation (`393802512`) | 149 | 67 | 47 | 125 | 88.85 | 71.52 |
| QA-05/09 Windows candidate (`379623240`) | 142 | 36 | 34 | 34 | 111.15 | 111.15 |
| Windows native smoke (`374411662`) | 62 | 8 | 8 | 8 | 43.38 | 43.38 |
| **Total, these workflows only** | **353** | **111** | **89** | **167** | **243.38** | **226.05** |

All runner-minute columns are observed nonnegative job spans from GitHub's job timestamps, rounded to two decimal places. The 17.33-minute difference between total time in cancelled runs and time in individually cancelled jobs includes successful or otherwise concluded jobs inside a subsequently cancelled workflow. **No assumption that the entire 243.38 minutes is waste, avoidable or billable is warranted.** Neither Windows billing multipliers nor subscription cost are assigned here. All jobs in the same run are summed; parallel job spans therefore count as separate runner-minutes, as intended. Missing/unstarted jobs contribute no measured span, not a fabricated duration.

There were **22 cancelled runs without any started job** among these three workflows. A count of 111 cancelled *workflow runs* thus materially overstates how many started-job cancellations occurred. Conversely, the 89 cancelled runs with started jobs consumed 243.38 runner-minutes, which a run-count-only report misses.

## Wider exact-window run census

| Workflow | Runs in seven days | Observed run conclusions |
| --- | ---: | --- |
| Project tooling unit tests (`369800124`) | 1,180 | Latest 1,000 only: 641 success, 289 cancelled, 70 failure |
| Repository hygiene (`374916710`) | 1,205 | Latest 1,000 only: 849 success, 144 cancelled, 7 failure |
| Windows Visual Atlas PR validation (`393802512`) | 149 | 66 success, 67 cancelled, 16 failure |
| QA-05/09 Windows candidate (`379623240`) | 142 | 63 success, 36 cancelled, 42 skipped, 1 failure |
| Windows native smoke (`374411662`) | 62 | 52 success, 8 cancelled, 2 failure |
| HP seeded 2P research (`402410752`) | 72 | 69 success, 3 failure |

These six exact workflow IDs produced **2,810 runs** in the selected interval. GitHub's Actions list pagination returned only the newest 1,000 records for each of the two high-volume workflows; their exact `total_count` fields were cross-read using `per_page=1` in the same window. The additional 180 tooling and 205 hygiene runs were **not outcome-classified**. Consequently **at least 544 cancellations** were directly seen across six workflows; this is a lower bound, never the full seven-day cancellation rate. The three job-timed workflows' counts are complete under the same selection.

## Reproducibility and decision rules

1. Obtain each workflow's run list through `GET /repos/gamesbyian/UR-Recomp/actions/workflows/{workflow_id}/runs?created=2026-10-29T08:14:05Z..2026-11-05T08:14:05Z&per_page=100&page=N`, incrementing `N` while comparing retrieved count to `total_count`. Never infer an interval-wide conclusion from a list capped at 1,000.
2. For each `conclusion=cancelled` run, read `GET /repos/gamesbyian/UR-Recomp/actions/runs/{run_id}/jobs?per_page=100` and fail if `total_count > 100` without fetching further pages. Include each job with real `started_at` and `completed_at` in the total. Record cancelled-*job* time separately from total started time in cancelled-*workflow* runs.
3. Compare only source-compatible candidate campaigns with identical test intent, actual executed-case identities, hosted OS, all relevant acceptance checks, exact source/PE/package envelopes and measured queue delays. **Do not** claim that cancellation totals would be eliminated by batching, or skip required ready-state tests.
4. Preserve the existing protective `cancel-in-progress` rules until matched evidence proves an alternative saves runner-minutes without letting obsolete source consume a scarce runner. The Visual Atlas expensive model-export job already waits for ready PRs; Windows candidate validation also gates its full hosted Windows job on ready state.
5. P1 source verification is still under review in [PR #3146](https://github.com/gamesbyian/UR-Recomp/pull/3146), specifically whole-composite tree membership and file-mode integrity. Do not promote shared builds or install the five-agent prompt addendum from this observational baseline.

**Prior sample reconciliation:** the existing read-only [CI runtime report run #41983549429](https://github.com/gamesbyian/UR-Recomp/actions/runs/41983549429) covered 300 most recent runs across roughly 12 hours, with `window_census_complete=false`. The exact-window numbers here use separately enumerated workflow IDs and are not extrapolated from that sample. The sample is useful for step-level bottleneck analysis but does not replace the seven-day baseline above.

**Next P3 measurement:** quantify seven-day *started* job-minutes for the cancelled tooling/hygiene population using bounded UTC-day partitioning so the 1,000-item API cap cannot obscure losses. Then compare any real P2 shared-qualification experiment against matching existing-workflow runs. In the absence of comparable candidates, retain this baseline without inventing a benchmark.
