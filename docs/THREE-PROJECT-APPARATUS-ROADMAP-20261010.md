# Three-project synthesis implementation roadmap

Part of the [apparatus audit](THREE-PROJECT-APPARATUS-SYNTHESIS-20261010.md) and the [shared evidence spine contract](THREE-PROJECT-SHARED-EVIDENCE-SPINE-20261010.md). This is **ordered guidance, not an independent task queue**. The live `WORK-QUEUE.md` owners accept work when it advances their already assigned Windows/gameplay/presentation deliverables.

## Milestones and acceptance, in dependency order

| Stage | Bounded task and reused apparatus | Reviewable exit | Non-goal / stop |
| --- | --- | --- | --- |
| **0. Source/rights safety** | Re-run `audit_imported_references.py`, `audit_baldosa_source_census.py`, `audit_three_project_apparatus.py`. Review source/license/ROM distribution with repository owner. | Pinned source and imported bytes audit green; recorded ROM-visibility decision. | Do not auto-delete ROMs, rewrite Git history, relicense or publish additional binaries. |
| **1. Bind one real route to its capture** | Extend existing evidence envelope and tool interop, using one current USA original/Baldosa route, exact binary, observed P1/P2 masks and SRAM seed. | Reproducible observed original/native input receipts with candidate identity and a negative-path test for each missing/mismatched input. | Stop if a route only has a stored script but no proof the emulator consumed it. No new runner. |
| **2. First complete strict USA game event** | Use original Snes9x, paired native route and QA-01/07. Investigate Switcher stack/NMI or select a shorter source-proven result route. Query mal effective-address tools only for a narrowly identified gap. | One **complete settled original/native event** and authentic time/winner/score/progression, unmasked relevant stack, exact original/native time domains and independent review. | Three non-discriminating experiments → preserve the negative result and revise causal hypothesis. No +1 frame guess or masked release oracle. |
| **3. First verified original DMA/PPU path** | Reuse bounded `report_ppu_direct_write_provenance.py`, `report_snes9x_dma_entry_provenance.py`, original PPU observer and mal register-order insight. | One live original DMA entry **plus** relevant latch/state/transfer completion evidence, and native comparison through source-visible P1/P2 final pixels. | No inferred HDMA, VMADD/OAMADD or OBJ winner from a descriptor. No HD art shipping authority from decoder tests. |
| **4. Complete Modern Windows player journey** | Current Baldosa guest + Modern frontend/profile/SRAM transaction/record/ghost/replay/2P modules, QA-02 and physical Windows packages. | Single exact Windows ZIP/candidate: cold start, two pads, real 1P and 2P events/results, legitimate Records, quit/restart and fresh-process save recovery. | Don't count host-created results, UI screenshots, a Linux CI smoke or a partially completed tour. |
| **5. Promote tested discoveries once** | Baldosa USA byte-identical assembly + mal PAL map + UR original traces, via existing canonical symbol crosswalk, adapters and agent context. | Individually reviewed original address/semantic evidence; one canonical name propagates into supported tools and regenerated source without modifying guest meaning. | No automatic promotion of ambiguous PAL intervals or external source names. |
| **6. Optimize proven hot paths and CI** | Use Baldosa Tier-2 advisory on the accepted real route; consider isolated M/X root/clock/HDMA/framework port. Run a read-only mal dependency-closure reuse pilot on one stable expensive CI gate. | Quantified work reduction, unchanged source/native acceptance, changed real dependency forces a new test. | Don't merge the 86 framework commits or introduce automatic evidence skipping without adversarial validation. |
| **7. Breadth and definitive research** | Expand 45-course/event/mode matrix, PAL/USA homolog/code-data maps, RNC/graphics/audio, seeded fuzz after an accepted baseline; assemble reusable technical atlas. | Every item classified original-observed, independently accepted native, candidate, rejected or untested; complete repeatable reproduction packets. | No unbounded source archaeology ahead of Windows beta work or inflated percent-complete claims. |
| **8. Future platforms/features** | Web/PS5/Switch/macOS and editor/tooling after Windows architecture stabilizes. | Platform-specific controller, storage, renderer and packaging smoke on real hardware/platform. | No takeover of the current Windows x64 engineering lanes. |

## How adoption decisions are made

All **35 concrete capability families** are enumerated in `analysis/data/three-project-apparatus-capability-matrix-20261010.json`; every reference path is validated against the pinned source trees.

