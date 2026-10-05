# Operations acceleration

This document owns the project-wide process changes that reduce repeated agent, CI and evidence-production work. It does not replace subsystem plans or the work queue.

## Structured evidence

Durable machine-consumed acceptance should emit the common envelope defined by `analysis/evidence-envelope.schema.json` and constructed/validated by `tools/evidence_contract.py`.

Logs remain useful diagnostics, but new gates should not depend on prose formatting when a typed assertion can be emitted instead. The envelope records producer, subject, inputs, metrics, named assertions, outcome and provenance. Subsystem-specific evidence may carry additional fields.

The first migration target is VS Widescreen capacity. `tools/check_widescreen_capacity_evidence.py` accepts any strip-granular margin from +16 upward, derives the required host-shadow depths, checks calibration counts, geometry and protected-state parity, and emits the common envelope. Future +40/+48 work should call this tool instead of cloning margin-specific grep/Python validation.

## Parameterized experiments

When successive experiments differ only by one monotonic parameter, keep one harness and vary the parameter. Do not create a new permanent workflow for every value.

For Widescreen capacity the final product threshold is +48 per viewport. Once the active +40 branch is reconciled, the next experiment should probe +48 directly with the generalized validator. If +48 fails, localize the first failing depth rather than manufacturing a new sibling workflow for every intermediate value.

## Racer HD pose equivalence

Exact synchronized composition guards remain runtime identities. Art-production identity is narrower.

`tools/build_racer_pose_equivalence.py` groups dossier representations only when their deterministic stock RGBA hashes are byte-identical for the same player. It emits:
- unique visual-pose groups;
- semantic registrations collapsed by visual equivalence;
- the authored source representation for each group;
- safe reuse candidates;
- an unauthored unique-pose worklist;
- duplicate-authored groups that may indicate wasted art work.

Use this worklist for future authored batches. Do not create duplicate art merely because a semantic guard is distinct.

## Cross-workstream transfer rules

When one lane establishes a stronger acceptance or ownership pattern, reuse the pattern before creating a subsystem-specific variant.

### Separate runtime identity from production identity

The Racer HD work proved that exact runtime/semantic guards can outnumber the visual assets that actually need independent production. Apply the same distinction anywhere evidence permits it:

- keep exact semantic/runtime identity for correctness and provenance;
- derive a narrower equivalence identity for expensive authored or processed outputs;
- reuse one canonical output for byte-identical/evidence-equivalent inputs;
- generate variants through deterministic transforms only after the transform roles are proven;
- require equivalence again on the final authored output, not only on the source.

This rule is not racer-specific. It should govern later background/tile/UI replacement families, audio conversions, shader/reference captures and any other batch where multiple semantic states can share one production artifact.

### Bind approvals to exact inputs and outputs

Racer HD shipping approval is useful because it is fail-closed and hash-bound. Generalize that rule to reviewed generated or authored product assets:

- approval records name the exact source/provenance set and exact reviewed output digest;
- a changed source, transform version or output digest invalidates the approval automatically;
- stale approval must become visibly non-shipping rather than silently inheriting trust;
- review packets should be generated from the same canonical manifest used by runtime/tooling, not from a hand-maintained parallel list.

Use this for later visual families and any future audio/remaster asset pipeline before inventing a second approval mechanism.

### Transactional live-setting changes

Output Resolution, Display Mode, VSync and related Modern settings established the correct product pattern: **resolve capability → apply candidate → persist candidate → commit in-memory state; rollback the live effect if persistence fails**.

Use the same transaction shape for future live host settings wherever a failed save could otherwise leave runtime and persistence disagreeing. Likely consumers include audio presentation, controller/accessibility preferences and later renderer options. Do not implement each setting with bespoke partial-success semantics.

### Semantic input and renderer-neutral view models

Quick Practice demonstrates a useful UI split: backend events map to a small semantic command vocabulary, pure product logic owns selection/state, and a renderer-neutral view model owns display text before the host draws it.

Prefer this pattern for new Modern selectors and browsers, including profile management, records/statistics, local multiplayer setup and future accessibility/configuration screens. Extend shared command/view primitives when behavior is genuinely common; do not clone another keyboard branch, controller branch and overlay formatter for every screen.

### Canonical validator before copied parsing

When two workflows or tools parse the same artifact format or repeat the same acceptance logic, extract one repository-owned parser/validator and make both consume it. The evidence-envelope helper, consolidated knowledge builders and parameterized Widescreen validators already follow this direction.

