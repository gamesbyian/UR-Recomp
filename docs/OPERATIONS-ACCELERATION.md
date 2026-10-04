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

Automatic `push`/merge workflows must remain path-scoped to inputs that can change their result. A change to the canonical `snesrecomp` toolchain entry or one of its registered framework patches is intentionally treated as execution-affecting by the bootstrap gate plus the small native/reference canary set; that fan-out is not accidental merge tax. Do not add broad `push` triggers to manual research probes merely for visibility.

Use `concurrency` on every automatic workflow. Superseded branch/PR runs should cancel. Evidence-writing workflows may serialize `main`, but should still cancel stale non-main runs with `cancel-in-progress: ${{ github.ref != 'refs/heads/main' }}`.

Shard only independent expensive work. Current high-cost examples already using useful parallelism are Native UI capture (four shards), toolchain build-smoke (per-tool matrix), SNESRecomp C2 audit (backend matrix), and the independent Widescreen capacity probes. Long workflows such as the native Widescreen runtime hook and the 2P/VS reference replays intentionally reuse one generated/native build and then consume dependent evidence serially; do not duplicate that expensive build merely to claim sharding. If those become repeated merge-path costs, first split out a reusable build artifact, then fan independent replay/analysis jobs from that artifact.

## Integration-unit rule

Choose the PR boundary to match the inference boundary. Independent architectures should stay separate, but monotonic capacity sweeps and batches of equivalent visual poses should not be split into tiny PRs solely because each parameter value or pose can be.

If an active PR owns the shared runtime surface, additive tooling/configuration may land independently, then the runtime migration should be rebased onto the shared infrastructure rather than spawning a superseding branch.
