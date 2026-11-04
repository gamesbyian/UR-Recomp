# HP safe job broker: initial constrained pilot (2026-11-03)

This experimental local broker is for **read-only, source-bound** work dispatched
through Desktop Commander by ChatGPT tasks. It is NOT an unattended code executor,
self-hosted GitHub Actions replacement, or authorization to run arbitrary PR code.

## Contract

- `tools/hp_safe_job_broker.py` offers `submit`, `run-once`, `diagnose`, and `status`.
- `submit` requires a 40-character commit on the locally fetched
  `origin/main` ancestry, an agent identifier 1..5 and an allowlisted kind.
- `repo-status` reads the submitted immutable commit's title and hash.
- `agent-selector` runs the repository's selector for an agent only if the
  dedicated checkout is clean and HEAD equals the requested trusted commit.
- Job payloads cannot specify shell commands, repository paths, environment,
  arbitrary script names, or execution timeouts. Two concurrent pipe readers
  retain at most 64 KiB per stream, killing the direct child on overflow and
  recording a failed receipt. Direct subprocesses time out after 45 seconds.
  Git and the advisory Windows tasklist probe also use bounded capture
  (64 KiB per stream for Git, 1 MiB for tasklist), refusing overflow.
  A second direct-child termination timeout is recorded as unconfirmed
  instead of bypassing pipe-reader cleanup. Windows descendants may survive
  direct-child termination; no job type launching descendants is permitted
  until job-object containment and process-tree exit validation are implemented.
- `run-once` attempts one pending job, writing a durable JSON success/failure
  receipt, then exits. A directory lock prohibits simultaneous runners.
  Its owner metadata records the worker PID and start time.
- `diagnose` reports the worker lock owner and potentially stranded running
  receipts without modifying any state or retrying anything.
- A new `run-once` refuses to consume pending work if an earlier running
  receipt remains unresolved; the pending job is preserved exactly as submitted.
- `host-status` reads available physical RAM and observes selected Windows
  builder processes (`Runner.Worker`, MSBuild, cl, link, Ninja, CMake, clang-cl).
  This is advisory telemetry, not a process lease or proof of idle capacity.
- The owner must separately arrange any automatic invocation. This PR does
  **not** create Windows scheduled tasks or modify GHA, runner services,
  machine settings, credentials, or the five hourly ChatGPT schedules.

## Windows example

Use a dedicated clean checkout pinned to trusted main, never the active GHA
runner's worktree. An operator fetches origin/main before using a new SHA.

```powershell
$script = 'C:\DevNode\repos\UR-Recomp-hp-broker\tools\hp_safe_job_broker.py'
$repo = 'C:\DevNode\repos\UR-Recomp'  # clean trusted-main checkout
$state = 'C:\DevNode\hp-agent-jobs'
$sha = git -C $repo rev-parse HEAD
python $script --repo $repo --state-dir $state submit --kind repo-status --sha $sha --agent agent-1
python $script --repo $repo --state-dir $state run-once
python $script --repo $repo --state-dir $state diagnose
python $script --repo $repo --state-dir $state host-status
python $script --repo $repo --state-dir $state status --job-id <returned-job-id>
```

## Planned GHA resource coordination

A separate, opt-in reservation protocol and exact deployment prerequisites
are documented in `docs/HP-RUNNER-COORDINATION-PROTOCOL-20261103.md`.
That local prototype is not installed into GHA runner hooks and is not yet
connected to `run-once`. It provides no live resource arbitration today.

## Guardrails and unresolved work

Do not execute this against arbitrary PR heads or the trusted-main GHA runner
checkout. `agent-selector` requires a dedicated source-matched clean checkout.
A process crash may strand a receipt in `running` or leave `worker.lock`.
Use `diagnose` to inspect lock PID, start time and running receipts; independently
verify actual Windows processes before any manual recovery. A PID may have been
reused, so its presence or absence alone does not establish job completion.
Do not silently requeue an uncertain job. There is no automatic retry, watchdog,
heartbeat, resource scheduling, workload priority, multihost support, or
cross-process proof of noninterference with existing Windows builds.
`host-status` only samples instantaneously; absent process names do not prove
GHA idle, and future CPU-intensive jobs must fail closed without an explicit
shared reservation protocol between this broker and the GHA service.
Timeouts constrain the direct subprocess only; they do not establish that a
spawned descendant process has exited. No long-running job kind is admitted.

Before authorizing mutation-capable work: implement bounded leases/recovery,
proper machine-resource coordination with the existing self-hosted GHA runner,
unique worktrees per writer, explicit command/job kinds, audit logging,
sandbox/credential boundaries, and independent exact-head acceptance.
No results from this read-only pilot count as Windows product qualification.

Focused qualification:
`python -m unittest discover -s tests/unit -p test_hp_safe_job_broker.py -v`.
