# GitHub Actions workflow design and efficiency

This document is the canonical repository policy for designing, reviewing, and maintaining GitHub Actions workflows in UR-Recomp.

The goal is not to minimize CI at any cost. The goal is to get the **cheapest trustworthy answer** for each repository invariant while keeping expensive research and evidence collection from waking on unrelated work.

## Workflow classes

Every workflow must fit one primary class.

1. **Durable merge validation** — fast checks protecting an active product, runtime, data, or tooling contract. Prefer pull-request triggers with narrow `paths`.
2. **Main-branch regression** — durable checks that must validate the integrated tree. Prefer `push` to `main` with narrow `paths`.
3. **Reproducible analysis** — deterministic evidence builders whose outputs matter when their inputs change. Trigger only on their true producers/inputs, or keep them manual.
4. **Manual research infrastructure** — expensive probes, archaeology, historical replay, counterfactual experiments, and one-off discriminators. Default to `workflow_dispatch`.
5. **Retained research instrument** — a closed experiment whose harness may still be useful diagnostically. Keep it manual-only.
6. **Obsolete experiment** — delete it once its conclusion is promoted and neither its harness nor its historical reproducibility has durable value.

Do not leave a completed branch-specific experiment automatic merely because its trigger is technically correct. With a large workflow catalog, a correct trigger on a closed question is still CI waste. A closed experiment must either become a durable invariant, become manual-only, or be removed.

## Workflow lifecycle and default posture

A new workflow is **manual by default**. Automatic execution is something a workflow earns after its result protects a current, durable repository invariant.

Before adding `pull_request` or `push`, write down:

- the exact invariant that can block merge or shipping;
- the smallest set of files capable of changing that invariant;
- why a cheaper unit/static check is insufficient;
- which existing workflow, if any, already builds or validates the same candidate;
- the retirement condition: what future event makes this workflow manual-only or removable.

Research questions, branch-specific probes, archaeology, historical replay, comparison studies, capacity sweeps, platform feasibility work, and evidence-gathering experiments stay `workflow_dispatch` unless their conclusion is deliberately promoted into a durable gate.

When a research question closes, clean up in the same integration pass:

1. promote the conclusion into the owning code/data/test/doc;
2. remove automatic triggers from the probe;
3. parameterize or consolidate sibling probes where useful;
4. delete the workflow if retaining the harness has no realistic diagnostic value;
5. update `tests/unit/test_ci_trigger_policy.py` when the boundary should remain mechanically enforced.

Do not rely on branch names to make old workflows harmless. Branch-scoped `push` triggers are still permanent repository policy and should be removed when that branch experiment is over.

## Automatic-CI budget

Automatic CI is reserved for the active Windows x64 shipping path and cheap repository integrity contracts.

A workflow should not be automatic merely because:
- its inputs are easy to name;
- it used to answer an important research question;
- it produces interesting evidence;
- it validates a deferred platform;
- its runtime is currently affordable;
- it has always been automatic.

Prefer one broad shipping canary plus narrow subsystem contracts over many overlapping end-to-end builds. If two workflows build the same native candidate, either justify the distinct seam they protect or share/collapse the build. If one workflow has several independent evidence slices, prefer one build feeding those slices over a matrix that rebuilds the candidate per shard.

Current policy examples:
- Windows x64 packaging/boot validation runs on final `main`, not both PR and merge.
- Deferred Switch/S2 workflows are manual-only.
- Closed Widescreen reconnaissance/capacity workflows are manual-only; the shipping 4:3 invariant remains automatic.
- Native UI evidence is one native build running multiple evidence slices, not four independent builds.
- The full multi-tool bootstrap matrix is manual; its lightweight contract remains automatic.

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

## Failure triage and recent-run interpretation

Review CI by **root cause**, not by the color count in the Actions list.

When auditing recent health:

1. inspect roughly the last 5-10 runs of each active automatic workflow when that history exists;
2. treat `cancelled` runs caused by a newer commit on the same branch as superseded work, not failures;
3. look at the newest relevant run on the current branch/head before spending time on an older red run;
4. inspect failed **job and step names first**, then the bounded log/artifact for that step;
5. classify the failure before editing code: product/runtime regression, stale test assumption, UI/harness navigation coupling, orchestration/cascade failure, runner/toolchain failure, or known evidence gap;
6. fix the owning assumption/harness and then verify the latest current-head result. Do not rerun every historical red.

A branch with six cancelled runs followed by one green run has one useful result, not a 14% pass rate. Cancellation volume is still an efficiency signal: it may mean agents are pushing tiny CI-triggering commits faster than useful gates can finish.

### Do not manufacture secondary failures

Use `if: always()` only for diagnostics, artifact upload, cleanup and summaries that are explicitly safe when upstream work never ran.

A validation step that consumes an artifact produced by an earlier step should normally use default success semantics. If the producer is skipped or fails, the consumer should be skipped rather than emit a second misleading error such as "missing screenshot." The **first failing invariant** should remain visually obvious.

