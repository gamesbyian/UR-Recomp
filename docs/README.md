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
| [`COURSE-FORMAT.md`](COURSE-FORMAT.md) | RNC/course-format investigation and current structural understanding |
| [`UI-STATE-MAP.md`](UI-STATE-MAP.md) | Frontend/menu state graph, navigation evidence, screenshot-atlas workflow, and unresolved UI transitions |
| [`RESEARCH-LEDGER.md`](RESEARCH-LEDGER.md) | Evidence-backed ROM/hardware/runtime claims, including hypotheses and rejected interpretations |
| [`SYMBOLS.md`](SYMBOLS.md) | Reconstructed code/data/RAM symbols |
| [`FRAMEWORK-PIN.md`](FRAMEWORK-PIN.md) | SNESRecomp revision and pin rationale |
| [`ROM-SAFETY.md`](ROM-SAFETY.md) | Private-ROM handling and public-release boundary |
| [`WIDESCREEN.md`](WIDESCREEN.md) | Focused implementation notes and invariants for the Widescreen feature; subordinate to the project plan |
| [`TOOLCHAIN.md`](TOOLCHAIN.md) | Research/development tool roles, installation policy, and selection guidance |
| [`TOOL-INTEROPERABILITY.md`](TOOL-INTEROPERABILITY.md) | Tool input/output formats, verified handoffs, adapter seams, and efficient multi-tool chains |
| [`TOOLING-AUDIT-CLOSEOUT.md`](TOOLING-AUDIT-CLOSEOUT.md) | Remaining tooling-audit scope, priority order, transfer/defer rules, and closure condition |
| [`THIRD-PARTY-CODE-AUDIT.md`](THIRD-PARTY-CODE-AUDIT.md) | Review status, defects, adaptation rules and promotion checklist for imported executable/source artifacts |
| [`PERIODIC-REPOSITORY-HYGIENE.md`](PERIODIC-REPOSITORY-HYGIENE.md) | Recurring repository entropy-control procedure |
| [`original-development/DEVELOPER-TECHNICAL-HISTORY.md`](original-development/DEVELOPER-TECHNICAL-HISTORY.md) | Confidence-labelled history of original DMA development |
| [`original-development/ACQUISITION-LEDGER.md`](original-development/ACQUISITION-LEDGER.md) | Acquired/missing external artifacts and intake status |
| [`original-development/SOURCE-INDEX.md`](original-development/SOURCE-INDEX.md) | Original-development source provenance |

External research sources are owned by `references/catalog.yml`; see `references/README.md`. Compact machine-generated ROM analyses live in `analysis/generated/`.

- `HD-VISUAL-REFERENCE-PIPELINE.md` — controlled emulator/shader/upscaler reference strategy for Phase E and 4K replacement art, including provenance and headless-capture requirements.
## Documentation hygiene

Current authorities say what is true now. Replace stale claims instead of appending corrections beneath them. Chronology belongs in `BRINGUP.md`, dated evidence, or the research ledger as appropriate.

The knowledge base is intentionally cross-cutting: it may summarize conclusions owned elsewhere in order to explain how systems fit together. It should link to or name the owning evidence surface instead of becoming a competing provenance or milestone ledger.

A mutable fact gets one owner. Do not copy milestone state, hashes, tool pins, or current conclusions into several live documents unless duplication is required for a machine contract.

Large histories and imported sources are drill-down material, not required orientation. If a current authority starts becoming an append-only diary, move dated detail to the appropriate evidence surface and keep the current contract compact.