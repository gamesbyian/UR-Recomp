# UR-Recomp agent guide

Compact router for coding and research agents. Load the smallest current authority that answers the task. Repository state is canonical over conversational summaries.

## Route by task

| Task | Read first |
|---|---|
| Current priority / continue work | `docs/WORK-QUEUE.md`, then the owning specialist doc; for active standard lanes, `python3 tools/build_agent_context.py <lane>` may generate a bounded orientation packet |
| Understand how the game currently appears to work / orient to a subsystem | `docs/knowledge/README.md`, then the relevant concept page |
| Overall project architecture / product plan | `docs/PROJECT-PLAN.md` |
| Widescreen feature implementation | `docs/WIDESCREEN.md`, then `docs/PROJECT-PLAN.md` |
| Bonus emulator-assisted widescreen ROM hack | `docs/bonus/WIDESCREEN-ROM-HACK.md`; keep isolated from the shipping/native path |
| Research strategy / external-resource work | `docs/RESOURCE-COLLECTION-AND-DEV-RESEARCH-PLAN.md` |
| Native build / boot / runtime failure | `docs/BRINGUP.md`, `docs/VALIDATION.md`, then the changed workflow/runtime files |
| GitHub Actions / CI workflow design or optimization | `docs/CI-WORKFLOW-BEST-PRACTICES.md`, `docs/OPERATIONS-ACCELERATION.md`, then the affected workflow files |
| ROM identity / preserved build comparison | `analysis/generated/reference-rom-inventory.md`, `analysis/generated/reference-rom-comparison.md` |
| RNC / course-format work | `docs/COURSE-FORMAT.md`, then relevant generated analyses/tools |
| Frontend / menu / screen-flow / UI-state work | `docs/UI-STATE-MAP.md`, `analysis/ui-state-map.yml`, then `analysis/ui-capture-manifest.json`; for 2P/VS input coverage also read `docs/TWO-PLAYER-FIXTURE-PLAN.md` |
| Established reverse-engineering claim | `docs/RESEARCH-LEDGER.md` |
| Recovered code/data symbol | `docs/SYMBOLS.md` |
| Original DMA development history / missing artifacts | `docs/original-development/DEVELOPER-TECHNICAL-HISTORY.md`, `docs/original-development/ACQUISITION-LEDGER.md` |
| External source, acquisition lead, or imported research artifact | `docs/EXTERNAL-EVIDENCE-INTAKE.md`, `reference/evidence-worklist.json`, `reference/catalog.yml`, then `docs/THIRD-PARTY-CODE-AUDIT.md` as applicable |
| Tool choice / installing research software | `docs/TOOLCHAIN.md`, `tools/toolchain.json`; for producer/consumer chains and adapters, `docs/TOOL-INTEROPERABILITY.md` |
| AI/LLM-assisted reverse-engineering method | `docs/AI-ASSISTED-REVERSE-ENGINEERING.md`; apply it as technique guidance, not as a second work queue |
| Adopting or adapting imported scripts/source | `docs/THIRD-PARTY-CODE-AUDIT.md`, then the imported source |
| Periodic repository hygiene | Execute `docs/PERIODIC-REPOSITORY-HYGIENE.md` from current `main` |

`docs/README.md` inventories document ownership. It is not a second agent guide.

## Fresh-agent priority rule

If you have no project history, do **not** reconstruct priority from chronology, old PR references, completed phase headings, or the amount of documentation devoted to a topic. Use this order:

1. read the top of `docs/WORK-QUEUE.md`;
2. identify the first unresolved gate on the shipping critical path;
3. use current generated evidence and specialist docs to attack that gate;
4. prefer work that removes uncertainty for multiple downstream features over locally interesting archaeology.

At present the critical path is: first native/reference divergence → semantic executable/state map → exact stock-race and multiplayer fidelity → course/rendering model → stock-art Widescreen → HD Presentation → modern product layer/editor. Acquisition, unused-content research, translation archaeology, and toolchain cleanup are supporting lanes unless they directly unblock that path.


## Working rules