If diagnostic collection must run after failure, make missing producer artifacts informational in that diagnostic path and keep the original failed step as the job's root cause.

### Keep UI acceptance semantic

Host UI evolves quickly. Avoid encoding menu structure as repeated literal cursor counts in shell snippets.

Prefer, in order:

- semantic input/selection APIs or pure product-controller tests;
- a shared row enum/model queried by the test harness;
- one bounded end-to-end keyboard/controller route that is updated in the same change as the menu;
- literal `xdotool key Down` counts only at the outermost acceptance edge.

When an Options row is inserted, all end-to-end routes that navigate below it must be treated as dependents. Do not copy comments such as "seventh row" into multiple workflows and hope they stay synchronized.

### Test rules, not today's example object

Validator/unit tests for policy schemas should construct the invalid state they intend to reject. Do not depend on a live production feature remaining a `redesign_candidate`, deprecated field, legacy schema, or other temporary state merely so the test has an example.

For example, a test that proves "`redesign_candidate` requires `decision_gate`" should mutate a fixture into that state and then remove the gate. Settling the real product policy must not make the validator test crash before it reaches the assertion.

### Avoid one subsystem masking the rest of a smoke gate

A smoke job with many serial product acceptances can turn one local failure into dozens of skipped checks. Keep build/boot/basic-route identity near the front and consider moving volatile product-specific end-to-end flows to focused workflows once they become independently valuable.

Skipped downstream checks after the first failure are **unknown**, not failed and not passed. When deciding whether a merge introduced multiple regressions, do not count skipped steps as evidence either way.

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

## Repository-wide audit baseline — 2026-10-05

A full workflow-catalog audit after a 100+ run fan-out reclassified automatic CI around the active Windows x64 shipping path.

The audit established these repository-wide rules:

- deferred Switch/S2 validation is manual-only;
- closed Widescreen capacity, scene-policy, preparation, composition and other reconnaissance is manual-only;
- historical emulator/TAS/SRAM, course/RNC/TCRF, reference-core, challenge-discriminator and other archaeology workflows are manual-only;
- settled regional NTSC/PAL comparison workflows are manual-only once their evidence has been captured;
- superseded Racer research/provenance probes are manual-only while the shipping Racer presentation acceptance remains automatic;
- Windows native package/boot validation runs only on final `main`;
- the 4:3 Widescreen regression remains automatic but watches only actual Widescreen authority;
- Native UI evidence performs one build for all evidence slices rather than rebuilding per matrix shard;
- the full toolchain build matrix is explicit/manual while the cheap bootstrap/island/interoperability contract remains automatic;
- docs-only edits do not trigger native onboarding or local-multiplayer validation;
- completed-run replay acceptance does not wake for generic Modern host edits;
- automatic workflows must remain path-scoped and use concurrency; coordination docs are never executable trigger inputs.

The retained automatic surface should stay deliberately small: current product acceptances, broad native smoke, final-main Windows packaging, the shipping Authentic/4:3 parity invariant, cheap product contracts, tooling/unit validation, repository/import integrity, and other checks whose failure would change an immediate merge or shipping decision.

`tests/unit/test_ci_trigger_policy.py` is the mechanical backstop. Extend it when a newly learned CI boundary should be permanent rather than relying only on prose.

## Recent failure-pattern lesson — 2026-10-05

The dominant CI problem was not broken concurrency syntax. It was **correctly configured workflows answering questions the project no longer needed on every PR**, compounded by broad trigger surfaces and duplicated native builds.

Operational conclusions:

- first ask whether a workflow still deserves to be automatic;
- then ask whether its trigger paths are the smallest true invalidation set;
- then ask whether another workflow is already paying for the same build;
- only after those questions optimize caching, sharding, or runner details;
- diagnose from the latest completed current-head run and the first failed step;
- do not count superseded cancellations as regressions;
- avoid tiny commit chains through high-fan-out paths;
- reserve `always()` for diagnostics/cleanup rather than dependent assertions;
- after changing many workflow files, verify YAML shape and inspect the live Actions fan-out on the merged head.

## Periodic maintenance

The repository hygiene pass must review:

- every newly added automatic workflow and the durable invariant that justifies it;
- whether closed research should be manualized or deleted;
- jobs without concurrency or timeouts;
- broad `push` or `pull_request` paths;
- documentation/planning files in runtime trigger sets;
- specialist workflows watching global registries instead of precise inputs;
- repeated native/toolchain setup that can be shared or collapsed;
- matrix/shard designs that multiply builds rather than only parallelize post-build work;
- PR validation duplicated again on `main`;
- deferred-platform checks leaking into the active Windows path;
- failing workflows that are evidence gaps rather than merge gates;
- stale claims in this document about which workflows are automatic.

Use the manual `CI runtime report` and recent Actions history to rank actual cost, but do not wait for a runtime crisis before retiring workflows whose decision value is already zero.

See `PERIODIC-REPOSITORY-HYGIENE.md` for the broader recurring audit.
