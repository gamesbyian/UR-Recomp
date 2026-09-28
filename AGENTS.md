# UR-Recomp agent guide

Compact router for coding and research agents. Load the smallest current authority that answers the task. Repository state is canonical over conversational summaries.

## Route by task

| Task | Read first |
|---|---|
| Current priority / continue work | `docs/WORK-QUEUE.md`, then the owning specialist doc |
| Overall widescreen/HD remaster architecture | `docs/WIDESCREEN-HD-REMASTER-PLAN.md` |
| Research strategy / external-resource work | `docs/RESOURCE-COLLECTION-AND-DEV-RESEARCH-PLAN.md` |
| Native build / boot / runtime failure | `docs/BRINGUP.md`, `docs/VALIDATION.md`, then the changed workflow/runtime files |
| ROM identity / preserved build comparison | `analysis/generated/reference-rom-inventory.md`, `analysis/generated/reference-rom-comparison.md` |
| RNC / course-format work | `docs/COURSE-FORMAT.md`, then relevant generated analyses/tools |
| Established reverse-engineering claim | `docs/RESEARCH-LEDGER.md` |
| Recovered code/data symbol | `docs/SYMBOLS.md` |
| Original DMA development history / missing artifacts | `docs/original-development/DEVELOPER-TECHNICAL-HISTORY.md`, `docs/original-development/ACQUISITION-LEDGER.md` |
| External source or imported research artifact | `references/README.md`, `references/catalog.yml` |
| Tool choice / installing research software | `docs/TOOLCHAIN.md`, `tools/toolchain.json` |
| Periodic repository hygiene | Execute `docs/PERIODIC-REPOSITORY-HYGIENE.md` from current `main` |

`docs/README.md` inventories document ownership. It is not a second agent guide.

## Working rules

1. Read the current authority and relevant implementation before editing. Historical notes, imported references, generated reports, and old workflow logs do not override current project state.
2. Treat the prompt as the goal, not an artificial file boundary. Do adjacent work when it materially completes the task; avoid unrelated cleanup.
3. Keep current truth separate from chronology. Replace stale state in current authorities; put dated attempts and failures in `BRINGUP.md`, the research ledger, reports, or preserved evidence.
4. A mutable fact should have one owner. Other documents should link rather than maintain competing copies.
5. Close the loop. If code, tooling, or evidence changes a current conclusion, rerun the invalidated check and update the owning authority.
6. Prefer cheap discovery before broad reading. Query filenames, symbols, generated manifests, and the source catalog before opening large histories or imported corpora.
7. Generated bulk output is disposable unless a compact artifact has durable evidence value. Commit reproducible tooling and compact manifests/reports, not giant generated C, traces, dumps, extracted assets, or Ghidra workspaces.
8. External claims are leads until reproduced locally. Record observation, evidence, interpretation, and uncertainty separately.
9. Preserve exact provenance for imported artifacts: source, retrieval date, original filename, hashes/revision, container relationship, and rights/licensing status where known.
10. Do not weaken a deterministic validation guard to make a failure disappear. Fix the underlying assumption, dependency, or harness.
11. Use the cheapest check that answers the current iteration question. GitHub Actions is execution infrastructure, not automatically research evidence.
12. Do not add a recurring workflow merely because a one-off experiment used CI. Durable checks need a durable repository invariant.
13. Keep provider-specific instruction files thin. Shared rules live here.
14. Keep mandatory reading small. Repository growth is acceptable; mandatory-context growth is expensive.

## Repository boundaries

- `reference/` contains project-input and project-local reference material needed to reproduce work, including preserved ROM builds and historical tool packages.
- `references/` is the provenance-managed external research corpus: imported third-party evidence under `references/imported/`, project summaries under `references/notes/`, and the source registry in `references/catalog.yml`.
- `analysis/generated/` contains compact reproducible analysis products suitable for version control.
- `.tools/` is ignored local installation/build space populated by `tools/bootstrap_toolchain.py`.
- Scratch captures, savestates, traces, extracted assets, generated recompilation output, emulator workspaces, and bulky intermediate products stay ignored unless deliberately promoted with provenance and a documented reason.

The private repository intentionally tracks preserved ROMs under `reference/roms/`. Do not move, duplicate, publish, or silently substitute them. `reference/roms/retail/Uniracers_USA.sfc` is the canonical recompilation input unless the task explicitly concerns another preserved build.

## Validation

For repository structure/hygiene:

```bash
python3 tools/check_repo_hygiene.py
```

For ROM identity or analysis work, use the existing deterministic tools in `tools/` and regenerate the owning compact report. For native execution, follow `docs/VALIDATION.md`; SNESRecomp's `snesref` is the preferred differential harness once deterministic input/state comparison is needed.

Do not use GUI-only observations as the sole basis for a fidelity claim when a deterministic trace, frame dump, memory comparison, or reproducible script can decide it.
