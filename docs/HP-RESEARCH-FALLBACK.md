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

## Dispatch algorithm

Each check uses `gh api` to read **the latest 30 runs for the specific research workflow**, the two other owner HP workflows, and exact current `main` SHA. It refuses to dispatch when: any research run is queued/active; an owner HP main build or benchmark is queued/active; latest research run started less than **60 minutes** ago (manual or schedule); latest run failed/cancelled on the **same main SHA** (stop retrying an unresolved source defect); the API response is missing/malformed/unauthorized; or a second process already holds the local lock. It performs second censuses of **research and both priority HP workflows** immediately before dispatch and aborts when any run changes, including a same-ID rerun's status, or a priority job becomes active. It then re-reads the exact `main` ref and refuses dispatch if it changed since the initial source-bound decision. All shared-status writes, including error reports, occur only under the acquired Windows process lock; a losing timer never overwrites its winner's result. If GitHub accepted a dispatch but the local receipt could not be persisted, stdout explicitly reports **dispatch accepted; inspect Actions before retry** rather than falsely asserting no dispatch. No per-PR or arbitrary SHA is accepted. A qualifying gap results in exactly one `workflow_dispatch` of `.github/workflows/owner-hp-seeded-2p-research.yml` on `main` through the owner's existing `gh` login. GitHub's own research workflow concurrency remains in force.

This is **fallback dispatch**, not an additional fixed-volume research schedule. It cannot guarantee that a late GH cron trigger will not arrive immediately *after* the final census; that race remains bounded by GitHub's same-workflow queue/concurrency group. Nor can it atomically pin `workflow_dispatch ref=main` against a branch update after the final ref read; the resulting Actions run's own `head_sha` and audited executable, not the pre-dispatch local receipt, establish the source that actually executed. The **60-minute pilot** was introduced after the physical HP completed a separate successful genuine cron research run and an additional recovered `workflow_dispatch` run on November 2, both with eight accepted seeds/32 real Windows guest processes and 9–10-minute total HP jobs. The previous 90-minute gap frequently left more than an hour of idle HP time during missed cron periods. With the same 15-minute task checks, a 60-minute window can raise the fallback-only theoretical upper bound from 8 cases/90 minutes to 8 cases/60 minutes (+50%), **only when actual cron remains missing and priority builds are idle**. Those maxima are not observed production throughput or a release-quality gain. The owner-only PR-comment dispatcher retains its separately implemented 90-minute guard. Keep a 360-second research horizon, main-branch identity checks, all same-source failure lockouts, re-read fences and HP Windows main-build/benchmark priority. Return the fallback to 90 minutes if a reproducible owner HP main-build delay greater than 10 minutes is attributable to the added fallback occupancy, if research starts overlap unexpectedly, or if the recovered cases per HP busy hour decline materially. The script does not reconfigure a task by itself; the owner can apply the optional source-hash-checked local edit above; no new installer is required. It also intentionally does not autonomously recover a persistent same-source science failure or claim release credit. An hourly agent may separately inspect a stopped run and fix the root cause.

## Evidence and acceptance

Read `%LOCALAPPDATA%\UR-Recomp\HPResearchFallback\last-status.json` for an exact source SHA, latest run ID and whether the check actually dispatched. The script never emits raw CLI errors or credentials. Run `py -3 hp_research_fallback.py --dry-run` for a non-dispatch census, using the script from the installed directory. Exit code 2 fails closed and writes a bounded status when persistence is available. The script runs no game code itself; after GitHub completes, **audit the resulting Windows artifact** with `python -m tools.hp_science_archive_audit` and separately fetched run API JSON. A successful CLI API dispatch is *not* a successful run, and neither counts as original/native parity or release acceptance.

**Validation:** Synthetic `tests/unit/test_hp_research_fallback.py` covers cooldown, active jobs, main ref, failure lockout, API malformation, delayed schedule and same-ID rerun races, local mutex, receipt failure after accepted dispatch, the full-script SHA-256 old/new update identity, retired ZIP absence and dry run. Python logic can be exercised on Linux without installing or dispatching a Windows task. **Local patch execution and recurrence still require physical HP verification. No hosted test can establish that a Defender finding is a false positive.**
