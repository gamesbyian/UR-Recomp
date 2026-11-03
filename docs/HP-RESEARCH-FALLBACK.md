# Owner HP missed-schedule research fallback (opt-in)

**Problem, November 1 2026 UTC:** GitHub's normal `schedule` delivery for the HP hourly research workflow has not been reliably observed since October 31 21:36 UTC. An eight-worker `workflow_dispatch` run completed successfully, so the runner and research code are known to work when GitHub *does* dispatch. GitHub cron is retained, not duplicated or disabled.

## Security advisory and local upgrade (November 2, 2026)

Windows Defender detected the downloadable owner installer ZIP as
`Trojan:Script/Wacatac.B!ml`. The detection is unresolved: neither a
false positive nor a real infection has been established. Do **not** restore
or allow-list the ZIP, change Defender settings, or disable scanning.
Distribution of that ZIP is withdrawn from current `main`; its former
bytes remain in Git history for forensic review. The already installed
90-minute fallback has completed real Windows research successfully, so
leaving it unchanged is supported.

### Optional in-place update without downloads or installer execution

The **repaired** installed 90-minute Python file from source
`edd4c3b5f06be3b54bddb12374fe1c5d75a8e795` and the tested 60-minute
file from `6268103310e132c795d74ed73e6474e78edacddd` differ by exactly
one text line. To avoid replacing a working task, the owner can apply that
single-line edit directly in normal **non-administrator PowerShell**. The
operation is fail-closed: full-script SHA-256 checks before and after,
one exact occurrence of the old line, symlink rejection, an atomic
same-directory file swap, and a retained original backup. It performs
**no GitHub dispatch**, network download, task registration or
execution-policy change. If Defender flags the installed Python file
itself, do not run this update; investigate the alert instead.

```powershell
$path = Join-Path $env:LOCALAPPDATA 'UR-Recomp\HPResearchFallback\hp_research_fallback.py'
$oldHash = '5756e12471d2241300915abbb06eabaef087007eb54f58e2ee557aa96e91d64b'
$newHash = '316cfe232d476fed5af65d0e72543b16f506150c638b428edb31df7a89db629d'
$found = (Get-FileHash -LiteralPath $path -Algorithm SHA256 -ErrorAction Stop).Hash.ToLowerInvariant()
if ($found -eq $newHash) {
    Write-Host 'The verified 60-minute pilot is already installed.'
} elseif ($found -ne $oldHash) {
    throw 'Unexpected installed source. No change made.'
} else {
    $file = Get-Item -LiteralPath $path -Force -ErrorAction Stop
    if (($file.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw 'Refusing redirected installed file.'
    }
    $oldLine = 'COOLDOWN = timedelta(minutes=90)'
    $newLine = 'COOLDOWN = timedelta(minutes=60)  # Measured HP idle-capacity pilot; still main-build priority.'
    $utf8 = New-Object System.Text.UTF8Encoding($false, $true)
    $source = $utf8.GetString([IO.File]::ReadAllBytes($path))
    if ($source.Split([string[]]@($oldLine), [StringSplitOptions]::None).Length -ne 2) {
        throw 'Unexpected cooldown line. No change made.'
    }
    $patched = $utf8.GetBytes($source.Replace($oldLine, $newLine))
    $sha = [Security.Cryptography.SHA256]::Create()
    try {
        $digest = ([BitConverter]::ToString($sha.ComputeHash($patched))).Replace('-', '').ToLowerInvariant()
    } finally { $sha.Dispose() }
    if ($digest -ne $newHash) { throw 'Unrecognized update. No change made.' }
    $temporary = "$path.60-minute-temporary"
    $backup = "$path.before-60-minute-pilot"
    if ((Test-Path -LiteralPath $temporary) -or (Test-Path -LiteralPath $backup)) {
        throw 'Existing temporary or backup file. Inspect before retrying.'
    }
    [IO.File]::WriteAllBytes($temporary, $patched)
    [IO.File]::Replace($temporary, $path, $backup)
    Write-Host 'Verified 60-minute source installed. Original backup preserved.'
}
```

Confirm the new SHA-256 with `Get-FileHash`, then run the **installed**
Python source with `--dry-run` to check the API without dispatching.
The already registered task will read the new file on its next run;
**no new installer or Task Scheduler edits are required**.

**Rollback** if added HP occupancy materially delays priority main Windows
builds: verify that the backup hashes to `$oldHash`, copy it to a fresh
temporary pathname in the same directory, and atomically replace the
installed file. Do not overwrite an unknown source or delete the backup
without verifying the hashes. The former installer remains retired while
Defender's finding is investigated.

The existing scheduled task runs every 15 minutes under the owner's
interactive logged-in account, using the authenticated `gh` client.
A locked screen is supported; a logged-out session is not. It uses no new
token or elevated rights.

