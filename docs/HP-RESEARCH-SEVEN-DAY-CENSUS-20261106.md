# HP research: full seven-day delivery and uptime census (2026-11-06)

**Observation:** independently executed read-only on the authorized owner HP at approximately `2026-11-06T10:43Z`. Exact settled UTC creation window: **`2026-10-30T00:00:00Z..2026-11-05T23:59:59Z`** (seven full calendar days). This complements the shorter [November 2–5 baseline](HP-RESEARCH-RELIABILITY-AUDIT-20261106.md), and is the requested weekly operational repeatability check under the [November 4 infrastructure plan](CI-COLLECTIVE-QUALIFICATION-INFRASTRUCTURE-PLAN-20261104.md).

## Source and collection integrity

The existing, reviewed manual collector `tools/ci/hp_research_delivery_census.py` was fetched by immutable trusted-main commit **`4d4fb7df25a11041f7412c1dbd1d220b88c1b123`**, confirmed to be Git blob **`3a9d8356ca2f53f2a29dfb3f176069883cd4afef`** both remotely and with local `git hash-object`, and executed only after these checks succeeded. The temporary source file was deleted in cleanup. Command arguments: `--start 2026-10-30T00:00:00Z --end 2026-11-05T23:59:59Z --workers 4`. It exited **0**, runtime **21.70 seconds**.

The collector verified the complete GitHub API inventory of one exact trusted-main research workflow (ID `402410752`), source SHA/attempt/event, all latest-job records and expected `hpmini-ur-recomp` runner identities, valid UTC job timestamps, no duplicate IDs, and an end-of-job re-read of the run population. It makes authenticated GitHub REST GET requests only. It did not dispatch a run, monitor the PC persistently, execute a game, alter a service or configure hardware.

## Measured full-week results