A third copy of format parsing, checksum logic, PPM/frame inspection, run-artifact validation, profile/catalog validation or semantic catalog joining is a signal to centralize. `tools/check_ppm.py` is now the concrete frame-inspection example: native smoke and Racer HD review tooling consume the same binary-P6 parser rather than maintaining inline variants. CI should invoke the same validator product tools use where practical rather than maintaining grep/Python lookalikes.

### Fresh-process and corruption acceptance for persisted product data

Completed runs, Modern profiles and host settings all benefit from validation outside the process that created them. Any new durable local product format should therefore prove:

- versioned decoding/migration policy;
- bounded input and malformed/corrupt rejection;
- atomic or replace-on-success writes where replacement is allowed;
- fresh-process reload;
- namespace/isolation behavior when profiles are involved;
- Authentic-mode inertness when the data is Modern-only.

Do not accept a persistence feature solely because save and load work inside one process.

### Plan documents describe decisions, not run history

Apply the existing work-queue density rule to all canonical planning documents. A plan should retain the current boundary, next decision, acceptance gate and stop condition. Detailed run IDs, frame-by-frame histories and superseded intermediate conclusions belong in the owning subsystem document or generated evidence.

If a plan paragraph requires repeated append-only updates after every successful family/run, replace the chronology with a compact current-state statement and point to the machine-readable evidence surface.

## Modern settings catalog

`analysis/modern-product-settings.json` is the machine-readable inventory of host-owned settings and their persistence/UI/runtime status. `tools/check_modern_product_settings_catalog.py` keeps it aligned with the current C++ codec and Options symbols.

The v1-v5 codecs retain their strict historical field sets. Version 6 is the stable additive envelope: its administrative core remains required, any number of explicitly known additive keys may be absent and receive typed defaults, and unknown keys still fail closed. Add future optional settings by extending that known-key/defaulting set; reserve a new schema version for an actual grammar or compatibility change. Runtime-specific adapters remain explicit.

## Agent-throughput model

The implementation workforce is autonomous agents, so optimize for **independent runnable work**, not for minimizing the number of simultaneously open branches. Dependency correctness still matters, but unrelated product slices should proceed concurrently by default.

### Keep a ready queue, not one next task

Maintain at least **three independent Windows-x64-ready tasks** whenever the roadmap contains that much useful work. A ready task must already have:

- one player-visible or release-facing outcome;
- the owning files/surfaces named;
- dependencies that are already satisfied or explicitly outside the branch;
- one bounded acceptance path an agent can run without inventing new research;
- a stop condition that prevents the task expanding into adjacent archaeology;
- no requirement to wait for another agent merely to discover what to do next.

When fewer than three tasks are ready, the highest-leverage planning work is to decompose the next blocked product requirement until more independent leaves exist. Do not spend an agent on speculative research while a shippable requirement can be decomposed into parallel leaves.

### Parallel lanes and collision budget

Prefer parallel work whose write sets are naturally disjoint. Current Windows product work should normally be decomposable across lanes such as:

- profile/progression lifecycle;
- controls/rebinding/accessibility;
- run/timing/statistics presentation;
- Quick Practice/navigation/rematch;
- Racer HD family coverage;
- display/presentation policy;
- packaging/release acceptance;
- tooling/validator consolidation.

Two agents may read the same authority and evidence. They should not both redesign the same central runtime/menu file unless one task is explicitly the integration owner. Shared hotspots such as `uniracers_modern_host.*`, central pause/frontend navigation, host-state schema files and high-fan-out workflow files should have **one integration owner at a time**. Other agents should land leaf models, pure policies, tests, catalogs and adapters that the integration owner can consume.

Do not serialize independent leaf work merely because all leaves eventually connect to one host. Build stable narrow interfaces first, then integrate completed leaves in a short reconciliation pass.

### Task size for autonomous agents

Default to a task that can become **one coherent PR with one acceptance story**. Avoid both extremes:

- tiny PRs that split one inference/feature boundary into bookkeeping;
- broad “finish subsystem” prompts that cause an agent to rediscover requirements, touch many shared surfaces and stall.

A good agent task usually owns one of: a pure policy/model, one product surface, one bounded runtime adapter, one acceptance harness, one asset family, or one release gate. If the prompt needs several independent “and then” clauses, split it unless those steps share one unavoidable inference boundary.

### No CI babysitting

An agent should run the cheapest relevant local/static/narrow acceptance it can, push the PR, record the expected gate, and move to another useful task. Do not spend an agent turn repeatedly polling GitHub Actions. Reconcile CI opportunistically when returning to the branch, or in a dedicated integration/CI lane that can repair failures across several recently landed PRs.