1. Read the current authority and relevant implementation before editing. Historical notes, imported references, generated reports, and old workflow logs do not override current project state.
2. Treat the prompt as the goal, not an artificial file boundary. Do adjacent work when it materially completes the task; avoid unrelated cleanup.
3. Keep current truth separate from chronology. Replace stale state in current authorities; put dated attempts and failures in `BRINGUP.md`, the research ledger, reports, or preserved evidence.
4. A mutable fact should have one owner. Other documents should link rather than maintain competing copies.
5. Close the loop. If code, tooling, or evidence changes a current conclusion, rerun the invalidated check and update the owning authority.
6. Prefer cheap discovery before broad reading. For conceptual orientation, read the relevant `docs/knowledge/` page before opening large histories or imported corpora. Query filenames, symbols, generated manifests, and the source catalog for exact evidence.
7. Generated bulk output is disposable unless a compact artifact has durable evidence value. Commit reproducible tooling and compact manifests/reports, not giant generated C, traces, dumps, extracted assets, or Ghidra workspaces.
8. External claims are leads until reproduced locally. Record observation, evidence, interpretation, and uncertainty separately.
9. Preserve exact provenance for imported artifacts: source, retrieval date, original filename, hashes/revision, container relationship, and rights/licensing status where known.
10. Do not weaken a deterministic validation guard to make a failure disappear. Fix the underlying assumption, dependency, or harness.
11. Use the cheapest check that answers the current iteration question. GitHub Actions is execution infrastructure, not automatically research evidence.
12. Do not add a recurring workflow merely because a one-off experiment used CI. Durable checks need a durable repository invariant.
   For trigger/concurrency/timeout/build/artifact rules, follow `docs/CI-WORKFLOW-BEST-PRACTICES.md`.
13. Keep provider-specific instruction files thin. Shared rules live here.
14. Keep mandatory reading small. Repository growth is acceptable; mandatory-context growth is expensive.
15. Terminology: `Widescreen` and `HD Presentation` name specific features only. Never use `widescreen`, `HD`, or combinations such as `widescreen/HD` as shorthand for the project, its architecture, or its overall goal.
16. `docs/knowledge/` is a synthesis layer, not an evidence ledger. Rewrite it when the current model changes; keep chronology, provenance, raw observations and rejected alternatives in their owning evidence documents.
17. For native/trace CI, never infer runtime failure from a permissive executable fallback, an external wall-clock timeout, or a disconnected debug client. Require the exact generated game target, distinguish harness/tooling failure from guest/runtime failure, and inspect the preserved host log before changing game/runtime code.
18. SNESRecomp's trace TCP server is command/response, not greeting-based. Reuse the established trace client/workflow rather than inventing a new handshake. Trace builds are much slower than ordinary runs, so batch early stepping within the server's synchronous step deadline and give the outer host timeout generous headroom.
19. A full-WRAM differential is a discovery surface, not automatically a fidelity verdict. Classify differences by writer/history and semantics first; stale stack bytes and free-running timing/presentation counters are not simulation mismatches unless they affect a proven invariant.

20. Imported executable code is raw material, not a trusted dependency. Preserve provenance, but normalize useful behavior into project-owned tools and add regression coverage before depending on it.
21. Two-player fixture work is a required fidelity dependency. If touching shared input grammar or engine adapters, preserve or advance `docs/TWO-PLAYER-FIXTURE-PLAN.md`; do not let one-player coverage silently stand in for multiplayer coverage.
22. A UI-atlas gap is not automatically project debt. Apply the completion tiers in `docs/UI-STATE-MAP.md`: close critical-fidelity gaps, harvest cheap evidence, and leave archaeology-only gaps open unless they become implementation-, validation-, compatibility-, or product-relevant.
23. Apply **value-of-information discipline** before expensive evidence work. State the decision/uncertainty being resolved, the cheapest discriminator likely to change that decision, and the stopping condition. Do not collect every available surface merely because it can be collected.
24. Match rigor to consequence. Core simulation, first-divergence, save-state, multiplayer and SNES hardware claims may justify independent corroboration and fine traces. Cosmetic observations, obvious UI behavior, provenance leads and low-impact archaeology usually do not.
25. Escalate evidence progressively: existing artifact/documentation → one bounded observation → targeted state/frame/write capture → first-divergence trace → independent-core/hardware corroboration. Skip levels only when the cheaper level cannot answer the actual question.
26. For video/frame work, search coarsely first and inspect narrowly. Use hashes/deltas/timestamps/state anchors to localize the interesting interval; do not manually inspect or enhance long frame ranges when a binary search or machine comparison can reduce the search space.
27. Stop when the next measurement is unlikely to change implementation, priority, confidence category, or a validation gate. “More evidence” is not itself a deliverable.
28. For opaque RE questions, give the agent a compact semantic neighborhood before broad dumps: callers/callees, xrefs, relevant state/PPU accesses, dynamic participation, competing hypotheses, and the smallest useful trace window.
29. Prefer the narrow debugger primitive that answers the question: writer watch → execution breakpoint → code/data coverage → bounded trace → full trace only if needed.
30. The mechanical oracle decides. Model confidence, documentation completeness, decompiler output, or agreement between agents never substitutes for deterministic bytes/state/execution evidence when a falsifiable check exists.
31. When a bounded approach repeatedly fails to reduce uncertainty, record why and what new evidence would justify retrying before another agent repeats it. Use an existing owning ledger/doc unless repetition becomes common enough to justify a dedicated dead-end artifact.
32. When successive experiments differ only by a parameter, extend a shared harness and structured evidence contract instead of cloning a sibling workflow. Probe the product-relevant endpoint when monotonicity makes that informative, then localize failures with the same harness.
33. Treat exact semantic identity and production identity separately. If deterministic evidence proves multiple semantic states have byte-identical presentation, preserve their semantic guards but reuse the visual asset/work product.
34. Keep `WORK-QUEUE.md` current-state oriented. Move long run histories and repeated measurements to the owning evidence/subsystem surface; `tools/check_work_queue_density.py` is an advisory entropy detector.
35. Prefer a lane context packet from `tools/build_agent_context.py` over repeatedly pasting large authority lists into agent prompts. The generated packet is derived orientation, never a competing authority.

