# Research Ledger

Use this for claims about the ROM, formats, routines, RAM, graphics or hardware behavior. Separate observation from interpretation.

## Entry template

### R-000 — Title

**Status:** hypothesis | supported | confirmed | rejected  
**Date:** YYYY-MM-DD  
**Area:** CPU | RAM | PPU | DMA/HDMA | physics | camera | course | compression | UI | audio | other

**Observation:** what was actually observed.  
**Evidence:** addresses, traces, hashes, debugger output, source references or repeatable steps.  
**Interpretation:** what it probably means.  
**Discriminating test:** smallest test distinguishing this from alternatives.  
**Dependencies:** assumptions this relies upon.  
**Propagation:** after a supported/confirmed semantic claim, note any high-value readers/writers, callers/callees, sibling fields/tables, cross-ROM matches, existing gaps resolved/constrained, and concrete follow-up artifacts or tests. Write `none — bounded/no downstream value` when the pass finds nothing worth pursuing.

---

### Semantic propagation rule

For supported or confirmed claims with semantic value, do one bounded fan-out pass before treating the claim as complete. The purpose is to make each solved field, routine, table or format reduce uncertainty elsewhere.

Use the smallest useful subset of: xrefs/readers/writers, caller/callee neighborhood, sibling/paired storage, adjacent or parallel tables, four-ROM structural correspondence, recovered-source references, and deterministic runtime checks. Promote consequences into existing symbols/tests/parsers/atlas/queue surfaces rather than creating a separate tracking system.

Do not propagate weak names as facts. Hypotheses remain hypotheses, cross-ROM labels retain provenance/confidence, and the value-of-information rule still governs how far the fan-out travels.

## Retrospective semantic propagation — 2026-09-30

### R-PROP-001 — Racer-frame marshal exposes exact P1/P2 workspace pairings

**Status:** confirmed  
**Date:** 2026-09-30  
**Area:** RAM | physics | other

**Observation:** `Race_UpdateRacersFrame` at `82:89B9..9384` performs a P1 persistent-state → shared-workspace → common simulation → persistent-state writeback pass, then repeats the same structure for P2 when active.  
**Evidence:** recovered Nitrodon `bank 82.txt`; exact copy pairs summarized in `analysis/generated/retrospective-semantic-propagation-2026-09-30.md`.  
**Interpretation:** P2 X/Y position, X/Y velocity, air time, facing, pitch, Z-state and boost slots are structural siblings of the already established P1 fields; `11CD` is definitively the shared boost workspace with `11CF/11D1` as persistent P1/P2 storage. `0FEF` is explicitly set to 0/2 for the two passes.  
**Discriminating test:** none needed for the storage-boundary claims; isolated 2P causal fixtures remain useful only for game-facing value conventions.  
**Dependencies:** recovered bank-82 listing is treated as an exact disassembly of the canonical USA ROM.  
**Propagation:** promoted high-confidence P2 position/speed, boost-copy, selector and P2 air-time semantics in `docs/SYMBOLS.md`; narrowed the historical `0F63` conflict by showing it is shared workspace loaded from different per-player backing fields.

### R-PROP-002 — Historical course addresses align with RNC boundaries

**Status:** confirmed, with one supported typo repair  
**Date:** 2026-09-30  
**Area:** course | compression

**Observation:** four of Nitrodon's five recovered course addresses convert from LoROM CPU addresses to exact canonical RNC stream starts: `18:8000` → stream 1, `18:8183` → stream 2, `18:A07E` → stream 4, and `1A:9678` → stream 13. The remaining Bowl entry `18:94BA` misses every header, while `18:9B4A` converts exactly to stream 3 at file offset `0x0C1B4A`.  
**Evidence:** `reference/imported/reverse-engineering/nitrodon/ROM addresses.txt`; `analysis/generated/rnc-stream-manifest.json`; derivation in `analysis/generated/retrospective-semantic-propagation-2026-09-30.md`.  
**Interpretation:** historical addresses are SNES CPU addresses for packed course streams. Streams 1/2/4/13 independently identify Dragster/Zoom Zoo/Switcher/Jumps. Bowl is strongly supported as stream 3 with a transposed historical address (`1894BA` vs `189B4A`).  
**Discriminating test:** no further test is warranted unless contradictory evidence appears; the corrected Bowl address landing exactly on the sole adjacent RNC boundary is sufficient for current planning.  
**Dependencies:** standard LoROM CPU-address to file-offset mapping; canonical USA RNC manifest.  
**Propagation:** five course identities are now independent of order-only inference; future historical ROM addresses should be tested as LoROM CPU addresses first.

### R-PROP-003 — Stunt messages are queued in explicit per-player 32-entry rings

**Status:** confirmed  
**Date:** 2026-09-30  
**Area:** RAM | physics | UI

**Observation:** `81:C5B3` enqueues a message into one of two 32-entry WRAM rings, selected by player. P1 storage is `0CBB+` with write index `0CE3`; P2 storage is `0CE5+` with write index `0D0D`; all indices wrap with `AND #$1F`. The stunt finalizer calls the long-entry wrapper `81:C5AF` with stunt/result message IDs.  
**Evidence:** recovered Nitrodon bank-81/bank-82 disassembly; Dessyreqt USJO v14a independently parses `0CBB/0CE1/0CE3` and converts queued stunt-message IDs into delayed boost credit.  
**Interpretation:** the historical queue-aware optimizer is observing the actual in-game stunt-message pipeline. Message presentation and delayed stunt boost are structurally linked, although the exact ROM-side message→boost conversion remains untraced.  
**Discriminating test:** trace the queue consumer that mutates boost, or run one deterministic landing with queue/boost checkpoints before and after message consumption.  
**Dependencies:** exact queue-consumer role of `0CE1/0D0B` is not yet statically named.  
**Propagation:** promoted queue storage/write-index symbols and upgraded `HUD_QueueMessage`; future boost-unit work should begin from this queue consumer rather than from isolated boost writes.

### R-PROP-004 — Racer OAM builder exposes the world→camera→screen boundary

**Status:** confirmed  
**Date:** 2026-09-30  
**Area:** camera | PPU | RAM

**Observation:** `82:ACA5` projects P1 world coordinates `0411/0415` and P2 `0413/0417` relative to camera `0419/041D`, applies horizontal scaling/culling/wrap policy, and writes P1 screen X/Y to `1509/150A` and P2 X/Y to `150D/150E`.  
**Evidence:** recovered Nitrodon bank-82 disassembly; detailed derivation in `analysis/generated/semantic-propagation-boost-oam-2026-09-30.md`.  
**Interpretation:** this routine is a concrete presentation seam for widescreen/HD work: authoritative simulation coordinates are upstream; viewport/culling policy lies in the projection step; screen/OAM state is downstream.  
**Discriminating test:** exact meanings/units of `03ED`, `0421/0423`, and `0D49` should be resolved only when widescreen/course-wrap implementation requires them.  
**Dependencies:** ordinary-race path analyzed; alternate split-screen/mode branches may adjust limits.  
**Propagation:** corrected `1509` from generic TAS “screen X” to P1 screen X, promoted paired screen-coordinate outputs, and marked the projection-policy fields as future widescreen anchors.

### R-PROP-005 — Runtime object code 0x14 is checkpoint/finish behavior

**Status:** confirmed  
**Date:** 2026-09-30  
**Area:** course | RAM | physics

**Observation:** `81:82E6` reads an object byte from `7E:C000,X`, clears bit 0, and dispatches through the jump table at `81:8320`. Even code `0x14` selects `81:8050`, the already-confirmed checkpoint/finish handler.  
**Evidence:** recovered Nitrodon bank-81 disassembly; deterministic Dragster finish fixture already validates the handler's `1199/119D/0EF1` state transitions.  
**Interpretation:** at least part of `7E:C000+` is a runtime course-object behavior map, and `0x14` is a checkpoint/finish object code.  
**Discriminating test:** locate `0x14` cells in the active Dragster map, map them to known checkpoint/finish positions, and trace them backward into the decoded RNC payload.  
**Dependencies:** exact `7E:C000` dimensions/index geometry remain open.  
**Propagation:** promoted `Course_RuntimeObjectMap`, updated the course-format bridge, and made `0x14` the first concrete behavior code for future editor/course decoding.

### R-PROP-006 — Bounce trace contains collision-shape construction plus velocity transform

**Status:** supported at instruction level  
**Date:** 2026-09-30  
**Area:** collision | physics | RAM

**Observation:** the recovered bounce trace through `81:9E2A` reads a compact bank-21 record, uses one byte as a selector into a 16-byte row at `20:BC9F`, combines alternating offsets with base bytes, mirrors by facing, and writes derived geometry under `125B+`. A later block at `81:9546..961B` applies four matrix-like elements to current-player X/Y velocity and writes the transformed pair back to `0F9F/0FA1`.  
**Evidence:** exact Nitrodon trace `bounce tracelog.txt` plus matching bank-81 disassembly.  
**Interpretation:** `81:9E2A` is best treated as collision/contact-shape construction, while `81:9546..961B` is a distinct 2×2 velocity-transform boundary for bounce response.  
**Discriminating test:** replay the recovered bounce case as a deterministic fixture and compare derived `125B+` geometry plus pre/post `0F9F/0FA1`; trace the four transform coefficients upstream only if a collision fidelity defect requires exact surface semantics.  
**Dependencies:** individual `125B+` point meanings and the semantic identity of the `20:BC9F` templates remain open.  
**Propagation:** upgrades the historical trace from archival evidence to a bounded collision fixture and narrows future physics work to shape generation and transform coefficients rather than broad collision archaeology.

### R-PROP-007 — Course header points to a tail resource-ID list

**Status:** confirmed  
**Date:** 2026-09-30  
**Area:** course | compression | RAM

**Observation:** `Course_LoadAndMaterialize` reads the 16-bit word at decoded offsets `0x000B..0x000C` as a cursor into the active `7F:0000` payload, increments it after each byte read, and stops when the resource byte is `FF`. On Dragster the word advances from `0x840F` to `0x8416`; decoded size is `0x8417`.  
**Evidence:** exact bank-82 instruction flow at `82:E1D1..E1F2`; prior runtime traces showing low byte `0x0F→0x16`; canonical decoded size.  
**Interpretation:** the long-standing byte-11 mutation is fully explained as the low byte of a mutable resource-list cursor. Dragster's tail span `0x840F..0x8415` contains six resource IDs followed by the terminating `FF`.  
**Discriminating test:** recover the six IDs and record each resource's cumulative A000/C000 materialization span.  
**Dependencies:** the final decoded byte at `0x8416` remains semantically unassigned.  
**Propagation:** promoted `Course_ResourceListCursor`; revised COURSE-FORMAT; redirected checkpoint-object back-mapping through resource spans rather than raw-byte search.

### R-PROP-008 — Course resources materialize paired A000/C000 runtime planes

**Status:** confirmed structurally  
**Date:** 2026-09-30  
**Area:** course | RAM | rendering

**Observation:** each decoded resource ID enters a five-byte descriptor lookup through `82:B2AD` and a four-byte bank-17 pointer lookup at `17:A000`. `82:E329..E380` appends derived data from the selected resource into separate runtime planes at `7E:A000` and `7E:C000`, with independent cumulative cursors.  
**Evidence:** exact `Course_LoadAndMaterialize` instruction flow.  
**Interpretation:** decoded course data references reusable resources/chunks; the final runtime behavior map is synthesized from selected bank-17 templates. This explains why checkpoint/finish code `0x14` should be attributed to a selected resource span rather than expected verbatim at a simple decoded-stream coordinate.  
**Discriminating test:** for Dragster, enumerate six selected resource IDs, descriptor sizes, C000 output ranges, and which range contains `0x14`.  
**Dependencies:** exact semantic roles of A000, descriptor fields, and chunk dimensions remain open.  
**Propagation:** course/editor planning should model reusable resources explicitly; next format work is reduced to six Dragster resources rather than the full bank-17 corpus.

### R-PROP-009 — Dragster resource 0x24 materializes checkpoint/finish cells

**Status:** confirmed for Dragster  
**Date:** 2026-09-30  
**Area:** course | RAM | methodology

**Observation:** Dragster's resource list is `01 02 14 24 16 18 FF`. Descriptor-derived C000 spans are `1,1,4,9,4,1`, totaling the exact 20-byte runtime behavior plane. Resource `24` therefore owns offsets 6–14, which are nine consecutive `0x14` behavior bytes.  
**Evidence:** frame-exact run 36517460851; recovered bank-82 descriptor table and materializer instruction flow; runtime C000 snapshot.  
**Interpretation:** on Dragster, resource ID `0x24` is the chunk whose behavior-plane contribution consists entirely of checkpoint/finish cells. Resource ID `0x14` is not the checkpoint resource and instead emits `12 1C 00 00`.  
**Discriminating test:** extract all 45 resource lists and match checkpoint-resource candidates by incidence/descriptor/output/behavior fingerprints rather than numeric ID.  
**Dependencies:** game-wide semantic identity of resource `24` is not yet claimed; IDs may be reused/renumbered across builds or contexts.  
**Propagation:** added address-independent course-resource fingerprint tooling and updated COURSE-FORMAT to make structural equivalence, not address equality, the matching rule.

### R-METHOD-001 — Cross-build semantic anchors must survive relocation

**Status:** implemented and corpus-confirmed  
**Date:** 2026-09-30  
**Area:** tooling | decompilation | multi-ROM

**Observation:** recent course-resource work demonstrated a concrete failure mode for literal identity: resource ID `0x14` did not own runtime behavior code `0x14`; structural span attribution instead identified resource `0x24`. The same risk applies to code/data correspondence across builds.  
**Evidence:** `analysis/generated/dragster-resource-span-attribution-2026-09-30.md`; `docs/AI-ASSISTED-REVERSE-ENGINEERING.md`; new `tools/compare_semantic_anchors.py`.  
**Interpretation:** cross-build matching must treat address/ID equality as supporting evidence only. Candidate correspondence should survive relocation by using instruction/byte shape, semantic WRAM/PPU references, callers/callees, table relationships, and runtime role.  
**Discriminating test:** run the matcher over the four preserved ROMs, then manually corroborate the top candidates for the trusted semantic-anchor set before promoting any non-USA labels.  
**Dependencies:** current lightweight matcher proposes candidates from byte n-grams plus semantic-reference recall; it is intentionally not a full CFG matcher.  
**Propagation:** added a synthetic relocation regression and wired the matcher into the comparative-atlas plan; future atlas work can layer normalized CFG/caller-callee evidence on top when useful.

### R-METHOD-002 — Trusted anchors expose build-specific WRAM layout motion

**Status:** supported across multiple independent anchors  
**Date:** 2026-09-30  
**Area:** multi-ROM | RAM | decompilation

**Observation:** relocation-tolerant matching of eight trusted USA semantic anchors finds exact legacy-beta matches and coherent relocated PAL/Europe counterparts. At structurally aligned operand positions, PAL prototype repeatedly maps USA semantic WRAM words by `+0x04`, while Europe repeatedly maps the same classes by `+0x0A`; Europe’s message-ring block instead moves by `+0x06`.  
**Evidence:** workflow runs `36806186428` and `36806317142`; `analysis/generated/cross-build-semantic-anchor-findings-2026-09-30.md`; `tools/compare_semantic_anchors.py`.  
**Interpretation:** cross-build WRAM layouts evolved by structure-specific insert/remove/repack operations. Shared field motion is useful evidence of logical structure membership and should be treated as a semantic signal, not merely relocation noise.  
**Discriminating test:** completed by `tools/build_wram_motion_atlas.py` / run `36807393022`; further splitting is warranted only when an active subsystem question needs it.  
**Dependencies:** Europe checkpoint/finish and HUD queue now have independent edge corroboration; remaining weak cross-build areas are narrower, especially some Europe OAM substructure and single-anchor RAM projections.  
**Propagation:** the bounded atlas confirms multiple independently moving logical blocks; literal USA addresses must not be copied into PAL/Europe symbol maps. The next comparative priority is the isolated USA/beta delta corpus.


### R-METHOD-003 — WRAM motion atlas separates stable and independently moving field families

**Status:** supported across the trusted anchor corpus  
**Date:** 2026-09-30  
**Area:** multi-ROM | RAM | decompilation

**Observation:** clustering structurally aligned semantic operands from the eight trusted anchors produces distinct build-specific motion families. Europe retail has a dominant `+0x0A` family spanning 6 anchors / 29 fields / 99 observations, a `+0x04` family spanning 3 / 12 / 38, a `+0x06` family spanning 2 / 9 / 28, plus stable fields. The PAL prototype has a `+0x04` family spanning 7 / 31 / 108 alongside a stable family spanning 6 / 31 / 90. Legacy beta remains `+0` across all 8 anchors / 62 fields / 212 observations. Repeated USA fields seen in multiple anchors project consistently; no conflicting repeated-field projection appears in the accepted top-match corpus.  
**Evidence:** `tools/build_wram_motion_atlas.py`; `analysis/generated/wram-motion-atlas.{json,md}`; evidence run `36807393022`; unit coverage in `tests/unit/test_build_wram_motion_atlas.py`.  
**Interpretation:** the comparative builds expose logical WRAM block boundaries: Europe underwent several structure-specific insert/remove/repack shifts rather than a global relocation, while the PAL prototype preserves a broad stable block beside a recurrent four-byte-shifted family. Shared motion can therefore constrain likely structure membership before every field is named.  
**Discriminating test:** none needed for the clustering claim. Investigate a cluster boundary or exception only when it intersects an active physics, course, renderer, or fidelity question.  
**Dependencies:** the atlas inherits the correspondence confidence of each accepted top anchor match; weak Europe checkpoint/HUD/OAM candidates remain non-promoted.  
**Propagation:** close the generic WRAM-clustering task. Use the atlas as a lookup/evidence surface for future semantic propagation, and move comparative effort to the bounded 486-byte USA-retail vs legacy-beta cross-analyzer classification corpus.


### R-METHOD-004 — USA/beta delta corpus collapses to SRAM-bank aliasing plus three edits

**Status:** supported; executable delta interpreted  
**Date:** 2026-09-30  
**Area:** multi-ROM | RAM | decompilation

**Observation:** the USA-retail vs legacy-beta non-RNC corpus contains 486 changed bytes. Of these, 483 are exactly `0x77→0x70`, all in file bank 00. snes2asm marks only 39 changed bytes as code-related: 36 operand changes, 2 reachability disagreements, and 1 opcode change. The only three non-`77→70` edits are header byte `00:FFDA 01→33`, `83:8AFF A9 12→A9 32`, and `83:8B16 F0 04→80 04`.  
**Evidence:** `analysis/generated/usa-beta-cross-analyzer.{json,md}`; evidence run `36808261152`; recovered Nitrodon bank-83 listing; local Snes9x `map_LoROMSRAM` and `getset.h` mapping formula.  
**Interpretation:** for 8 KiB SRAM, `SRAMMask=$1FFF`; Snes9x maps banks `$70..$7D` through `(((bank<<16)>>1)|(addr&$7FFF)) & $1FFF`, so the bank contribution is discarded. The pervasive `$77→$70` rewrite is therefore consistent with an SRAM-bank alias convention rather than a gameplay change. The two executable non-alias edits occur in the SRAM boundary/mirroring probe at `83:8AF7`: retail writes across `$77:1FFF`, verifies the wrapped high byte at `$77:0000`, and conditionally jumps to `80:94EB` on failure; beta changes the saved/test seed and replaces that conditional branch with an unconditional branch, bypassing the failure path.  
**Discriminating test:** no blanket second-disassembler pass is justified. Use da65/Ghidra only if a current compatibility/protection question needs independent confirmation of this routine or one of the two snes2asm reachability disagreements.  
**Dependencies:** the 483-byte alias interpretation is strongest where the changed byte is an SRAM bank byte; the corpus-wide systematic substitution plus exact mapper equivalence supports treating the remainder as the same build convention unless contradicted locally.  
**Propagation:** downgrade USA/beta as a broad semantic-difference source. Preserve the SRAM probe as an emulator/protection seam and redirect comparative effort toward PAL/prototype/Europe regions with genuine structural motion.


### R-METHOD-005 — Named cross-build semantics can now be projected with evidence tiers

**Status:** supported and machine-queryable  
**Date:** 2026-09-30  
**Area:** multi-ROM | RAM | decompilation

**Observation:** joining the trusted semantic-anchor matcher, WRAM-motion atlas, and named USA symbol corpus produces a durable build-specific correspondence surface. Repeated cross-anchor support yields strong PAL/Europe mappings for player-1 X/Y position and current-player X/Y velocity. Combined matcher evidence also promotes PAL prototype racer update, stunt finalization, racer OAM build, HUD queue, collision shape/velocity, and course load as strong function correspondences. Europe collision shape/velocity and course load are strong; racer update, OAM build, and stunt finalizer are supported. Europe HUD queue is independently call-edge confirmed at `81:C59C`, and checkpoint/finish is dispatch-confirmed at `81:8050`; the earlier matcher candidate `81:8042` is rejected.  
**Evidence:** `tools/build_cross_build_symbol_correspondence.py`; `analysis/generated/cross-build-symbol-correspondence.{json,md}`; evidence run `36809041878`; permanent tooling-unit suite green on commit `d3117a9`.  
**Interpretation:** regional/prototype reverse engineering no longer needs literal USA addresses or ad hoc prose translation. Known semantics can be projected conservatively with explicit evidence tiers, while weak mappings stay visibly unpromoted.  
**Discriminating test:** use repeated-support RAM mappings directly in regional watch/probe configuration. For single-anchor fields, choose a runtime watch, local xref/disassembly, or another matched routine before promotion.  
**Dependencies:** semantic equivalence remains distinct from address correspondence; supported/candidate function matches may still contain behavioral changes.  
**Propagation:** prefer the generated correspondence surface whenever a PAL prototype or Europe runtime/static question needs known USA semantics translated into that build.


### R-METHOD-006 — Independent edges correct Europe checkpoint and promote HUD queue

**Status:** confirmed for correspondence  
**Date:** 2026-09-30  
**Area:** multi-ROM | course | HUD | control flow

**Observation:** Europe retail has exactly two direct JSR references to the proposed HUD queue target `81:C59C`, matching the USA/PAL call-count pattern; one caller is the structurally corresponding checkpoint/finish path at `81:81BA`. Separately, the relocated Europe course-object dispatcher begins at `81:82BB`, its table at `81:82F5`, and object code `0x14` points directly to `81:8050`.  
**Evidence:** `tools/verify_europe_semantic_edges.py`; `analysis/generated/europe-hud-finish-discriminators.{json,md}`; evidence run `36809304325`; regenerated cross-build correspondence artifact.  
**Interpretation:** Europe `HUD_QueueMessage = 81:C59C` is independently corroborated. Europe `Race_HandleCheckpointFinish = 81:8050` is directly confirmed by the same object-code dispatch relation as USA; the lightweight matcher’s earlier `81:8042` window was a false alignment caused by nearby structurally similar bytes.  
**Discriminating test:** no further identity test is required for these two function correspondences. Future work should focus on behavioral differences inside the confirmed handlers or on weaker OAM/single-anchor RAM mappings.  
**Propagation:** corrected generated correspondence, cross-build findings, `docs/SYMBOLS.md`, and work queue. Treat dispatch/call edges as higher-value corroboration than raw window similarity when they disagree.


### R-METHOD-007 — Regional racer state preserves P1/P2 marshal and writeback roles

