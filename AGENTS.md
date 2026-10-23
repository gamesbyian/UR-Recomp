# UR-Recomp: agent guide

**Goal:** deliver a fully playable, faithful Uniracers remaster, with usable modern menus, complete controller journeys and reliable records/profiles. The immediate critical path is the **private Windows x64 release**, independently qualified against original/native behavior, exact packaged builds and release QA. The repository itself is public; avoid assuming that a private distribution target makes source, ROMs or third-party assets publishable.

This is the **small orientation and enduring contract**, not a progress diary. The [live work queue](docs/WORK-QUEUE.md) owns priority, the [durable project plan](docs/PROJECT-PLAN.md) owns product intent, the [document map](docs/README.md) owns reference routing and [release quality ledger](docs/RELEASE-QUALITY-LEDGER.json) alone owns acceptance. Read current source, PRs and recent merged evidence before trusting a dated description. An unclosed test, ongoing research or tool prototype does not grant a release gate.

## Dispatch and task routes

| Task | Start here |
|---|---|
| New agent / current release blocker | `docs/WORK-QUEUE.md`, current PRs, then the owning specialist and direct code. For assigned lanes: `python3 tools/build_agent_context.py <lane>` |
| Five scheduled agents, slot assignments, manual/vault coordination | `docs/HOURLY-AGENT-LINES.md` (only live slot owner), `docs/AGENT-COORDINATION.md`, relevant active PR. Position numbers are not durable work IDs |
| Windows boot/build, exact package, native host | `docs/BRINGUP.md`, `docs/VALIDATION.md`, `docs/PLATFORM-TARGETS.md`, current workflow/host source |
| Modern menus, controller, screen state and 2P | `docs/UI-STATE-MAP.md`, `analysis/ui-state-map.yml`, `analysis/ui-capture-manifest.json`, `docs/TWO-PLAYER-FIXTURE-PLAN.md` |
| Original/native gameplay, fidelity, timing, QA | `docs/QA-BOUNDED-RELEASE-CAMPAIGN.md`, `docs/QA-PLAYER-JOURNEYS.md`, `docs/VALIDATION.md`, `docs/RELEASE-QUALITY-LEDGER.json` |
| Baldosa/Modern adapter, records, profiles or migration | `docs/BALDOSA-FIRST-CORE-MIGRATION-20261009.md`, `docs/BALDOSA-UR-RECOMP-REUSE-AUDIT-20261009.md`, current adapters and tests |
| Widescreen/presentation or racer art | `docs/WIDESCREEN.md`, `docs/HD-RACER-CHARACTER-RECONSTRUCTION.md`, `docs/HD-ART-DIRECTION.md`, `docs/DISPLAY-PRESENTATION-POLICY.md` |
| Course formats, original/code archaeology, recovered symbols | `docs/COURSE-FORMAT.md`, `docs/RESEARCH-LEDGER.md`, `docs/CROSS-PROJECT-BEHAVIOR-CORROBORATION.md`, `docs/SYMBOLS.md` as appropriate |
| C guest/ABI, platform portability | `docs/RECOMP-C-PRACTICES.md`, `docs/VALIDATION.md`, `docs/PLATFORM-TARGETS.md` |
| Tool choice, third-party research or source adoption | `docs/TOOLCHAIN.md`, `docs/TRUSTED-UPSTREAM-ADOPTION.md`, `docs/THIRD-PARTY-CODE-AUDIT.md`, `docs/EXTERNAL-EVIDENCE-INTAKE.md` |
| CI/workflow efficiency, heavyweight analysis | `docs/CI-WORKFLOW-BEST-PRACTICES.md`, `docs/OPERATIONS-ACCELERATION.md`, `docs/VALIDATION.md` |
| Vault recovery / stranded source / publication | `docs/recovery/RECOVERY-AGENT-DIRECT-INTAKE-HANDOFF.md`, `docs/recovery/RECURRING-VAULT-INTAKE.md`, `docs/recovery/SANDBOX-EVIDENCE-RECOVERY.md`, `docs/recovery/DIRECT-VAULT-INTAKE.md`, publication and preservation contracts |
| Research method or orientation to a subsystem | `docs/knowledge/README.md`, `docs/AI-ASSISTED-REVERSE-ENGINEERING.md`, then source/evidence |
| Periodic repo hygiene, historical diary | `docs/PERIODIC-REPOSITORY-HYGIENE.md`; for diary specifically `prod_diary/README.md` and editorial guide |

For **three-project reuse**, `python3 tools/select_three_project_reuse.py --lane <lane> --include-conditional` identifies existing Baldosa/Malmazuke/UR approaches. Use it before substantial new implementation, not as a reason to create a new R&D programme. The selected option must solve a *current* work-queue problem.

## Owner-aligned execution contract

