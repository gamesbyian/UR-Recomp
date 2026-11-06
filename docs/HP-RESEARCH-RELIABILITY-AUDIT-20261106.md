# HP research delivery, queue and host-recovery evidence

**Recorded 2026-11-06 UTC.** Four complete UTC days: **2026-11-02T00:00:00Z through 2026-11-05T23:59:59Z**. This is a read-only operational measurement under [P5 of the collective infrastructure plan](CI-COLLECTIVE-QUALIFICATION-INFRASTRUCTURE-PLAN-20261104.md), not new host instrumentation, release acceptance or approval to run unmerged code on the HP.

## Source and population

Live GitHub REST run census: `GET /repos/gamesbyian/UR-Recomp/actions/workflows/402410752/runs?created=2026-11-02T00:00:00Z..2026-11-05T23:59:59Z&per_page=100&page=1`. The returned `total_count` and enumerated run rows both equalled **77**. The matching `/actions/runs/{id}/jobs?filter=latest&per_page=100` inventories were fully read for all 77 runs, and 77 valid started/completed jobs were found on runner `hpmini-ur-recomp`. Source times are offset-aware GitHub timestamps; group UTC dates from the original `created_at` UTC string. A first exploratory PowerShell date-conversion grouping wrongly reported **72** and was corrected with an exact string/date census; do not reuse that earlier figure.

| Observation | Four-day measured value | Meaning and limit |
| --- | ---: | --- |
| Completed research workflows | **77** | 14 `schedule`; 63 `workflow_dispatch`. A workflow dispatch event does **not** identify which client sent it. |
| GitHub run conclusion | **76 successful, 1 failed** | One run failure does not mean a host failure. Do not count it as successful science. |
| Started/completed HP job spans | **513.48 minutes** | 91.67 minutes on scheduled runs; 421.82 on dispatch runs, subject to rounding. This is 8.91% of four-day **calendar time**, and is **only this workflow's observed job intervals**, not total PC usage, active CPU or a bill. |
| Total observed enqueue-to-job-start delay | **301.35 minutes** | A single queued scheduled run contributed **291.62 minutes**; the other 76 jobs combined contributed just **9.73 minutes**. |
| Queue delay distribution | **median 0.07 min; p90 0.07 min; maximum 291.62 min** | This is source run `created_at` to HP job `started_at`; it includes offline/availability, priority work, orchestration and other causes, not automatically CPU contention. |
| HP job span distribution | **median 5.93 min; p90 9.27 min** | Job `completed_at-started_at`; no claim about billed or available capacity. |
| Research run creation spacing | **median 75.0 min; p90 approximately 104.98 min** | Not a guaranteed cadence, and not evidence that each dispatched workflow came from the fallback. |

**Schedule-delivery context:** the checked-in research workflow currently lists `cron: '11,41 * * * *'` and `cancel-in-progress: false` in a single source-bound HP concurrency group. This defines nominal opportunities, not guaranteed delivered executions. GitHub observed 14 scheduled and 63 workflow-dispatch events in the four-day cohort. One installed local fallback task, `UR-Recomp HP Research Missed-Schedule Fallback`, runs approximately every 15 minutes and uses a completed-run **60-minute** cooldown plus active-job, source and priority safeguards. The observed approximately 75-minute recurring spacing is consistent with a 15-minute poll crossing a 60-minute cooldown, but individual dispatch attribution must be supported by a local decision/status receipt.

## Long queue: recovered host outage, not proven science starvation