**Status:** confirmed for correspondence  
**Date:** 2026-09-30  
**Area:** multi-ROM | physics | 2P | RAM

**Observation:** matched `Race_UpdateRacersFrame` routines in USA, PAL prototype, and Europe preserve bidirectional persistent→working→persistent relations for racer position, velocity, and boost. A first bounded pass proves P1 X/Y speed and boost against known working slots. A second discovery pass finds exactly two persistent slots for each tested state family (X/Y position, X/Y speed, boost), allowing P2 to be recovered as the unique second record without assuming a regional displacement. PAL P2 is `0413/0417`, `04B9/04BD`, boost `11D5`; Europe P2 is `0417/041B`, `04BD/04C1`, boost `11DB`.  
**Evidence:** `tools/verify_regional_racer_state_relations.py`; `tools/discover_regional_racer_slots.py`; generated `regional-racer-state-relations` and `regional-racer-slot-discovery` artifacts; green evidence runs `36809888227` and `36810453122`; permanent tooling tests green.  
**Interpretation:** regional builds preserve the same two-racer marshal→simulate→writeback architecture. These addresses correspond semantically as persistent racer state even where the earlier WRAM-motion atlas did not expose them.  
**Discriminating test:** identity is sufficiently established for these fields. Runtime tests are needed only for behavioral/value differences between builds, not to establish which fields correspond.  
**Dependencies:** matched racer-update routine boundaries and already-established current-player workspace semantics.  
**Propagation:** promote PAL/Europe P1 and P2 position/speed/boost mappings to strong in the cross-build correspondence surface and use them directly for regional 1P/2P watch/probe configuration.


### R-METHOD-006 — PAL apparent boundary churn collapses under homolog alignment

**Status:** supported by independent second witness  
**Date:** 2026-09-30  
**Area:** multi-ROM | decompilation | analyzer calibration

**Observation:** the first same-address snes2asm pass over Europe retail vs the 1994-11-29 PAL prototype reported 2,812 instruction-boundary disagreements and 1,528 reachability disagreements among 5,979 code-related changed bytes. Bounded da65 probes were then aligned independently from trusted USA recovered-code anchors by local raw-byte similarity and supplied M/X state from architectural reset semantics or local REP/SEP transitions, not from snes2asm. Three representative homologs all preserve da65 instruction count, mnemonic sequence and instruction-size sequence despite relocation: reset/init (Europe +0, prototype -9), 16-bit PPU/init block (Europe +15, prototype -9), and joypad helper (Europe +17, prototype -2).  
**Evidence:** `analysis/generated/pal-retail-vs-prototype-snes2asm.{json,md}`; `analysis/generated/pal-da65-adjudication.{json,md}`; `tools/run_pal_da65_adjudication.py`.  
**Interpretation:** a material fraction of same-address snes2asm boundary/reachability churn is relocation/alignment noise rather than true instruction-boundary change. Comparative analysis must align homologous regions before counting analyzer disagreement.  
**Next discriminator:** rebuild the PAL/prototype snes2asm disagreement corpus on locally aligned homolog windows, then send only disagreements that survive alignment to Ghidra/xref analysis.  
**Propagation:** treat same-file-offset code diffs as raw evidence only; analyzer disagreement becomes meaningful after homolog alignment.


### R-METHOD-007 — Homolog alignment removes 96.9% of PAL snes2asm role disagreement

**Status:** supported; residuals bounded  
**Date:** 2026-09-30  
**Area:** multi-ROM | decompilation | analyzer calibration

**Observation:** rescoring the 32 high-value Europe-retail / PAL-prototype snes2asm windows after local raw-byte homolog alignment reduces whole-window code-role disagreements from 3,662 to 114 (96.9%). Twenty-nine of 32 windows fall to zero role disagreement, and the apparent M/X disagreement vanishes in nearly every aligned window.  
**Evidence:** `analysis/generated/pal-snes2asm-homolog-alignment.{json,md}`; independent da65 calibration in R-METHOD-006.  
**Residuals:** only `00:ABA9..ADE2` (91), `00:8C49..8CCA` (18), and `00:C3A9..C450` (5) retain role disagreement. The five `C3A9` residuals fall inside the known frontend command-handler pointer table around `00:C3CB..C3EC`, so they are code-vs-data classification noise rather than an executable boundary dispute. The other two residual windows have low whole-window raw similarity and mix code with text/data, so they require finer-grained homolog alignment before Ghidra escalation.  
**Interpretation:** same-offset disassembly diffing dramatically overstates executable change when regional/prototype layout moves. Homolog alignment is now a required normalization stage before counting analyzer disagreement.  
**Next discriminator:** split the two low-similarity survivor windows along known code/data boundaries, realign subregions, and use bounded da65/Ghidra only if role disagreement survives within high-similarity executable homologs.  
**Propagation:** comparative-atlas disagreement metrics should distinguish raw same-offset disagreement from homolog-aligned disagreement.

## Seed leads to verify locally

### R-SEED-001 — Rob Northen Compression

**Status:** confirmed at packed-data level  
**Date:** 2026-09-28  
**Area:** compression | course

**Observation:** both canonical USA retail and 1994-11-29 PAL prototype ROMs contain exactly 45 valid RNC headers, all Method 1, at identical offsets with matching packed/unpacked sizes and CRCs.

**Evidence:** `analysis/generated/retail-vs-prototype-structure.md`; preserved ProPack sources under `reference/imported/tools/rnc_propack-2.14/`.

**Interpretation:** RNC Method 1 is established binary fact for this 45-stream corpus. Whether every stream is course data remains to be established.

**Action:** independently decompress all 45 streams, verify CRCs, locate the game decoder, and identify semantics.

### R-SEED-002 — Course structure

Historical work reported block/tile-based course representations and very wide layouts.

**Action:** verify exact units, dimensions and indexing rather than inheriting old terminology.

### R-SEED-003 — OAM/HDMA special behavior

Snes9x has historically carried Uniracers-specific handling related to OAM address behavior during HDMA.

**Action:** test the current SNESRecomp runtime before designing a workaround.


---

## External evidence harvested 2026-09-28

### R-EXT-001 — Historical RNC/course extraction

**Status:** supported historical lead  
**Date:** 2026-09-28  
**Area:** compression | course

**Observation:** A preserved ROMhacking.net investigation records successful extraction/decompression of Uniracers course data after Mike Dailly reportedly identified it as Rob Northen Compression (RNC). The same work reports a 256-tile course width and says generated viewer output aligned with independently hand-made maps.  
**Evidence:** `reference/notes/course-reverse-engineering-history.md` and its pinned source URLs.  
**Interpretation:** The ROM should contain an identifiable RNC-based course-data path, but exact record boundaries, RNC method and the meaning of “tile” remain to be reproduced.  
**Discriminating test:** locate candidate RNC headers/decompressor calls in the supported ROM and produce one course image/data structure that independently matches gameplay.  
**Dependencies:** historical forum archive and reported Mike Dailly correspondence.

### R-EXT-002 — Uniracers depends on active-display OAM behavior

**Status:** supported  
**Date:** 2026-09-28  
**Area:** PPU | DMA/HDMA

**Observation:** Current Snes9x source enables an explicit `UNIRACERS` game fix during HDMA writes to $2104, forcing OAM address 0x10c. MAME independently documents Uniracers as the known game that accesses OAM during active display and routes such access to byte offset 0x0218.  
**Evidence:** `reference/notes/oam-active-display.md`; Snes9x revision `1bcc369e89f08243e0a462882fb1f3e42e51de3a`, `dma.cpp` blob `e1ad324c6e94149a777b69054bda5e09337631a6`, `memmap.cpp` blob `04ce87e7362b8dda8cb7a79abfa226e13d3568f4`; MAME revision `dcca0e9b281be806813848db869d9ee54b4ad92e`, `snes_ppu.cpp` blob `525911c9cf3015b27676bcc0aebfecd6e6dd3b64`.  
**Interpretation:** The values are consistent because word-style OAM address 0x10c corresponds to byte offset 0x218. This is a concrete compatibility seam for SNESRecomp bring-up.  
**Discriminating test:** trace Uniracers HDMA writes to $2104 and compare sprite/OAM results on SNESRecomp, a known-correct emulator and, if needed, hardware behavior documentation.  
**Dependencies:** correct interpretation of emulator OAM address units.

### R-EXT-003 — Cheat database as behavioral-address probe set

**Status:** hypothesis generator  
**Date:** 2026-09-28  
**Area:** RAM | physics | UI | other

**Observation:** libretro-database contains 24 Uniracers cheat entries affecting timer behavior, CPU braking, racer speed, stunt scoring, color state, course selection and race/qualification completion.  
**Evidence:** `reference/imported/libretro/Uniracers (USA).cht`, upstream revision and license recorded in `reference/imported/libretro/ATTRIBUTION.md`.  
**Interpretation:** Even without trusting cheat descriptions blindly, these codes are a compact set of candidate ROM/RAM locations for quickly locating important gameplay systems.  
**Discriminating test:** decode each Game Genie code to ROM addresses where applicable, classify RAM-vs-ROM effects, and verify each behavior against the supported ROM.  
**Dependencies:** cheat-code format/version compatibility with the supported US ROM.


### R-EXT-004 — Exact HBlank OAM writes in Vs. mode

**Status:** supported  
**Date:** 2026-09-28  
**Area:** PPU | DMA/HDMA

**Observation:** jgenesis issue #164 reports OAMDATA writes on scanlines 0 and 112 every frame, with values 0xA5 and 0x5A respectively. Both writes are expected to affect high-OAM byte $18, controlling sprites 96–99. The top-half/bottom-half split is implemented by alternately moving sprite pairs 96–97 and 98–99 on/off screen.  
**Evidence:** jgenesis issue #164 and mirrored `reference/imported/emulators/jgenesis/sprites.rs`.  
**Interpretation:** This specifies the exact raster-time mechanism behind the long-known Uniracers OAM quirk and gives us concrete trace assertions for SNESRecomp.  
**Discriminating test:** trace $2104 writes during Vs. mode and verify scanlines, values and resulting high-OAM location against these expectations.  
**Dependencies:** supported ROM behaves equivalently to the version tested by jgenesis.

### R-EXT-005 — Released PAL prototype exists

**Status:** confirmed external artifact  
**Date:** 2026-09-28  
**Area:** other

**Observation:** Hidden Palace lists a publicly released European prototype built 1994-11-29 from a 4-EPROM SHVC-4PV5B-01 board labelled UNIRALLY PAL.  
**Evidence:** `reference/catalog.yml` entry `hidden-palace-uniracers-prototype`.  
**Interpretation:** Binary-diffing this build against retail PAL and US versions could reveal late changes to physics, content, censoring, region logic, compression tables or rendering workarounds.  
**Discriminating test:** acquire the prototype artifact, hash it, identify header/version differences and perform structured binary/behavioral diffs.  
**Dependencies:** exact public prototype file retrieval.


### R-EXT-006 — Recovered Canoe compatibility patch

**Status:** confirmed external artifact  
**Date:** 2026-09-28  
**Area:** PPU | DMA/HDMA | other

**Observation:** The surviving public Google Drive file `uniracers_canoe.ips` was recovered byte-for-byte. It is a 295-byte IPS file created/modified on 2018-03-30. It contains seven records, including JSL hooks at ROM offsets `0x01534C` and `0x015714` into code installed at `0x1FFF00`, plus several smaller patches.  
**Evidence:** `reference/imported/patches/uniracers_canoe.ips` and `reference/imported/patches/uniracers_canoe.md`; SHA-256 `35b695d9cc0667d09f950a05cb3066ada5f0078a50818bc04d348f5ef4f852cf`.  
**Interpretation:** This preserves an independent software workaround for the same active-display OAM behavior documented by Snes9x, MAME and jgenesis. Disassembling it may reveal exactly which game routines Canoe needed redirected and what state the patch synthesizes.  
**Discriminating test:** apply to the verified US baseline, disassemble changed routines, and compare runtime OAM writes with unpatched hardware-faithful behavior.  
**Dependencies:** exact patch revision chronology is inferred from public 2018 discussion and Drive timestamps.

### R-EXT-007 — SRAM tour/progression layout

**Status:** locally corroborated by controlled historical save snapshots  
**Date:** 2026-09-28; updated 2026-09-30  
**Area:** RAM | other

**Observation:** TASVideos research attributes medal state to nine 16-byte tour blocks beginning at SRAM `0x069C`, with one byte per unicycle and values 00/01/02/03 for none/bronze/silver/gold, and reports progression/unlock state near `0x10D3–0x10E2`. Dessyreqt's directly recovered 8 KiB SRAM snapshots now provide the requested controlled differential: `Clean → All Silvers - No Hunter` changes exactly 144 bytes, comprising `0x069C..0x071B` (128 bytes, all `00→02`) and `0x10D3..0x10E2` (16 bytes, all `00→02`). `No Hunter → With Hunter` changes only the same 16-byte `0x10D3..0x10E2` block, uniformly `02→03`.  
**Evidence:** `reference/notes/tas-and-sram-research.md`; `reference/imported/reverse-engineering/dessyreqt/SRAM/`; `analysis/generated/dessyreqt-sram-diff.json`.  
**Interpretation:** The historical progression map is strongly corroborated and the Hunter-associated transition is isolated to a tiny 16-byte region. Do not yet over-name the exact record structure or assume every byte is literally a medal tier without a one-change-at-a-time runtime/save experiment.  
**Discriminating test:** create one controlled Bronze/Silver/Gold change for a single racer/tour and one Hunter unlock transition, then verify the predicted byte(s) and any checksum/copy behavior.  
**Dependencies:** none for byte-layout reconnaissance; semantic promotion still requires controlled in-game writes/saves.

### R-EXT-008 — USJO autonomous stunt bot

**Status:** v8 and later v14/v14a source lineage recovered  
**Date:** 2026-09-28; updated 2026-09-30  
**Area:** physics | RAM | other

**Observation:** TASVideos submission #3072 describes a Lua script named USJO that automated frame-precise stunt behavior and reportedly evolved toward autonomous play. Internal v8 (2008-02-10) is preserved at `reference/imported/tas-bots/usjo8.lua`; Dessyreqt's direct workspace additionally recovers internal v14 (2008-02-14), v14a (2009-11-19), a v14a backup and a v14a test sibling. V14 changes the boost read to a 16-bit word; v14a refactors the optimizer and adds queue-aware delayed boost scoring.  
**Evidence:** recovered v8 source; `reference/notes/tas-and-sram-research.md`; TASVideos submission #3072.  
**Interpretation:** The historical USJO line is now executable source evidence rather than a purely documentary lead. Version 8 directly exposes practical RAM addresses, timing rules, search strategy, stunt grammar, boost scoring and controller-state generation.  
**Discriminating test:** inventory every v8 memory read and timing/scoring assumption, then validate each candidate semantic against the supported ROM/runtime before promotion.  
**Dependencies:** exact v13 remains missing, but v14/v14a supersede it technically; v13 is historical gap-filling only.

### R-EXT-009 — Halamantariel course-map corpus

**Status:** confirmed external reference corpus  
**Date:** 2026-09-28  
**Area:** course | UI

**Observation:** VGMaps currently indexes 44 complete Uniracers course maps credited to Halamantariel. Several are extremely large stitched images, including a 28,128×152 Dragster map and a 36,864×16,111 Downer map.  
**Evidence:** `reference/notes/tas-and-sram-research.md`; VGMaps Uniracers index.  
**Interpretation:** These maps can serve as independent geometric ground truth for a ROM course extractor and may connect directly to the hand-made maps mentioned in the historical level-viewer investigation.  
**Discriminating test:** reproduce a course from ROM data and align its topology/segment ordering against the corresponding map.  
**Dependencies:** obtain direct image files or sufficient map access for pixel-level comparison.


### R-EXT-010 — RetroAchievements independently corroborates progression RAM and exposes stunt-state RAM

**Status:** supported  
**Date:** 2026-09-28  
**Area:** RAM | physics | other

**Observation:** A public snapshot of the Uniracers RetroAchievements set contains 24 raw memory-condition definitions. Its medal addresses at `0x02069C`, `0x0206AC`, ... `0x02071C` independently match Halamantariel's historical per-tour medal offsets. It additionally exposes a dense stunt-state block from `0x02076B` through `0x0207AF` and per-tour five-byte state groups from `0x021075` through `0x0210A1`.  
**Evidence:** `reference/imported/retroachievements/1295.json` and `reference/notes/retroachievements-ram.md`.  
**Interpretation:** These are high-value watchpoints for reconstructing stunt and race state because they were used in live achievement conditions, not merely guessed from static inspection.  
**Discriminating test:** instrument the supported ROM while deliberately triggering one stunt/result at a time and map exact transition semantics.  
**Dependencies:** RetroAchievements' SNES address-domain mapping must be translated correctly to native WRAM/SRAM addresses.


### R-EXT-011 — Period SNES RNC decoder source preserved

**Status:** confirmed external artifact  
**Date:** 2026-09-28  
**Area:** compression | course

**Observation:** The public mirror of RNC ProPack 2.14 includes the original packer package and separate SNES assembly unpackers for RNC Method 1 and Method 2. The package has been mirrored byte-for-byte into this repository.  
**Evidence:** `reference/imported/tools/rnc_propack-2.14/`; upstream revision `08406a33e700aa33936e4c4800cd0887a468a31b`; SNES source blobs `ad4f5c58590dcc1357fb01c138084ff78ad22d75` (Method 1) and `0055f7fad678ef226757b3b7fa9fb06e48fc8929` (Method 2).  
**Interpretation:** We now have period reference implementations suitable for structural comparison with the Uniracers ROM. This can independently test the historical claim that course data uses RNC and determine the exact method/variant.  
**Discriminating test:** locate candidate RNC records and the ROM decompressor, compare against both supplied SNES implementations, then decompress one candidate and connect it to a known course load.  
**Dependencies:** The public 2.14 package may not be the exact ProPack revision used by DMA Design, so algorithmic agreement matters more than byte-identical source.


### R-EXT-012 — TAS-native WRAM watch addresses

**Status:** supported historical lead  
**Date:** 2026-09-28  
**Area:** RAM | physics | camera

**Observation:** Halamantariel published an explicit Snes9x memory-watch list used during Uniracers TAS work: `7E:04B7` signed 16-bit speed, `7E:11CD` unsigned 16-bit boost meter, `7E:0411`/ `7E:0415` unsigned 16-bit X/Y position, `7E:1509` screen-X, plus one-byte stunt counters at `7E:11FD`, `7E:11F9`, `7E:0F61`, `7E:042B`, and `7E:042F`.  
**Evidence:** `reference/notes/tas-and-sram-research.md`; TASVideos Uniracers topic post dated 2008-03-12.  
**Interpretation:** These provide directly named native WRAM watchpoints for core movement/boost/stunt state and are prime anchors for symbol reconstruction.  
**Discriminating test:** watch each address during controlled gameplay and verify direction, units, signedness and reset/update behavior.  
**Dependencies:** Snes9x memory-domain notation is interpreted as native banks `7E/7F`; exact supported US ROM should be verified.

### R-EXT-013 — USJO v13 exact filename and behavioral role

**Status:** v13 artifact missing; v8 ancestor recovered  
**Date:** 2026-09-28; updated 2026-09-30  
**Area:** physics | RAM | other

**Observation:** The 2008 Snes9x Lua-development thread links `usjo13.lua` under the title “Uniracers Stunts & Jump Optimizer v13.” Its author describes it as starting before a jump, intelligently trying stunt combinations, optimizing for speed and replaying the best input. Internal v8 now independently demonstrates that exact architecture in surviving source.  
**Evidence:** `reference/imported/tas-bots/usjo8.lua`; `reference/notes/tas-and-sram-research.md`; historical v13 URL preserved in `reference/catalog.yml`.  
**Interpretation:** v13 is now primarily a five-revision delta target: it may expose later fixes, discoveries or autonomy work, but the evaluator/search/RAM/timing core is already available in v8.  
**Discriminating test:** if v13 or another sibling appears, byte/code-structure diff it against v8 and promote only genuinely new mechanics or state knowledge.  
**Dependencies:** passive recovery of a later sibling; no implementation blocker.

### R-EXT-014 — Recovered USJO internal v8 source

**Status:** confirmed external artifact; local semantic validation active  
**Date:** 2026-09-30  
**Area:** physics | RAM | input | TAS

**Observation:** A surviving source file identifies itself as **February 10th, 2008 (Internal Version 8)** and implements a savestate-driven Uniracers stunt optimizer. It reads signed X/Y speed, air state, twist/tabletop/Z-flip/roll/flip counters, Z-rotation/pre-rotation state and boost state; searches jump/stunt timing; scores candidates as derived boost plus resulting horizontal speed; and replays the best candidate through controller input.  
**Evidence:** `reference/imported/tas-bots/usjo8.lua`; source provenance and hashes in `reference/catalog.yml` and `docs/original-development/ACQUISITION-LEDGER.md`; reproducible static inventory in `analysis/generated/usjo8-static-inventory.{json,md}` generated by `tools/inventory_usjo8.py`.  
**Interpretation:** This is a direct historical behavioral oracle and reverse-engineering accelerator. Its addresses/constants are working hypotheses until locally reproduced, while its source-level control/search architecture is directly established. One source-level nuance now exposed by the inventory: v8 reads `7E:11CD` as one byte and only uses it as a zero/nonzero gate, while the retained TAS watch list describes a 2-byte unsigned Booster Meter there; v8 reconstructs its own boost score from stunt counts rather than using the runtime meter magnitude directly.  
**Discriminating test:** the complete static read/constant/state inventory is generated. `analysis/generated/usjo8-validation-matrix.{json,md}` classifies the 11 read addresses against the canonical symbol map: 3 runtime-confirmed and 8 strong-static fields. Writer analysis now supports all five stunt counters, resolves `$0DFD/$0DFF -> $0F57` as paired persistent-to-current-player Z-state flow, identifies `$0F61` as current-player working twist count, and establishes `7E:11CD` as 16-bit with exact game-facing units still open. `analysis/generated/usjo8-boost-model.{json,md}` extracts the exact historical stunt-reward ladder and score gates, while `analysis/generated/usjo8-control-model.{json,md}` records the optimizer's recovered state domains and controller translation. Targeted WRAM store-site run 36769525945 now covers all eight formerly unresolved USJO addresses; `analysis/generated/usjo8-writer-scan.md` preserves the compact findings. Its coherent bank-02 candidates resolve `7E:11CD` as a 16-bit game field and identify narrow writer landmarks for each stunt counter and Z-state lead. Dynamic run 36776825024 adds the first event-causal stunt validation: matched X input produces `7E:042F` **0→1→2→3→4→0** every two frames in both native and pinned Snes9x, while matched control does not. Because that byte clears after the short progression, the historical `numtabletops` label is supported as a tabletop detector but a simple accumulated completed-tabletop-count interpretation remains unproven; `analysis/generated/usjo8-x-tabletop-transient.{json,md}` preserves the evidence.  
**Dependencies:** period Snes9x Lua API compatibility is relevant only if executing the script itself; static mining and semantic validation do not require Snes9x 1.43.

---

## Original-development leads added on main

### R-SEED-004 — Copier-sensitive anti-piracy path

**Status:** supported historical lead  
**Date:** 2026-09-28  
**Area:** CPU | other

Andrew Innes states that DMA discovered a behavioral difference between a proper cartridge and their fast copy-device development image and deliberately used it for anti-piracy protection. Mike Dailly independently confirms Magicom/devkit use during Unirally development.

