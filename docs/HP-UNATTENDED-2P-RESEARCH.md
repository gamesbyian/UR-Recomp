# HP unattended research: source-bound seeded native 2P gameplay

**Purpose:** keep producing new, independently checkable real Windows game
evidence between source changes, without reserving a sixth LLM agent.
The five existing hourly generalist agents and their work queue are unchanged.

## Active first lane

[HP unattended seeded 2P gameplay research](../.github/workflows/owner-hp-seeded-2p-research.yml)
uses GitHub's UTC cron `11,41 * * * *` (twice hourly, 48 nominal
opportunities a day), plus optional owner manual dispatch. GitHub scheduled runs are
best-effort: they may start late or be dropped under load. Counting expected
cron slots is not equivalent to counting real source-qualified HP runs. This
is a deterministic bounded compute pipeline, not a guarantee that the PC
stays busy during every interval.
**Scheduling reliability probe (November 1 UTC):** GitHub's former hourly
`:17` cron yielded no new source-qualified research event after the
October 31 21:36 UTC four-worker success, despite several subsequent
eligible slots. The single cron minute is moved to `:41` as an isolated
re-registration experiment, following GitHub's documented ability to
reactivate schedules through a cron change. GitHub may still delay or drop
cron events; the first `:41` recovery **did** produce a true scheduled
8-worker success, [run #41348698814](https://github.com/gamesbyian/UR-Recomp/actions/runs/41348698814)
at `2fb65e7469053bca6e4e7b788669f8b0620d30ae`. Its Windows job log records
**8 distinct accepted cases, 32 real game processes, 218.953 seconds of
research and zero issues** under the standard 360-second wall limit, with a
ROM-free artifact uploaded. This confirms a positive source-owned collector
receipt, **not** a separately performed artifact byte audit, original/native
parity, or a release QA gate. The prior four-worker signed result is retained.

**November 1 half-hourly pilot:** after this successful scheduled run, add a
`:11` UTC opportunity to the existing `:41` cadence. This remains one
schedule expression, one serialized trusted-main HP job, the same Windows
build/package/QA checks and the same 360-second research wall limit. The
first scheduled job occupied about 9 minutes 20 seconds end-to-end, within
one nominal 30-minute interval. Twice as many cron slots do not guarantee
twice as many delivered runs: compare actual accepted cases/hour and total
HP occupancy, especially delays to priority main-push product builds. Stop
or revert to hourly `:41` if source-bound science fails or product builds
experience unacceptable queue delay. Cron re-registration can change schedule
delivery; this is an explicitly reversible capacity experiment.

It reuses the **canonical trusted-main HP Windows x64 build/packaging/QA**
rather than creating another compiler toolchain, backend or private
release-candidate producer. The exact original game ROM is read locally
and never uploaded.

Each run:

1. Checks out exact main on the known `hpmini-ur-recomp` runner; requires
   the exact repository/ref and a schedule or deliberate manual dispatch.
   PRs, forks, arbitrary labels and other branches cannot reach this job.
2. Compiles actual game using owner receipt-verified Ninja when available,
   or explicitly selects the retained Visual Studio fallback. The existing
   package integrity, main-menu, real Win32 renderer, QA-09 pad/menu,
   5/5 QA-05 audio/Restart, same-run race-result, user-state, and startup
   checks must pass *before* the scientific workload can run.
3. Runs **eight independent source-owned QA02 native 2P cohorts** with unique
   private root, controller input, rendered script, per-variant game process,
   user state and 128-KiB WRAM checkpoints. Every seeded case includes an
   actual treatment, identical replay, muted P1 and muted P2, using the
   same `tools/qa02_native_2p_seeded_endurance.py` four-way invariants
   already used for Linux native research. On Windows the source-owned
   guest is invoked directly with SDL offscreen/dummy instead of Linux
   `xvfb-run`. No comparison oracle is rewritten.
4. Uses an exact per-run seed namespace derived from GitHub's numeric run
   identity, with disjoint paired shard offsets. No manual prompt, guessed
   LLM scenario or repeated fixed control stream is needed. Per cohort:
   nominal 15-minute admissible budget, shortened by a strict 360-second
   research wall horizon for every genuine scheduled run or default manual
   dispatch. An explicitly owner-selected 600-second manual experiment may
   widen that horizon without changing `schedule`. Every cohort still has
   up to 12 unique plans and up to 90 seconds for
   each real Windows guest process. Eight cohorts execute concurrently and
   the coordinator **joins all** even if one fails. The canonical job's
   existing 45-minute deadline remains authoritative.
5. Validates all eight upstream source-owned signed receipts, same actual
   game executable/ROM/controller fixture/source identity, distinct
   control stream digests, replay determinism and both seat-response
   checks. Any missing or invalid cohort fails the research step; a
   failed real guest is *not* converted to a green campaign.
6. Emits an exact, hashed, ROM-free `hp-seeded-2p-research-receipt.json`
   inside the existing seven-day evidence artifact and a readable Actions
   job summary. The signed receipt remains authoritative; the summary
   reports bounded typed failure categories or, on a positive campaign,
   research-only cases/processes per minute and per-worker case counts.
   Neither raw ROM, guest log, gameplay dump, source build, user data nor
   proprietary game asset enters this receipt or summary. The existing
   strict upload allowlist includes this one JSON pathname only.

The scheduled runs do **not** claim physical pad testing, historical
emulator/original parity, full-course completion, or any of the 12 release
gates or 45 authentic USA original/native events. The four-way test is
native guest-input determinism and independent-seat reachability research.
Treat a failure as an exact reproducible seed and first failure to debug,
not a verified regression in authentic SNES behavior by itself.

## Manual-only 600-second throughput pilot: actual Windows result

The trusted-main [HP two-player research workflow](../.github/workflows/owner-hp-seeded-2p-research.yml)
offers `research_wall_seconds` of **360** (default) or **600** through deliberate
`workflow_dispatch`. The exact owner-only PR comment
`/ur-ci hp-research 600` also selects the 600-second manual trial using
the established global owner gateway and 90-minute deduplication guard;
`/ur-ci hp-research` without the argument uses 360. A genuine GitHub
`schedule` event and the [owner-installed local missed-cron fallback](HP-RESEARCH-FALLBACK.md)
always use **360**. The source-owned research validator rejects a scheduled
600-second horizon. Neither route bypasses the canonical Windows Ninja/VS
build, exact portable package, QA-09, QA-05, race, user-data or launcher
checks, nor the 45-minute job cap.

**First real 600-second positive result, November 1 UTC:** [owner-authorized
Windows run #41286835360](https://github.com/gamesbyian/UR-Recomp/actions/runs/41286835360)
is an actual `event=workflow_dispatch` at
`6c23045ee244ded3c5d51365b6448bbe54a15392`, not a scheduled
delivery. Its Windows job and all required package/QA checks passed.
Eight independent workers each accepted **two distinct four-process
treatment/replay/P1-muted/P2-muted cases**: **16 accepted seeds, 64 actual
Windows game processes, 0 research issues, 452.282 seconds** of research.
The 600-second budget is included in the source-owned SHA-256 receipt
*self-hash*, not independently signed by a trusted key. The retained
[76-member ZIP artifact #13076395136](https://github.com/gamesbyian/UR-Recomp/actions/runs/41286835360/artifacts/13076395136)
was inspected for member CRCs, unique names, matched Actions run/source
identity and independently checked ROM-free executable/binding SHA-256;
no ROM or player-data upload and no physical/original-parity acceptance.

**Measured capacity:** research-phase accepted cases/minute were **2.123**
for the 600-second trial, versus **2.149** for [the earlier 360-second
manual run #41272207332](https://github.com/gamesbyian/UR-Recomp/actions/runs/41272207332)
which accepted 8 cases/32 real processes in 223.390 research seconds.
The actual raw Windows job log spans were approximately **784 seconds
(16 cases, 73.5 cases per whole HP job-hour)** versus **578 seconds
(8 cases, 49.8 per whole HP job-hour)**: **+47% observed overall
yield**, largely by amortizing the same ~5–6-minute build/QA overhead.
These are **different source SHAs, distinct seed populations and run
epochs**. This is an operational observation, **not** a controlled
same-source speedup or proof that a third case per worker is admissible.
The first 600-second run's GitHub API job `completed_at` showed a
one-hour discrepancy relative to its last actual UTC job step and raw
log across the local DST fallback. Use the verified raw log/step times,
not the inconsistent run-level end, for this bounded comparison;
[CI timing correction PR #2979](https://github.com/gamesbyian/UR-Recomp/pull/2979)
tracks the measurement issue separately.

**Decision:** retain **360** for cron/default/local fallback. Any
promotion to a longer unattended horizon requires repeated source-bound
science with acceptable priority Windows-build queue latency, accurate
CPU/memory and whole-job accounting, a same-source comparison where
practical, and genuine reliable automatic dispatch. Do not change the
five hourly LLM agents or create a second HP job. No 1/45 original/native
USA event, physical pad verification or formal release gate follows
from seeded *native-only* research.

## Read-only offline archive audit

`python -m tools.hp_science_archive_audit --artifact windows-native-smoke.zip --run-json hp-run.json` independently checks the retained GitHub Actions ZIP CRCs, safe member paths, source/run/event identity in the separately retrieved **GitHub Actions run API JSON**, the collector's self-hash and eight/four-cohort seed/case totals, the ROM-free PE's **actual bytes** against both the source-owned science candidate and the independent Windows PE binding, and the stock input/script file digests from this checkout. Nothing is executed or uploaded, and source/fixture differences fail closed. Fetch the run's actual `/repos/gamesbyian/UR-Recomp/actions/runs/RUN_ID` API JSON independently; the ZIP by itself **cannot prove** that GitHub delivered a scheduled event.

The SHA-256 research receipt is **self-hashed, not cryptographically signed by an independent trusted key**. Even a valid archive audit cannot reconstruct the 4-way guest traces absent from the retained compact summary or grant 1/45 genuine original/native events, physical gamepad checks or release gates. The audit's positive result must be paired with the trusted Actions run and its successful producer job. Compare historical run rates only with labeled source/epoch, total wall time and accepted cases; never describe the four-to-eight worker shift as an eight-to-sixteen-case gain.

## Safeguards and source integration

- The main HP source-push workflow remains separate and automatic, including
  its independent concurrency scope; normal product and agent CI are not
  canceled by this scheduler. GitHub routes one job at a time to the
  owner's single self-hosted runner. A research run may queue behind a main
  build or briefly delay a newly arrived main build; its eight-cohort
  research horizon and overall timeout bound this effect. Do not add a second HP
  runner or let scheduled execution check out PR source.
- Work roots are unique per run ID/attempt. Research never mutates the
  installed Ninja, SDL3 cache, repo history, machine settings, service
  credentials or player files. It refuses stale scratch output.
- The scientific post-QA phase is opt-in only through `hp_seeded_2p=true`;
  the regular HP/hosted/main/PR routes remain unchanged.
- The normal `tools/ci/check_windows_smoke_upload_policy.py` continues
  to require exactly one artifact upload and an exact literal allowlist.
  Research failures remain visible. This is not a production QA waiver.

## Decisions and next research lanes

1. **Eight-worker manual and scheduled proof acquired; twice-hourly cadence is a new pilot:** the owner-authorized [manual HP run #41264488130](https://github.com/gamesbyian/UR-Recomp/actions/runs/41264488130) at source `d6eb79fc` completed all Windows package/QA checks and **eight real concurrent source-owned cohorts**, accepting **8 distinct cases, 32 Windows guest processes in 200.718 s** with zero collector issues. The retained [four-worker genuine scheduled run #41244390541](https://github.com/gamesbyian/UR-Recomp/actions/runs/41244390541) at different source `fde3b6c3` accepted **8 cases, 32 processes in 289.282 s**; it is **not** an eight-worker throughput receipt. Research-only observed rates were **2.391 vs 1.659 accepted cases/min**, a 44.1% increase, but unlike-source cohorts and changed parallel load preclude a controlled speedup claim. The manual eight-worker canary does **not** prove true GitHub `schedule` delivery. The actual eight-worker `event=schedule` job #41348698814 establishes schedule delivery and positive source-owned eight-worker execution; the artifact still requires independent byte-level review. Twice-hourly frequency must earn its own measured yield and priority-queue observations. Neither trial earns gameplay/physical-pad/release credit.
2. **Value measurement:** quantify distinct valid seeded cases/day, actual
   native Windows process count, host CPU/memory/time, whether source/fixture
   identity was maintained, failure reproducibility and delay to normal
   HP builds. More CPU usage without distinct accepted cases is not a win.
3. **Other deterministic candidates:** reusable read-only native title/2P
   journey permutations, Win32 C++ codec/storage fault-injection at safe
   private scratch roots, source-bound screenshot atlas verification and
   original/native first-causal-divergence experiments. Do not copy Linux
   pipelines with `/proc`/xvfb/glibc dependencies into Windows unchanged.
   Move each only after a minimal physical HP acceptance and shared artifact
   contract. The existing seven-family cumulative-research coordinator
   remains manual-only due its earlier scheduler/admission failures;
   silently switching its costly Linux job matrix to HP is not appropriate.
4. **When to stop or reschedule:** halt an unproductive/failing research
   population, an actual credential/ROM provenance mismatch, evidence
   leakage, source-binding error or repeated priority-build delay.
   Revert only the scheduled caller or set its cron less frequent. Maintain
   the five agents and existing authoritative release pipeline.

The [HP throughput tracking issue](https://github.com/gamesbyian/UR-Recomp/issues/2885)
owns measured rollout figures, while `docs/WORK-QUEUE.md` owns shipping
priority. This page is an execution contract, not a rival work queue.
