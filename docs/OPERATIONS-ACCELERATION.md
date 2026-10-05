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

A third copy of format parsing, checksum logic, PPM/frame inspection, run-artifact validation, profile/catalog validation or semantic catalog joining is a signal to centralize. CI should invoke the same validator product tools use where practical rather than maintaining grep/Python lookalikes.

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

### Automatic-trigger and sharding policy

Pure validation runs should execute on `pull_request`, not repeat on the merge commit. A `push` trigger for `main` is reserved for work that is meaningfully post-merge, such as persisting canonical evidence. `tests/unit/test_ci_trigger_policy.py` enforces that rule and keeps the explicit evidence-writing exceptions small.

Automatic `push`/merge workflows must remain path-scoped to inputs that can change their result. A change to the canonical `snesrecomp` toolchain entry or one of its registered framework patches is intentionally treated as execution-affecting by the bootstrap gate plus the small native/reference canary set; that fan-out is not accidental merge tax. Do not add broad `push` triggers to manual research probes merely for visibility.

Use `concurrency` on every automatic workflow. Superseded branch/PR runs should cancel. Evidence-writing workflows may serialize `main`, but should still cancel stale non-main runs with `cancel-in-progress: ${{ github.ref != 'refs/heads/main' }}`.

Shard only independent expensive work. Current high-cost examples already using useful parallelism are Native UI capture (four shards), toolchain build-smoke (per-tool matrix), SNESRecomp C2 audit (backend matrix), and the independent Widescreen capacity probes. Long workflows such as the native Widescreen runtime hook and the 2P/VS reference replays intentionally reuse one generated/native build and then consume dependent evidence serially; do not duplicate that expensive build merely to claim sharding. If those become repeated merge-path costs, first split out a reusable build artifact, then fan independent replay/analysis jobs from that artifact.

## Integration-unit rule

Choose the PR boundary to match the inference boundary. Independent architectures should stay separate, but monotonic capacity sweeps and batches of equivalent visual poses should not be split into tiny PRs solely because each parameter value or pose can be.

If an active PR owns the shared runtime surface, additive tooling/configuration may land independently, then the runtime migration should be rebased onto the shared infrastructure rather than spawning a superseding branch.
