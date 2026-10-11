# Three-project R&D apparatus synthesis: one evidence spine, three independent strengths

**Working audit, 2026-10-10 (UTC 2026-10-11).** This is a bounded engineering plan, not a new task queue, an AOT promotion authority, a release gate, a distribution approval, or an assertion that upstream systems have all been executed. The live [WORK-QUEUE](WORK-QUEUE.md), enduring [PROJECT-PLAN](PROJECT-PLAN.md) and sole [release ledger](RELEASE-QUALITY-LEDGER.json) retain their existing authority. Keep the recruitment-media agent's exclusive lane independent.

## 1. Scope and what has actually been inspected

This audit uses **frozen Git trees**, not changing default-branch URLs:

| System | Audited commit | Scope of file-level inventory | Research strength |
| --- | --- | --- | --- |
| Baldosa | [`10b864b9d14a7b7416dd909eb7b054c88faef101`](https://github.com/baldosa/uniracers-recomp/tree/10b864b9d14a7b7416dd909eb7b054c88faef101) | **210 total Git entries** (186 blobs), indexed already in `analysis/data/baldosa-upstream-file-census.json`; 85 maintainer-authored files imported and independently audited | USA-first SNESRecomp native backend, M/X-aware analyzer/disassembler, byte-round-trip matching assembly, automatic root promotion, route coverage and named source |
| malmazuke | [`42d444594641d23f5d3c15da7b7c454bb5180e43`](https://github.com/malmazuke/unirally-reconstruction/tree/42d444594641d23f5d3c15da7b7c454bb5180e43) | **1,062 total Git entries** (1,006 blobs; 116 files under `tools/`) captured in `analysis/data/malmazuke-upstream-file-census-20261010.json`; 18 selected files already imported under audited provenance | Independently authored PAL native C++ semantics, bsnes/replay laboratory, effective-address and transfer provenance, instruction mapping, differential fuzz, risk review and reproducibility |
| UR-Recomp | `a6537bd10d76e95e239529b9133a89cd00dab4d0` | **7,908 blobs** in audited Git tree; project-owned apparatus/evidence snapshot contains **2,680 entries** including 506 `tools/`, 938 `tests/`, 200 `docs/`, 132 workflows, 358 `analysis/`, 311 `reference/` and 235 `native/` entries. All individually inventoried in `analysis/data/ur-project-apparatus-census-20261010.json`; excludes 5,067 third-party files and unrelated artifacts | Cross-ROM archaeology, original-reference multicore QA, Windows Modern product and persistence, accurate source-backed widescreen/4K/HD, agent operations and release evidence |

The **35-family [machine capability matrix](../analysis/data/three-project-apparatus-capability-matrix-20261010.json)** pairs concrete file paths with adoption decisions, the specific remaining gap, priority and required acceptance evidence. Run:

```bash
python3 tools/audit_three_project_apparatus.py
python3 -m unittest tests.unit.test_audit_three_project_apparatus
```

The audit script fails if an upstream file is missing from the pinned census, a path is duplicated, a snapshot pin/count changes, a claim cites an unknown source path, or a capability has no disposition/proof. **It does not claim to have run or semantically reverse-engineered every one of the 1,006 malmazuke files or 7,908 UR files.** Full *file* coverage and *behavioral capability* verification are different guarantees. An upstream rebase requires a separately pinned census and evidence comparison, not silent refresh.

### Confidence grades for future adoption reports

- **I: inventoried.** Original path, blob SHA, frozen repo identity and license recorded. Completeness is checked against a frozen tree.
- **S: source inspected.** Inputs, outputs, side effects, hidden dependencies and source assumptions identified; code/data/region provenance named.
- **P: ported/adapted.** First-party adapter or allowed imported reference present, dependency conflict resolved, no duplicative authoritative system.
- **T: contract tested.** Synthetic negative-path tests, representative real artifacts and validation in CI; tests identify truncated/ambiguous/invalid evidence.
- **R: real-route accepted.** Original ROM identity, exact input bytes, emulator/native candidate and independent reference witness are captured, immutable and replayable.
- **G: product/release gated.** Source-true game result, Modern/storage/presentation obligations and any withheld reviewer requirements satisfied **on the exact candidate** and entered by authorized QA into the release ledger.

Report all six distinctly. A tool can be I/S/P/T without being R or G. The recent Baldosa Tier-2 advisor and malmazuke DMA entry analysis are **contract tools**, not proof of a real Tier-2/PPU race transfer or a release-ready feature.

## 2. Keep one owner for each truth

**Original USA ROM plus independent original-emulator observations** own original-game behavior, game rules, timing, artifacts, PPU/OAM and settled race results for the Windows target. Known emulator quirks and PAL clock differences need independent probes. Baldosa's matching USA source is an excellent annotation and native implementation; *its own native result is not an independent original-game oracle*. malmazuke's PAL C++ source is a corroborating, region-specific hypothesis; PAL findings cannot establish unobserved USA semantics.

**UR-Recomp's Baldosa-backed runtime** owns shipping guest execution. Keep existing SNESRecomp generator/config and Modern host contract, no second PAL game engine, no wholesale fork upgrade, no hand-editing of emitted guest C. M/X/E variants and any `paced_bus`/interrupt/HDMA changes remain independent patch hypotheses until a named failure and regression support them.

**UR's Modern product** owns profile selection, controller flow, per-profile SRAM, real settled-result admission, records, ghosts/replays, tournaments, safe exit, true 342-wide geometry, 4K-capable output, selectable authentic graphics and HD assets. Neither external project's smaller host scope can redefine these product requirements.

**UR's evidence contract and release ledger** are the only acceptance authorities. Original/native checksum parity, masked route success, a source-name match, a passing parser test, media capture or arbitrary LLM reviewer opinion cannot mint a QA pass. `docs/SYMBOLS.md` is the sole canonical named-symbol authority; third-party descriptions are attributed leads until independently promoted.

**Existing ownership and CI** stay: `docs/WORK-QUEUE.md`, `AGENTS.md`, `tools/tool_interop.json`, `tools/evidence_contract.py`, `reference/catalog.yml`, the import manifest, and the Windows beta campaign. Do not create another ticket registry, emulator harness, build matrix or release-status store.

## 3. What each donor contributes to the shared machine

### Baldosa: compiler-informed source/execution feedback

1. `tools/capture_coverage.sh`, `coverage_iter.sh` and `promote_roots.py` discover native/interpreter transfer costs and 65816 entry mode variants, retain previous capture profiles, then regenerate. **We adopt the advisory analysis and targeted promotion logic, not an autonomous promotion loop**. `tools/report_baldosa_tier2_route_coverage.py` already offers a read-only entry point. It still needs one live captured route, a verifiable input-script binding and a measured optimization/problem.
2. `tools/decomp/{decode_dump,gen_disasm,export_names,annotate_gen,ownership}.py` make the ROM/analyzer's M/X-aware assembly, labels and RAM observations reusable. Our independent `query_baldosa_symbols.py`, `build_baldosa_symbol_crosswalk.py`, comparative code atlas and canonical symbol adapters own the receiving seam. Add no automatic semantic promotion from an external name. For suspicious code, independently verify original bytes and disassembly, then decide whether the canonical reference needs an update.
3. Nine deterministic route scripts and independent reference runner are **distinct inputs**, not drop-in UR fixture replacements. Normalize their executed masks, deterministic SRAM seed and result observations before comparison; their masking of the stack page and tolerance of timing-phase differences are not allowed to soften QA-01.
4. The `baldosa/snesrecomp` 86-commit post-UR fork delta is **not** a monolithic upgrade. Isolate the optional HDMA OAM pin, clock-driven $4212 reads, compiled entry/interrupt handoff or `paced_bus` only against a reproduced candidate-bound issue.
5. Baldosa's `firstdiff.py` has a potential short-trace equality pitfall; UR's `check_framedump_identity.py` already guards frame counts and missing extents. **Do not copy the weaker comparator.**

### malmazuke: causality, coverage classes and research discipline

1. `unirally_lab/access/{derive,modes}.py`, `content/provenance.py` and `reference/bsnes.py` map instruction/read-write/PPU transfer chronology to original code. Our new first-party CPU-direct and DMA-entry reporters capture *some* fields but **do not yet know DMA completion, PPU address latches, scanline HDMA ownership or final visibility**. A real original/reference probe is the next step; avoid a misleading inferred pixel.
2. `coverage/{static_map,native_symbols,mapping}.py` plus annotated PAL C++ and research records create a coherent original address-to-meaning map. We've adopted a pinned 1,739-address map, cautious USA interval candidates, searchable research links and gap reports. Continue from existing `cross-build-symbol-correspondence.json` and compare the original USA code; don't create a second symbol system or extrapolate PAL percentages.
3. `replay/commands.py`, native reference/freezes and `dragster_diff_fuzz.py` make first divergence and minimal counterexamples repeatable. UR already has stricter source/native checks; only introduce seeded fuzz after one fully accepted USA event so the output is meaningful.
4. `native/gate_identity.py` demonstrates how Ninja dependency closure can safely reuse unchanged expensive QA artifacts. First independently test a **read-only reuse recommendation** against adversarial file/toolchain/fixture mutations. A false cache hit is worse than rerunning CI; never auto-skip strict release gates based on filename guesses.
5. `docs/AGENT_WORKFLOW.md` and decisions D-0006/D-0008 advise capability-sized work, limited experiments, fresh independent review scaled to risk and preserved negative findings. Incorporate into the **existing** lane documents and context packets, rather than installing a second coordination framework.
6. Evidence retention can preserve recipe/digest/source identity rather than raw terabytes where truly reproducible, but preserve active gates and unrepeatable original observations. No automatic pruning until regenerated evidence is actually checked.

### UR-Recomp: combine them at our existing decision surfaces

Our strengths are not substitutes for upstream's methods: a multi-original-emulator oracle, three-version structural comparison, 45-course original game breadth, source-visible P1/P2 PPU models, genuine wide-world and HD presentation, full Windows Modern lifecycle, transaction-safe records, reproducible packaging, dual technical-reference ambition and independent release QA. This system must prioritize **accepted playable outcomes** rather than maximizing investigations or native coverage percentages.

