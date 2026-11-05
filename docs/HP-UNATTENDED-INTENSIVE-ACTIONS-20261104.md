# Enabling intensive unattended work on the existing HP runner

Status: implementation PR, subject to exact-head CI and independent review.

## Why the execution route is GitHub Actions

The HP already runs a self-hosted, single-job Windows GitHub Actions runner
named `hpmini-ur-recomp`. Its scheduled seeded two-player native research and
main Windows smoke campaigns have produced genuine passing Windows results.
A locally executed CPU-heavy broker would race with a newly assigned Actions
job unless **both** use the same durable reservation protocol. That runner-hook
integration remains unqualified under `NETWORK SERVICE`.

The safe route for intensive work today is to **dispatch it into GitHub Actions
itself**, where the existing single-job worker queues it behind any already
assigned work. This avoids creating a second independently scheduled
CPU-intensive process on the same computer.

## New on-demand intensive workflow

`.github/workflows/hp-unattended-intensive.yml` exposes two **fixed**,
source-controlled choices. It accepts no arbitrary script or shell command.

- `seeded-2p-600`: runs the established, fully source-bound seeded two-player
  HP research campaign with the already supported 600-second manual horizon.
- `native-smoke`: runs the canonical owner HP Windows native smoke pipeline,
  including its existing packaging, startup and verification checks.

Both call the existing `windows-native-smoke.yml` reusable workflow with
`run_on_hp=true` and the established guarded HP/Ninja configuration. The
caller is allowed **only** for `gamesbyian/UR-Recomp` on `refs/heads/main`
through owner-authorized `workflow_dispatch`. The downstream workflow also
checks the owner HP runner name, source, event and execution mode.

To request an unattended job **after this workflow is merged**, use:

```powershell
gh workflow run hp-unattended-intensive.yml --repo gamesbyian/UR-Recomp --ref main -f mode=seeded-2p-600
gh workflow run hp-unattended-intensive.yml --repo gamesbyian/UR-Recomp --ref main -f mode=native-smoke
```

Find its run through the normal GitHub Actions run list and inspect its actual
source SHA, receipt artifacts, tests and final conclusion. A dispatch HTTP
success is **not** proof that the job ran or succeeded. Do not dispatch
repeatedly solely because a job is queued. Scheduled background science
continues on its existing workflow and cadence, without additional workers.

## Scope and remaining limitations

This gives an **unattended intensive execution route managed by the existing
GHA runner**, not permission for the separate `hp_safe_job_broker.py` to
execute heavy jobs locally. GitHub runner job serialization is specific to
the runner; it does not serialize arbitrary interactive/local Windows
processes. The existing read-only broker remains restricted to its original
allowlisted actions.

Separately, the `hp_service_account_job_probe.py` investigation is designed
to establish whether atomic Win32 Job Object creation works under the actual
GHA service account, but cannot substitute for native runner hooks, state-dir
ACL validation, or process and memory limits for arbitrary workloads. No
hooks, Windows task registrations, runner services or user credentials are
modified by this intensive workflow.

The owner can extend the fixed work-kind list through a new reviewed code
change with source-bound tests. Do not add user-supplied command execution,
PR/fork source, or ambiguous inputs.
