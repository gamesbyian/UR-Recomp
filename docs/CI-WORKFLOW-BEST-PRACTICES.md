# GitHub Actions workflow design and efficiency

This document is the canonical repository policy for designing, reviewing, and maintaining GitHub Actions workflows in UR-Recomp.

The goal is not to minimize CI at any cost. The goal is to get the **cheapest trustworthy answer** for each repository invariant while keeping expensive research and evidence collection from waking on unrelated work.

## Workflow classes

Every workflow must fit one primary class.

1. **Durable merge validation** — fast checks protecting an active product, runtime, data, or tooling contract. Prefer pull-request triggers with narrow `paths`.
2. **Main-branch regression** — durable checks that must validate the integrated tree. Prefer `push` to `main` with narrow `paths`.
3. **Reproducible analysis** — deterministic evidence builders whose outputs matter when their inputs change. Trigger only on their true producers/inputs, or keep them manual.
4. **Manual research infrastructure** — expensive probes, archaeology, historical replay, counterfactual experiments, and one-off discriminators. Default to `workflow_dispatch`.
5. **Obsolete experiment** — remove it once its conclusion is promoted and no durable invariant depends on rerunning it.

Do not leave a completed branch-specific experiment in `.github/workflows/` merely because it is harmless. With dozens of workflows, harmless files become routing and maintenance cost.

## Trigger policy

### Use the narrowest correct trigger

A workflow should run because an input capable of changing its result changed.

Prefer:

```yaml
on:
  pull_request:
    paths:
      - "native/presentation/**"
      - "tests/native/racer_*.cpp"
      - ".github/workflows/racer-native-presentation-acceptance.yml"
```

Do not trigger an expensive runtime workflow from planning prose merely because that prose describes the feature. Documentation changes do not invalidate a native binary unless a document is itself a machine-consumed input.

### Prefer per-tool trigger snapshots

When a workflow consumes one or two repository-managed tools, depend on their exported tool entries rather than the monolithic registry:

```yaml
- "tools/bootstrap_toolchain.py"
- "tools/toolchain-entries/snesrecomp.json"
- "tools/toolchain-entries/snes9x-libretro.json"
- "tools/toolchain-entries/_global.json"
```

Avoid `tools/toolchain.json` in specialist runtime/research workflows. A change to an unrelated tool otherwise wakes every workflow that watches the global registry. The global registry remains appropriate for the toolchain-bootstrap contract itself.

### Separate evidence fixtures from fast gates

If a fixture is owned by a dedicated evidence workflow, changing that fixture should not also wake a generic smoke workflow unless the smoke job actually consumes it.

The fast native gate owns boot, basic deterministic race entry, product-host sanity, and narrowly selected product acceptance. The UI-evidence workflow owns the broader UI capture corpus. Do not make the fast gate depend on every UI script.

### Push versus pull request

Use pull-request validation when the result is primarily needed before merge. Add a main-push run only when integrated-main validation provides additional value.

**Do not include a workflow's own `.github/workflows/<name>.yml` path in its `push.paths` merely to prove that workflow edits execute.** That creates a redundant full rerun immediately after every workflow-maintenance merge.

Use this pattern instead:

- if the workflow already has a `pull_request` trigger, include its own YAML path there so workflow edits are exercised before merge;
- if it is push-only research/evidence infrastructure, keep its own YAML out of `push.paths`; use `workflow_dispatch` for an explicit full execution when the workflow implementation itself needs proving;
- keep main-push triggers restricted to real runtime/evidence inputs whose integrated state can change the result;
- allow a workflow self-path on main only when there is a documented reason that the integrated-main execution proves something a PR execution cannot.

Research/evidence workflows that can be run manually should not gain `push` merely for convenience.

## Concurrency

Automatic workflows should normally include:

```yaml
concurrency:
  group: <workflow-name>-${{ github.ref }}
  cancel-in-progress: true
```

This prevents rapid agent commits from burning runner time on superseded heads.

Exception: a workflow that may **write generated evidence back to the branch** should serialize rather than cancel:

```yaml
concurrency:
  group: <workflow-name>-${{ github.ref }}
  cancel-in-progress: false
```

Do not allow two writer runs to race the same branch.

Manual-only, read-only probes may omit concurrency when duplicate runs are intentionally independent, but adding a group is still preferred when duplicate execution has no evidentiary value.

## Timeouts

Every job that invokes an emulator, native executable, compiler toolchain, networked diagnostic, or external process must have an explicit `timeout-minutes`.

Small pure-Python checks may omit a timeout only when their runtime is intrinsically bounded. Prefer a timeout anyway for new workflows.

Inner `timeout` commands do not replace the job-level limit. The job timeout protects setup, package installation, build hangs, and cleanup too.

## Dependency installation

Do not optimize package installation by making it fragile.

- Keep system packages focused on the job's actual backend.
- Avoid installing GUI/display/audio dependencies for pure analysis jobs.
- Reuse the repository-owned offline toolchain wherever possible.
- Prefer a tool-specific repository snapshot over refetching upstream sources.
- Do not add a cache blindly. A cache is useful only when restore/save time is materially lower than rebuilding and its key invalidates correctly.

GitHub-hosted runners are ephemeral. `apt` caching is usually poor value for this repository; reducing how many jobs need the package set is more valuable.

## Build work

### Do not build the same thing without a reason

Before adding another native build, ask whether an existing workflow already proves the same target under the same patch/toolchain inputs.

Separate workflows are justified when they protect genuinely different seams, but overlapping jobs should share the smallest possible build scope.