### Physical HP confirmation: 60-minute pilot in operation

The owner confirmed the installed Python source's complete SHA-256 changed
from the previously verified 90-minute version
`5756e12471d2241300915abbb06eabaef087007eb54f58e2ee557aa96e91d64b`
to the reviewed 60-minute version
`316cfe232d476fed5af65d0e72543b16f506150c638b428edb31df7a89db629d`
after performing the bounded local one-line update without downloading
the quarantined ZIP. In Windows PowerShell, Task Scheduler reported
**LastRunTime November 2 14:50:50 MST, LastTaskResult 0, NextRunTime
15:05:05 MST** for the existing
`UR-Recomp HP Research Missed-Schedule Fallback` task.

The owner's actual `last-status.json` from **2026-11-02 21:50:47.884 UTC**
reported `decision=skip:recent-research`, `dispatched=false`,
`dry_run=false`, and latest research run
[#41522940636](https://github.com/gamesbyian/UR-Recomp/actions/runs/41522940636).
GitHub created that successful run at **20:50:57 UTC**, **59 minutes
50 seconds before** the task check. The 60-minute cutoff was therefore
working correctly, **not** an API timestamp anomaly. The next local
check window yielded successful
[dispatch #41534266867](https://github.com/gamesbyian/UR-Recomp/actions/runs/41534266867)
at 22:05:58 UTC, followed by successful dispatches
[#41544730154](https://github.com/gamesbyian/UR-Recomp/actions/runs/41544730154)
at 23:20:57,
[#41557456296](https://github.com/gamesbyian/UR-Recomp/actions/runs/41557456296)
at 01:05:59 November 3 (after a separate real cron run),
[#41565550358](https://github.com/gamesbyian/UR-Recomp/actions/runs/41565550358)
at 02:21:00 and
[#41573163644](https://github.com/gamesbyian/UR-Recomp/actions/runs/41573163644)
at 03:35:58. GitHub `workflow_dispatch` does not label its client:
this is strong timing evidence of local unattended operation plus a genuine
successful local Task Scheduler receipt, rather than definitive per-run
client attribution.

**Observed fallback-only dispatch intervals are about 75 minutes**, not
60, because a task checking every 15 minutes often tests just before the
60-minute boundary. The pilot's 192 cases/day ceiling assumes perfect
hourly eligibility and is **not** actual accepted throughput. Priority
Windows product [push #41481409141](https://github.com/gamesbyian/UR-Recomp/actions/runs/41481409141)
was created at 16:26:01 UTC while research
[#41480568113](https://github.com/gamesbyian/UR-Recomp/actions/runs/41480568113)
was occupying the HP. The product job reached its first recorded HP
output only at 16:30:42 after research completed, then passed at 16:35:33.
So the pilot has a real several-minute priority queue cost to monitor.
Do not describe priority queue delay as zero or relax full product QA.

No future Defender allowlisting or ZIP reinstallation is authorized by this
confirmation. Source hash identity and successful Task Scheduler status
are not malware-clearance verdicts.

## Dispatch algorithm

Each check uses `gh api` to read **the latest 30 runs for the specific research workflow**, the two other owner HP workflows, and exact current `main` SHA. It refuses to dispatch when: any research run is queued/active; an owner HP main build or benchmark is queued/active; latest research run started less than **60 minutes** ago (manual or schedule); latest run failed/cancelled on the **same main SHA** (stop retrying an unresolved source defect); the API response is missing/malformed/unauthorized; or a second process already holds the local lock. It performs second censuses of **research and both priority HP workflows** immediately before dispatch and aborts when any run changes, including a same-ID rerun's status, or a priority job becomes active. It then re-reads the exact `main` ref and refuses dispatch if it changed since the initial source-bound decision. All shared-status writes, including error reports, occur only under the acquired Windows process lock; a losing timer never overwrites its winner's result. If GitHub accepted a dispatch but the local receipt could not be persisted, stdout explicitly reports **dispatch accepted; inspect Actions before retry** rather than falsely asserting no dispatch. No per-PR or arbitrary SHA is accepted. A qualifying gap results in exactly one `workflow_dispatch` of `.github/workflows/owner-hp-seeded-2p-research.yml` on `main` through the owner's existing `gh` login. GitHub's own research workflow concurrency remains in force.

This is **fallback dispatch**, not an additional fixed-volume research schedule. It cannot guarantee that a late GH cron trigger will not arrive immediately *after* the final census; that race remains bounded by GitHub's same-workflow queue/concurrency group. Nor can it atomically pin `workflow_dispatch ref=main` against a branch update after the final ref read; the resulting Actions run's own `head_sha` and audited executable, not the pre-dispatch local receipt, establish the source that actually executed. The **60-minute pilot** was introduced after the physical HP completed a separate successful genuine cron research run and an additional recovered `workflow_dispatch` run on November 2, both with eight accepted seeds/32 real Windows guest processes and 9–10-minute total HP jobs. The previous 90-minute gap frequently left more than an hour of idle HP time during missed cron periods. With the same 15-minute task checks, a 60-minute window can raise the fallback-only theoretical upper bound from 8 cases/90 minutes to 8 cases/60 minutes (+50%), **only when actual cron remains missing and priority builds are idle**. Those maxima are not observed production throughput or a release-quality gain. The owner-only PR-comment dispatcher retains its separately implemented 90-minute guard. Keep a 360-second research horizon, main-branch identity checks, all same-source failure lockouts, re-read fences and HP Windows main-build/benchmark priority. Return the fallback to 90 minutes if a reproducible owner HP main-build delay greater than 10 minutes is attributable to the added fallback occupancy, if research starts overlap unexpectedly, or if the recovered cases per HP busy hour decline materially. The script does not reconfigure a task by itself; the owner can apply the optional source-hash-checked local edit above; no new installer is required. It also intentionally does not autonomously recover a persistent same-source science failure or claim release credit. An hourly agent may separately inspect a stopped run and fix the root cause.

## Seeded HP research acceptance-cost pilot (November 3, 2026)

The successful trusted-main [HP run #41549934055](https://github.com/gamesbyian/UR-Recomp/actions/runs/41549934055) occupied its single HP job from **00:02:37 to 00:11:15 UTC** (518 seconds). The actual eight-worker native game experiment ran for **193 seconds**, producing eight distinct positive seeds and 32 independent game processes. The other 325 seconds included full Windows build, package verification and general product QA. The owner Ninja/SDL3 cache was already healthy: Ninja configure+compile took 30 seconds, so more build tuning was not the obvious long pole.

A bounded **science-only routing pilot** now skips seven *unchanged* product acceptance steps when `hp_seeded_2p=true` and no explicitly nominated tournament acceptance is requested: Win32/default renderer (19 s); QA-09 root/pad navigation (27 s); QA-05 audio/restart/race overlap (73 s); package refresh (11 s); legacy migration (20 s); second main-menu boot (9 s); and startup-diagnostics fault matrix (5 s). These measured step durations total **164 seconds**. A naive no-interference projection reduces the same 518-second job to roughly **354 seconds**, but this is a counterfactual, **not measured improvement** or an acceptance result. Compare the next actual HP research run's step/job timings, source SHA, case count, compiler cache verdict and research outcome; account separately for GitHub queue delay and run-to-run variability.

The research route **still requires** the trusted owner HP/main/schedule-or-manual guard, fresh exact checkout and ROM verification, pinned toolchain, complete native compile, independently verified portable ZIP, clean extracted-package boot, the eight-worker/four-treatment source-bound science oracle, telemetry and artifact receipt. Three isolated offscreen *packaged* boot fanouts and the package-policy Python unit modules remain required by the normal hosted/HP product routes and explicit tournament nomination, not by recurrent science; see the measured second-stage economy below. Any negative or missing science artifact fails; no check is replaced by a stale source-independent game result. Normal hosted and owner HP product Windows smoke (`hp_seeded_2p=false`) retains **every original acceptance step**; nominated tournament runs also retain the full suite. Human physical H01–H07, QA-05/09 product certification, formal 0/12 release and 0/45 authentic-event evidence remain independent.

**Stop or revert** if a new science-only failure exposes a dependency on one of the skipped product checks, executable/package/provenance assurance degrades, source identity is unclear, real production Windows validation stops running on changed product sources, or run-time/accepted-seed throughput fails to improve over several comparable successful HP runs. Do not shorten or suppress the source-bound science oracle to make a metric greener. The 60-minute local fallback and its antivirus constraints are unchanged by this workflow pilot.

### Measured first post-merge science result and telemetry refinement

The first source-bound scheduled science execution after [merged #3079](https://github.com/gamesbyian/UR-Recomp/pull/3079) was [run #41591727338](https://github.com/gamesbyian/UR-Recomp/actions/runs/41591727338), **386 seconds of actual HP job occupancy**, with all eight distinct positive cases and 32 real processes in 212 seconds. The immediately preceding successful [run #41587760370](https://github.com/gamesbyian/UR-Recomp/actions/runs/41587760370) occupied **559 seconds**, including 210 seconds of science, for an observed **173-second / 30.9% shorter HP job**. This is a successful first field validation, not a controlled same-SHA comparison; source epochs and host load differ. The normal HP and hosted Windows product-smoke runs on merged #3079 also completed successfully ([HP #41589522366](https://github.com/gamesbyian/UR-Recomp/actions/runs/41589522366), [hosted #41589522306](https://github.com/gamesbyian/UR-Recomp/actions/runs/41589522306)).

One previous successful HP science job [#41549934055](https://github.com/gamesbyian/UR-Recomp/actions/runs/41549934055) printed valid CPU/memory summary readings but omitted the optional `hp-commit-pressure.csv` from its artifact, unlike both the immediate pre- and post-merge samples. A bounded repair separates CSV export from optional summary parsing and stages the file under a non-uploaded partial name before final rename, with up to three short attempts to tolerate a short-lived sampling write handle. Missing telemetry remains explicit and non-fatal; no process names or local error messages are uploaded. The normal product-build trigger now names actual HP provisioning scripts rather than monitoring-only files, so this repair does not itself spawn a redundant six-minute Windows product build. Recheck the next actual HP science artifact; a passing source/parse test cannot establish the intermittent race is eliminated.

### Second-stage trusted HP science acceptance economy (November 3, 2026)

The first optimized source-bound eight-worker scheduled science job [#41591727338](https://github.com/gamesbyian/UR-Recomp/actions/runs/41591727338) occupied **386 seconds** end to end; the successful serial rollback [#41608249955](https://github.com/gamesbyian/UR-Recomp/actions/runs/41608249955) occupied **408 seconds**. Both completed eight distinct positive native cases / 32 real native guest processes and kept the independent Windows portable package built and booted. Actual HP steps reveal another **three redundant preflight computations** that answer separate product/host-environment questions while adding no distinct source-bound *science* evidence:

- ClangCL standalone toolset preflight averaged about **6 seconds** in both runs; the source-generated game is subsequently configured and compiled for real with the same compiler, mandatory in science.
- Four product/package policy Python unit modules are executed as part of the 12-second canonical-ROM-and-package-contract step; science continues to rehash the canonical source ROM and independently assembles, archives, verifies and boots the actual same-run portable ZIP. These Python unit suites remain in full ready-PR CI and normal product Windows flows. The ROM verification has **not** been skipped. Exact net unit-only savings remain unmeasured.
- The three isolated packaged-boot fanouts each added **20 seconds**. Normal HP product Windows smoke and hosted Windows main/ready PR still own that particular multi-root packaged-app acceptance. Science keeps the separately verified, extracted packaged-game main-menu boot and executes 32 independent source/ROM-bound real guest processes in isolated private roots. Native 2P research does **not** claim to validate independent packaged-app startup variants or replace full Windows product QA.

The second-stage condition is **science-only and fail-closed**: `hp_seeded_2p=true` without an explicit `run_tournament_acceptance` may reuse only those three product-specific checks; ordinary product CI and nominated tournament runs execute every original preflight and package fanout. The compiler, source, ROM, ZIP checks, one extracted boot, four-way 2P oracle, eight workers, 360-second science budget, HP provenance guards, telemetry and artifact publisher are unchanged. The projected source-step savings are about **26 seconds plus the four Python modules**, not a measured run-level improvement. Because editing the reusable workflow triggers a **one-time hosted/HP full Windows product acceptance** on main, judge breakeven using actual subsequent science-run occupancy, source identity and tests, not skipped-step counts alone.

**Stop/revert** if the first actual optimized science job loses eight passing cases/32 real processes, source/checksum/ZIP or extracted boot verification becomes weaker, any independent packaged-app requirement is wrongly promoted from the science receipt into product QA, or ordinary HP/hosted/tournament steps stop running in a matching source-change acceptance. Preserve the product fanouts instead of moving them into the parallel game guest population; the failed 16-process experiment shows the host is already close to its useful CPU limit.

## Evidence and acceptance

Read `%LOCALAPPDATA%\UR-Recomp\HPResearchFallback\last-status.json` for an exact source SHA, latest run ID and whether the check actually dispatched. The script never emits raw CLI errors or credentials. Run `py -3 hp_research_fallback.py --dry-run` for a non-dispatch census, using the script from the installed directory. Exit code 2 fails closed and writes a bounded status when persistence is available. The script runs no game code itself; after GitHub completes, **audit the resulting Windows artifact** with `python -m tools.hp_science_archive_audit` and separately fetched run API JSON. A successful CLI API dispatch is *not* a successful run, and neither counts as original/native parity or release acceptance.

**Validation:** Synthetic `tests/unit/test_hp_research_fallback.py` covers cooldown, active jobs, main ref, failure lockout, API malformation, delayed schedule and same-ID rerun races, local mutex, receipt failure after accepted dispatch, the full-script SHA-256 old/new update identity, retired ZIP absence and dry run. Python logic can be exercised on Linux without installing or dispatching a Windows task. **Local patch execution and recurrence still require physical HP verification. No hosted test can establish that a Defender finding is a false positive.**