1. **Work ahead with real deliverables.** Start at fresh `main`, identify the earliest unresolved shipping dependency and work a bounded useful portion autonomously. Treat the prompt as a goal rather than an artificial file boundary; adjacent work is welcome when it materially closes the task. Do not create busywork or resurrect completed archaeology.
2. **Coordinate by actual writes.** Inspect the scheduled five-agent board, Claude's live lanes, current branches/PRs and current file owners. Prefer disjoint work and short, focused PRs. An open PR is not proof of active ownership; a concurrent change to the same source path is a real conflict. Reconcile after merges before claiming completion.
3. **Keep the project executable.** Use existing build, QA, menu and guest abstraction seams; do not fork a competing modern frontend, records store, emulator or replay harness. Reuse one compiled candidate for equivalent tests; keep different evidence classes and platforms separately qualified.
4. **Record truth with one owner.** The queue describes current work, the release ledger controls gate status, knowledge pages synthesize current understanding and dated evidence/report/diary captures history. Correct stale authorities instead of appending another competing status paragraph.
5. **Publish GitHub-first.** Manually launched agents publish code/tests/evidence/progress to branch, PR, issue and owning docs; successful GitHub publication is a complete handoff, with **no routine Drive mirror**. Scheduled agents follow their separate recovery fallback contract. Keep coherent source/tests durable before risky publication, preserve failed operations, and do not disguise or repeatedly evade a safety refusal. The vault is a source of recoverable work, not a second project board.
6. **Finish with verifiable facts.** Tests run and their actual outputs, commit/build identity, remaining failures, evidence provenance, release gates unchanged/changed and one executable next step belong in the PR/issue. A blocked lane gets an exact blocker and conditions for reopening. Merge through existing checks and branch protections when safe.

## Faithfulness and evidence rules

- Preserve genuine original **simulation semantics**, gameplay and player-visible behavior while modernizing presentation, controls and menus. 1P does not stand in for 2P. Widescreen is one feature; do not use 'widescreen/HD' as shorthand for the entire project.
- Independent original ROM/hardware/emulator observation, recomp/native parity and a completed Windows package/controller/storage journey are **different proof classes**. A green build, smoke boot, stage exit, visual screenshot, WRAM similarity or previous-agent declaration never automatically accepts an authentic USA event or a release gate.
- When fidelity differs, seek the **first causally meaningful divergence**. Inspect writers/state transitions and use the existing `snesref` differential route, traces, fixtures and controlled source builds. Stale WRAM bytes, free-running presentation counters, missing producer artifacts, harness timeouts and cancelled/obsolete CI runs should not be mislabeled as gameplay regressions.
- Treat mechanical or reproducible evidence as the oracle when available. A decompiler, model explanation, external patch, generated illustration, imported script or agreement among agents is a hypothesis until qualified. The [research ledger](docs/RESEARCH-LEDGER.md) and [cross-project corroboration](docs/CROSS-PROJECT-BEHAVIOR-CORROBORATION.md) identify negative results and when claims may be reopened.
- For visual art, respect the owner's rejection of procedurally enlarged character artwork lacking original title/packaging likeness. Old render hashes alone are **not artistic approval**. Inspect multiple original poses and seek new explicit visual acceptance before describing shipping art as approved.
- Preserve exact provenance, build hashes and rights of imported evidence. `reference/` houses preserved source material; bulky ROMs, traces, generated C, extracted assets, Ghidra workspaces and captured media are **not automatically suitable for public commits**. The canonical original ROM input and rights constraints belong to the owning inventory; never duplicate or redistribute assets incidentally.

## Evidence economy and CI

Before an experiment, define the decision, prior evidence/control, exact candidate/source/build, cheapest discriminator, expected outcomes, stopping rule and where the result will be recorded. Escalate from existing artifacts → bounded observation → targeted capture → first-divergence trace → independent-core/hardware only as consequence demands. Stop when more observation cannot change a gate, implementation decision or confidence class. After repeated uninformative attempts, consult other emulators, recompilation projects, tooling/source issues and retro-development literature, then report what new premise justifies another trial.

Prefer the cheapest targeted local test, then the owning [validation strategy](docs/VALIDATION.md). `python3 tools/check_repo_hygiene.py` checks repository structure. Native guest/ABI work follows [portable C rules](docs/RECOMP-C-PRACTICES.md). For CI failures inspect the current head and **first failed step**, not cascading skips; producer failures are not scientific negatives.

**Automatic workflows consume a budget.** Classify new workflows as durable PR validation, release regression, manual research, bounded diagnostics or obsolete experiments. Reuse shared builds and proven runner/toolchain paths. Avoid creating recurring CI for one-off research; retire temporary triggers after the question closes. Long evidence runs and Git-writing workflows must not be cancelled by frequent branch pushes; writers serialize with `cancel-in-progress: false` and do not force-push stale output. After workflow changes check trigger-policy tests, YAML and actual fan-out. See [CI workflow practices](docs/CI-WORKFLOW-BEST-PRACTICES.md).

## Boundaries and specialized instructions

Keep generated files and large imported research separate from hand-edited core code. The bonus emulator-assisted ROM hack, future decentralized P2P, extra platforms and promotional experiments do not silently become Windows release blockers. New platforms use host adapters rather than changes to authoritative game simulation. No proprietary SDKs, keys or confidential materials in source.

The historical [pre-audit AGENTS snapshot](docs/archive/AGENTS-PRE-ROUTER-2026-10-22.md) preserves detailed old operational incidents and one-off rules for reference. It is **not another current work queue or override**. When a rare subsystem requires more detail, route to its named current owner above, confirm current source and avoid compulsory full-history reading.