**Evidence:** docs/original-development/SOURCE-INDEX.md entries OD-004 and OD-005.  
**Action:** identify cartridge/copier-sensitive code paths and validate them against a trustworthy reference emulator or hardware model.

### R-SEED-005 — Bespoke DMA SNES framework and SNasm conventions

**Status:** supported historical lead  
**Date:** 2026-09-28  
**Area:** CPU | DMA/HDMA | other

Mike Dailly credits himself with the Uniracers SNES framework/tools, lists SNasm as a bespoke 65816 macro assembler, and stated in 2008 that he had found his old SNES framework source.

**Evidence:** OD-001 through OD-004 in docs/original-development/SOURCE-INDEX.md.  
**Action:** search for surviving framework/tool source and compare recovered code idioms against the ROM before imposing modern assembler conventions.

### R-SEED-006 — Multidimensional unicycle animation corpus

**Status:** supported historical lead  
**Date:** 2026-09-28  
**Area:** PPU | other

Developer recollections describe rendered unicycle graphics with multiple pose dimensions, while Dailly lists dedicated Unicycle Compression and A0-plotter tools.

**Evidence:** OD-001, OD-003, OD-005.  
**Action:** correlate controlled animation states with ROM source ranges and sprite uploads; seek stride/table dimensions rather than assuming a simple linear frame strip.

### R-SEED-007 — 1994-11-29 PAL prototype as differential oracle

**Status:** acquired, fingerprinted, and structurally diffed  
**Date:** 2026-09-28  
**Area:** other

Hidden Palace documents a European prototype from a four-EPROM SHVC-4PV5B-01 development cartridge.

**Evidence:** OD-007.  
**Action:** acquire, hash, normalize, and diff against canonical USA retail at byte, block, pointer-table and disassembly levels.


### R-SEED-008 — Intentional per-scanline sprite-state changes

**Status:** strong developer-confirmed historical behavior  
**Date:** 2026-09-28  
**Area:** PPU | DMA/HDMA

**Observation:** Mike Dailly explicitly states that Uniracers changed SNES state on a scanline basis, and separately identifies the split-screen method as C64-style sprite ripping. His later technical explanation describes changing sprite position while the raster is drawing it and says the Uniracers implementation required Nintendo R&D hardware verification.

**Evidence:** OD-019 through OD-021 in docs/original-development/SOURCE-INDEX.md.

**Interpretation:** the two-player renderer deliberately changes sprite/OAM-related state within the visible frame to obtain a clean viewport split.

**Discriminating test:** trace writes to OAM address/data and any DMA/HDMA or sprite-position state around the split scanlines; compare one-player and two-player modes; correlate exact scanlines with visible sprite discontinuities.

**Dependencies:** the later explanatory article accurately describes the same shipped implementation Dailly referenced in 2008.


### R-SEED-009 — Four-build differential ROM corpus

**Status:** confirmed at byte-identity level  
**Date:** 2026-09-28  
**Area:** other | compression

**Observation:** the local reference set now contains four verified 2 MiB images: USA retail, Europe retail, the historical GoodSNES-listed `Uniracers (Beta)`, and the 1994-11-29 PAL prototype. USA retail vs the legacy beta differs in exactly 486 bytes across 486 one-byte runs; all 45 RNC streams are byte-identical and remain at identical offsets. The legacy beta also shares the USA retail reset vector and header checksum/complement.

Europe retail contains 45 Method 1 streams, but only 38 are byte-identical by content with the other three builds. By ordinal stream position, the differing PAL-retail streams are 4, 16, 20, 26, 27, 35 and 36. The other 38 move after size-changing streams but preserve exact packed bytes.

**Evidence:** `analysis/generated/reference-rom-inventory.md`; `analysis/generated/reference-rom-comparison.md`; deterministic generators `tools/inventory_reference_roms.py` and `tools/compare_reference_roms.py`.

**Interpretation:** the legacy beta is extraordinarily close to USA retail and is a high-sensitivity oracle for isolated late byte changes, but its historical “beta” label does not by itself establish build chronology or authenticity. PAL retail contains seven genuine decoded-content candidates that changed after the 1994-11-29 prototype/USA content corpus; these are unusually strong candidates for region-specific or late content edits.

**Discriminating test:** independently decompress the seven changed PAL streams and their USA/prototype counterparts, then characterize the exact decoded deltas before assigning course or localization semantics.

**Dependencies:** stream ordinal is used only as a stable comparison index, not yet as a semantic course ID.


### R-SEED-010 — Independent RNC1 decompression verified across preserved builds

**Status:** confirmed  
**Date:** 2026-09-28  
**Area:** compression | course

**Observation:** project-owned `tools/rnc_method1.py` independently decoded every detected Method 1 stream in all four preserved ROMs. All 180 decode operations (45 per build) passed both the packed CRC16 in the RNC header and the unpacked CRC16 after decompression. Each build contains 45 unique decoded outputs.

USA retail, the legacy beta, and the 1994-11-29 PAL prototype have identical decoded content for all 45 stream positions. Europe retail differs after decompression at exactly seven ordinal positions: 4, 16, 20, 26, 27, 35 and 36.

**Evidence:** `analysis/generated/rnc-stream-manifest.json`; `analysis/generated/rnc-stream-manifest.md`; CI run 36491695742; decoder `tools/rnc_method1.py`; generator `tools/analyze_rnc_streams.py`.

**Interpretation:** RNC extraction/decompression is no longer a blocker. The seven PAL-retail deltas are real content changes rather than merely recompression or relocation, because their unpacked CRCs, lengths and SHA-256 hashes differ.

**Discriminating test:** characterize record structure in decoded bytes and map at least one stream to an independently known course; compare the seven PAL deltas structurally after the record format is understood.

**Dependencies:** semantic mapping of stream ordinal to course/content identity remains unresolved.


### R-SEED-011 — Shipped RNC1 unpacker identified in ROM code

**Status:** confirmed  
**Date:** 2026-09-28  
**Area:** CPU | compression | course

**Observation:** a masked opcode signature derived from the preserved 1992 Super NES ProPack Method 1 source, `reference/imported/tools/rnc_propack-2.14/SOURCE/SUPERNES/RNC_1.S`, produces one unpacker-entry hit per preserved build. The USA retail and legacy beta entry is ROM offset `0x00B8F1` (LoROM `01:B8F1`); Europe retail is `0x00B8E2` (`01:B8E2`); the 1994-11-29 PAL prototype is `0x00B8D1` (`01:B8D1`). Surrounding instructions reproduce the period routine's distinctive entry sequence: `REP $39`, stack-relative source/destination argument loads, direct-page stores, `PHB/XBA/PHA/PLB/PLB`, input pointer adjustment by 17 bytes, block-count read, bit-buffer initialization, and calls into the Huffman/bit-reader machinery.

The same search also finds the expected Huffman-builder-shaped code later in the routine region, with build-relative address shifts consistent with the unpacker entry shifts.

**Evidence:** `analysis/generated/rnc-decoder-signature-search.md`; generator `tools/find_rnc_decoder_signature.py`; preserved period source `reference/imported/tools/rnc_propack-2.14/SOURCE/SUPERNES/RNC_1.S`.

**Interpretation:** Uniracers/Unirally contains a directly recognizable integration of Rob Northen's SNES Method 1 unpacker, rather than merely a format-compatible independent decoder. Build-to-build movement of the routine provides an additional code-alignment landmark.

**Discriminating test:** map direct callers and packed-stream pointer references, then trace one course-load path from a caller through `RNC1_Unpack` into the decoded WRAM buffer.

**Dependencies:** LoROM address notation uses the low-bank mirror; equivalent high-bank mirrors may appear in call operands.


### R-SEED-012 — 45 RNC payloads align with track order; stunt timer field identified

**Status:** supported, with byte-level observation confirmed  
**Date:** 2026-09-28  
**Area:** course | compression

**Observation:** the canonical USA ROM has 45 validated decoded RNC Method 1 payloads. When grouped into nine sets of five, decoded byte offset 2 equals `0x2D` only at ordinals 3, 8, 13, 18, 23, 28, 33, 38 and 43. It is `0x00` for the other 36 payloads. No exception occurs.

External gameplay documentation states that each tour's five tracks occur in the fixed order Race, Circuit, Stunt, Race, Circuit, and independently describes stunt courses as 45-second events. Decimal 45 is `0x2D`.

**Evidence:** `analysis/generated/course-header-cadence.md`; generator `tools/analyze_course_header_cadence.py`; `reference/notes/course-order-and-stunt-timer.md`.

**Interpretation:** the simplest explanation is one RNC payload per shipped track, ordered by tour and slot. Decoded byte 2 is very likely the stunt-course time limit in seconds, or a directly equivalent stunt-only parameter. This is the first semantically identified field in the decompressed course record.

**Discriminating test:** trace selection/loading of one known stunt track and one race track, then trace decoded byte 2 into the gameplay timer initialization. Independently verify the stream ordinal through the course selector.

**Dependencies:** external track-order/timer descriptions are used only for semantic interpretation; the 45-stream count and byte cadence are local binary observations.


### R-SEED-013 — Recovered frontend and race-state RAM reproduced in native and reference runs

**Status:** confirmed for observed states  
**Date:** 2026-09-28  
**Area:** RAM | UI | race

**Observation:** Dessyreqt's 2014 bot labels WRAM `7E:009F` as the current frontend menu and `7E:0313` as `inRace`. The project-owned shared deterministic input fixture reproduces, in both native SNESRecomp execution and Snes9x through `snesref`, the sequence `0xD7` main menu, `0x3C` one-player rider selection, `0x6D` first one-player tours page, `0xF6` track selection, `0x16` now-playing, then `7E:0313 = 0x01` after race entry.

**Evidence:** `reference/imported/tas-bots/uniracers-tabletop-bot-2014.lua`; GitHub Actions runs 36506120930 and 36506281320; `tests/input/reach-first-race.script`; `docs/BRINGUP.md`.

**Interpretation:** the recovered frontend state model and active-race flag are now locally validated cross-runtime rather than merely inherited historical labels. A newly visible menu-state byte can precede input readiness; the deterministic fixture therefore retains a conservative scene-settle period before confirmation.

**Discriminating test:** compare complete WRAM dumps at each shared checkpoint byte-for-byte, then extend the same fixture into controlled movement and validate the bot's race-driving RAM labels.

**Dependencies:** only values/scenes actually reproduced are promoted; other recovered bot fields remain historical leads until independently observed.


### R-SEED-014 — Native and Snes9x race-entry timing/state differential

**Status:** confirmed as timing/residual-state differential  
**Date:** 2026-09-28  
**Area:** timing | RAM | other

**Observation:** the shared race-entry script reaches `7E:0313 = 1` at native frame 984 and Snes9x/snesref frame 975. Full 128 KiB WRAM comparison at seven settled checkpoints shows 19 differing bytes at main menu, roughly 250 through the animated frontend scenes, and only **7 differing bytes** at settled race entry.

The final seven are `0x00C6`, `0x00C8`, `0x00C9`, and contiguous `0x01D1–0x01D4`. At race entry the four-byte block is native `90 13 20 80` versus Snes9x `00 00 00 00`.

**Evidence:** GitHub Actions runs 36506120930, 36506281320 and combined differential run 36508095522; artifact 11007769197; `tools/compare_wram_checkpoints.py`.

**Interpretation:** much of the frontend mismatch is compatible with the known several-frame timing offset inside animated scenes, because the difference set collapses drastically after race entry settles. The persistent `0x01D1–0x01D4` block is a sharper candidate for a genuine runtime/state divergence. The three `0x00C6/0x00C8/0x00C9` differences remain unclassified, but all three take changing small values across every captured frontend/race checkpoint rather than preserving a fixed native-only payload. That temporal pattern makes timing/phase counters a stronger working explanation than a stable semantic-state split.

**Resolution:** trace run 36511207129 shows `0x00C6` is decremented once per frame by `bank_80_FADF_M1X0`, while `0x00C8` and `0x00C9` are periodic countdown/phase values written by interpreted code at `$00:8588` (`0x00C8` changing every frame within its cycle and `0x00C9` on a seven-frame cadence). Their different race-entry values therefore reflect the already-observed native/reference phase offset rather than a stable semantic race-state mismatch. The remaining four bytes are resolved separately in R-SEED-015.

**Dependencies:** both engines execute the same script and zero-filled initial WRAM; Snes9x reports its existing Uniracers-specific compatibility hack as active.


### R-SEED-015 — Persistent 0x01D1–0x01D4 divergence is stale stack residue

**Status:** confirmed  
**Date:** 2026-09-28  
**Area:** CPU | RAM | timing

**Observation:** the settled native/reference race-entry differential leaves four contiguous differing bytes at WRAM `0x01D1–0x01D4`: native `90 13 20 80`, Snes9x `00 00 00 00`. This block appears by rider-select and persists through later captured frontend states into race entry. A checkpoint-by-checkpoint reinspection of the full-WRAM artifact shows many other transient native/reference differences throughout page `$01` before race entry (13 at main menu, 13 at rider select, 20 at tours, 13 at tracks, 18 after confirmation, 18 at now-playing), but all of those other page-$01 differences disappear at the settled race checkpoint, leaving only `0x01D1–0x01D4`. The block lies in the conventional 65C816 stack page, and SNESRecomp's own low-WRAM differential tooling explicitly treats this region as containing stack state as well as game logic.

**Evidence:** combined differential run 36508095522; `tools/compare_wram_checkpoints.py`; SNESRecomp low-WRAM trace/debug infrastructure and stack model.

**Interpretation:** one plausible explanation is differing residual stack contents caused by different call/interrupt execution paths or stack depth, rather than a durable gameplay variable. The broader page-$01 pattern strengthens that hypothesis: the region behaves like a churned scratch/stack area whose cross-runtime differences mostly evaporate once the race settles, while this four-byte residue survives. This is still not proof: Uniracers could also use page `$01` for ordinary RAM while in native mode.

**Static candidate scan:** run 36509923408 scanned raw 65816 store/RMW encodings for all seven divergent offsets. For `0x01D1–0x01D4` it found only a small set of instruction-shaped byte patterns, dominated by RMW/STZ forms; it did not expose an obvious direct semantic store sequence. Because this is a raw-byte candidate scan rather than control-flow-aware disassembly, hits may be data and absence of a direct store does not cover stack pushes, JSR/JSL return frames, interrupts or indirect/indexed effects. The result is therefore weakly consistent with, but does not establish, the stack-residue interpretation.

**Dynamic resolution:** trace run 36511207129 reaches `inRace = 1` at native frame 984 with the 65C816 in native mode (`E = false`) and `SP = $01FF`. The four bytes remain `90 13 20 80` at `$01D1–$01D4`, far below the live top of stack. Reverse-debug writer history records zero ordinary WRAM writes to all four addresses across the captured run, while explicit semantic/timing variables such as `$00C6/$00C8/$00C9` produce abundant attributed writes. Together with the broader transient `$01xx` churn seen at earlier checkpoints, this identifies the four-byte block as stale stack history rather than live gameplay state. Its exact historical push sequence is not needed for fidelity gating.

**Dependencies:** the stack interpretation depends on actual Uniracers stack-pointer behavior at the relevant frames; address location alone is insufficient.


### R-SEED-016 — Player-1 X position and signed X speed validated cross-runtime

**Status:** confirmed  
**Date:** 2026-09-28  
**Area:** RAM | physics | input

**Observation:** Dessyreqt's effective player-1 word table labels `7E:0411` as X position and `7E:04B7` as X speed. In deterministic run 36512546762, native and Snes9x begin at `xPos=1088`, `xSpeed=0`, receive the same staged Right input, and match exactly at every semantic checkpoint. At `accel-180`, both report `xPos=1655` and `xSpeed=+447`.

**Evidence:** workflow run 36512546762; artifact 11009592846; recovered bot source; `tests/input/race-acceleration.script`.

**Interpretation:** `7E:0411` and signed `7E:04B7` are confirmed player-1 horizontal position/velocity anchors for the observed stock race. Positive speed corresponds to rightward movement.

**Next discriminator:** use the moving state as the baseline for B-jump and L/R rotation while validating Y speed, effective air state and pitch.


### R-SEED-017 — Recovered race countdown field advances in 8.8-style frame quanta

**Status:** supported  
**Date:** 2026-09-28  
**Area:** RAM | timing

**Observation:** the recovered bot labels `7E:11BA` as `countdownTimer`. Across the event-relative checkpoints in run 36512546762, both engines produce the same sequence: 54528, 46592, 38656, 30720, 22784, 7168. Each 31-frame staged interval decreases the word by 7936 = 31 × 256, and the final 61-frame interval decreases it by 15616 = 61 × 256.

**Interpretation:** the field decrements by exactly `0x0100` per guest frame during this race-start window, strongly supporting a fixed-point/frame-countdown interpretation. The precise player-visible thresholds and meaning of the low byte remain to be characterized.

**Evidence:** workflow run 36512546762 and its native/reference player-state reports.


### R-SEED-018 — B-jump execution matches cross-runtime; airborne-state address requires causal control

**Status:** supported / active discriminator  
**Date:** 2026-09-28  
**Area:** input | physics | RAM

**Observation:** run 36513247475 applies a two-frame `Right+B` pulse from the validated moving Dragster state and samples through `jump-settle`. Native and Snes9x match exactly at every recovered semantic field checkpoint. X motion continues identically, `pitch` reaches 33 at `jump-mid`, and the earlier duplicate `7E:0547` follows 0 → 3 → 9 → 9 → 0 while the Lua-effective `7E:0545` remains 0.

**Complication:** the recovered bot source contains duplicate player-1 keys, with later Lua semantics selecting `7E:0545` as `airValue`, but the observed B-window response is at `7E:0547`. The race framebuffer contains two unicycles/ghost-like sprites, so visual correlation alone cannot safely assign the changing byte to the controlled player.

**Paired-slot clue:** the same dumps show the table-[2] block changing coherently with the apparent airborne event: at `jump-mid`, `7E:0417=796`, signed `7E:04BD=-21`, and `7E:0547=9`, while table-[1] remains `7E:0415=859`, `7E:04BB=0`, `7E:0545=0`. The preserved bot runs `singlePlayer=true`, `controller=1`, and reads table [1], so this strongly suggests the visually obvious arc belongs to the second racer rather than the intended controlled-player block.

**Recovered-policy timing:** on Dragster, `jumpAreas[0]` spans X 1090–25278 and Y 790–870. At the validated moving checkpoint (X 1655, Y 858), `ShouldJump()` would continue returning true every bot frame until its own air/Y-speed conditions changed. The original policy therefore behaves like a sustained B hold in this region, not a two-frame pulse.

**Matched-control result:** run 36513805265 replays the same route/timing with Right-only instead of the two-frame Right+B pulse. A paired-slot reinspection of the artifact confirms that every sampled table-[1] and table-[2] field is numerically identical between B and no-B at every checkpoint, including the second racer's full arc (`ySpeed=-154`, `air=9` at `jump-rise`). The short B pulse therefore produces no semantic player-state change. In native, the only persistent full-WRAM difference is `$0069`, but it already differs at `accel-180` before B is pressed and therefore is not B-causal. In Snes9x, jump-vs-control differences are limited to transient stack bytes. The second-slot airborne arc therefore occurs independently of the two-frame B pulse.

**Interpretation:** the initial "jump" fixture was a negative intervention. It did not launch the intended table-[1] player. The visually obvious airborne motion belonged to the second racer. This validates the duplicate-key/paired-slot caution and prevents falsely promoting `$0547` as player-1 air state.

**Next discriminator:** replace the short pulse with sustained Right+B input across the Dragster jump area, matching the recovered bot's actual per-frame `ShouldJump()` policy, and require a causal change in table-[1] Y/air/related state before calling the controlled player airborne.

**Evidence:** workflow run 36513247475; `tests/input/race-jump.script`; matched control `tests/input/race-jump-control.script`.


### R-SEED-019 — Active Dragster payload is resident at 7F:0000

**Status:** confirmed  
**Date:** 2026-09-28  
**Area:** course | RAM | decompression

**Observation:** run 36514985916 independently decodes all 45 USA streams and scores them against live WRAM `7F:0000`. Stream 1 matches 33,814 of 33,815 decoded bytes across its entire 33,815-byte payload. The sole mismatch is decoded offset `0x000B`, which changes from `0x0F` to live `0x16`.

**Interpretation:** decoded stream 1 is the active Dragster course payload and is loaded directly at `7F:0000`; at least byte 11 is subsequently mutable in place. This supersedes the older `7E:2080` breadcrumb as the primary decoded-course runtime landmark.

**Evidence:** decoded stream-1 structural report and native race-entry WRAM artifact from run 36508095522.


### R-SEED-020 — Dragster header X coordinate maps exactly to runtime start X at ×16

**Status:** strongly supported single-course field hypothesis  
**Date:** 2026-09-28  
**Area:** course | RAM | physics

**Observation:** decoded stream 1 has LE16 pairs `(68,50)` at offsets 3/5 and again at 7/9. At settled Dragster race entry, both racer slots have X position 1088; `68 × 16 = 1088` exactly. Runtime Y is 858/857, not `50 × 16 = 800`.

**Interpretation:** the header pairs are coordinate-like and may encode the two racer spawn/start locations in 16-unit X coordinates. Y either uses an additional object-anchor offset or has different semantics.

**Discriminating test:** load a second known course and compare its header pairs with runtime racer positions, or mutate one decoded coordinate causally and observe the predicted runtime displacement.


### R-SEED-021 — Sustained B input produces coherent player-1 airborne state cross-runtime

**Status:** supported; matched sustained control pending  
**Date:** 2026-09-28  
**Area:** input | physics | RAM

**Observation:** run 36514394117 advances the validated moving Dragster state with sustained `Right+B` input. Before an unrelated workflow-ordering failure, both native and Snes9x completed and summarized the sustained intervention identically. At `accel-180`, player 1 is grounded: `x=1655`, `y=858`, `xSpeed=447`, `ySpeed=0`, effective `airValue(0545)=0`, effective `pitch(0F49)=7`. At `jump-hold-024`, both engines report `x=2005`, `y=797`, `xSpeed=447`, signed `ySpeed=-21`, `airValue=9`, `pitch=27`. By `jump-hold-048`, both are back at `y=858`, `ySpeed=0`, `airValue=0`.

**Interpretation:** unlike the earlier two-frame negative intervention, sustained B produces a coherent airborne transition in the intended table-[1] player block, and the recovered effective addresses `7E:04BB` and `7E:0545` now move in the expected direction together. Native and reference semantics match exactly at every sampled sustained-jump checkpoint.

**Caution:** because the matched sustained Right-only control did not run in this failed workflow instance, causality is not yet formally closed. The repaired workflow runs the control before its paired-slot analysis.

**Next discriminator:** require the timing-identical sustained Right-only control to remain grounded at the corresponding table-[1] checkpoints; then promote Y speed and air state and proceed to controlled rotation.


### R-SEED-022 — Dragster payload is installed after Now Playing confirm, before active race

**Status:** confirmed timing window  
**Date:** 2026-09-28  
**Area:** course | compression | RAM

**Observation:** run 36515555816 compares decoded stream 1 with live `7F:0000` at `tracks-ready`, `after-track-confirm`, `now-playing-ready`, and `race-entered`. Stream 1 is not installed at the first three checkpoints. At `race-entered` it matches 33,814 / 33,815 decoded bytes, with only offset `0x000B` changed from `0x0F` to `0x16`.