Scheduled [workflow run #41660067090](https://github.com/gamesbyian/UR-Recomp/actions/runs/41660067090) was created **2026-11-03 15:04:34 UTC**, its HP job started **19:56:11 UTC** (**17,497 seconds / 291.62 minutes** later), and it **succeeded** at **20:02:14 UTC**.

Read-only Windows System event evidence on `DESKTOP-TRH1VBI` showed unexpected-shutdown EventLog **6008** and Kernel-Power **41**, with a boot/6005 event at **2026-11-03 19:54:04 UTC**, roughly two minutes before the queued job started. Event 6008 reports prior unexpected shutdown at **08:19:03 local Nov 3**. The PC currently reports `Central Standard Time` (UTC-06:00 on Nov 3), making the prior shutdown about **14:19:03 UTC**, and indicating a roughly **5h35m unavailable interval** until boot. This aligns with the GitHub queued-job observation. A second unexpected-shutdown/Kernel-Power event was present on **October 30** in the checked Windows System log.

The November 3 Kernel-Power record had `BugcheckCode=0` and `SleepInProgress=0`; that is **not a proved power-supply failure, thermal issue, Windows defect or user action**. No exact cause has been established, and the current Windows timezone must not be assumed to have been identical at the historical event without additional evidence. The queued job did resume after the host returned, so the available evidence does **not** justify blaming fallback dispatch, disabling research, changing workflow concurrency, or triggering the plan's >10-minute **fallback-attributable product-delay** rollback threshold.

**Time-zone caution:** the machine's Windows timezone was read as `Central Standard Time`, whereas the project's user-facing time basis is `America/Edmonton`. The installed fallback code uses `datetime.now(timezone.utc)` and normalizes GitHub timestamps to UTC; there is **no observed UTC scheduler decision failure caused by this difference**. Retain UTC in logs and acceptance; changing the PC's time zone would be a separate owner-visible OS setting change, not part of this audit.

## The failed science run is a different failure class

Dispatch [#41599042074](https://github.com/gamesbyian/UR-Recomp/actions/runs/41599042074), created **2026-11-03 07:50:59 UTC**, reached the HP immediately and its real research step failed. The actual job log records `HP_SEEDED_2P_RESEARCH=research_failure`, approximately **358.734 seconds** of research, **0 accepted seeds**, **0 Windows game processes**, and **16 issues**. This is a research/tooling failure on that exact source, not the unexpected-shutdown incident later the same day. Other science workflows subsequently succeeded; don't silently reclassify this run as green or retry unchanged failure evidence to improve a rate.

## Verified fallback recovery chain

Local task status at **2026-11-06 01:20:47 UTC** recorded `decision=dispatch:missed-research-window`, `dispatched=true`, then GitHub created [run #42143234781](https://github.com/gamesbyian/UR-Recomp/actions/runs/42143234781) at **01:20:58 UTC**. That workflow executed on **`hpmini-ur-recomp`** from **01:21:01** to **01:26:11 UTC** and completed **success**. This is one verified decision-to-success recovery, not proof of continuous perfect availability. The installed scheduled task reported `Ready` and last result `0` on the readback; no local service, task, security or workflow setting was changed.

## P5 operational decision and repeatable review

1. **Keep the existing trusted-main, single-runner workflows and 60-minute fallback cooldown unchanged for now.** There is no source-grounded >10-minute fallback-attributable priority product delay in this cohort. Continue giving product Windows builds priority over optional research.
2. **Investigate host uptime/power recovery separately** if unexpected Kernel-Power/6008 events recur. Read System Event 41, 6005, 6008, bugcheck flags, supported hardware telemetry, current runner service and Task Scheduler status; inspect outlet/UPS/firmware AC-return setting through an owner-controlled maintenance procedure. Never change BIOS, power, security, timezone, restart services or reboot automatically from this document.
3. **Queue triage:** when a scheduled HP job waits over 30 minutes, check runner online/OS boot/shutdown evidence and long-lived priority jobs before concluding the fallback caused contention. A completed source-bound run after an outage is recovery evidence, not admission of all interrupted jobs or product release approval.
4. **Weekly reproducibility:** pin exact `created` UTC bounds; use fully paginated authenticated GitHub run/job inventories with explicit `filter=latest`; validate counts/IDs, job timestamps, runner identity, event/conclusion, all attempts where relevant, and source. Report total started-job minutes separately from queue, scheduled vs dispatch and successful/failed runs. Re-read installed fallback receipt and HP machine state where authorized. Separate **nominal cron slots** from actually observed events and never infer API caller identity from `workflow_dispatch` alone.
5. **Preserve safeguards:** no execution of PR/fork code on owner HP, no additional heavyweight local broker, no weakening product packaging or original/native gates. The [existing fallback runbook](HP-RESEARCH-FALLBACK.md) and [plan](CI-COLLECTIVE-QUALIFICATION-INFRASTRUCTURE-PLAN-20261104.md) govern any further tested change.

## Evidence links

- [Owner HP research workflow](../.github/workflows/owner-hp-seeded-2p-research.yml), source-guarded main-only caller.
- [HP fallback runbook](HP-RESEARCH-FALLBACK.md) and [intensive trusted-main route](HP-UNATTENDED-INTENSIVE-ACTIONS-20261104.md).
- [Infrastructure plan issue/PR evidence](https://github.com/gamesbyian/UR-Recomp/pull/3141#issuecomment-6674203297) and [the exact confirmed fallback completion](https://github.com/gamesbyian/UR-Recomp/pull/3141#issuecomment-6674239530).
