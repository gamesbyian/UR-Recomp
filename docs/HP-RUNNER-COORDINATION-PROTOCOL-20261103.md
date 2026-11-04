# HP broker / GitHub Actions resource coordination plan

Status: **prototype, disabled**, 2026-11-03. Companion:
`tools/hp_resource_reservation.py` and
`tests/unit/test_hp_resource_reservation.py`.

## Why hooks, not process detection

The owner HP runs the self-hosted `hpmini-ur-recomp` GitHub Actions
runner as `NT AUTHORITY\\NETWORK SERVICE` and may have work assigned
at any time. A snapshot showing no `Runner.Worker.exe` or compiler
does not establish an idle reservation. A race exists between any
resource check and GitHub assigning a new job.

GitHub supports admin-configured, synchronous runner pre/post-job
hooks via `ACTIONS_RUNNER_HOOK_JOB_STARTED` and
`ACTIONS_RUNNER_HOOK_JOB_COMPLETED`. See:
https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/run-scripts

The hook approach could make *all* jobs on the single HP runner participate
without editing the repository's many Windows workflows. However,
nonzero hook exit codes can fail otherwise valid GHA jobs; hooks have
no platform-defined execution timeout; and modifying the runner's
`.env` requires a service restart. Do not install them casually.

## Prototype protocol and local evidence

`hp_resource_reservation.py` supports `reserve`, `release`, and
`status`. The two roles are `github-actions` and `hp-broker`.
An atomic directory creation serializes reservation updates; a
single durable `active.json` records the current role, token, unique
reservation ID and UTC timestamp. One claimant succeeds; a second
claimant fails closed. The original holder must explicitly release using
**both** its role/token and its exact reservation ID, preventing delayed
completion from freeing a later reservation that reused the same token.
Corrupt records or abandoned operation locks require operator
inspection. There is no automatic expiry or retry.

On the physical HP, five focused contract tests passed, including
four simultaneous contestants and corrupt/stale-record cases.
A cross-process PowerShell/CLI smoke with the current fenced-release
contract demonstrated GHA reserve, broker conflict, exact-ID GHA release,
broker reserve, exact-ID broker release and final empty state. This is a
*standalone protocol test*, not a running GitHub runner integration test.

## Safe integration prerequisites (not implemented)

1. Pin a service-accessible Python interpreter and code location
   controlled by the owner, not PR-controlled working files. Test as
   NETWORK SERVICE. Verify state-dir ACLs for that account and for
   the Desktop Commander user; `C:\\DevNode` inheritance alone is
   not proof of sufficient access to the intended child directory.
2. Add fixed, owner-controlled hook wrappers outside the GHA runner
   application directory. Validate unique job tokens across workflow
   jobs, retries and attempts. A GHA start hook must acquire
   reservation *before any job steps*, using a bounded, instrumented
   wait if the HP broker is active. A completion hook must release
   only that job's reservation, including on failure/cancellation.
3. Under explicit maintenance, install the hook environment variables
   in the runner's `.env` and restart the service once. Preserve the
   exact prior configuration and have an owner-verified rollback.
4. First run a harmless workflow with no competing broker job; verify
   both hook logs and final empty reservation state. Next run bounded
   synthetic contention tests in both orderings, including a forced
   cancellation, hook failure and machine restart. Preserve all
   logs and test that pre-hook failures never silently proceed.
5. Only after these pass may the broker admit any new CPU-heavy job
   kind. Every such job must reserve before launching work, hold the
   reservation for all descendants, and release after verifying they
   have exited. A timeout of only the parent process is insufficient.
6. Never automatically clear a stale lease or cancel the owner's
   existing native Windows qualification jobs. Failure must leave
   a distinct actionable diagnostic and preserve original evidence.

For now the broker continues to support only read-only, 45-second
allowlisted jobs. No hooked GHA job or long-running broker job was
attempted, and the `shared_enforcement_enabled` status intentionally
remains false. This prototype does not itself prove GHA/broker
noninterference or source-linked product qualification.

## Validation

```powershell
python -m unittest discover -s tests/unit -p test_hp_resource_reservation.py -v
python -m unittest discover -s tests/unit -p test_hp_safe_job_broker.py -v
```