**Interpretation:** Dragster decompression/copy into `7F:0000` occurs after the final A confirm on the Now Playing screen and before the race-active state. In the deterministic reference route this is a roughly 151-frame transition window.

**Caution:** pre-load "best stream" scores are not semantic evidence because sparse decoded streams can coincidentally match zero-heavy live WRAM. The focused expected-stream full-length match is the useful test.

**Discriminating test:** add dense post-confirm checkpoints to locate the first full stream-1 residency frame and observe byte 11 before/after its runtime mutation.


### R-SEED-023 — L input rejects 0F49 as the direct rotation accumulator and implicates 04C7

**Status:** supported; mirror-R discriminator active  
**Date:** 2026-09-28  
**Area:** input | physics | RAM

**Observation:** airborne-rotation run 36515746538 applies eight frames of L during the causally validated player-1 airborne interval and compares against a timing-identical jump-only control. Native and Snes9x agree on every sampled recovered semantic field. The recovered bot field `7E:0F49` is identical between L and control at the intervention checkpoint (`45` in both) and throughout the sampled window.

The full-WRAM causal differential, however, shows `7E:04C7` changing from `0x07` in jump-only control to `0x37` under L at the eight-frame intervention checkpoint, then `0x3C` vs `0x07` at the next checkpoint before relaxing toward baseline. The adjacent paired-racer byte `7E:04C9` follows the second-racer trajectory and does not show this player-1 L-causal response.

**Interpretation:** `7E:0F49` may still be a useful derived/display/stunt-facing quantity used by the historical bot, but it is not the direct player-1 rotation accumulator for this intervention. `7E:04C7` is a much stronger candidate for player-1 physical rotation/orientation state, with `7E:04C9` plausibly the paired player-2 slot.

**Discriminating test:** run the mirrored eight-frame R intervention against the same jump-only control. If `7E:04C7` responds in the opposite direction while native/reference agree, promote the paired `04C7/04C9` rotation interpretation.


### R-SEED-024 — Course payload installs progressively between +16 and +64 frames

**Status:** confirmed  
**Date:** 2026-09-28  
**Area:** course | compression | RAM

**Observation:** run 36516395510 samples `7F:0000` after final Now Playing confirm. Through +16 frames, stream 1 is not installed. At +32 frames, the live buffer has an exact 10,307-byte prefix of decoded Dragster and byte 11 is still `0x0F`. At +64 frames, the full 33,815-byte payload is resident with only byte 11 changed to `0x16`; that state persists thereafter.

**Interpretation:** the active RNC payload is written progressively during the transition, not atomically at race activation. The byte-11 mutation occurs sometime after its decoded value has been written and by the time the full payload is resident.

**Discriminating test:** sample every 4 frames from +32 through +64 to bracket decompression completion and byte-11 mutation separately.


### R-SEED-025 — Dragster header coordinates map exactly to racer initialization at ×16

**Status:** confirmed for Dragster initialization; pair ownership unresolved  
**Date:** 2026-09-28  
**Area:** course | physics | RAM

**Observation:** decoded stream 1 contains two identical LE16 pairs `(68,50)`. At +64 frames after Now Playing confirm, when the full course payload is resident, both runtime racer slots are exactly `(1088,800)`. These are exact ×16 mappings: `68×16=1088`, `50×16=800`.

**Interpretation:** the header pairs are coordinate fields in 1/16 runtime racer units and supply or coincide with racer initialization/spawn positions. The later settled race Y≈858/857 reflects subsequent state evolution.

**Limitation:** Dragster cannot identify pair1→slot1 vs pair2→slot2 because both encoded pairs and both initial runtime positions are identical.

**Discriminating test:** load a course whose two header pairs differ, or causally mutate one pair, and observe which racer slot moves.


### R-SEED-026 — 04C7/04C9 are paired persistent pitch slots; 0F49 is shared working state

**Status:** confirmed structural pairing; direction convention still under mirror test  
**Date:** 2026-09-28  
**Area:** CPU | RAM | physics

**Observation:** targeted store scan run 36516801647 finds exactly one direct absolute writer candidate for `7E:04C7`: `STY $04C7` at LoROM `02:8D84`. Its surrounding shipped bytes decode to a player-copy sequence including `LDY $0F49; STY $04C7`, plus stores to player-1-shaped destinations `$0BA1/$0BAD/$0BB1`.

A sibling sequence at `02:9272` performs `LDY $0F49; STY $04C9`, with the neighboring destinations shifted coherently to `$0BA3/$0BAF/$0BB3`. The same source scratch values `$0F49/$0F4B/$0F4D` feed both sibling routines.

Dynamic run 36515746538 independently shows airborne L input changing `$04C7` from `0x07` in jump-only control to `0x37` at the intervention checkpoint, while the historical bot-read `$0F49` is unchanged between intervention and control at sampled checkpoints.

**Interpretation:** `$04C7/$04C9` are persistent paired per-racer pitch/rotation state slots. `$0F49` is a shared current-player working/scratch value copied into whichever racer slot is being updated, explaining why the historical bot could use it operationally while it is not stable player-1 storage.

**Discriminating test:** mirrored R input should drive player-1 `$04C7` complementarily to L, establishing the input-direction convention.


### R-SEED-027 — Player pitch is a modulo-64 persistent angle with L/R direction confirmed

**Status:** confirmed  
**Date:** 2026-09-28  
**Area:** input | physics | RAM

**Observation:** mirrored rotation run 36516524308 applies eight frames of L or R during the same validated airborne state, with jump-only control. Native and Snes9x produce identical persistent slot values. At the intervention checkpoint, control is `7E:04C7 = 0x07`; L gives `0x37`; R gives `0x17`. The paired player-2 `7E:04C9` and scratch `7E:0F49` follow the second/current-player update path rather than the controlled player-1 intervention.

**Interpretation:** the observed player-1 pitch/orientation domain is circular modulo 64. From 7, L changes the angle by −16 modulo 64 (`7−16 ≡ 55 = 0x37`), while R changes it by +16 (`7+16 = 23 = 0x17`). This matches the historical bot's threshold bands around 14/24/32/40/50 much better than treating the value as an unconstrained linear byte.

**Evidence:** run 36516524308; artifact 11011037312; direct WRAM dumps; sibling shipped-code stores at `02:8D84` and `02:9272`.

**Consequence:** `7E:04C7` is confirmed persistent player-1 pitch angle; `7E:04C9` is the paired player-2 slot; `7E:0F49` remains shared current-player working state. Rotation milestone is cleared.


### R-SEED-028 — Course completion, header mutation and racer initialization are distinct setup phases

**Status:** confirmed sequencing windows  
**Date:** 2026-09-28  
**Area:** course | compression | RAM | physics

**Observation:** run 36516675672 samples the Dragster setup transition every four frames. At +40, stream 1 has a 29,289-byte exact prefix and byte 11 is still decoded value `0x0F`; racer slots are `(0,0)`. At +44, the full 33,815-byte payload is resident and byte 11 is already `0x16`, but racer slots remain `(0,0)`. At +48, the course remains complete and both racer slots have become `(1088,800)`.

**Interpretation:** progressive decompression/copy, byte-11 postprocessing, and racer-coordinate initialization are separable phases. Course completion/header mutation occur in +40→+44; racer initialization occurs later in +44→+48.

**Discriminating test:** sample individual frames +41 through +48 to split these windows further.


### R-SEED-029 — Dragster setup sequence is frame-exact: complete +43, header settles +44, spawns +45

**Status:** confirmed  
**Date:** 2026-09-28  
**Area:** course | compression | RAM | physics

**Observation:** run 36517460851 samples every guest frame around setup completion. At +42, stream 1 is incomplete with a 33,359-byte exact prefix and byte 11=`0x0F`. At +43, all 33,815 bytes are resident (33,814 exact) and byte 11=`0x12`, while racer slots remain zero. At +44, byte 11=`0x16`, racers remain zero. At +45, both racers become `(1088,800)`.

**Interpretation:** course decompression/copy completes on guest frame +43; header byte 11 is postprocessed across +43/+44; racer spawn initialization occurs on +45. These are ordered, separable setup phases.

**Next discriminator:** dynamic writer history for `7F:000B` and nearby course-buffer bytes to identify the responsible guest routines and distinguish decompressor output from header postprocessing.


### R-SEED-030 — Landing transition matches cross-runtime and exposes two-stage contact settling

**Status:** confirmed event-relative landing behavior  
**Date:** 2026-09-28  
**Area:** physics | RAM | input

**Observation:** landing run 36517502791 samples the validated player-1 jump trajectory in both native SNESRecomp and pinned Snes9x. Every tracked semantic checkpoint matches exactly. At `landing-032`, player 1 is still airborne (`Y=843`, `YSpeed=182`, `air=9`). At `landing-034`, position has reached track height `Y=859` and `air=0`, while `YSpeed=222` remains non-zero. At `landing-036`, `Y=859`, `YSpeed=0`, `air=0` in both engines.

**Interpretation:** the sampled update sequence clears airborne/contact state when the racer reaches the track surface, then settles/resets vertical velocity by the next observed checkpoint. Native/reference simulation agrees through this transition.

**Harness caveat:** each scripted `press` entry is followed by one idle frame in the pinned runner/snesref grammar. These are event-relative checkpoints under a deterministic 2-held/1-idle input cadence, not claims about an uninterrupted B-held guest-frame number.

**Consequence:** the landing milestone is cleared for functional native/reference validation. A continuous-hold microtrace is optional future archaeology, not required before moving to collision/finish coverage.


### R-SEED-031 — Course decode and header mutation writers identified dynamically

**Status:** confirmed writers; routine roles under static classification  
**Date:** 2026-09-28  
**Area:** CPU | RAM | course | compression

**Observation:** trace run 36517696016 records `interp@$81BB73` writing the decoded Dragster output buffer at frame 867, including `7F:000B: 0x00→0x0F`. At frame 879, `interp@$81BA96` performs seven successive writes to `7F:000B`, incrementing `0x0F→0x10→0x11→0x12→0x13→0x14→0x15→0x16` within one guest frame. Attempt-2 run 36538122650 then captured exact interpreted PCs: the decoded `0x0F` write occurs at IPC `81:B9C8`, while every `0x10..0x16` mutation write occurs at IPC `82:E1E1`. The durable capture is `analysis/generated/course-byte11-exact-writes.json`.

**Interpretation:** the settled `0x16` value is not an unexplained differential or copy artifact. It is produced explicitly after the decoded `0x0F` has been written. The exact-IPC capture also resolves the tooling ambiguity: `81BB73` and `81BA96` are interpreter bridge scope entries, while the literal mutation store is at `82:E1E1`.

**Consequence:** do not attribute course-buffer stores to bridge scope labels. Static RNC classification and dynamic store-PC attribution are now separate, reconciled evidence surfaces.

**Next discriminator:** disassemble/label the code around exact IPC `82:E1E1` and connect that store to the course-loader control path; retain `81:B9C8` as the exact decoded-output write site for comparison.


### R-SEED-032 — Recovered 2008 WIP controller stream is directly parseable

**Status:** confirmed container/input facts; modern-reference replay desynchronization confirmed  
**Date:** 2026-09-28  
**Area:** input | TAS | autonomous play

**Observation:** `reference/imported/tas-bots/uniracers-2008-wip-microstorage.smv` is a raw SMV v1 file, 10,542 bytes, reset-anchored, with one recorded controller and 4,974 header frames. Controller data starts at offset 592. Per the SMV v1 reset-movie format, the block from the savestate offset to controller data is a gzip-compressed 128 KiB SRAM snapshot; the replay tooling now extracts it and emits the canonical game's 8 KiB cartridge SRAM for both reference and native preload. Direct bit translation into the project/snesref 12-bit mask exposes a long regular control block around frames 1184–2655, including repeated `B+Right+R`, periodic `X`, short left corrections, and a final 359-frame Right interval. A later complex block begins around frame 3472.

**Interpretation:** this is a high-value candidate source for an exact known-working Dragster controller sequence, potentially preferable to approximating the 2014 Lua policy. The apparent race boundaries are not yet promoted because they are inferred from input shape alone.

**Replay result:** the repaired evidence-persistence path has now promoted `analysis/generated/historical-2008-dragster-reference.json`. The full 4,975-sample reference replay completes, but under the current pinned modern Snes9x/snesref route it never reaches the project's `inRace` or race-results states: `first_in_race_frame=null`, `first_race_results_frame=null`, `reference_reached_race=false`, `reference_reached_results=false`. The trace does record frontend/menu transitions, so this is a synchronization/timing failure rather than a parser/no-input failure.

**Interpretation:** do not use the 2008 WIP as a modern reference oracle until WIP1 timing compatibility is reproduced or otherwise explained. The 2014 movie is now the preferred exact historical reference corpus for race/finish work.


### R-SEED-033 — 2008 WIP requires no mid-movie reset emulation

**Status:** confirmed  
**Date:** 2026-09-28  
**Area:** input | TAS | replay fidelity

Direct inspection of all 4,975 controller samples in the reset-anchored 2008 WIP finds no `0xFFFF` SMV reset markers. The historical replay therefore needs the movie's reset-anchored initial machine state and embedded SRAM, but no later reset event. Treating reset markers as neutral input is harmless for this specific corpus; generic SMV tooling should still preserve/report marker positions.


### R-SEED-034 — Header bytes 13/14 form a fixed-area dimension pair

**Status:** strong structural evidence  
**Date:** 2026-09-28  
**Area:** course | format | dimensions

**Observation:** across all 45 decoded USA course payloads, header bytes 13 and 14 are restricted to complementary power-of-two-style pairs. Interpreting encoded byte value `0x00` as 256, every pair multiplies to exactly 1024. Observed pairs span `256×4`, `128×8`, `64×16`, `32×32`, `16×64`, `8×128` and `4×256`.

**Interpretation:** bytes 13/14 very likely encode complementary dimensions or strides for a fixed 1024-unit course-layout structure. This is compatible with, but does not yet prove, historical descriptions involving 256-wide course data.

**Discriminating test:** compare decoded structure and runtime traversal for courses at the extreme `256×4` / `4×256` encodings versus `32×32`; identify which subsequent region length/stride changes with the header pair and trace one consumer of either byte.


### R-SEED-035 — 1024-byte block-map hypothesis

**Status:** strong combined local/historical hypothesis; not yet runtime-confirmed  
**Date:** 2026-09-28  
**Area:** course | format | geometry

**Local evidence:** decoded header bytes 13/14 reshape to 45/45 complementary dimension pairs with constant area 1024 when zero is interpreted as 256.

**Historical evidence:** OD-006 preserves Spinal's report that Mike Dailly described levels as 256 tiles wide; after RNC decompression and map-overlay work, Spinal reported that one byte in the decompressed level corresponds to a 64×64 block.

**Hypothesis:** one immediate 1024-byte decoded region is a one-byte-per-64×64-block course-layout plane whose width/height are encoded by bytes 13/14. Provisional name alignment is suggestive rather than decisive: Dragster maps to `256×4`, Vertical to `16×64`, and Little Dipper to `4×256`.

**Discriminating test:** mechanically characterize the first several 1024-byte post-header regions across all 45 payloads, then trace whichever region exhibits map/index-like structure into a runtime course consumer. A mutation/viewer round trip should follow only after that consumer relationship is identified.


### R-SEED-036 — Interpreter writer labels are scope entries, not store PCs

**Status:** confirmed tooling-semantics correction  
**Date:** 2026-09-28  
**Area:** tracing | course | RNC

**Observation:** SNESRecomp synthesizes `interp@$XXXXXX` from the entry PC of an interpreter bridge run and uses that string as the write-attribution scope for all still-interpreted writes during the run. Therefore run 36517696016 proves that the Dragster install and byte-11 mutation write groups occur under scopes entered at `81BB73` and `81BA96`, but does not identify those addresses as the literal store instructions.

**Static cross-check:** `01:BA96` is inside generic RNC Method-1 `GTBITS2`; the shipped bytes align with preserved source `LSR A / ROR BITBUFL / DEY / BEQ / DEX / ...`. That makes a literal “course-byte store at BA96” interpretation impossible and validates the scope-entry reading.

**Discriminating test:** capture exact interpreted opcode PC at WRAM-write time, or narrow the interpreter bridge scope enough to isolate the true store instruction. Keep the established write values/timing unchanged.


### R-SEED-037 — 2008 WIP sample zero is correctly aligned; legacy WIP1 timing remains a compatibility variable

**Status:** sample alignment confirmed; legacy timing compatibility open  
**Date:** 2026-09-28  
**Area:** TAS | input | emulator compatibility

**Source-level observation:** Snes9x movie playback reads sample 0 as baseline controller data before starting movie playback, then sets movie frame/sample counters to zero. The next movie update advances to later samples. The project's `start-frame:duration:mask` conversion therefore has the correct frame-zero convention.

**Movie-specific observation:** the 2008 WIP is SMV v1 with sync-data-present and `MOVIE_SYNC_WIP1TIMING` set; all other legacy behavioral sync flags except ROM-info are clear. Modern Snes9x no longer uses WIP1 timing.

**Observed modern behavior:** the durable reference result in `analysis/generated/historical-2008-dragster-reference.json` confirms that current pinned Snes9x/snesref does diverge before race: no `inRace` or results transition is reached across the full movie stream.

**Interpretation:** do not introduce an arbitrary input-frame offset to force synchronization. The next meaningful discriminator is reproducing/characterizing Snes9x 1.43 WIP1 timing semantics, or demonstrating another exact legacy-state difference that explains the desync.


### R-SEED-038 — 2008 WIP embeds the canonical USA ROM identity

**Status:** confirmed  
**Date:** 2026-09-28  
**Area:** TAS | provenance | replay fidelity

The SMV v1 ROM-info record embedded in `reference/imported/tas-bots/uniracers-2008-wip-microstorage.smv` identifies internal ROM name `UNIRACERS` and CRC32 `383858c7`. That CRC exactly matches the canonical project's USA ROM in `rom_identity.txt`. The movie metadata names its author as `Olivier Bellemare aka Halamantariel`.

This closes ROM-revision mismatch as a possible cause of historical replay desynchronization. The extractor now preserves author/ROM metadata and the historical replay workflow refuses to proceed when an embedded movie CRC disagrees with the canonical ROM.


### R-SEED-039 — 2014 full-game movie provides a post-WIP1 timing oracle

**Status:** reference-side first-race replay confirmed; native comparison open  
**Date:** 2026-09-29  
**Area:** TAS | input | emulator compatibility

TASVideos submission #4250 identifies Dessyreqt's full-game Uniracers movie as Snes9x 1.51 v17 and describes a blank-SRAM start. Its sync notes record successful verification using the movie's embedded settings. Unlike the 2008 SMV-v1 WIP, this movie therefore does not depend on the obsolete WIP1 timing flag.

**Local replay evidence:** attempt-2 run 36538122590 successfully extracts the reset-anchored movie, verifies the canonical ROM identity, replays the first historical race window on pinned Snes9x/snesref, and composes the durable result `analysis/generated/historical-2014-first-race-reference.json`. The trace reaches `inRace` at frame 794 and the first race-results state at frame 2874. The emitted canonical 8 KiB SRAM hash is recorded alongside the source/movie metadata in `analysis/generated/historical-2014-smv-metadata.json`.

**Interpretation:** a post-WIP1 historical movie now supplies a deterministic reference-side race-and-finish oracle independent of the 2008 WIP timing regime. This does not yet prove native replay fidelity.

**Next discriminator:** drive the same extracted frame masks and starting SRAM through the native bridge and compare the same transition/state checkpoints. Keep the 2008 WIP as a separate old-timing corpus rather than conflating a failure there with generic SMV playback.


### R-SEED-040 — Shipped RNC1 body ends at BB6E; BB73 is following helper code

**Status:** confirmed static source alignment  
**Date:** 2026-09-28  
**Area:** RNC | course loader | code archaeology

The preserved Method-1 `MAKEHUFF` tail aligns at USA `01:BB60`; its source-final `RTS` is exactly `01:BB6E`. This establishes the USA/legacy-beta RNC1 body boundary as `01:B8F1..01:BB6E`. The next helper starts at `01:BB6F`; `01:BB71` increments the input pointer and `01:BB73` is its following `BNE`.

Combined with the prior `GTBITS2` alignment at `01:BA96`, the two trace attribution scopes are statically separated: BA96 is generic RNC bit-reader code; BB73 is integration/helper code after RNC. Attempt-2 exact-IPC capture in run 36538122650 closes the remaining attribution gap: the `0x10..0x16` mutation stores execute at `82:E1E1`, not at BA96.


### R-SEED-041 — BB6F is the LoROM-safe RNC packed-word reader

**Status:** confirmed static behavior  
**Date:** 2026-09-29  
**Area:** RNC | LoROM | course loader | code archaeology

**Observation:** USA `01:BB6F` starts with a 16-bit `LDA [IN]`, probes whether `INC IN` wrapped, and on the wrap path reconstructs the high byte from next-bank `$8000` before restoring the original packed-stream pointer. On the normal path it simply restores `IN` and returns. The helper is called from the shipped RNC integration where preserved source performs direct `LDA [IN]` packed-word reads.

**Interpretation:** name the helper `RNC1_ReadWordLoROMSafe`. It adapts the preserved linear RNC decoder to LoROM bank-boundary semantics. `01:BB73` is the helper's `BNE` wrap test, so the earlier `interp@$81BB73` write attribution is conclusively a bridge-scope label rather than a literal store PC.

**Exact-IPC follow-up:** run 36538122650 identifies the decoded `0x0F` write at `81:B9C8` and all seven increment writes at `82:E1E1`. Future analysis should explain those literal store sites and their callers rather than infer store ownership from interpreter scope labels.


### R-SEED-042 — LE16@11 is a 16-byte-aligned pre-trailer cursor

**Status:** runtime behavior confirmed on two courses; exact trailer semantics open  
**Date:** 2026-09-29  
**Area:** course format | runtime mutation | loader

**Observation:** across all 45 USA decoded streams, `LE16@11 + 1` is 16-byte aligned. Between 7 and 36 decoded bytes remain after that cursor. Dragster has `LE16@11=0x840F`, so its trailing region starts at aligned offset `0x8410` and contains exactly seven bytes through EOF at `0x8416`. The already observed seven runtime increments produce `0x8416`, exactly the final valid decoded offset.

**Rejected stronger claim:** `LE16@11 + 8 == decoded_size` is **not** a corpus invariant; it holds only for stream 1. The other 44 gaps range from 11 through 37 bytes.

**Second-course runtime confirmation:** attempt-2 run 36538122823 loads the first event of tour index 2. The best decoded match is the expected stream 11 (`best_equal_fraction=0.9999842263829519`). Its decoded cursor is 63375, 21 bytes remain after it, and the live cursor settles at 63396: an advance of exactly 21 to `decoded_size - 1` for decoded size 63397. The durable result is `analysis/generated/course-runtime-tour2-tail-cursor.json`.

**Interpretation:** Dragster's seven-step mutation was not a one-course coincidence. On two courses with different trailer lengths, the field starts immediately before the variable trailing region and advances by exactly that region's length to the final decoded byte. Treat `LE16@11` as a mutable pre-trailer/setup cursor. The meaning and grammar of the bytes it traverses remain open.

**Next discriminator:** decode the trailer grammar and trace the exact `82:E1E1` store consumer/loop. A third course is useful as regression coverage but is no longer required to justify the cursor model.