| Measure | Complete seven days | Meaning |
| --- | ---: | --- |
| Research workflow runs | **86** | 20 `schedule`, 66 `workflow_dispatch`; the latter does not identify its caller |
| Outcomes | **83 success, 3 failure** | Complete latest-attempt outcome population; not all failures are the same cause |
| Valid started/completed research job intervals | **655.17 minutes** | 6.50% of 10,080 calendar minutes, this one research workflow only |
| Total run-creation-to-job-start delay | **301.75 minutes** | Includes offline time and other causes, not necessarily blocked CPU |
| Largest single queue | **291.61667 minutes** | [Scheduled run #41660067090](https://github.com/gamesbyian/UR-Recomp/actions/runs/41660067090), November 3 |
| Other 85 queues combined | **10.13333 minutes** | Median/p90 queue both **0.06667 minutes** (about 4 seconds) |
| Long queues exceeding 30 minutes | **1** | Manual host-availability investigation only; no automatic resource-contention attribution |

**Actual UTC creation-day counts:** October 30 **0**, October 31 **3**, November 1 **6**, November 2 **17**, November 3 **18**, November 4 **21**, November 5 **21**. The October 30 zero count is *not* proof that the HP was off for that entire day; workflow setup, source eligibility, dispatch policy or other causes may explain it.

The original separately measured **November 2–5** subset still exactly reconciles: **77 runs**, **14 schedule/63 dispatch**, **76 success/1 failure**, **513.48 job-interval minutes**, and **301.35 queue minutes**. The added October 30–November 1 portion consists of nine runs (six schedule, three dispatch), seven successes and two failures, **141.69** more observed job-interval minutes and only **0.40** more queue minutes, subject to displayed rounding. The change from four-day 8.91% to seven-day 6.50% is partly the larger period and sparse initial days, *not* demonstrated performance degradation.

## Three failures: distinct classifications

| Failed run | UTC creation | Actual failed step and evidence | Classification |
| --- | --- | --- | --- |
| [#41189610338](https://github.com/gamesbyian/UR-Recomp/actions/runs/41189610338) | Oct 31 09:39:57 | `HP bounded independent offscreen package boot fanout` exited **2**; log says `HP_BOOT_FANOUT=refused_event`, after earlier build/package checks passed | **Source/event policy refusal**, not demonstrated research execution or host crash; review the historical exact-SHA workflow gating before assuming a current defect |
| [#41223647258](https://github.com/gamesbyian/UR-Recomp/actions/runs/41223647258) | Oct 31 17:15:35 | `HP unattended real two-player seeded gameplay research` returned `HP_SEEDED_2P_RESEARCH=research_failure seeds=0 windows_processes=0` | **Research execution failure**, root cause not identified by this brief job receipt |
| [#41599042074](https://github.com/gamesbyian/UR-Recomp/actions/runs/41599042074) | Nov 3 07:50:59 | Same real research step returned failure with zero accepted seeds/Windows processes and 16 recorded issues | **Separate research execution failure**, already documented in the four-day audit |

These failures are **not** attributable to the later November 3 unexpected shutdown merely because the overall week contains that incident. Don't rerun unchanged failed source to cosmetically improve the success rate; check source/issue evidence or a distinct corrected commit first.

## Windows availability evidence, independently inspected

Read-only Windows **System** log query for EventLog **6005/6008** and Kernel-Power **41** since October 28 found two unexpected-shutdown incidents:

- **October 30:** Kernel-Power 41 at **02:18:46Z**, EventLog 6008 and 6005 at approximately **02:18:56Z**. Event 6008 refers to an unexpected prior shutdown at **19:46:30 local October 29**. Kernel-Power `BugcheckCode=0`, `SleepInProgress=0`, `LongPowerButtonPressDetected=false`. `PowerButtonTimestamp` was nonzero, but these fields alone do not establish an accidental button press or a PSU/firmware cause.
- **November 3:** Kernel-Power 41 at **19:53:55Z**, EventLog 6008/6005 at approximately **19:54:04Z**, preceding the long-queued job's **19:56:11Z** start. Event 6008 cites prior unexpected shutdown **08:19:03 local November 3**. Again `BugcheckCode=0`, `SleepInProgress=0`, `LongPowerButtonPressDetected=false`. The prior [four-day audit](HP-RESEARCH-RELIABILITY-AUDIT-20261106.md) contains the time-zone caveats.

At the November 6 check, OS `LastBootUpTime` was **2026-11-03T19:53:55Z**, with **no newer 41/6008 reboot** seen. Windows runner service `actions.runner.gamesbyian-UR-Recomp.hpmini-ur-recomp` was **running** and configured for automatic start. The existing Scheduled Task `UR-Recomp HP Research Missed-Schedule Fallback` was **Ready**, `LastTaskResult=0`, with last execution **2026-11-06T10:35:35Z** and next **10:50:50Z**. Its bounded last-status receipt said **`skip:recent-research`, `dispatched=false`, `dry_run=false`**. This proves one positive status readback, not uninterrupted continuous monitoring. The machine currently reports `Central Standard Time`, while the project uses `America/Edmonton`; all quantitative comparisons here use GitHub and Windows UTC records, and no OS time-zone change was made.

## Operational decision and next discriminator

**Keep** the present 60-minute cooldown, 15-minute fallback task cadence, main-only source fences, active-product priority, fail-closed same-SHA research locks and existing single runner. Do **not** replace the scheduler, increase research volume, reset the PC, loosen security, change power/BIOS settings or automatically roll back to 90 minutes based solely on the 291.62-minute shutdown-related queue. The prescribed rollback trigger is a separately proven **greater-than-ten-minute product-build delay caused by fallback**, which this source population has not demonstrated.

If a third unexpected shutdown occurs, conduct owner-controlled hardware/power/UPS/firmware/EventLog diagnosis before automation changes. If a future HP queue exceeds 30 minutes, compare Windows boot evidence, service state and genuine priority product jobs; never assign its duration to CPU saturation by default. Repeat this complete source-bound census on a **new settled UTC seven-day window** when operationally useful, retaining failure IDs and actual run statuses rather than optimizing success percentages.

**Limits:** GitHub job-intervals are not active CPU, power use, billing, saved time, or release qualification. The inferred failure classes use only recorded step outcomes, not private gameplay contents. No 0/12 Windows release or 0/45 original/native event admission changed; no P1 cross-PR source authorization or P2 speedup claim follows.
