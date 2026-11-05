# HP service-identity Job Object qualification (2026-11-04)

**Post-merge actual owner HP proof:** [run #41943194209](https://github.com/gamesbyian/UR-Recomp/actions/runs/41943194209) succeeded under `nt authority\\network service` with both `atomic_job_list=pass` and `kill_on_close=pass`. It validates this bounded primitive only; hooks, a shared GHA/broker reservation and heavyweight local broker remain uninstalled. The earlier below-described pre-qualification checklist is retained as historical procedure. See the [integrated plan](CI-COLLECTIVE-QUALIFICATION-INFRASTRUCTURE-PLAN-20261104.md).

This standalone, main-only probe tests the Windows execution identity and
atomic Job Object creation under GitHub Actions on the existing HP. It does
not create a new runner, install hooks, change Windows services, or enable
a second local CPU-intensive worker.

The guarded workflow is
`.github/workflows/hp-service-account-job-probe.yml`. It runs **only**
via owner-initiated `workflow_dispatch` on `gamesbyian/UR-Recomp` `main`
and requires the exact `hpmini-ur-recomp` runner. It uses the already
provisioned HP Python 3.12.10 runtime; it never downloads code or toolchains
into a privileged installation. Source is checked out from the assigned main
SHA with persisted checkout credentials disabled.

The import-only native probe tests whether its execution identity is
`NT AUTHORITY\\NETWORK SERVICE` and whether a subprocess can be attached
to a Windows Job Object **at process creation** with
`PROC_THREAD_ATTRIBUTE_JOB_LIST`. It verifies the test child is alive
before closing the Job Object and terminated afterwards. It records
`IsProcessInJob`, to expose nested-job context. It only executes a fixed
15-second sleep in its own Python interpreter and has a bounded five-second
termination check and emergency cleanup. No commands or child executable
names are accepted from workflow inputs.

Local interactive HP proof:
`python -W error::ResourceWarning -m unittest discover -s tests/unit -p test_hp_service_account_job_probe.py -v` passed.

**Before claiming service-account qualification:** merge the exact reviewed
source, dispatch this workflow on main, and inspect the actual run receipt.
Local interactive execution is not a substitute. Even a passing service
probe would not establish output-stream bounding, crash recovery or
GHA/broker reservation arbitration. GHA hooks remain disabled and this
test does not authorize heavy broker jobs to execute outside GitHub Actions.

**Immediate safe intensive execution path:** continue to submit main-only
work to the existing self-hosted GitHub Actions runner; its single-worker
queue serializes jobs and already runs intensive seeded two-player research.
Do not start a separate CPU-intensive broker process until both the broker
and every competing runner job participate in the same reservation protocol,
or route the broker's heavy jobs through the existing Actions queue instead.