### R-SEED-043 — Cursor boundary is 16-byte aligned, not generally 1024-byte aligned

**Status:** stronger interpretation rejected  
**Date:** 2026-09-29  
**Area:** course format | layout | negative evidence

**Observation:** `LE16@11 + 1` is 16-byte aligned for all 45 USA decoded streams. Dragster additionally happens to satisfy `LE16@11 + 1 = 16 + 33×1024`, which superficially meshes with the independent header-dimension product of 1024.

**Falsification:** only 4/45 USA streams satisfy `LE16@11 + 1 = 16 + N×1024` (streams 1, 7, 9 and 16). The other 41 boundaries land on smaller 16-byte subdivisions.

**Conclusion:** retain the 16-byte boundary invariant. Do **not** interpret the cursor as the end of a stack containing only whole 1024-byte planes, and do not merge this fact with the separate 1024-unit dimension invariant without new runtime/structural evidence.


### R-SEED-044 — Post-cursor region length varies by track-order role

**Status:** confirmed corpus association; semantics open  
**Date:** 2026-09-29  
**Area:** course format | track type | structural statistics

**Observation:** using `LE16@11 + 1` as the aligned start of the decoded trailing region, the nine known stunt-slot streams (tour slot 3) have lengths 10–21 bytes, median 17 and mean 17.0. The other fixed tour slots have medians 26 (slot 1 Race), 27 (slot 2 Circuit), 23 (slot 4 Race) and 27 (slot 5 Circuit); their means are approximately 23.89, 27.22, 23.78 and 26.78 respectively.

**Interpretation:** the trailing region is unlikely to be arbitrary alignment padding alone. Its length distribution is associated with the fixed Race/Circuit/Stunt track-order role, with stunt courses systematically shorter. This does not yet identify the records or prove the trailer is track-type metadata; geometry complexity or another correlated property could produce the same pattern.

**Evidence update:** attempt-2 run 36538122757 regenerated the full trailer corpus; the durable human-readable report is `analysis/generated/course-trailer-structure.md`. Attempt-2 run 36538122823 independently confirms that the non-Dragster stream-11 runtime advances through all 21 trailer bytes to EOF−1.

**Discriminating tests:** classify the trailer byte grammar and compare Europe-retail variants. The former runtime question, whether a non-Dragster course walks the entire region, is now closed positively.

### R-SEED-045 — Beetle/bsnes teardown abort has a concrete double-free path

**Status:** root cause fixed and cross-core validated  
**Date:** 2026-09-29  
**Area:** emulator oracle | libretro | island toolchain

**Observation:** independent-reference run 36627766874 completes the full first-race fixture under the repository-owned Beetle/bsnes core, writes all expected evidence, and then exits 134 during libretro teardown. The vendored core's `retro_deinit()` manually frees `surf->pixels` / `surf->pixels16` and immediately executes `delete surf`. `MDFN_Surface::~MDFN_Surface()` independently frees the same pixel pointer. Therefore the normal teardown path contains a deterministic double free.

**Interpretation:** the post-fixture abort is an adapter/core cleanup defect, not evidence of failed emulation or incomplete fixture execution. The smallest correction is to let `MDFN_Surface` own and free its allocation exactly once, preferably as a narrow project-owned patch rather than silently editing the pristine vendored source.

**Concurrency note:** the active OAM/2P branch currently owns `tools/toolchain.json`, so registering the patch there is intentionally deferred until that work lands or moves clear. Preserve the current exit-134 allowance only until the ownership-safe patch can be applied and validated.

### R-SEED-046 — Beetle emulates cartridge SRAM but does not expose it through libretro

**Status:** interface gap fixed and exact cross-core SRAM roundtrip validated  
**Date:** 2026-09-29  
**Area:** emulator oracle | SRAM | libretro | LoROM

**Observation:** the vendored Beetle/bsnes cartridge loader allocates `SNES::memory::cartram` from the ROM header's RAM size, maps it into the cartridge bus, and leaves it writable. However, the core's `retro_get_memory_data()` and `retro_get_memory_size()` implementations recognize only `RETRO_MEMORY_SYSTEM_RAM`; every other libretro memory type returns null / zero. This exactly explains the existing independent-reference log reporting `wram=131072 ... sram=0` despite Uniracers declaring 8 KiB SRAM.

**Interpretation:** Beetle's current `sram=0` is a frontend API omission, not evidence that the emulated cartridge lacks SRAM or that LoROM SRAM mapping itself is absent. A narrow future patch should expose `SNES::memory::cartram.data()` and `SNES::memory::cartram.size()` for `RETRO_MEMORY_SAVE_RAM`, then rerun the exact preload/dump roundtrip fixture before promotion.

**Concurrency note:** register that patch only after the active OAM/2P branch clears `tools/toolchain.json`; until then the SRAM probe should preserve the zero-byte exposure as evidence rather than conceal it.


### R-SEED-045/046 validation closeout

**Status:** validated  
**Date:** 2026-09-29  
**Area:** emulator oracle | SRAM | libretro | LoROM

Run `36661148644` validates both narrow Beetle compatibility fixes against the canonical Uniracers ROM and the historical 2008 movie SRAM image.

- Reference SRAM: 8192 bytes, SHA-256 `15650bb496292c6fc9c1ea35f8b26070d8c1617169fbe75be3c0482d98649fd1`.
- Pinned Snes9x: reports `sram=8192`, preloads the reference image and dumps an exact byte-for-byte match.
- Repository-owned Beetle/bsnes: after the project patch, reports `sram=8192`, preloads and dumps the same exact 8192-byte image, and terminates cleanly instead of aborting in framebuffer teardown.
- Toolchain run `36661148675` independently validates the patch through the normal fail-closed offline Beetle build path.

This closes the historical LoROM SRAM-mapping compatibility seam at the libretro reference layer. The earlier Beetle `sram=0` observation was an API-export defect, not missing cartridge SRAM emulation.

### R-SEED-047 — Canoe compatibility patch synthesizes the active-display OAM seam

**Status:** patch mechanics confirmed; emulator-faithfulness interpretation open  
**Date:** 2026-09-30  
**Area:** OAM | HDMA | compatibility | Canoe

The recovered Canoe IPS patch is now mechanically reconstructed end to end. GitHub Actions run `36670381748` independently disassembles the injected code with repository-owned da65; `tools/analyze_canoe_ips.py` now makes the same structure a permanent machine-readable regression against the actual patch and canonical USA ROM.

Confirmed patch structure:

- header checksum/complement update at `0x007FDC`;
- `02:D34C -> JSL BF:FF00; RTS`, replacing the stock `$1599 -> $2104` OAMDATA path;
- `02:D714 -> JSL BF:FF36`, replacing stock HDMA source setup;
- `03:8B16` changes `BEQ +4` to `BRA +4`;
- two `STA long` operands are redirected from `7E:2065/2069` to `7F:FFE1/FFEB`;
- a 230-byte handler is injected at `3F:FF00` (called through mirror bank BF).

The OAM wrapper transforms `7E:20A2` to `(value & F0) | 05` and `7E:20A3` to `(value & 0F) | 50`, mirrors those values into `7F:FFF1` and `7F:FFF4`, and writes them through `$2104`. This construction can yield the already reproduced VS values `A5` and `5A`.

The HDMA initializer builds two WRAM tables. Channel 7 uses mode 4, B-bus base `$2100`, and table `7F:FFE0` with descriptors `6F [0F 83 0C 01]`, `02 [80 83 0C 01]`, `60 [0F 83 0C 01]`, `00`. These payloads target `$2100..$2103` and repeatedly select OAM address `$010C`, corresponding to the independently established high-OAM byte destination `0x218`. Channel 1 uses mode 2 and table `7F:FFF0 = 70 55 55 70 55 55 00`; the OAM wrapper dynamically replaces the first data byte of each descriptor. The two redirected stock stores feed the first payload byte of channel-7 descriptors one and three.

**Interpretation:** Canoe works around the same split-screen active-display OAM seam reproduced by the project's unpatched VS fixture. It does so by synthesizing replacement OAM/HDMA state, not by simply suppressing the operation. This is strong independent localization evidence, but the workaround itself is not evidence that Canoe models original SNES hardware correctly.

Full reconstruction and remaining comparison questions: `docs/CANOE-COMPATIBILITY-PATCH.md`.

### R-SEED-048 — Active-display OAM models converge on the VS destination by different mechanisms

**Status:** source-model comparison complete; minimal behavioral reduction open  
**Date:** 2026-09-30  
**Area:** OAM | emulator compatibility | raster timing

Pinned source inspection now explains why several independent emulators agree on the observed Uniracers VS destination while encoding different general rules.

- **Snes9x** `1bcc369e89f08243e0a462882fb1f3e42e51de3a`: `ApplyROMFixes` enables `SNESGameFixes.Uniracers` for ROM names beginning `UNIRACERS`. During HDMA, a transfer to B-bus register `$04` then forcibly sets `PPU.OAMAddr = 0x10C` and `PPU.OAMFlip = 0`; the source labels this a hack for unknown “OAM Address Invalidation.” The project `snesref` debug patch only observes this path and does not create it.
- **MAME** `573fd0e2df004e533c560cd04d7dd9166125f772`: active-display OAM access is redirected to fixed physical address `0x0218`. Its source comment names Uniracers and explicitly says the real address varies while the PPU renders, so the fixed address is an approximation.
- **ares** `4cb8d92b441557cb6bcaf133c4cbc7f6819b1122`: object evaluation and tile fetch update a live `latch.oamAddress`. During active display, OAM reads/writes are redirected through that latch. For high OAM the address is `0x200 | (latch.oamAddress >> 2)`, so sprite index 96 maps to `0x218`.
- **jgenesis** `cc10b2bdd32deb51f1f7a15efa18bae2ba20a41f`: an active-display OAM write first advances sprite evaluation/fetch to the current dot, obtains the current sprite index, then writes the corresponding high-OAM byte. Its source explicitly records that preserving the last fetched sprite index in the no-visible-sprite case is required by Uniracers VS mode.

**Result:** fixed-target compatibility implementations and live-pipeline implementations converge on the same concrete `0x218` observation. Together with the unpatched VS trace and recovered Canoe workaround, the evidence favors a general implementation whose effective OAM destination is derived from raster-time sprite-engine state. The next experiment should reduce that state transition to the smallest deterministic case rather than transplanting a game-name/address exception.

Detailed comparison: `docs/CANOE-COMPATIBILITY-PATCH.md`.

### R-SEED-049 — Unused-song records are ordinary but unreachable CPU audio records

**Status:** static/replay-corpus reconciliation confirmed; unused-song selector identity independently corroborated by TCRF; package attribution strongly supported; causal reconstruction open  
**Date:** 2026-09-30  
**Area:** audio | APU | CPU | unused content

The audio resolver model is now corrected and unified. `02:812A APU_ResolveBlockPointer` walks the contiguous length-prefixed pool beginning at `10:8000`; `0x00..0x31` is only the ID universe appearing inside the six 64-byte package tables, not the resolver's upper bound. Existing direct setup calls to `02:807E` use IDs through `0x42`, and the extended correlation tooling parses `0x32..0x42` from the same record stream.

Within the song-record range, records `0x3B` and `0x3D` are exceptional in exactly the useful way: their payloads uniquely match **Unused Song 1** and **Unused Song 2** at APU `0x1D00`, while they are the only missing ordinary setup selectors in the otherwise populated `0x38..0x42` range. There are no alternate immediate `LDX #$003B/#$003D` setup forms and no unbound direct calls to the setup wrapper in the current scan. Canonical-ROM framing run `36771852989` independently shows every record `0x38..0x42`, including both unused songs, begins with identical bytes `00 04 00 1D` (LE words `0x0400`, `0x1D00`); stripping those four bytes yields the data correlated at APU `$1D00`. The unused records therefore share the ordinary song-record serialization rather than using a special dormant format. Full-pool run `36776390764` extends the parser across all 67 records `0x00..0x42` and exposes a clean late-record framing partition: `0x32..0x33` use word pair `0x0000/0x0400`, `0x34..0x37` use `0x0000/0x1600`, and the complete `0x38..0x42` song family uses `0x0400/0x1D00`. This makes the song-family boundary structural rather than an inference from the SPC corpus alone. Pairwise similarity run `36776832898` then finds `0x3B` and reachable `0x3C` are exceptional near-duplicates: both are 536-byte payloads, share a 165-byte prefix plus 10-byte suffix, and differ at only 16 byte positions. `0x3B` is Unused Song 1; `0x3C` is a reachable song-family record paired with `03:FC15` but absent from the preserved SPC archive. This is strong evidence they are related variants; exact delta semantics remain open.

The six known package tables contain one orphan, `03:FB95`. It has no direct `JSL $82:82A5` caller and is a strict slot-preserving subset of called Celebration table `03:FAD5`: only slots 29, 33 and 49 differ, replacing block IDs `0x15`, `0x29` and `0x07` with `0xFF`. This strongly supports an intentional dormant package variant rather than random bytes.

**Interpretation:** full package/SPC correlation run `36777071311` (artifact `11126836085`, digest `sha256:64944bcb5437dd0858ad71d07759b639d30734aa03de0f0635f7963710d92496`) correlates all 50 package blocks against the ten preserved SPC snapshots. Block `0x00` is the sole mechanically untestable record because its 22-byte payload is below the correlator's 32-byte minimum. Excluding only that block, the method reproduces every known reachable package association exactly: Title=`03:FBD5`, Demo=`03:FB15`, Celebration=`03:FAD5`, and all five numbered races=`03:FB55`. It then gives Unused Song 1 the exact same 18-block correlatable signature as Demo Race, strongly supporting `03:FB15` reuse, and Unused Song 2 the exact same 23-block signature as every numbered race, strongly supporting `03:FB55` reuse. Independent live FB55 transfer evidence corroborates the second attribution. `03:FB95` remains an intentional orphan/reduced package variant but is not supported as the complete package of either preserved unused song. The `0x3B/0x3C` near-duplicate keeps `03:FC15` as a useful sequence-sibling control for Unused Song 1.

**Evidence:** `analysis/generated/audio-setup-selector-map.json`; `analysis/generated/audio-package-map.json`; `analysis/generated/audio-extended-block-correlation.json`; `analysis/generated/audio-package-spc-signatures.json`; `analysis/generated/audio-unused-path-analysis.{json,md}`; `analysis/generated/audio-record-pool-reconciliation.md`.
Independent secondary-source corroboration: The Cutting Room Floor's Uniracers article reports title-screen PAR substitutions selecting audio records `$3B` and `$3D` for its two preserved unused tracks. This agrees with the project's independently derived record identities. Source registry: `reference/catalog.yml` entry `tcrf-uniracers-unused-content`; reconciliation note: `reference/notes/tcrf-unused-content.md`. Treat the PAR patch semantics beyond the selector identity as a lead until locally reproduced.

**Discriminating test:** reconstruct the evidence-backed primary pairs `0x3B + 03:FB15` and `0x3D + 03:FB55` in a reference APU harness and compare resulting RAM against the preserved unused-song SPCs. Retain `0x3B + 03:FC15` as the near-twin-sequence control and `0x3B + 03:FB95` as the orphan-table control.

---


### R-EXT-015 — Nitrodon reverse-engineering workspace

**Status:** supported historical evidence with several locally corroborated promotions  
**Date:** 2026-09-30  
**Area:** CPU | RAM | physics | camera | course | UI | other

**Observation:** Nitrodon directly supplied a nine-file 2008–2009 reverse-engineering workspace containing a detailed WRAM map, course/ROM offsets, annotated bank-80–83 listings, focused stunt disassembly, message IDs and a bounce trace. The bank-82 material directly describes the shipped stunt finalizer, movement/boost paths and controller decode. Three adjacent stunt-weight tables are exactly `[0,125,250,375,500]`, `[0,25,50,75,100]`, and `[0,5,10,15,20]`; Z-flips are added directly, proving the stunt combination index `125*flips + 25*rolls + 5*twists + zflips` into the 625-byte table at `02:9DAA`.
**Evidence:** `reference/imported/reverse-engineering/nitrodon/`; `reference/notes/nitrodon-reverse-engineering-mining.md`; `analysis/generated/nitrodon-reconciliation.json`; canonical symbol changes in `docs/SYMBOLS.md`. The tabletop-duration interpretation independently explains dynamic run 36776825024's `0→1→2→3→4→0` transient.
**Interpretation:** This workspace materially narrows several formerly broad reverse-engineering tasks. It resolves shared-current-player versus stable-player state for velocity/boost, corrects multiple field widths/labels, exposes exact stunt-combination encoding, and gives bounded addresses for stunt, gravity, input, checkpoint/finish and collision work.
**Discriminating test:** decode the `FE/FF` stunt-table sentinels; trace `11CF/11D1 ↔ 11CD`; watch `1199/119D/0EF1` through a deterministic Dragster finish; trace isolated stunt combinations into `12AF`; reconcile Nitrodon's ROM map offsets against decoded RNC course payloads; replay/interpret the bounce trace against current collision code.
**Dependencies:** Nitrodon's annotations remain historical working evidence where not independently reproduced; the promoted symbol changes are limited to cases with direct instruction-level or dynamic corroboration.

### R-EXT-016 — Dessyreqt direct historical workspace

**Status:** supported historical evidence; selected conclusions corroborated by Nitrodon/current runtime  
**Date:** 2026-09-30  
**Area:** RAM | physics | camera | course | UI | other

**Observation:** Dessyreqt directly supplied an 80-file historical Uniracers working directory containing 17 Lua scripts, 9 glitch/test SMVs, 45 course-map PNGs, 3 SRAM images, 2 memory-watch files and 4 research documents. The scripts recover a visible `movebot → teststuntbot → tabletopbot` autonomy lineage plus USJO internal v14/v14a development material. V14/v14a read `7E:11CD` as a 16-bit boost word; v14a additionally parses the message queue at `0CBB/0CE1/0CE3` and scores live boost plus queued stunt credit relative to a no-stunt baseline. The directly recovered Tabletop bot differs from the public 2014 source by a Dragster-specific direction/rotation correction and one changed jump rectangle.

**Evidence:** `reference/imported/reverse-engineering/dessyreqt/`; `reference/notes/dessyreqt-workspace-mining.md`; `analysis/generated/dessyreqt-workspace-index.json`. Independent Nitrodon evidence corroborates several paired-racer/stunt addresses and the 16-bit boost interpretation.

**Interpretation:** v13 recovery is no longer technically important; the project now has later optimizer source and a broader autonomous-policy development history. The 45 maps satisfy the practical need for a complete local visual course corpus. The glitch SMVs provide deterministic collision-boundary seeds. The P2 watch/bot fields are particularly useful for the existing two-player fidelity lane.

**Discriminating test:** reconcile v14a queue-message IDs against Nitrodon's message table and ROM-side message/boost routine; verify P2 facing/tabletop/roll/flip/Z/checkpoint fields during deterministic 2P play; replay one recovered Jumpover SMV unchanged before reducing it to a minimal collision discriminator; compare `magicnumber.lua` start/finish coordinates to runtime/course-stream identity.

**Dependencies:** imported Lua remains historical working code with old-Snes9x assumptions and deliberate WRAM mutation in several utilities. Preserve source unchanged and promote semantics only after local corroboration.



### R-SEED-050 — 2014 pre-race mismatch is frontend timing reuse, not established gameplay divergence

**Status:** reclassified; useful semantic dispatch discovery retained  
**Date:** 2026-09-30  
**Area:** CPU | frontend | validation | timing

Dense historical replay run `36793691236` moved the first sampled low-WRAM mismatch to frame 437. A bounded +5-frame phase experiment in run `36794900073` delayed the first mismatch to frame 455 but did not restore race-entry/results alignment. State matching shows the offset is not fixed: it grows from roughly +2 to +5 frames through startup.

Run `36795810324` explains why the early tuple was a bad semantic oracle. Nitrodon's exact listings show `83:8B79-8B8B` bulk-fills WRAM `$0200-$09FF` with `$004C`, covering `$0313/$0411/$0415`, while `80:C3AB/C3C8` interprets frontend/text commands and reuses DP `$9F` as layout state. The live trace reaches `interp@$80C3C8` during this transition. Therefore the pre-race values sampled at the player/race addresses are frontend workspace, not authoritative race simulation.

**Interpretation:** stop spending evidence budget on absolute pre-race frame equality for this old SMV. Use it event-relatively until a mutually valid semantic anchor exists. The useful decompilation result is that analyzer gap `80:C3C8` is a live 17-way frontend/text command dispatcher and should be mapped as such.

**Evidence:** `analysis/generated/historical-2014-native-replay-gap.md`; runs `36793691236`, `36794900073`, `36795810324`; Nitrodon bank 80/83 listings.


### R-SEED-051 — Deterministic Dragster finish mechanism matches native/reference

**Status:** confirmed and promoted  
**Date:** 2026-09-30  
**Area:** race | checkpoint | finish | validation

Run `36801728342` reuses the existing deterministic Dragster finish route and adds only three paired semantic fields per racer: next checkpoint `1199/119B`, finish gate `119D/119F`, and laps remaining `0EF1/0EF3`. No additional framebuffer or dense-frame capture was required.

Native and pinned Snes9x agree at every existing racer-state checkpoint and on every added finish field. The shared progression is:

- finish-probe-start: checkpoint/gate/laps = `0 / 0 / 2`;
- finish-probe-05: `1 / 1 / 1`;
- finish-probe-20 through terminal: `3 / 0 / 1`;
- race-results: `1 / 1 / 0`.

Both runtimes reach stock results with `Frontend_CurrentMenu = 0x99` and `Race_ActiveState = 0x00`. Both players exhibit the same paired checkpoint/gate/lap sequence.

Static bank-81 analysis independently localizes the checkpoint/finish handler to `81:8050`, dispatched from the course object/collision table at `81:8334`. That routine gates on `119D/Y`, snapshots the race timer, decrements `0EF1/Y`, and advances checkpoint state including `1199/Y`.

**Interpretation:** deterministic 1P finish fidelity is closed at the current semantic evidence level. Further finish tracing should be demand-driven by a specific product discrepancy, not collected for completeness.

**Evidence:** run `36801728342`; `.github/workflows/race-finish-differential.yml`; `tools/summarize_paired_player_slots.py`; Nitrodon bank-81 listing.

### R-SEED-052 — PAL survivor disagreements collapse under trusted-boundary piecewise alignment

**Status:** confirmed methodological closure with one genuine executable lineage delta  
**Date:** 2026-09-30  
**Area:** CPU | decompilation | comparative analysis | tooling

The first homolog-aligned PAL retail versus 1994-11-29 prototype snes2asm pass reduced same-offset role disagreement from 3,662 to 114 but left three survivor windows. A second pass subdivided only at independently recovered boundaries from Nitrodon's bank-80 listing, the decoded frontend dispatch table, and known control-flow entries, then realigned each executable island separately.

All 114 remaining role disagreements disappear. In `00:ABA9..00:ADE2`, executable `ABB9..AD0F` aligns at -31 while `AD34..ADE2` aligns at -13, with embedded frontend data between them. In `00:C3A9..00:C450`, code on both sides of the 17-entry `C3CB..C3EC` dispatch table aligns cleanly at -19. In `00:8C49..00:8CCA`, executable `8C4E..8C73` is byte-identical at -5 and `8C78..8CCA` is byte-identical at -9; PAL retail alone contains a four-byte JSL at `80:8C74..80:8C77`.