A red workflow is a blocking task only when it reveals a real regression or prevents integration. Queue delay, runner delay and already-superseded runs are not engineering work.

### Integrate in batches

When several independent PRs target disjoint surfaces, prefer a short integration sweep after they are ready rather than serially merging one and waiting for its entire CI fan-out before starting the next. Rebase/reconcile only where Git reports a real overlap. After a batch reaches `main`, fix the resulting current-main CI state rather than preserving obsolete intermediate branch states.

### Precompute the work packet

Fresh agents should not spend their first substantial pass rereading the whole repository. Extend `analysis/agent-context-lanes.json` and `tools/build_agent_context.py` so each recurring lane can produce the minimum authority packet: current boundary, relevant files, current tests/evidence, active neighboring branches, prohibited reopenings and exact acceptance commands. When the same orientation instructions appear in two prompts, move them into the lane packet.

### Prefer product completion over research utilization

An available research tool or known unknown is not a reason to occupy an agent. Assign research only when its output changes a queued product decision, unblocks an implementation, or creates a reusable acceptance surface that will remove repeated work. Otherwise spend the agent on a ready shipping leaf.

## Agent context

Use:

```bash
python3 tools/build_agent_context.py widescreen
python3 tools/build_agent_context.py racer-hd
python3 tools/build_agent_context.py modern-product
python3 tools/build_agent_context.py ci
```

The tool derives a bounded packet from current authorities plus recent git history. It is an orientation aid, not a new authority. Add a lane to `analysis/agent-context-lanes.json` rather than copying another long prompt into repository prose.

## Work-queue density

`WORK-QUEUE.md` should answer current priority, accepted boundary, next decision, cheapest discriminator and stop condition. Long run histories and detailed measurements belong in generated evidence or the owning subsystem document.

`python3 tools/check_work_queue_density.py` reports oversized blocks so repository hygiene can identify current-state prose that has become a historical ledger. It is advisory by default. Do not make it a merge gate until the existing oversized blocks have been deliberately compacted.

## Measured CI optimization

Use the manual `CI runtime report` workflow before undertaking another repository-wide CI optimization pass. It summarizes recent workflow wall time, average/max duration, failures and cancellations. Optimize the highest repeated cost only after measurement.

This intentionally avoids automatic scheduling. The profiler should not become background CI tax.

### Automatic-trigger and build-sharing policy

Treat automatic CI as scarce execution budget. A workflow may be useful and still belong behind `workflow_dispatch`.

Pure validation should normally run on `pull_request`; final integrated Windows package/boot validation is the deliberate exception and runs on `main` after merge. `tests/unit/test_ci_trigger_policy.py` enforces that Windows final-main boundary and rejects PR+main duplication for ordinary validation.

Closed research stays manual. This includes deferred Switch/S2 work, historical/reference archaeology, settled regional comparisons, closed Widescreen reconnaissance and capacity probes, and superseded challenge/Racer research. Reopen one explicitly when a concrete product counterexample or new decision needs it rather than making the whole family automatic again.

Use `concurrency` on every automatic workflow. Superseded branch/PR runs should cancel. Evidence-writing workflows may serialize when branch writes are genuinely required.

Optimize build topology before sharding. Parallelism is useful only when it avoids waiting without multiplying the dominant setup/build cost. Current Native UI evidence deliberately performs one native build and runs its evidence slices from that candidate rather than rebuilding in four matrix shards. The full multi-tool bootstrap matrix is manual-only; ordinary PRs run the lightweight bootstrap/island/interoperability contract instead.

Before adding a sibling workflow, ask:
- can the existing harness take another parameter?
- can one build feed several acceptance/evidence slices?
- is a cheap unit/static contract sufficient for PRs with the expensive acceptance reserved for final integration or explicit dispatch?
- does another automatic workflow already validate the same host/toolchain boundary?
- what condition will retire this workflow from automatic execution?

When a research branch closes, workflow cleanup is part of integration: remove branch-only triggers, manualize retained diagnostic harnesses, delete valueless experiments, and update the CI policy regression if the new boundary should be permanent.

## Integration-unit rule

Choose the PR boundary to match the inference boundary. Independent architectures should stay separate, but monotonic capacity sweeps and batches of equivalent visual poses should not be split into tiny PRs solely because each parameter value or pose can be.

If an active PR owns the shared runtime surface, additive tooling/configuration may land independently, then the runtime migration should be rebased onto the shared infrastructure rather than spawning a superseding branch.