## Research before reinvention

When a task exposes unfamiliar behavior, a stubborn failure, or a technique the repository does not already own, search the broader retro-development ecosystem before building a bespoke answer.

This is a standing problem-solving rule, not a separate archival workstream:

- search externally for analogous failures, techniques, tools, patches, issue threads, postmortems, test ROMs and implementation patterns;
- do not require an exact Uniracers precedent. Relevant ideas may come from other SNES games or from NES, Genesis/Mega Drive, N64, PS1 and other decompilation, recompilation, source-port, emulator, ROM-hacking, randomizer, TAS/debugging, restoration and enhancement projects;
- search the upstream histories and issue trackers of the actual tools involved, especially SNESRecomp/N64Recomp-family projects, emulator cores, debuggers, disassemblers and asset tools;
- favor technical terms that describe the observed failure over generic game-name searches;
- after two or three materially different local attempts fail to reduce uncertainty, broaden the search before adding another custom probe, workaround or instrumentation layer;
- treat discovered solutions as leads, not authority. Reproduce the relevant behavior locally and preserve the smallest useful citation/provenance trail;
- adopt concepts rather than blindly copying historical quirks. Anything promoted into project infrastructure should become a project-owned reproducible tool, fixture, assertion or documented invariant;
- if the search finds nothing useful, record that briefly only when the negative result materially informs the next approach. Do not create ceremonial search logs.

Useful hunting grounds include emulator source/history and issue trackers, consoledev documentation, decomp/recomp repositories, ROM-hacking archives, TAS and randomizer tooling, debugger/test-ROM projects, restoration/enhancement hacks, and technical writeups from native-port projects.

The goal is to make outside knowledge an automatic escape hatch from local tunnel vision without weakening the project's evidence standard.

## Repository boundaries

- `reference/` is the unified research/reference root: preserved ROM builds and historical tool packages live alongside provenance-managed external evidence under `reference/imported/`, project summaries under `reference/notes/`, and the source registry in `reference/catalog.yml`.
- `analysis/generated/` contains compact reproducible analysis products suitable for version control.
- `.tools/` is ignored local installation/build space populated by `tools/bootstrap_toolchain.py`.
- Scratch captures, savestates, traces, extracted assets, generated recompilation output, emulator workspaces, and bulky intermediate products stay ignored unless deliberately promoted with provenance and a documented reason.

The private repository intentionally tracks preserved ROMs under `reference/roms/`. Do not move, duplicate, publish, or silently substitute them. `reference/roms/retail/Uniracers_USA.sfc` is the canonical recompilation input unless the task explicitly concerns another preserved build.

Bonus-project material must not silently become a main-line dependency. In particular, emulator-assisted widescreen ROM-hack work belongs under `docs/bonus/` and a future `bonus/widescreen-romhack/` implementation tree; promote independently useful findings into main authorities only after validating them outside the bonus architecture.

## Validation

For repository structure/hygiene:

```bash
python3 tools/check_repo_hygiene.py
```

For ROM identity or analysis work, use the existing deterministic tools in `tools/` and regenerate the owning compact report. For native execution, follow `docs/VALIDATION.md`; SNESRecomp's `snesref` is the preferred differential harness once deterministic input/state comparison is needed.

Do not use GUI-only observations as the sole basis for a fidelity claim when a deterministic trace, frame dump, memory comparison, or reproducible script can decide it.


## Long evidence workflows

Do not set `cancel-in-progress: true` on long-running evidence workflows whose trigger paths are likely to be edited during the same active research session. That can starve the evidence run indefinitely while an agent makes legitimate incremental commits. Use non-cancelling concurrency for long historical replay, trace, and static-classification jobs; reserve cancellation for cheap superseded checks where losing an earlier run does not erase the only pending discriminator.


## Platform-port tasks

For Windows/macOS/Web/console-host portability work, read `docs/PLATFORM-TARGETS.md` first. For Nintendo Switch homebrew work, also read `docs/SWITCH-HOMEBREW-PORT.md`, `third_party/platform/switch/pins.json`, and the pinned examples under `reference/imported/platforms/switch/`.

Platform agents must preserve the authoritative recompiled simulation and keep OS/console APIs below host interfaces. Do not introduce proprietary SDK files, confidential platform material, keys or device-specific secrets. Compile-only feasibility is not hardware acceptance.