**Interpretation:** analyzer disagreement is now zero inside homologous executable subregions for all 32 high-value PAL/prototype windows. The remaining evidence is structural: mixed code/data windows need piecewise alignment, and real instruction insertions/deletions can change the homolog shift within a function. Do not escalate these closed windows to da65 or Ghidra. Preserve the retail-only JSL as a genuine lineage delta.

**Evidence:** `analysis/generated/pal-snes2asm-homolog-alignment.{json,md}`; `analysis/generated/pal-snes2asm-subregion-alignment.{json,md}`; `tools/refine_pal_snes2asm_survivors.py`; Nitrodon `reference/imported/reverse-engineering/nitrodon/bank 80.txt`.

### R-SEED-053 — Fresh Europe/USA exact misses resolve structurally

**Status:** supported/strong cross-build correspondence; atlas queue corrected  
**Date:** 2026-09-30  
**Area:** CPU | decompilation | comparative analysis | symbols

After closing the PAL/prototype analyzer survivors, the exact-fingerprint atlas still exposed five Europe/USA function misses. HUD queue and stunt finalizer already had structural correspondence evidence. The three remaining useful misses were added to the relocation-resistant semantic-anchor corpus.

`Player_ApplyVerticalAcceleration` maps USA `82:A968` to PAL prototype `82:A959` (0.912 similarity, strong) and Europe `82:A96F` (0.897, supported). Europe’s changed operands follow established regional motion families: `0F41→0F4B`, `0FEF→0FF9`, `0FA1→0FAB`, with `0541→0547` in a +6 family.

`Input_DecodePlayer1Buttons` maps USA `82:AA6E` to PAL prototype `82:AA5F` (0.988, strong) and Europe `82:AA75` (0.846, strong). Europe coherently translates the controller-state block by +4, including `030D→0311`, `030F→0313`, and the output fields through `0335→0339`.

`Text_TestCharacterMetadataBit7` maps USA `80:8C41` to PAL prototype `80:8C3C` (0.923, strong) and Europe `80:8C41` (0.846, supported).

**Interpretation:** exact byte-window failure and unresolved correspondence are different states. The comparative atlas now consumes the canonical structural-correspondence surface and removes supported-or-better structural matches from the structural-alignment queue while retaining their exact-match status unchanged.

**Evidence:** `tools/compare_semantic_anchors.py`; `tools/build_cross_build_symbol_correspondence.py`; `tools/build_comparative_code_atlas.py`; `analysis/generated/semantic-anchor-cross-build-matches.{json,md}`; `analysis/generated/cross-build-symbol-correspondence.{json,md}`; `analysis/generated/cross-build-semantic-anchor-findings-2026-09-30.md`.

### R-SEED-054 — Seeded Europe/USA homologs preserve opcodes across selected core routines

**Status:** confirmed bounded analyzer consensus; operand-only regional variation in accepted corpus  
**Date:** 2026-09-30  
**Area:** CPU | decompilation | comparative analysis | regional layout

The first Europe/USA snes2asm probe initially returned zero role disagreement for the newly matched bank-81/bank-82 routines, but inspection showed every compared byte was `unreached→unreached`. That unseeded result is rejected as vacuous: snes2asm's default vector walk does not reach these routines.

The accepted pass seeds only independently recovered function entries before path discovery. `Collision_TransformVelocity` additionally seeds at the local `REP #$10 / SEP #$20` width setup immediately before the compared matrix body, so M/X context is established independently rather than guessed.

Fourteen executable subregions now cover text metadata, vertical acceleration, three independently bounded input-decoder pieces, collision velocity/contact-shape logic, HUD enqueue, the racer-frame state-marshal prefix, two stunt-finalizer blocks, and three course-loader/materializer blocks.

Across **1,152 aligned opcode positions** there are:
- **0 opcode-byte substitutions**;
- **0 opcode/operand role disagreements**;
- **0 M/X disagreements**;
- **427 changed operand bytes**.

Raw similarity ranges from 0.674 to 0.990. The racer-frame marshal prefix is the strongest example: only 67.4% of raw bytes match, yet all 208 aligned opcode bytes are identical and 203 changed bytes are operands. This is direct comparative evidence of regional state-layout retargeting inside preserved executable structure.

**Interpretation:** do not escalate these fourteen regions to da65/Ghidra. Preserve their operand changes as regional address/constant evidence. Also treat analyzer reachability itself as part of the comparison contract: `unreached→unreached` is not consensus.

**Evidence:** `tools/compare_europe_usa_snes2asm_homologs.py`; `analysis/generated/europe-usa-snes2asm-homologs.{json,md}`; run `36816088608`; Nitrodon bank-80/81/82 listings.

### R-SEED-055 — Europe retail contracts checkpoint timer normalization after the PAL prototype

**Status:** confirmed four-ROM lineage delta  
**Date:** 2026-09-30  
**Area:** CPU | checkpoint/finish | regional timing | comparative analysis

The expanded Europe/USA seeded snes2asm corpus adds bounded checkpoint/finish and racer-OAM projection regions.

The OAM player-1 and player-2 projection blocks align at Europe shift `+7` with 141 aligned opcode positions, zero opcode substitutions, zero role/M/X disagreements, and 48 operand-byte changes.

`Race_HandleCheckpointFinish` is more interesting. Its dispatch-confirmed entry remains `81:8050` in USA and Europe. Code through USA/Europe `81:8101` is structurally aligned at shift 0. The later record and lap/HUD blocks align cleanly at shift `-14`. The intervening timer-frame normalization block is a real regional size/logic change:

- USA `81:8102..81:8117`: 22 bytes, opcode shape `AD C9 30 3A 0A 18 6D C9 30 A9`.
- Europe `81:8102..81:8109`: 8 bytes, opcode shape `AD 0A 18 6D`.
- Net Europe contraction: **14 bytes**.

Under the independently established 16-bit state, USA reads the frame field, conditionally decrements it when it is at least 4, doubles it, adds `$0300`, then clamps the result to 9. Europe reads its relocated frame field, doubles it, and adds `$0300`, omitting both adjustment/clamp branches.

Four-ROM shape classification sharpens the lineage:
- USA retail: 22-byte style.
- Legacy beta: 22-byte style.
- PAL prototype 1994-11-29: 22-byte style with the expected relocated frame-field operand.
- Europe retail: 8-byte style.

**Interpretation:** this simplification occurred after the November 1994 PAL prototype and is specific to the later Europe-retail line among the four preserved builds. Do not generalize it to all PAL code. It is preserved as a genuine executable delta, while the surrounding checkpoint/finish code remains homologous after piecewise alignment.

**Evidence:** `tools/compare_europe_usa_snes2asm_homologs.py`; `analysis/generated/europe-usa-snes2asm-homologs.{json,md}`; run `36816833830`; dispatch-confirmed `Race_HandleCheckpointFinish` identity.

### R-SEED-056 — PAL prototype preserves USA opcode stream across trusted semantic corpus

**Status:** confirmed bounded analyzer consensus  
**Date:** 2026-09-30  
**Area:** CPU | PAL prototype | comparative analysis | regional layout

The trusted Europe/USA semantic corpus was reused against the 1994-11-29 PAL prototype, preserving the same independently recovered subregion boundaries and trusted-entry seeding discipline.

Across **19 bounded executable subregions** and **1,465 aligned opcode positions**:
- **0 opcode substitutions**;
- **0 opcode/operand role disagreements**;
- **0 M/X disagreements**;
- **296 changed operand bytes**.

The tested corpus spans text metadata, vertical acceleration, the recovered input decoder, collision velocity/contact-shape logic, HUD enqueue, racer-frame state marshal, stunt finalizer, course load/materialization, checkpoint/finish, and both racer-OAM projection blocks.

The prototype is therefore instruction-for-instruction USA-shaped throughout this bounded corpus while already carrying substantial regional operand/address motion. Europe retail shows 510 operand-byte changes across the comparable corpus, versus 296 in the prototype, consistent with additional regional layout evolution after November 1994.

Checkpoint/finish provides the clearest lineage discriminator: the PAL prototype retains the USA-style 22-byte frame-normalization logic at `81:8102`, while Europe retail alone contracts it to 8 bytes.

**Interpretation:** the surviving PAL prototype is best treated as an intermediate regional-layout snapshot with largely frozen executable structure, not merely as a noisy alternate build. For the current trusted-anchor corpus, additional second-analyzer escalation is not warranted unless new evidence contradicts the seeded snes2asm consensus.

**Evidence:** `tools/compare_usa_palprototype_snes2asm_homologs.py`; `analysis/generated/usa-pal-prototype-snes2asm-homologs.{json,md}`; run `36817274047`.

### R-SEED-057 — Post-prototype WRAM repacking separates into +6, +4, and stable families

**Status:** confirmed structural lineage clustering  
**Date:** 2026-09-30  
**Area:** WRAM | cross-build lineage | structure inference

The existing `tools/build_wram_motion_atlas.py` was extended rather than replaced. For USA fields that project consistently in both the 1994-11-29 PAL prototype and Europe retail, the atlas now computes a second displacement: Europe candidate address minus prototype candidate address.

This isolates layout motion that occurred **after** the surviving PAL prototype.

The accepted cross-build field set collapses into three clean secondary-motion families:

- **+6 bytes:** 38 fields. This includes message/UI state (`0BA1/0BA3`, `0CBB`, `0CE1..0CE5`, `0D0B/0D0D/0D49`) and a large shared gameplay/state family (`0E89..0E93`, `0F47/0F49/0F61/0F7B/0F9F/0FA1/0FEF`, stunt/progress fields, OAM-related `1509..150E`, and course/runtime fields).
- **+4 bytes:** 12 fields concentrated in racer position/camera/velocity state, including `0411..042F` and `04B7/04BB`.
- **+0 bytes:** 10 stable fields, primarily DP/hardware/DMA registers such as `000B`, `02C0..02C6`, `2100/2115/2116`, and `420B/420C`.

No contradictory projection appears within the accepted field corpus.

**Interpretation:** Europe retail is not merely “prototype layout plus a global shift.” At least two distinct logical WRAM families were repacked after November 1994: one by +6 and the racer position/velocity family by +4, while hardware-facing addresses remained fixed. This is stronger evidence for structure boundaries than raw address adjacency alone.

**Evidence:** `tools/build_wram_motion_atlas.py`; `analysis/generated/wram-motion-atlas.{json,md}`; one-shot refresh run `36817638025`.

### R-SEED-058 — Europe retail WRAM repacking is bracketed by two post-prototype insertions

**Status:** confirmed structural brackets; exact inserted fields still open  
**Date:** 2026-09-30  
**Area:** WRAM | cross-build lineage | structure inference

The prototype→Europe secondary-motion atlas was tightened with additional trusted semantic fields from input decoding, stunt/result state, persistent racer state, camera state, and air-time handling.

The accepted low-address corpus now separates into three structural families:
- **+0:** stunt/result scratch through at least `026A`, plus other stable low/MMIO fields;
- **+4:** raw/controller state beginning by `030D`, persistent racer position/stunt/velocity/pitch state, and camera velocity through at least `04FB`;
- **+6:** air/physics state beginning by `0541`, and the broad later gameplay/UI/state families above it.

This brackets two post-1994-11-29 insertions/expansions in the Europe-retail WRAM layout:

1. **+4-byte insertion bracket:** after the last confirmed +0 field `026A` and no later than the first confirmed +4 field `030D`.
2. **+2-byte insertion bracket:** after the last confirmed +4 field `04FB` and no later than the first confirmed +6 field `0541`.

The second bracket is independently supported by bounded camera anchors: `04F5/04F7/04F9/04FB` all remain prototype→Europe +4, while `0541` and `0545` are +6.

Nitrodon's recovered RAM map gives useful semantic landmarks around the second bracket: `04F1/04F3` are map-size geometry, `04F5/04F7/04F9/04FB` are camera-velocity/state slots, and `0545` is player air time. The exact new Europe-only field(s) responsible for the +2 jump are not yet identified.

A hygiene correction also excludes `Text_TestCharacterMetadataBit7`'s ROM table at `80:C6F8` from the WRAM-motion atlas; its prior +19 projection was not WRAM evidence.

**Interpretation:** treat these as address-space insertion brackets, not exact field locations. The highest-value next step is to inspect code/data references inside `026A..030D` and `04FB..0541` for Europe-only or resized state, rather than broadening the homolog corpus.

**Evidence:** `tools/compare_semantic_anchors.py`; `tools/build_wram_motion_atlas.py`; `analysis/generated/wram-motion-atlas.{json,md}`; Nitrodon `RAM addresses.txt`; boundary-refresh runs `36818170140`, `36818242325`.

### R-SEED-059 — Post-prototype WRAM insertion brackets narrowed to 0309→030D and 053B→0541

**Status:** confirmed structural brackets; inserted-field semantics remain unidentified  
**Date:** 2026-09-30  
**Area:** WRAM | cross-build lineage | structure inference

Two narrow probes refine R-SEED-058 without changing its basic interpretation.

For the first Europe-retail +4 displacement jump, additional trusted anchors show:
- `0302` remains fixed across USA retail, the PAL prototype, and Europe retail.
- unnamed live state `0306` remains fixed.
- unnamed live state `0309` remains fixed.
- USA/prototype raw-controller word `030D` maps to Europe `0311` (+4), and `030F` maps to `0313`.

No credible recovered references were found for `030A..030C`. The formal insertion bracket is therefore **after `0309`, no later than old field `030D`**. The evidence is consistent with a four-byte Europe-only allocation immediately before the old controller block, but its contents are not yet semantically identified.

For the later +2 jump, same-function camera-state anchors progressively tighten the boundary:
- `0521`, `052B`, `052F`, `0533`, `0535`, `0537`, `0539`, and `053B` all remain in the prototype→Europe +4 family.
- `0541` is already in the +6 family, mapping to Europe `0547`.
- `0545` likewise maps at +6 to Europe `054B`.

The formal second insertion bracket is therefore **after `053B`, no later than old field `0541`**. Recovered code has no trustworthy references to `053D/053F`, so static evidence currently cannot place the two-byte insertion more precisely.

A separate trusted-entry operand scan corroborates the family transitions without being used as semantic proof. Its evidence is preserved in `analysis/generated/wram-insertion-bracket-probe.{json,md}`.

**Interpretation:** Europe retail added or expanded four bytes of low WRAM state immediately before the old controller-state family, and later accumulated a further two-byte expansion somewhere after `053B` but before `0541`. These are structure-boundary facts; the identities of the added fields remain open.

**Evidence:** `tools/compare_semantic_anchors.py`; `tools/build_wram_motion_atlas.py`; `tools/probe_wram_insertion_brackets.py`; `analysis/generated/wram-motion-atlas.{json,md}`; `analysis/generated/wram-insertion-bracket-probe.{json,md}`; Nitrodon bank-81/bank-82 listings.

### R-SEED-060 — Europe controller-buffer shift is not extra auto-joypad capture state

**Status:** negative result; insertion semantics remain open  
**Date:** 2026-09-30  
**Area:** WRAM | input | regional lineage

The final trusted inserted-state probe seeded every accepted semantic anchor and searched the two narrow post-prototype insertion neighborhoods.

For the first +4 bracket, Europe retail has **no trusted direct references to `030A..0310`**. USA and the PAL prototype reference the old raw-controller bytes `030D..0310`; Europe instead uses the relocated controller buffer beginning at `0311`.

The recovered Europe auto-joypad capture sequence still reads only SNES auto-joypad registers `4218..421B`; there are no trusted reads of `421C..421F`. Europe prepends width-state setup and stores the four captured bytes at `0311/0313/0312/0314`, preserving the same four-byte controller payload after the +4 WRAM displacement.

Therefore the four inserted bytes before the old controller block are **not explained by expanded controller-register capture**. Within the trusted direct-address corpus they are currently unreferenced; padding, reserved state, indexed/indirect access, or as-yet-unrecovered use remain possible.

For the second +2 bracket, the only numerically Europe-only trusted operand inside `053C..0546` is `053D`, which is fully explained as the established +4 relocation target of USA/prototype `0539`. No unexplained Europe direct operand is present in that inserted neighborhood either.

**Interpretation:** absence of direct references is meaningful negative evidence but does not prove padding. Do not assign semantics to either inserted span without direct indexed/runtime evidence.

**Evidence:** `tools/probe_wram_insertion_brackets.py`; `analysis/generated/wram-insertion-bracket-probe.{json,md}`; run `36819609931` and final refreshed evidence.

### R-SEED-061 — External version-difference search yields actionable timing/OAM prior art, no public comprehensive diff

**Status:** external prior-art pass complete; local discriminators queued  
**Date:** 2026-09-30  
**Area:** regionalization | prototype | timing | emulation history

A dedicated public search was run across TAS/speedrun forums, GameFAQs archives, emulator changelogs/source history, NESdev/bsnes hardware discussions, preservation databases, developer interviews, and multilingual web results. This is distinct from earlier resource acquisition: the question was specifically what other people had already learned about USA/PAL/prototype differences.

High-value public evidence:

1. **Cross-region deterministic input desync.** A 2008 TASVideos poster accidentally replayed a USA Snes9x movie against PAL `Unirally`; the run diverged immediately and failed Dragster. This is independent historical evidence that region choice materially changes deterministic replay behavior.
2. **Separate PAL/NTSC record populations.** Historic GameFAQs communities maintained distinct regional record tables. Representative Dragster records (~25.06 s NTSC vs ~29.85 s PAL) are roughly consistent with 60/50-Hz wall-clock scaling but are human records, not a timer oracle.
3. **Prototype chronology.** Hidden Palace explicitly identifies the Nov-29-1994 image as a European PAL prototype, preceding USA retail and roughly five months before Europe retail. This supports using it as an intermediate lineage discriminator.
4. **Active-display OAM prior art.** Snes9x historically carried a Uniracers-specific OAM/HDMA workaround; later bsnes/NESdev hardware research explains the game as an unusual active-display/HBlank OAM writer whose successful destination depends on internal PPU OAM addressing.
5. **Developer protection provenance.** Andrew Innes independently described DMA accidentally discovering real-cartridge versus copy-device behavior and deliberately turning it into anti-piracy protection; contemporary copier documentation also listed Uniracers as protected.

No trustworthy public source found provides a comprehensive USA-vs-Europe executable/gameplay change list. In particular, the search found no prior public documentation of:
- the Europe-retail-only checkpoint timer-normalization contraction;
- the post-prototype +4/+2 WRAM insertion chronology;
- the unresolved semantics of those inserted WRAM spans;
- a prototype-to-retail technical change log.

**Interpretation:** the public record supplies valuable independent discriminators but does not supersede the local multi-ROM atlas. The strongest next local experiment is a project-owned fixed input trace replayed across USA retail, PAL prototype, and Europe retail, with first divergent frame/state localized.

**Evidence:** `reference/notes/regional-version-differences-prior-art.md`; indexed sources in `reference/catalog.yml`; updated `regional-and-prototype-differential` evidence-worklist entry.

### R-SEED-062 — Racer-update island recovers code→table→code boundaries across all four builds

**Status:** confirmed structural recovery  
**Date:** 2026-09-30  
**Area:** CPU | racer update | code/data boundaries | comparative atlas

The reframed multi-ROM × multi-analyzer lane produced its first new structure outside the previously named semantic-anchor set.

Direct calls from `Race_UpdateRacersFrame`, explicit RTS boundaries, exact cross-build byte identity, and trusted-entry-seeded snes2asm recover the USA/beta island:

- routine `82:A22B..A27B` (81 bytes);
- routine `82:A27C..A2D3` (88 bytes);
- 128-byte / 64-word lookup table `82:A2D4..A353`;
- following routine `82:A354..A497`.

The 1994-11-29 PAL prototype and Europe retail omit the five USA/beta NOP bytes at `A2B2..A2B6`-equivalent position. Their second routine is therefore 83 bytes rather than 88, and the otherwise byte-identical lookup table plus following routine shift by an additional five bytes.

The 128-byte lookup table is **exactly identical in all four builds** and is directly consumed by the following routine via a long indexed load from its build-specific base. This independently establishes a durable code/data boundary.

Within the following routine, snes2asm leaves a 13-byte instruction-shaped pocket unreached in every build (USA/beta `A484..A490`, prototype `A475..A481`, Europe `A48B..A497`). The surrounding flow jumps over it and no direct bank-82 branch/call target was found. Preserve it as a dead-code candidate, not data.

**Interpretation:** this is the intended payoff of comparative structure recovery: function sizes, data-object boundaries, lineage edits and dead-code candidates become recoverable before full semantic naming.

**Evidence:** `tools/analyze_racer_update_structure_island.py`; `analysis/generated/racer-update-structure-island.{json,md}`; run `36821725861`.

### R-SEED-063 — Racer-update structural corridor extended 2.1 KiB into gravity/input anchors

**Status:** confirmed structural recovery  
**Date:** 2026-09-30  
**Area:** CPU | racer update | call graph | code/data boundaries

The first comparative structural island has been extended contiguously from USA `82:A22B` through `82:AA6D`, covering **2,115 bytes** of the per-frame simulation neighborhood.

The corridor now contains eleven bounded routines, one exact 128-byte/64-word inline table, and the long-entry wrapper immediately preceding the known input decoder. It directly bridges anonymous racer-update internals into the already-promoted `Player_ApplyVerticalAcceleration` routine and `Input_DecodePlayer1Buttons`.

All added routine boundaries relocate coherently across the PAL prototype and Europe retail after accounting for the five-byte PAL-line contraction already identified inside the `A27C` routine. Legacy beta remains byte-identical to USA throughout this corridor.

A second preserved unreachable instruction block is visible inside the `A6F1..A8C1` routine: USA/beta `A794..A7A5` (18 bytes), prototype `A785..A796`, Europe `A79B..A7AC`. Preserve it as a dead-code candidate pending runtime/indirect evidence.

**Interpretation:** the comparative lane is now recovering useful call-graph structure at kilobyte scale. The next priority is to repeat this process on other high-connectivity executed islands rather than further dissecting already-bounded regional WRAM gaps.

**Evidence:** `tools/analyze_racer_update_structure_island.py`; `analysis/generated/racer-update-structure-island.{json,md}`; run `36822022169`.

### R-SEED-064 — Collision/object island recovers embedded dispatch data and Europe-only handler prologue

**Status:** confirmed structural recovery  
**Date:** 2026-09-30  
**Area:** CPU | collision/object handling | code/data boundaries | comparative atlas

A second independent structural-recovery island has been established in bank 81 around the object/collision path entered from the racer-update hub.

USA/beta structure:
- long-entry wrapper `81:82E2..82E5`;
- dispatcher head `81:82E6..831F`;
- 30-byte / 15-word explicit handler-pointer prefix `81:8320..833D`;
- dispatcher tail `81:833E..8340`;
- handler `81:8341..8371`;
- exact 50-byte / 25-signed-word lookup table `81:8372..83A3`;
- following handler `81:83A4..84D1`.

The lookup table is byte-identical in all four builds and establishes a clean data→code boundary. It also corrects Nitrodon's linear listing, which begins decoding one byte early at `83A3`.

The explicit pointer prefix relocates coherently across builds. Its final entry targets USA/beta `8341`, prototype `8324`, and Europe retail **`8316`**.

Europe retail adds five executable bytes before the otherwise homologous handler body:

`C2 30 AD 2F 0F` = `REP #$30; LDA $0F2F`.