1. **Keep UR authority:** Native Baldosa Windows guest integration, original-multicore emulator QA, complete-event ledger, Modern product, profile persistence, true widescreen, HD/OBJ, packaging, recruitment capture and canonical symbols. Different upstream solutions become explanatory references, not parallel owners.
2. **Use external evidence now:** Baldosa's USA source/disassembly and deterministic routes; malmazuke's PAL annotated semantics, original-access/decode records, static map and research provenance. Require original USA observation before semantic promotion.
3. **Adopt bounded algorithms when a named blocker benefits:** mal effective-address reconstruction and full DMA/HDMA chronology for QA-01/08; selected Baldosa framework timing/OAM/root patches after actual failure; mal replay localization. New adapters must fail closed on missing fields.
4. **Consider measured performance work after proof:** Baldosa Tier-2 hot interpreted instruction list, mal gate-identity reuse, reproducible evidence retention. Savings count only after subtracting new CI, review and flaky-experiment costs.
5. **Defer or reject duplication:** second native core or frontend, reimplementing RNC and 65816 decoding, mal's incomplete mini-PPU as visual truth, Baldosa's weaker shortened-route comparator, general-purpose new coordinator, cross-region percent-transfer claims and automatic root promotions.

### Explicit backlog of unique upstream techniques not yet proved in UR

| Mechanism | Present level | Real acceptance proof required |
| --- | --- | --- |
| mal effective-address read/write reconstruction | Source-inspected; existing UR writer tools | Original pre-instruction PC/regs/opcodes trace, first named causal consumer, adversarial indirect-width test |
| mal DMA register-order provenance | Bounded first-party CPU-direct and entry diagnostic **adapted**, no complete original transfer | Live original channel, PPU latch history, HDMA context and resulting final PPU/OBJ visibility |
| mal fail-closed gate identity | Inspected, not enabled | Ninja dependencies including toolchain, generated program, ROM, fixture; changed input forces rerun |
| mal deterministic native fuzz | Inspected, deferred | Seeded native-vs-USA original perturbations on already accepted full course, new reproducible counterexample |
| mal original-code static breadth | Address index imported; USA maps remain selective | Mapped original USA instruction coverage, measured separately from PAL; links to original decoded bytes |
| Baldosa Tier-2 AOT cost feedback | First-party read-only advisor tested, no real integrated capture | Real route-bound report with complete build/fixture provenance and meaningful guest/native performance discriminator |
| Baldosa matching-assembly regeneration | Source imported; analyzer-derived names available | Reassemble byte-identical USA ROM and independently resolve important M/X/data ambiguity |
| Baldosa automatic naming and ownership | External process studied; local canonical adapters exist | Candidate-reviewed symbols fan out once; semantic grouping doesn't split coupled work or create conflicting owners |
| Baldosa framework delta | 86-commit audit exists; selected patch experiments | Isolated failing witness, independent original/native acceptance, no regression across 1P/2P, Windows and graphics |
| Three-way same-route evidence | Concept and existing envelopes, not one fully accepted shared end-to-end packet | Actual original/Baldosa/Modern route with observed same inputs and independent QA/product/graphics verdicts |

## Continuous effectiveness checks

Every accepted lane update should state **what changed for a player or original-game truth**, exact candidate, now-reproducible source witness, which prior experiment was superseded and how much costly repeated capture/review it eliminated. Compare accepted end-to-end journeys and independently adjudicated knowledge against agent-hours where measurable, not commits, total PRs or misleading unscoped percentage.

Keep stable QA and research artifacts content-addressed where possible. An agent may use a common receipt to avoid repeating an original ROM capture but **must still perform independent interpretation and review** for an affected high-risk gameplay, data or source-visible PPU decision. Experimental dead ends go to the research ledger; they do not silently turn into backlog tasks or release defects.

Future upstream refreshes are **explicit**: fetch a new pinned tree, diff the machine inventories, classify previously unseen/mutated source by family, prioritize only capabilities with expected marginal value, then independently test any adoption. No untracked default-branch update. Run the apparatus audit when the matrix or pinned snapshots change; CI should not invoke external ROM-dependent analyses by default.

## Distribution/rights action is separate and important

At the audit, GitHub reported `gamesbyian/UR-Recomp` **public**, while the audited `main` Git tree contains four approximately 2 MiB `.sfc` original-game ROM files under `reference/roms/`. The repo's `docs/ROM-SAFETY.md` says proprietary ROM bytes must not be publicly reachable. The owner should promptly resolve repository visibility and history exposure with appropriate legal/repository guidance before recruitment distribution. A later deletion commit **does not erase public Git history**, and tooling synthesis cannot cure a distribution problem. This plan does not make a privacy change, delete artifacts or rewrite history.

Baldosa's external code is PolyForm Noncommercial; malmazuke's is MIT. Maintain exact upstream copyright/license attribution. A first-party tool inspired by an algorithm is not carte blanche to copy restricted implementation code into a production binary.
