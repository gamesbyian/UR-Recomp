# Documentation ownership

Task routing lives in [`../AGENTS.md`](../AGENTS.md). This file inventories ownership; it is not a second agent guide.

| Document | Owns |
|---|---|
| [`WORK-QUEUE.md`](WORK-QUEUE.md) | Current execution milestones, completion state, and dependency order |
| [`knowledge/README.md`](knowledge/README.md) | Current synthesized mental model of how Uniracers works, with subsystem pages and explicit uncertainty |
| [`PROJECT-PLAN.md`](PROJECT-PLAN.md) | Canonical product/engineering plan for the Uniracers modern port; defines Widescreen and HD Presentation as separate features |
| [`RESOURCE-COLLECTION-AND-DEV-RESEARCH-PLAN.md`](RESOURCE-COLLECTION-AND-DEV-RESEARCH-PLAN.md) | Current combined research/execution strategy and next discriminating work |
| [`BRINGUP.md`](BRINGUP.md) | Chronological native build/runtime attempts and empirical outcomes |
| [`VALIDATION.md`](VALIDATION.md) | Fidelity hierarchy, deterministic comparison strategy, and finish-line validation principles |
| [`RECOMP-C-PRACTICES.md`](RECOMP-C-PRACTICES.md) | First-party handwritten C/C-ABI semantics, guest/host ownership, integer/address safety, warnings, and sanitizer policy |
| [`COURSE-FORMAT.md`](COURSE-FORMAT.md) | RNC/course-format investigation and current structural understanding |
| [`UI-STATE-MAP.md`](UI-STATE-MAP.md) | Frontend/menu state graph, navigation evidence, screenshot-atlas workflow, and unresolved UI transitions |
| [`RESEARCH-LEDGER.md`](RESEARCH-LEDGER.md) | Evidence-backed ROM/hardware/runtime claims, including hypotheses and rejected interpretations |
| [`SYMBOLS.md`](SYMBOLS.md) | Reconstructed code/data/RAM symbols |
| [`FRAMEWORK-PIN.md`](FRAMEWORK-PIN.md) | SNESRecomp revision and pin rationale |
| [`ROM-SAFETY.md`](ROM-SAFETY.md) | Private-ROM handling and public-release boundary |
| [`WIDESCREEN-RECONNAISSANCE.md`](WIDESCREEN-RECONNAISSANCE.md) | Phase F staged-exposure harness, horizontal-domain model, aspect policy, scene classification, and split-screen widening evidence contract |
| [`bonus/WIDESCREEN-ROM-HACK.md`](bonus/WIDESCREEN-ROM-HACK.md) | Quarantined emulator-assisted widescreen SNES ROM-hack bonus project; non-blocking and not part of the shipping architecture |
| [`TOOLCHAIN.md`](TOOLCHAIN.md) | Research/development tool roles, installation policy, and selection guidance |
| [`AI-ASSISTED-REVERSE-ENGINEERING.md`](AI-ASSISTED-REVERSE-ENGINEERING.md) | Imported AI/agent reverse-engineering workflow practices, evidence/oracle rules, and adoption guidance |
| [`TOOL-INTEROPERABILITY.md`](TOOL-INTEROPERABILITY.md) | Tool input/output formats, verified handoffs, adapter seams, and efficient multi-tool chains |
| [`MESEN-CDL-ADAPTER-CONTRACT.md`](MESEN-CDL-ADAPTER-CONTRACT.md) | Bounded fail-closed contract for translating Mesen CDL coverage into project-owned normalized semantics |
| [`TOOLING-AUDIT-CLOSEOUT.md`](TOOLING-AUDIT-CLOSEOUT.md) | Remaining tooling-audit scope, priority order, transfer/defer rules, and closure condition |
| [`THIRD-PARTY-CODE-AUDIT.md`](THIRD-PARTY-CODE-AUDIT.md) | Review status, defects, adaptation rules and promotion checklist for imported executable/source artifacts |
| [`PERIODIC-REPOSITORY-HYGIENE.md`](PERIODIC-REPOSITORY-HYGIENE.md) | Recurring repository entropy-control procedure |
| [`CI-WORKFLOW-BEST-PRACTICES.md`](CI-WORKFLOW-BEST-PRACTICES.md) | Canonical GitHub Actions trigger, concurrency, timeout, build, artifact, and research-workflow design policy |
| [`OPERATIONS-ACCELERATION.md`](OPERATIONS-ACCELERATION.md) | Shared structured-evidence, parameterized-experiment, pose-equivalence, agent-context, work-queue-density, and measured-CI optimization contracts |
| [`original-development/DEVELOPER-TECHNICAL-HISTORY.md`](original-development/DEVELOPER-TECHNICAL-HISTORY.md) | Confidence-labelled history of original DMA development |
| [`original-development/ACQUISITION-LEDGER.md`](original-development/ACQUISITION-LEDGER.md) | Acquired/missing external artifacts and intake status |
| [`original-development/SOURCE-INDEX.md`](original-development/SOURCE-INDEX.md) | Original-development source provenance |

External research sources are owned by `reference/catalog.yml`; see `reference/README.md`. Compact machine-generated ROM analyses live in `analysis/generated/`.

- `HD-VISUAL-REFERENCE-PIPELINE.md` — controlled emulator/shader/upscaler reference strategy for Phase E and 4K replacement art, including provenance and headless-capture requirements.
- `HD-ART-DIRECTION.md` — visual-language and asset-approval rules for coherent HD Presentation reconstruction.
- `ASSET-RESTORATION-PIPELINE.md` — production graphics/audio restoration hierarchy, tool families, provenance rules, model-handling policy, and approval workflow.
## Documentation hygiene

Current authorities say what is true now. Replace stale claims instead of appending corrections beneath them. Chronology belongs in `BRINGUP.md`, dated evidence, or the research ledger as appropriate.

The knowledge base is intentionally cross-cutting: it may summarize conclusions owned elsewhere in order to explain how systems fit together. It should link to or name the owning evidence surface instead of becoming a competing provenance or milestone ledger.

A mutable fact gets one owner. Do not copy milestone state, hashes, tool pins, or current conclusions into several live documents unless duplication is required for a machine contract.

Large histories and imported sources are drill-down material, not required orientation. If a current authority starts becoming an append-only diary, move dated detail to the appropriate evidence surface and keep the current contract compact.

## Platform targets

- `PLATFORM-TARGETS.md` — shipping/feasibility target matrix and host portability rules.
- `SWITCH-HOMEBREW-PORT.md` — public-toolchain Nintendo Switch homebrew feasibility plan.
- `WEB-HOST-FEASIBILITY.md` — bounded WebAssembly/browser host feasibility contract.