The PAL prototype lacks this prologue, proving it was added later in the Europe-retail lineage. The loaded value is immediately overwritten by the homologous body, so the addition appears semantically inert under ordinary WRAM-read behavior, but that semantic interpretation remains secondary to the confirmed structural fact.

The 30-byte handler-pointer run is deliberately recorded as a **prefix**, not a complete dispatch table: `JSR ($8320,X)` is guarded by `X < 0x003C`, which by itself permits a wider offset domain than these 15 words.

**Interpretation:** the comparative structure method now works in two independent race-critical subsystems, recovering embedded data boundaries and executable lineage edits without needing full semantic naming.

**Evidence:** `tools/analyze_object_collision_structure_island.py`; `analysis/generated/object-collision-structure-island.{json,md}`; object-collision structure runs ending at `36823094425`.



### R-SEED-062 — Comparative structural census seeded from recovered islands

**Status:** confirmed  
**Date:** 2026-10-01  
**Area:** CPU | other

**Observation:** the two comparative structure-recovery islands can now be queried through one normalized census rather than separate prose/artifact surfaces. The seed contains 20 bounded USA regions across banks 81 and 82: 17 code regions and 3 explicit data regions, totaling 2,611 bytes.  
**Evidence:** `analysis/generated/comparative-structural-census.{json,md}`, built deterministically by `tools/build_comparative_structural_census.py` from the racer-update and object/collision structural-island JSON artifacts. The current seed contains 2,403 code-region bytes, 208 explicit data bytes, and 1,001 analyzer-classified USA opcode bytes.  
**Interpretation:** comparative structure recovery now has a machine-queryable growth surface. Coverage counts are intentionally a floor, not a whole-ROM percentage, because only independently recovered boundaries are admitted.  
**Discriminating test:** extend the census with a third independent executed subsystem island and confirm that its regions can be added without weakening existing boundary provenance or turning raw linear-disassembly reachability into asserted structure.  
**Dependencies:** source island boundaries retain their existing evidence/provenance; this census does not independently prove them.  
**Propagation:** work queue item 9 now treats the seed census as completed infrastructure and directs the next pass toward a third high-connectivity subsystem rather than deepening the already-bounded racer or object/collision islands merely for byte count.


### R-SEED-063 — Full course-loader structure is stable across all four builds

**Status:** confirmed  
**Date:** 2026-10-01  
**Area:** CPU | course | PPU | DMA/HDMA

**Observation:** the complete named `Course_LoadAndMaterialize` corridor at USA `82:E165..E395` partitions cleanly into five executable phases: setup, resource-record/header handling, DMA row loop, resource materialization into `7E:A000/7E:C000`, and common exit.  
**Evidence:** ROM-backed unit run `36854224907`; `analysis/generated/course-materialization-structure-island.{json,md}`; `tools/analyze_course_materialization_structure_island.py`. All 554 USA bytes in the five partitions are analyzer-reached (257 opcode bytes + 297 operand bytes). Europe retail aligns at a constant -58-byte shift across all five partitions, PAL prototype 1994-11-29 at -100, and legacy beta is byte-identical to USA.  
**Interpretation:** the loader's internal architecture was preserved across the regional lineage even as code was relocated. The resource-to-WRAM materialization stage is now structurally bounded rather than inferred only from semantic traces, giving course/editor work a stable implementation seam.  
**Discriminating test:** none required for the five-part structural boundary claim. Deeper descriptor/plane semantics should be pursued only when editor/course implementation needs them.  
**Dependencies:** snes2asm trusted-entry seeding and existing Nitrodon/control-flow boundaries.  
**Propagation:** added the course island to `analysis/generated/comparative-structural-census.{json,md}`, expanding the census to 25 regions / 3,165 bytes; the queue now advances to a fourth independent subsystem rather than further decomposing this loader for coverage alone.


### R-SEED-064 — Full racer OAM builder exposes preserved viewport architecture

**Status:** confirmed  
**Date:** 2026-10-01  
**Area:** CPU | camera | PPU | other

**Observation:** the complete named `Race_BuildRacerOAMState` routine at USA `82:ACA5..B17F` forms a gapless 1,243-byte presentation corridor that can be partitioned into 12 instruction-aligned regions: entry/mode setup, ordinary P1/P2 projection, alternate-camera projection, split-camera P1/P2 projection, and shared post-projection adjustments.  
**Evidence:** ROM-backed project-tooling runs `36854671970`, `36854862093`, and corrected instruction-boundary run `36855218823`; `analysis/generated/racer-oam-structure-island.{json,md}`; `tools/analyze_racer_oam_structure_island.py`; contraction localization in `tools/localize_oam_split_contractions.py`. USA contains 498 opcode bytes, 714 operand bytes and 31 statically unreached bytes inside the alternate-camera block. Legacy beta is byte-identical throughout.  
**Interpretation:** the regional builds preserve the same viewport/OAM architecture. Europe shifts +7 through the ordinary and first split-camera path, then +5 and +3; the PAL prototype similarly shifts -15, -17 and -19. Both shift changes are caused by removal of redundant first copies from consecutive `REP #$20; REP #$20` pairs at USA `AF96..AF97` and `B01F..B020`. Those contractions were already present in the November 1994 prototype and do not change accumulator state.  
**Discriminating test:** none required for structural equivalence or the two redundant-instruction removals. Runtime validation of widened viewport policy belongs to the later widescreen implementation phase, not this comparative pass.  
**Dependencies:** Nitrodon disassembly provides canonical USA instruction boundaries; trusted-entry snes2asm supplies per-build code roles; adjacent homolog alignment is continuity-constrained to avoid matching repeated P1/P2 sibling blocks.  
**Propagation:** added the full viewport island to `analysis/generated/comparative-structural-census.{json,md}`, expanding the census to 37 regions / 4,408 bounded USA bytes. The result strengthens `Race_BuildRacerOAMState` as the presentation seam between authoritative world/camera state and downstream sprite/OAM state.


### R-SEED-065 — Per-racer sampler links materialized course planes to collision response

**Status:** confirmed  
**Date:** 2026-10-01  
**Area:** CPU | course | collision | physics

**Observation:** USA `81:8B95..8D13` is a 383-byte common per-racer routine invoked from both player simulation paths at `81:8DD9` and `81:8F2D`. Both calls follow the recovered collision/contact-shape constructor at `81:9E2A` and precede the later collision path at `81:8FB8`. Inside the routine, course coordinates/orientation are transformed and the materialized runtime planes at `7E:C000` and `7E:A000/A001` are sampled.  
**Evidence:** ROM-backed project-tooling run `36856034874`; `analysis/generated/course-surface-sampler-structure-island.{json,md}`; `tools/analyze_course_surface_sampler_structure_island.py`. Trusted-entry snes2asm classifies all 383 bytes as executable instruction/operand bytes in every build: 167 opcode bytes + 216 operand bytes + 0 unreached/data bytes.  
**Interpretation:** this routine is the first bounded common consumer joining the course loader's A000/C000 runtime materialization to per-racer surface/collision response. The old Nitrodon linear listing around USA `8C03..8C1F` looked like stray `BRK`/`RTI` opcodes because accumulator-width context was lost; trusted-entry analysis proves that region is ordinary executable code under the actual routine state. PAL prototype and Europe both preserve the complete function at shift -32, while legacy beta is byte-identical to USA.  
**Discriminating test:** exact meanings of individual A000/C000 values should be resolved only when a physics discrepancy or course/editor implementation decision requires them. The function boundary and code/data classification need no further adjudication.  
**Dependencies:** existing course-materialization proof for the runtime planes; trusted-entry snes2asm role recovery.  
**Propagation:** added `Course_SampleRuntimeSurface` to `analysis/generated/comparative-structural-census.{json,md}`, bringing the census to 38 regions / 4,791 bounded USA bytes. Future course-format work can now follow producer→materialized plane→sampler rather than treating A000 and C000 as isolated observations.

### R-SEED-066 — Race-frame orchestrator preserves loop architecture across the PAL-line cleanup

**Status:** confirmed  
**Date:** 2026-10-01  
**Area:** CPU | race state | orchestration | comparative atlas

**Observation:** USA `83:CBCC..CD9F` is a 468-byte race-frame orchestration corridor beginning from an explicit `SEP #$30` state seed. Trusted-entry analysis reaches the main loop header at `83:CC62`, the `JMP $CC62` back-edge at `83:CD9D`, and every byte in the accepted USA regions. The corridor directly calls into input decode, racer simulation, player-state marshaling, racer OAM construction, and additional HUD/race services.

**Evidence:** `tools/analyze_race_frame_orchestrator_structure_island.py`; `analysis/generated/race-frame-orchestrator-structure-island.{json,md}`; ROM-backed project-tooling runs `36930324751` and `36930588185`. The first whole-corridor probe showed USA/beta byte identity but a two-opcode deficit in both PAL-line builds. A 16-byte local-shift profile localized a shared two-byte contraction, and the raw transition window identifies the exact edit.

**Interpretation:** USA retail and legacy beta contain consecutive `SEP #$20` instructions at `83:CC83..CC86`. PAL prototype 1994-11-29 and Europe retail omit the second instruction, corresponding to USA `83:CC85..CC86`. The accepted structural representation therefore uses two homolog regions: USA `CBCC..CC86` (187 bytes; 185 in PAL-line builds) and USA `CC87..CD9F` (281 bytes at the post-contraction shift). This is a redundant state-width cleanup already present in the PAL prototype, not evidence of a different race-loop architecture.

**Discriminating test:** no further test is required for the contraction or the two-region homolog model. Deeper naming of individual HUD/race callees should be demand-driven by implementation or fidelity discrepancies.

**Dependencies:** trusted-entry snes2asm code-role recovery; preserved four-ROM corpus; exact raw-byte comparison at the shift transition.

**Propagation:** added both regions to `analysis/generated/comparative-structural-census.{json,md}`, expanding the census to **40 regions / 5,259 bounded USA bytes**, including **5,051 code-region bytes** and **2,108 analyzer-classified opcode bytes**, and adding bank 83 to the represented-bank set. The queue now advances to a seventh independent subsystem.

### R-SEED-067 — Checkpoint/finish handler resolves into two regional edit lineages

**Status:** confirmed  
**Date:** 2026-10-01  
**Area:** CPU | race state | course objects | comparative atlas

**Observation:** object code `0x14` dispatches to USA `81:8050`, and the handler runs through `81:82E0` before the shared object-handler continuation at `81:82E1`. The complete USA handler is 657 bytes and trusted-entry snes2asm reaches every USA byte. Legacy beta is byte-identical.

**Evidence:** `tools/analyze_checkpoint_finish_structure_island.py`; `analysis/generated/checkpoint-finish-structure-island.{json,md}`; ROM-backed project-tooling runs beginning with `36932038895` and the exact-boundary passes that followed. The earlier homolog pass had already isolated Europe retail's frame-normalization contraction. The seventh-island pass extended through the formerly width-ambiguous late handler and localized the remaining shift staircase to exact instruction-aligned deletions.

**Interpretation:** two separate lineages are superposed. Europe retail alone replaces USA `81:8102..8117` (22 bytes) with `81:8102..8109` (8 bytes), net -14. Independently, PAL prototype and Europe both omit five USA/beta blocks: `8210..8215` (6 bytes: TXA; STA $0E39,Y; LDA $00), `8227..822C` (6: TXA; STA $0E3D,Y; LDA $00), `823E..8243` (6: TXA; STA $0E41,Y; LDA $00), `8253..8259` (7: STA $0E35,Y; TXA; STA $0E45,Y), and `8278..827B` (4 NOPs). Those shared PAL-line deletions total -29, so the prototype exits at shift -29 and Europe at -43 after also applying the timer edit.

**Discriminating test:** no further boundary work is required. Exact semantic meaning of the deleted bookkeeping stores should be pursued only if race-results/finish fidelity or regional-timing behavior requires it.

**Dependencies:** object-code dispatcher mapping; trusted-entry snes2asm; four-ROM preserved corpus; exact transition-window byte comparison.

**Propagation:** represented the entire 657-byte USA handler as 15 gapless code regions, preserving USA/beta-only deleted blocks explicitly rather than hiding them inside shift arithmetic. Added the island to `analysis/generated/comparative-structural-census.{json,md}`, bringing the census to **55 regions / 5,916 bounded USA bytes**, including **5,708 code-region bytes** and **2,393 analyzer opcode bytes**.

### R-SEED-068 — Stunt finalization preserves scoring architecture across PAL-line cleanup

**Status:** confirmed  
**Date:** 2026-10-01  
**Area:** CPU | stunt physics | scoring | comparative atlas

**Observation:** USA `82:9A42..9D8B` is the complete stunt-finalization/scoring routine, followed immediately by three 10-byte score-weight tables at `9D8C..9DA9` and a 625-byte trick/praise lookup at `9DAA..A01A`; the next USA code begins at `82:A01B`. The combined island is 1,497 bytes.

**Evidence:** `tools/analyze_stunt_finalizer_structure_island.py`; `analysis/generated/stunt-finalizer-structure-island.{json,md}`; ROM-backed project-tooling run `36933522739`. Regional entry seeding reaches every accepted executable byte in all four builds. USA and legacy beta are byte-identical.

**Interpretation:** the PAL prototype and Europe preserve the full stunt state-machine/scoring architecture with one structural cleanup: both omit five USA/beta NOPs at `82:9D09..9D0D`. Before the deletion the prototype homolog shift is -5 and Europe +17; afterward they are -10 and +12 respectively. The three score-weight tables and the full 625-byte trick/praise table are byte-identical across all four ROMs after accounting for that shift.

**Discriminating test:** none required for code/data boundaries, the five-NOP contraction, or table identity. Exact semantics of individual praise-table values should be pursued only when implementing stunt messaging/scoring or validating a concrete discrepancy.

**Dependencies:** Nitrodon stunt disassembly; trusted-entry snes2asm; four-ROM preserved corpus; direct table hashes.

**Propagation:** added ten regions to `analysis/generated/comparative-structural-census.{json,md}`, expanding the census to **65 regions / 7,413 bounded USA bytes**, including **6,550 code-region bytes**, **863 data bytes**, and **2,743 analyzer opcode bytes**.

### R-SEED-069 — Stunt-message pipeline closes the finalizer→queue→reward/display chain

**Status:** confirmed  
**Date:** 2026-10-01  
**Area:** CPU | stunt scoring | HUD | message queues | comparative atlas

**Observation:** USA `81:C0DD..C604` is a connected 1,320-byte subsystem that consumes queued stunt-message IDs for both players, applies stunt-score and boost rewards, converts backing scores into display digits, exposes embedded message/reward lookup data, and appends new messages through the queue helper at `C5B3`.

**Evidence:** `tools/analyze_stunt_message_pipeline_structure_island.py`; `analysis/generated/stunt-message-pipeline-structure-island.{json,md}`; ROM-backed project-tooling runs culminating in `36934577086`. Trusted regional entry seeding reaches every accepted executable byte. USA and legacy beta are byte-identical.

**Interpretation:** the PAL prototype and Europe both omit the three USA/beta NOPs at `81:C24B..C24D`, shifting the later prototype stream from -32 to -35 and Europe from -15 to -18. Europe alone then replaces USA/prototype `81:C372..C37E` (13 bytes) with `81:C360..C367` (8 bytes), a compact equivalent two-player score-display gate that moves subsequent Europe code to shift -23. The apparent one-byte difference in the old embedded-data span was not data at all: USA `C572..C575` is executable `JSR $C576; RTL`, and its relocated JSR operand changes naturally in regional builds. The corrected data block `C458..C571` is 282 bytes and byte-identical across all four ROMs.

**Discriminating test:** no further code/data or lineage-boundary work is needed. Individual meanings inside the overlapping message/action, boost-reward and record-mapping lookup views should be decoded only when implementing HUD/message behavior or validating a concrete scoring discrepancy.

**Dependencies:** Nitrodon bank-81 listing; recovered `HUD_QueueMessage` homologs; stunt-finalizer producer semantics; trusted-entry snes2asm; four-ROM corpus.

**Propagation:** added eight regions to `analysis/generated/comparative-structural-census.{json,md}`, expanding the census to **73 regions / 8,733 bounded USA bytes**, including **7,588 code-region bytes**, **1,145 data bytes**, and **3,182 analyzer opcode bytes**. This closes a direct implementation chain from stunt recognition/scoring through delayed queue consumption, persistent score/boost mutation, and display-state refresh.

### R-SEED-070 — Race input normalization preserves instruction architecture across all four builds

**Status:** confirmed  
**Date:** 2026-10-01  
**Area:** CPU | input | racer control | comparative atlas

**Observation:** USA `82:AA6E..ACA0` is a 563-byte, fully executable input subsystem spanning P1 decode/fallback, P2 decode/activity tracking, and reverse-controls remapping immediately before the racer-OAM wrapper at `82:ACA1`.

**Evidence:** `tools/analyze_input_normalization_structure_island.py`; `analysis/generated/input-normalization-structure-island.{json,md}`; existing Europe/USA and USA/PAL-prototype snes2asm homolog adjudication for all three subregions. USA/legacy beta are byte-identical. PAL prototype stays at shift -15 and Europe at +7 across the full routine.

**Interpretation:** the routine's instruction structure is unchanged regionally. Across P1, P2, and postprocess blocks, PAL prototype and Europe each preserve all 237 aligned opcode positions with 100% opcode consensus, zero code/operand role disagreements, and zero M/X-width disagreements. Europe's lower raw byte similarity is therefore operand relocation, not altered control architecture; this includes the established regional controller-state family such as USA `030D` mapping to Europe `0311`.

**Discriminating test:** no further function-boundary or control-flow work is required. Decode individual regional WRAM operands only when an implementation or fidelity test needs them.

**Dependencies:** Nitrodon bank-82 listing; cross-build symbol correspondence; Europe/USA and USA/PAL-prototype snes2asm homolog reports; four-ROM corpus.

**Propagation:** added three code regions to `analysis/generated/comparative-structural-census.{json,md}`, expanding the census to **76 regions / 9,296 bounded USA bytes**, including **8,151 code-region bytes**, **1,145 data bytes**, and **3,419 analyzer opcode bytes**.

### R-SEED-071 — Race camera control is a preserved 1.5 KiB executable subsystem

**Status:** confirmed  
**Date:** 2026-10-01  
**Area:** CPU | camera | viewport | comparative atlas

**Observation:** USA `81:9FBF..A59D` forms a connected camera-control cluster: target-velocity/follow solving, a shared smoothing helper, course/scale configuration driven from `7F:000D`, and the per-frame camera update wrapper at `81:A52B/A52F`. All 1,503 USA bytes are executable under trusted-entry tracing.

**Evidence:** `tools/analyze_camera_control_structure_island.py`; `analysis/generated/camera-control-structure-island.{json,md}`; ROM-backed project-tooling runs `36938453986` and `36938508110`. USA and legacy beta are byte-identical. PAL prototype stays at shift -32 and Europe at -15 across all four regions.

**Interpretation:** regional builds preserve the camera instruction architecture wholesale. The velocity solver, smoothing helper, scale configuration, and per-frame update together contain 659 aligned USA opcode positions; both PAL prototype and Europe match all 659 with zero code/operand role disagreements. The old Nitrodon listing's BRK/COP clutter in the velocity solver is width/context drift rather than exceptional control flow.

**Discriminating test:** no further boundary work is required. Individual camera constants and WRAM operands should be named as widescreen/viewport implementation needs demand them.

**Dependencies:** Nitrodon bank-81 listing; trusted-entry snes2asm; four-ROM preserved corpus; camera position/velocity semantics already promoted in SYMBOLS.

**Propagation:** added four code regions to `analysis/generated/comparative-structural-census.{json,md}`, expanding the census to **80 regions / 10,799 bounded USA bytes**, including **9,654 code-region bytes**, **1,145 data bytes**, and **4,078 analyzer opcode bytes**.

### R-SEED-072 — Race/stunt timer lifecycle preserves one instruction architecture across all four builds

**Status:** confirmed  
**Date:** 2026-10-01  
**Area:** CPU | race timing | stunt timing | comparative atlas

**Observation:** USA `81:C697..C906` is a 624-byte timer lifecycle containing the long-entry wrapper, mode dispatcher, count-up race timer, stunt countdown timer, digit refresh, timeout/finalization handling, and warning-sound threshold. The next code starts at `81:C907`.

**Evidence:** `tools/analyze_race_timer_structure_island.py`; `analysis/generated/race-timer-structure-island.{json,md}`; ROM-backed project-tooling runs `36939582649` and `36939682024`. All 624 USA bytes are executable when the dormant `C6A4..C6A6` call slot is seeded explicitly. USA and legacy beta are byte-identical.

**Interpretation:** PAL prototype preserves the entire subsystem at shift -35 and Europe at -19. Across the five structural regions, both regional builds preserve all 244 aligned opcode positions with zero code/operand-role disagreements. `81:C6A4..C6A6` is valid dormant code (`JSR $CB37`) intentionally bypassed by `BRA $C6A7`, not an embedded data seam. The live timer representation is `0E0F` minutes, `0E13` tens of seconds, `0E17` seconds, `0E1B` tenths, and `0E1F` six-step sub-tick; both count directions share these fields and digit-display refresh paths.

**Discriminating test:** no further structural work is required. Exact semantics of mode selector `0E23`, finish flags `0EF5/0EF7`, and warning thresholds should be expanded only for a concrete fidelity or UI implementation need.

**Dependencies:** Nitrodon bank-81 listing; trusted-entry snes2asm; four-ROM corpus; checkpoint/finish timer snapshot evidence.

**Propagation:** replaced the generic race-timer TBD in `docs/SYMBOLS.md` with five concrete timer fields and added five code regions to `analysis/generated/comparative-structural-census.{json,md}`, expanding the census to **85 regions / 11,423 bounded USA bytes**, including **10,278 code-region bytes**, **1,145 data bytes**, and **4,322 analyzer opcode bytes**.

### R-SEED-073 — Two-player persistent-state marshal preserves shared simulation architecture

**Status:** confirmed  
**Date:** 2026-10-01  
**Area:** CPU | racer state | rotation | comparative atlas

**Observation:** USA `81:8D14..8FB7` is a 676-byte, fully executable bridge between paired persistent P1/P2 racer state and the shared current-player `0Fxx` workspace. It follows the recovered course-surface sampler and exits immediately before collision handling at `81:8FB8`.

**Evidence:** `tools/analyze_player_state_marshal_structure_island.py`; `analysis/generated/player-state-marshal-structure-island.{json,md}`; ROM-backed tooling run `36940294304`. USA and legacy beta are byte-identical. PAL prototype and Europe both remain at shift -32 throughout all three regions.

**Interpretation:** both regional builds preserve all 234 aligned opcode positions with zero code/operand-role disagreements. The P1 bridge copies persistent pitch angle `04C7` to shared `0F49` and persistent angular velocity `0BAD` to shared `0F4B`; P2 mirrors those relations from `04C9` and `0BAF`. Shared angular velocity is written back after the common simulation pass. This closes the stale generic rotation gap while keeping separate per-frame rotational delta `0F4D` distinct.

**Discriminating test:** no further structural work is required. Broaden individual shared-workspace labels only when a concrete physics/collision implementation needs them.

**Dependencies:** Nitrodon bank-81 listing; trusted-entry snes2asm; four-ROM corpus; existing P1/P2 pitch-angle semantics.