### Use parallelism deliberately

Parallel matrix/shard jobs are appropriate when they reduce wall time and the shards are independent. Avoid serializing independent capture work merely to reduce aggregate runner minutes.

Conversely, do not create a matrix whose members each repeat a costly build if a shared build artifact would materially reduce wall time or runner cost. Measure before refactoring: artifact upload/download can erase the gain for small binaries.

### Keep fast gates fast

A smoke workflow should answer a bounded question quickly. Rich screenshot atlases, long historical replays, broad evidence harvesting, and archaeology belong in specialist workflows.

When a fast gate grows, split evidence collection out before raising the timeout.

## Parameterized experiment harnesses

When a research sequence differs only by a numeric depth, margin, frame range or other monotonic parameter, prefer one parameterized harness over sibling workflows. A new workflow is justified by a new invariant or execution substrate, not merely a new parameter value.

For accepted capacity-style experiments, test the product-relevant endpoint once monotonicity is established. If the endpoint fails, localize the first failing value with the same harness. This avoids paying full setup/build cost for every intermediate rung.

## Structured evidence contracts

Human-oriented log lines are diagnostic output, not a durable machine API. New or generalized evidence gates should emit the common envelope in `analysis/evidence-envelope.schema.json` through `tools/evidence_contract.py` where practical. Keep subsystem-specific metrics, but express pass/fail conditions as named typed assertions.

Prefer validators that consume structured evidence plus raw logs only where the underlying runtime has not yet gained structured emission. Do not clone grep fragments across successive experiment workflows.

## Artifacts and logs

Upload the smallest artifact set needed to diagnose or reproduce a failure.

- Prefer compact JSON/Markdown summaries plus bounded logs.
- Retain raw dumps only when they are difficult to regenerate or required for visual/state review.
- Use short retention for diagnostic artifacts unless they are deliberate long-lived evidence.
- Do not upload identical build trees from every matrix member.

A green workflow must prove target identity. Never accept an arbitrary executable fallback from a build directory.

## Generated-evidence workflows

Workflows that commit generated evidence back to the repository are exceptional.

They must:

- have narrow input paths;
- be serialized with `cancel-in-progress: false`;
- make no commit when outputs are already current;
- fetch/rebase immediately before pushing;
- avoid triggering themselves from their generated output unless the rerun is guaranteed to be a no-op;
- prefer `--check` validation in pull requests and generation on main when practical.

If a generated artifact can be validated cheaply without committing from CI, prefer that design.

## Research workflows

A one-off research question should normally begin as `workflow_dispatch`, not permanent automatic CI.

Promote it to automatic validation only when the experiment has become a durable invariant. Once the conclusion is captured in canonical data/tests/docs, remove branch-only or superseded workflow files.

Research workflows may intentionally be slow. Their efficiency requirement is **selection efficiency**: they should run only when requested or when a true evidence input changes.

## Review checklist for new or edited workflows

Before merging a workflow, answer all of these:

- What durable decision or invariant does it protect?
- Which exact files can change its answer?
- Could a documentation-only edit trigger expensive runtime work?
- Does it depend on a per-tool entry rather than the global toolchain registry?
- Is it PR validation, main regression, reproducible analysis, or manual research?
- Does automatic work cancel superseded runs?
- If it writes to Git, is it serialized instead?
- Is there a job-level timeout?
- Does it install only dependencies it actually uses?
- Is another workflow already building/testing the same seam?
- Are matrix/shard boundaries reducing wall time rather than multiplying unnecessary setup?
- Are artifacts bounded and diagnostically useful?
- Can the same question be answered by a cheaper unit/static check first?
- Is the workflow still needed after the current experiment closes?

## Repository-wide audit baseline — 2026-10-03

The audit that established this policy inventoried **78 workflow files**; one obsolete branch-only workflow was removed, leaving **77 active workflow files**.

Key findings and actions:

- most expensive active runtime workflows already use path filters and concurrency cancellation;
- the native UI evidence suite is correctly separated from the fast native smoke gate and sharded across four capture jobs;
- the obsolete branch-only `ed2f-angle-physics-probe.yml` workflow was removed;
- historical replay, object-liveness, and finish-differential workflows were narrowed from `tools/toolchain.json` to the specific tool-entry snapshots they consume;
- Modern Restart acceptance was removed from prose-only plan/doc triggers and narrowed to the SNESRecomp entry it actually consumes;
- native build smoke stopped watching UI-only capture scripts owned by `native-ui-evidence.yml`;
- generated course-presentation writer workflows were given serialization groups;
- the SMV tooling regression now cancels superseded automatic runs.
- a follow-up post-merge audit removed workflow-self paths from main-push trigger sets across the suite; workflow edits are now validated pre-merge where PR validation exists, or explicitly via manual dispatch for push-only research/evidence jobs.

Remaining expensive workflows are retained because they test distinct runtime/evidence seams. Optimize them further only from measured job timing or duplicated-build evidence, not by weakening coverage. Use the manual `CI runtime report` workflow and `tools/report_ci_runtime.py` to rank recent workflows by measured wall time before another broad optimization pass.

## Periodic maintenance

The repository hygiene pass must review:

- newly added automatic workflows;
- jobs without concurrency or timeouts;
- broad `push` triggers;
- specialist workflows watching `tools/toolchain.json`;
- repeated package/build setup that has become a measurable wall-time problem;
- old research workflows whose conclusions are already promoted;
- failing workflows that are known evidence gaps rather than merge gates.

See `PERIODIC-REPOSITORY-HYGIENE.md` for the broader recurring audit.