**Propagation:** replaced the generic rotation TBD with angular-velocity/current-player workspace semantics and added three code regions to the comparative census, expanding it to **88 regions / 12,099 bounded USA bytes**, including **10,954 code-region bytes**, **1,145 data bytes**, and **4,556 analyzer opcode bytes**.

### R-SEED-074 — Collision/contact resolver preserves shared live architecture around two Europe-only insertions

**Status:** confirmed  
**Date:** 2026-10-01  
**Area:** CPU | collision | contact response | comparative atlas

**Observation:** USA `81:8FB8..99D5` is a 2,590-byte collision cluster consisting of the main per-racer contact resolver through `983A` and its directly called geometry helper `983B..99D5`. Trusted-entry tracing fully reaches the live paths. Four instruction-bounded USA-dormant alternatives total 53 bytes and are represented separately rather than force-seeded with fabricated width context.

**Evidence:** `tools/analyze_collision_resolution_structure_island.py`; `analysis/generated/collision-resolution-structure-island.{json,md}`; ROM-backed project-tooling runs `36940735178`, `36941007139`, and `36941413521`. USA and legacy beta are byte-identical.

**Interpretation:** PAL prototype preserves the shared cluster at constant shift -32. Europe preserves every live aligned opcode around two explicit insertions: after the homolog of USA `81:9302 D0 09`, the branch becomes `D0 0F` and six NOPs are inserted, moving subsequent homologs from -32 to -26; before the homolog of USA `81:9800`, Europe inserts 11 bytes `AD E7 0D 29 FE 00 C9 08 00 F0 08` (`LDA $0DE7; AND #$00FE; CMP #$0008; BEQ +8`), moving the following structure -26 to -15. Every live region has zero regional opcode or code/operand-role disagreement once the helper inherits M/X context through its real caller.

**Discriminating test:** exact semantics of the Europe-only gate should be pursued only if a regional collision/fidelity question requires it. The structural boundary, live/dormant classification and lineage insertions are closed.

**Dependencies:** player-state marshal island; trusted-entry snes2asm; Nitrodon bank-81 collision listing; four-ROM corpus.

**Propagation:** added twelve code regions to `analysis/generated/comparative-structural-census.{json,md}`, bringing the census to **100 regions / 14,689 bounded USA bytes**, including **13,544 code-region bytes**, **1,145 data bytes**, and **5,665 analyzer opcode bytes**.

### R-SEED-075 — Contact-geometry construction is invariant across all four builds

**Status:** confirmed  
**Date:** 2026-10-01  
**Area:** CPU | collision geometry | racer state | comparative atlas

**Observation:** USA `81:9E2A..9FBE` is a 405-byte per-racer contact-geometry constructor. Both player marshal paths call it (`81:8DD6`, `81:8F2A`) immediately before the recovered course-surface sampler and collision/contact resolver. The routine derives orientation-dependent geometry from shared current-player state and writes the active-player collision anchor at `125B,Y`. Camera control begins immediately at `81:9FBF`.

**Evidence:** `tools/analyze_contact_geometry_structure_island.py`; `analysis/generated/contact-geometry-structure-island.{json,md}`; ROM-backed project-tooling run `36942483867`. All 405 USA bytes are trusted-entry executable. USA and legacy beta are byte-identical.

**Interpretation:** PAL prototype preserves the complete routine at constant shift -32 and Europe at constant shift -15. Across the three structural regions, both regional builds preserve all 246 aligned opcode positions with zero code/operand-role disagreements. Therefore the Europe-only lineage edits recovered in the downstream collision resolver do not originate in contact-geometry generation.

**Discriminating test:** no further structural work is required. Individual geometry source tables/fields should be named only when a concrete collision-shape, editor, or native-physics implementation needs them.

**Dependencies:** P1/P2 state marshal callers; course-surface sampler; collision-resolution island; trusted-entry snes2asm; four-ROM corpus.

**Propagation:** added three code regions to the branch-local comparative census, expanding it to **103 regions / 15,094 bounded USA bytes**, including **13,949 code-region bytes**, **1,145 data bytes**, and **5,911 analyzer opcode bytes**. The adjacent fifteenth geometry-precompute island remains independently owned by PR #159.

### R-WIDE-001 — Dragster checkpoint/finish visibility and gameplay activation are separate domains

**Status:** confirmed  
**Date:** 2026-10-02  
**Area:** Widescreen | gameplay activation | presentation | collision/contact

**Observation:** the deterministic Dragster finish-tail probe gives a representative cross-domain timeline. Resource `0x24` graphics and its nine `7E:C000[6..14] = 0x14` checkpoint/finish behavior cells are prepared/materialized before active racing. In the retained dense tail, actual finish/checker pixels first enter the right edge of the framebuffer at guest frame **2789** (`object-tail-060`). The checkpoint/finish semantic transition does not occur until guest frame **2903** (`object-tail-174`), 114 frames later.

**Evidence:** workflow run `36954104693`; `analysis/generated/object-activation-static-boundary-2026-10-01.md`; `analysis/generated/object-activation-runtime-boundary-2026-10-02.md`; `tools/analyze_object_activation_probe.py`. At the behavior event, persistent collision/contact is `0x2020`, the dispatcher-derived C000 index is 8, code `0x14` is selected, and checkpoint/gate/laps changes `3/0/1 -> 1/1/0`. The preceding frame remains `3/0/1`.

**Interpretation:** camera exposure and gameplay activation are not the same liveness decision for this representative family. Static code proves `81:82E6` selects the behavior cell from current-player collision/contact state `$0F09`; it does not consume camera position, camera edges, or `$0DCD/$0DCF` update-list state. The compact camera-filtered VRAM lists are therefore presentation/preparation machinery, not an activation gate.

**Limits:** the per-frame dumps do not isolate a separate object-specific "draw eligible but not visible" state, and absence of direct `$2118`/DMA-to-`$2118` rows at the sampled event does not imply absence of presentation work. Ordinary PPU/VRAM course rendering continues. The proven boundary is resource prepared / behavior exists before race → framebuffer visible at 2789 → collision/contact behavior event at 2903.

**Discriminating test:** no further generic activation archaeology is required before first Widescreen exposure. Reopen only if +8/+16/+24 probes or another object family demonstrate a distinct activation mechanism.

**Propagation:** gameplay object activation/liveness is promoted to sufficient for the representative checkpoint/finish family in `docs/SEMANTIC-SUFFICIENCY.md`; the active queue no longer treats it as the highest unresolved blocker; `docs/WIDESCREEN-RECONNAISSANCE.md` records the invariant that widened presentation must not widen collision/contact activation. The object-activation workflow now asserts both the frame-2789 visibility boundary and frame-2903 behavior boundary.


---

### R-2026-10-02-206 — +8 presentation-phase divergence precedes center regression

**Status:** merged / retained  
**Date:** 2026-10-02  
**Area:** Widescreen | presentation | renderer

**Observation:** Full-renderer 0/+8 tracing preserves meaningful P2 race state event-relatively but finds the first P2 presentation-ID divergence at `object-tail-141`, followed by the first VRAM divergence at `142`; OAM remains equal throughout the retained presentation-gap interval. The previously retained two-pixel x=255 authentic-center regression at `object-tail-168` therefore occurs downstream of an earlier presentation-state phase difference. At `168`, x=255 main/sub/OBJ composition inputs and the right color-window boundary differ while CGRAM/OAM remain matched.

**Evidence:** merged PR #206; workflow run `36967629874`; `.github/workflows/widescreen-composition-matrix.yml`; `tools/analyze_widescreen_composition_trace.py`; `tools/analyze_widescreen_presentation_phase_gap.py`.

**Interpretation:** Do not patch final composition first. The next causal discriminator is why +8 advances/selects a different P2 presentation ID under otherwise equal meaningful racer state, and how that reaches VRAM. Layer-disabling diagnostics are not causally trustworthy because they perturb guest cadence.

**Next discriminator:** trace the P2 presentation-ID update/selection path around `object-tail-140..142` using full-renderer semantic/event-relative anchors.

### R-2026-10-02-207 — consolidated knowledge layer and two-pass inference audit

**Status:** merged / canonical query layer  
**Date:** 2026-10-02  
**Area:** research method | course | state | progression | presentation

**Observation:** Cross-domain evidence is normalized under `analysis/data/`, including course identity/geometry, course resources, state semantics, code correspondence, presentation assets, progression, deterministic fixtures and atomic claims. Two inference passes produced and guarded several exact or high-confidence relations: canonical RNC storage order matches progression-row order; Dessyreqt track IDs equal stream index minus one; the course resource cursor is exactly tied to resource-list length; only six fixed-area geometry families ship; header pair A.x matches historical start X ×1/16 on 43/45 tracks and the paired header coordinates are strongly constrained as racer spawns; conserved resource bundles survive all four preserved builds; persistent racer state shows repeated +2-byte P1/P2 interleaving; regional WRAM relocation is clustered rather than global; racer frame-header popcount equals packed-word count; and progression now has a predictive medal/tier/checksum model.

**Evidence:** merged PR #207; `analysis/data/*.json`; `analysis/generated/inference-audit*.{json,md}`; `docs/INFERENCE-AUDIT-PLAN.md`; `docs/KNOWLEDGE-CONSOLIDATION-PLAN.md`.

**Interpretation:** New research must query normalized evidence before launching broad traces or prose-side reconciliation. Extend the query layer when reusable joins are missing instead of creating another disconnected ledger.

**Next discriminator:** use the retained cheapest falsifiers only where a product-facing question remains open, especially unequal-pair spawn assignment, racer mask-bit→piece mapping, and real medal-changing save/load acceptance.

### R-2026-10-02-203 — representative camera-strip preparation/emission closure

**Status:** reconciled for merge after branch drift  
**Date:** 2026-10-02  
**Area:** camera | VRAM preparation | PPU

**Observation:** The representative Dragster scrolling path is demand-driven and strip based. `81:A52F` updates camera state and entering-edge coordinates; `81:AB88/ACB1` builds up to eight `$03xx` DMA descriptors; NMI `82:D19B..D2D0` consumes active descriptors through `$2116` and channel-0 DMA to `$2118`. Run `36966728136` observes 681 non-empty builds, 676 non-empty NMI-consume observations and 680 paired build→consume events. During steady rightward motion, one 16-word / 32-byte column is prepared and consumed in the same guest frame. Horizontal VRAM destinations form a 32-column ring. The older `$0DCD/$0DCF` lists stay zero and are not the active streaming path for this scene.

**Evidence:** recovered PR #203 work; `analysis/generated/camera-dma-preparation-causal-contract-2026-10-02.md`; camera-DMA/PPU trace tools and regression workflow.

**Interpretation:** There is no representative multi-frame stock background-prefetch horizon to reverse engineer. Widescreen preparation should be tested by deliberately scheduling earlier/additional strips against this known queue while preserving authoritative state.

**Next discriminator:** only after the current +8 presentation-ID phase seam is classified, prototype one bounded additional/earlier entering-column schedule and validate event-relative simulation invariance.

### R-2026-10-03-UI-01 — In-tour win progress persists across a power cycle

**Status:** reproduced locally (reference harness); medal award after a resumed tour still open  
**Date:** 2026-10-03  
**Area:** progression | SRAM | frontend product policy

**Observation:** Battery SRAM offsets `0x0230`, `0x0232` and `0x10A9` advance once per won Crawler race in the baseline replay (`0→1→2→3`). Power-on in a fresh process from the settled mid-tour images (counter 2 at frame 8500, 3 at frame 12000) changes only SRAM `0x0742`; the counter is unchanged through MAIN_MENU, PLAYER_SELECT, TOUR_SELECT, TRACK_SELECT, NOW PLAYING and race entry; the next won race increments it to 3 and 4 respectively. The reloaded run re-raced track 0, already won before the power cycle, and the counter still advanced, so it counts wins rather than distinct tracks. TRACK_SELECT shows the same five tracks with no completion markers with or without the persisted progress.

**Evidence:** `tools/probe_tour_progress_persistence.py` → `analysis/generated/tour-progress-persistence.json` (snesref + pinned snes9x-libretro, Dessyreqt 2014 movie input from its anchored SRAM; ~1 minute locally).

**Interpretation:** The planning premise that stock play loses unfinished tour progress on power-off is not supported. At least the win counter is battery-backed and resumes. Modern per-event/tour persistence is therefore a preservation of stock behavior, not a redesign.

**Uncertainty:** Lost races were not exercised. Whether completing the tour after a power cycle awards the medal is not observed: the historical movie desyncs on the modern core after the first reloaded race, and the accepted medal fixture uses the Snes9x 1.51-rr path (`historical-snes9x151-medal.yml`). The modern-core replay of `progression-sram-acceptance.yml` reaches four in-session Crawler wins but no medal by frame 40000 locally.

**Next discriminator:** only if a product decision needs it, resume the accepted Snes9x 1.51-rr medal route from a mid-tour SRAM image and check whether the medal cell still increments.

### R-2026-10-03-UI-02 — Stock menu typography, cursor and slide are mechanically decoded

**Status:** reproduced locally (reference harness), compact contract committed  
**Date:** 2026-10-03  
**Area:** frontend presentation | PPU

**Observation:**
- **Font:** MAIN_MENU and OPTIONS text is BG2 palette 7 (mode 3, 4bpp, priority tiles) using a 40-slot 16×16 glyph sheet. Glyph slot `s` occupies tiles `2s, 2s+1, 2s+0x50, 2s+0x51`. The sheet holds digits, `A-Z` without `O`, `OK`, two arrows and the circuit/stunt track-type icons.
- **Cursor:** two 32×32 OBJs (arrow on palette 7, shadow on palette 5 at +7,+7) spinning through 16 tiles at 2 frames each. On a one-row move it travels 6,4,3,3,2,1,1,1,1,0,0,1 px in y and settles in 12 frames.
- **Slide:** MAIN_MENU→OPTIONS changes `7E:009F` to `0x57`, then scrolls BG2 0→256 with velocity 1..7, twenty-five frames at 8, then 7..1 px/frame (39 frames). BG1 stays fixed and X-back mirrors the slide exactly.

**Evidence:** `tests/input/menu-visual-language.script`; `tools/extract_menu_visual_language.py` → `analysis/generated/menu-visual-language.json`. Its checks decode all ten MAIN_MENU/OPTIONS labels from VRAM.

**Interpretation:** Menu presentation is a small, fully specifiable grammar. The current modern host overlay draws generic white overlay text and does not yet follow it.

**Next discriminator:** extend the same extractor to TRACK_SELECT (small font plus icon column) and capture menu SFX timing only when a modern menu surface needs them.

### R-2026-10-03-UI-03 — Setup screens share one BG2 strip and a second 8×16 font

**Status:** reproduced locally (reference harness), folded into the menu contract  
**Date:** 2026-10-03  
**Area:** frontend presentation | PPU

**Observation:**
- **Strip:** PLAYER_SELECT_P1, TOUR_SELECT and TRACK_SELECT sit at BG2 scroll 256, 512 and 768 of the same strip that holds MAIN_MENU at 0.
- **Small font:** names and per-item data use an 8×16 font (top tile `t`, bottom `t+0x3C`). Digits are `0xA9..0xB2`, A–Z without O start at `0xB3`, and space is `0xCE`. It uses only outline value 8 and grey ramp 9–12 of BG palette 7.
- **Mixed composition:** titles can separate words with a single 8-px `0xCE` space (PICK YOUR UNI) where MAIN_MENU/OPTIONS use 16-px gaps. TRACK_SELECT places big-font icon glyphs (slots 37–39) before small-font names left-aligned at x=80.
- **Selection memory:** X-back from OPTIONS resets `7E:009B` to 0 and the cursor to 1P.

**Evidence:** `tests/input/menu-visual-language.script`; `tools/extract_menu_visual_language.py` → `analysis/generated/menu-visual-language.json` (13 decode/state checks, including every expected title and small-font label on the three setup screens).

**Interpretation:** The frontend's visual hierarchy is yellow-for-choices, grey-for-data, with track-type icons living in the font. Modern frontend surfaces can reproduce it from this contract without screen-by-screen guesswork.

### R-2026-10-03-UI-04 — Menu SFX timing measured; identity blocked on harness visibility

**Status:** timing reproduced locally; identity open  
**Date:** 2026-10-03  
**Area:** frontend audio

**Observation:** Subtracting a no-input control run's WAV from the menu-visual-language run isolates input-triggered sound, because the menu music is deterministic.
- **Timing (inputs with a quiet baseline):** cursor-move sound begins on the input frame (0–1 frames) and lasts 10–15 frames. A into OPTIONS begins +3 frames and lasts about 38. X back begins +3 frames; its 81-frame burst likely includes a music change.
- **Contamination:** after the X-back the runs keep differing between inputs, so later setup-screen confirms are flagged `baseline_quiet: false`.

**Evidence:** `tests/input/menu-visual-language-control.script`; `tools/extract_menu_visual_language.py --log --wav --control-wav` → `sound_timing` in `analysis/generated/menu-visual-language.json`.

**Uncertainty / dead end:** SFX identity was not recovered.
- **Waveform correlation:** cross-correlating difference bursts gives only 0.16–0.27 even between identical cursor moves, because stolen music voices contaminate the difference.
- **Harness:** the pinned snesref core produces no output for `SNESREF_DSPREG_TRACE_FILE` or `SNESREF_APURAM_TRACE_FILE` (it lacks the cosim memory IDs).
- **WRAM sampling:** per-frame sampling of `$0000-$1FFF` shows only stack churn at input frames, so the request is transient.

**Next discriminator:** log CPU writes to `$2140-$2143` (SNESRecomp native `audio_events` via `tools/analyze_audio_port_events.py`, or a core with the cosim memory IDs) across the same script, and only when a modern menu surface needs exact stock SFX.

### R-2026-10-03-UI-05 — The 16 classic racers are fully specified by rider index

**Status:** reproduced locally (reference harness + ROM table), preset table committed  
**Date:** 2026-10-03  
**Area:** frontend | racer identity | presentation

**Observation:** On PLAYER_SELECT_P1 the cursor walks `7E:000E` rows 0..7 and `7E:0C63` columns `0x06/0x07`. Confirming writes `$017D = 2 * row + column`, checked at five positions. Palette assets `0x06..0x15` from the `82:B32F` table differ only in a seven-entry body ramp (2, 4, 6, 7, 9, 11, 13). The end-of-frame rider-select OBJ palettes 0..7 equal assets `0x0E..0x15` byte-for-byte. HDMA (CGADD/CGDATA, channels 0/1) loads the bottom four grid rows mid-frame, so the menu icons reuse the in-race palettes.

**Evidence:** `tools/build_legacy_cast_presets.py` → `analysis/generated/legacy-cast-presets.json` (six checks), built from the `menu-visual-language.script` rider dump and the canonical ROM.

**Interpretation:** A classic preset is fully specified by its rider index: default name, grid slot, medal column and exact palette. Modern racer presets, ghosts and AI cast can key on that index without new archaeology.

**Uncertainty:** Default names are clean-boot values; the editable copy is the SRAM name table at offset `0x000C` (R-2026-10-03-UI-06). The menu HDMA table decode (`00:CD36/00:CD73`) was not completed; it was unnecessary once the end-of-frame cross-check matched. The tier opponents are covered in R-2026-10-03-UI-06.

### R-2026-10-03-UI-06 — Tier opponents are rider indices 17–19; the silver opponent is Silvia

**Status:** all three reproduced at runtime (Silvia/Goldwyn via the tier probe below)  
**Date:** 2026-10-03  
**Area:** racer identity | progression | frontend

**Observation:**
- **Name table:** the default player-name table at ROM `83:800C` uses 16-byte records (8 lowercase chars with `_` padding, `FF FF`, padding). It holds indices 0..15 for the selectable racers, then 16 `someone`, 17 `bronsen`, 18 `silvia`, 19 `goldwyn`, 20 `anti-uni`, then League `define_me` slots. A clean-boot SRAM image holds the identical table at offset `0x000C`, and all 16 rider-select names match it.
- **Bronze race:** on the Bronze Crawler Dragster race the NOW PLAYING card shows `MIKE VS BRONSEN` and `RECORD: SOMEONE`. In race, `$017F` (the P2 racer slot) is 17 and CGRAM `$C0` equals palette asset `0x17` byte-for-byte, so the CPU opponent occupies the ordinary P2 racer identity/palette path.
- **Palettes:** assets `0x17/0x18/0x19` use a brighter chassis than the 16 racer palettes, with bronze/orange, silver-white and gold ramps.

**Evidence:** `tests/input/menu-visual-language.script` (extended through NOW PLAYING and race entry); `tools/build_legacy_cast_presets.py` → `non_selectable_identities` and checks in `analysis/generated/legacy-cast-presets.json`.

**Interpretation:** The planning docs' "Silverton" is not the shipped name; the ROM table and its SRAM copy say `silvia`. Preserving the legacy opponents means preserving indices 17–19, their names and palettes, and their use of the P2 racer slot.

**Tier probe:** `tools/probe_tier_opponents.py` seeds only the Crawler/MIKE medal cell `77:069C` (0/1/2) plus the `73C` checksum before boot. TRACK_SELECT then shows BRONZE/SILVER/GOLD, the card shows `VS BRONSEN/SILVIA/GOLDWYN`, `$017F` is 17/18/19 and CGRAM `$C0` equals assets `0x17/0x18/0x19` (12 checks, `analysis/generated/tier-opponent-probe.json`). The opponent is therefore `17 + medal held for this tour and rider`.

**Hunter and generalisation:**
- **Hunter:** with MIKE's eight main-tour medals gold and tier tables `10D3/10FD` = 3, TOUR_SELECT becomes the nine-tour page `0x10`, and HUNTER sits at `$009B`=8. TRACK_SELECT lists GRILLER, TWO LOOPS, NEON, HAMSTER and TO AND FRO under a GOLD label, although MIKE holds no Hunter medal. The card shows `VS ANTI-UNI`, `$017F`=20, and the P2 palette equals asset `0x1A`.
- **Generalisation:** ANDREW (rider 1) on SHUFFLER (row 2) holding bronze faces SILVIA under a SILVER label, so the rule holds for a different rider column and tour row.
- **Probe size:** 20 checks in total.

**Uncertainty:** the opponent-selection code was not traced. The main-tour rule is black-box over medals 0–2 on two rider/tour pairs, and the Hunter tier label's source is unexplained.

### R-2026-10-03-UI-07 — Records/results screens reuse the menu grammar; small-font punctuation decoded

**Status:** reproduced locally (reference harness)  
**Date:** 2026-10-03  
**Area:** frontend presentation

**Observation:** RESULT_RACE (`0x99`, DRAGSTER COMPLETE) and the four Records screens decode with the same two fonts, yellow titles over grey headings and data:
- Track Records `0xCC` scrolls BG2 vertically (vofs 261).
- High Scores `0xBF`, Player Scores `0xD0` and Group Scores `0xF3` complete the set; the GROUP TABLES menu item opens GROUP SCORES.
- Small-font punctuation tiles are `0xA2 %`, `0xA4 (`, `0xA7 -`, `0xA8 .` and `0xCC :`. `)` is `0xA4` with the tilemap H-flip bit.
- A clean save shows `NO TIME` / `SOMEONE` placeholders and zero stats.

**Evidence:** `tools/extract_menu_visual_language.py --catalog` over the `ui-race-result-route` and `ui-records-submenus` captures → `screen_catalog` in `analysis/generated/menu-visual-language.json` (label checks per screen).

**Interpretation:** A modern records/statistics surface can embed these as faithful views, since their composition is a small, regular extension of the menu contract.
