# Cross-project behavioral corroboration: reuse decisions

**2026-10-10 pilot.** Advisory interpretation within the existing Research Ledger, not a new gate, symbol authority, task queue, or permission to waive original/native comparisons. The original USA ROM and independent execution remain the game's USA truth; `docs/RELEASE-QUALITY-LEDGER.json` alone owns release acceptance. Distinguish (1) an established mechanical fact, (2) its application to a particular ROM edition and path, and (3) its correct implementation in the current Windows candidate.

## Operational rule

Before a new investigation into a documented gameplay mechanism, inspect `docs/RESEARCH-LEDGER.md`, `docs/SYMBOLS.md`, the owning specialist document, and, only when relevant, `tools/query_upstream_knowledge.py` for pinned Baldosa USA and malmazuke PAL corroboration. Decide on the *narrow behavioral claim*, not by counting repositories, labels or green CI jobs.

- **Reuse / stop re-discovery:** exact original-code/data correspondence or original observations establish the scoped claim, with compatible premises; record its provenance and an explicit **reopen only if** condition in the existing ledger/owning doc. Additional semantic archaeology needs a contradictory original observation, a user-visible blocker or a necessary unverified boundary.
- **Qualified lead:** independent descriptions or tests align but region, state conditions, opcode/operand correspondence or coverage is incomplete. Use to choose the cheapest discriminating original observation; do not promote the hypothesis to a canonical USA fact.
- **Actual disagreement:** isolate the earliest meaningful different state/transition and its consumer. First rule out input/clock/ROM mismatch and observability limitations. Do not patch guest gameplay or relax a comparator to make a report green.
- **Integration still needs proof:** a settled mechanical claim does not certify Baldosa/Modern input, 1P/2P results, PPU visibility, storage, controller or physical Windows candidate. Preserve existing independent QA gates and the 45-USA-course denominator.

Corroboration is strongest where *independent original observations* test matching premises. Multiple projects copying the same source, emulator, route or inferred label are correlated evidence, not independent confirmations. Exact shared original instructions are strong **structural** evidence; they are not by themselves full-event **dynamic** evidence. PAL 50 Hz observations do not establish USA 60 Hz event timing.

When extending an existing ledger entry, append a compact `Corroboration` section with: **claim and boundary**, **independent sources (and shared dependencies)**, **region/opcode/state equivalence**, **verdict: established / qualified lead / contradicted**, **reuse permission**, and **reopen only if**. Link exact pinned source/artifact IDs. Do not create a second claim registry or blindly upgrade old “supported” records.

## Initial evidence-constrained pilot

### Pilot A: course-contact marshal storage correspondence

**Verdict: established structural cross-ROM correspondence; defer additional broad mapping.**

UR's original-ROM operand tests establish the per-player backing words and shared course-contact dispatcher workspace across USA retail, PAL prototype and Europe retail. Original structural prefix alignment additionally has zero opcode/role disagreements in its bounded region, with region-specific operand differences. Details and exact register values: [COURSE-PAL-REGISTER-HOMOLOG.md](COURSE-PAL-REGISTER-HOMOLOG.md). The original-USA racer marshal is independently described in [Research Ledger R-PROP-001](RESEARCH-LEDGER.md). malmazuke's PAL code/address index offers corroborating research leads, **not** an independent runtime measurement of every USA register transition.

**Reuse:** use existing accepted regional register mapping in analyses and adapters; do not repeat raw address hunting. **Reopen only if:** a new ROM/instruction conflict or runtime input/2P/contact witness contradicts the recorded storage mapping. Dynamic call timing, effects and complete-event parity remain separate and unaccepted.

### Pilot B: checkpoint/finish dispatch

**Verdict: established bounded USA instruction dispatch; cross-project full finish semantics still a qualified lead.**

UR's original-USA disassembly and deterministic Dragster fixture establish object code `0x14` dispatching through `81:82E6`/`81:8320` to `81:8050` (Research Ledger R-PROP-005). malmazuke identifies `race_progress.cpp:update_checkpoints` at PAL `81:8050`, which the frozen bounded interval tool projects to USA `81:8050`; that geometric agreement is a **candidate**, not independent proof of every PAL/USA operand, phase or finish rule. Baldosa's original-USA named code and native course runs are corroborating aids; its masked route comparisons do not make the whole event accepted. Source mapping caution: [malmazuke PAL intake](../reference/notes/malmazuke-pal-reconstruction-intake.md).

**Reuse:** do not rediscover USA code `0x14` handler ownership. **Reopen only if:** a real course/finish result contradicts the dispatcher or another course object/mode requires a different branch. Final-result timing, medal/winner/progression and strict 0/45 event acceptance stay open.

### Pilot C: collision/contact update ordering

**Verdict: strong original-PAL causal observation; USA equivalence unconfirmed.**

malmazuke [R-0086](https://github.com/malmazuke/unirally-reconstruction/blob/42d444594641d23f5d3c15da7b7c454bb5180e43/docs/research/R-0086-rolling-contact.md) traces an inverted high-face contact writing PAL scratch horizontal velocity before slope response reads it. A stale velocity produced a `72` versus `0` divergence; seven original PAL cases agreed after fixing order. UR has related USA collision/velocity transform observations (Research Ledger R-PROP-006), but that **does not establish** the same particular original-USA branch/order or an existing Baldosa gameplay bug. Compare USA source only when a relevant contact failure occurs.

**Reuse:** treat Mark's order as a high-value hypothesis, avoid generic physics re-derivation. **Reopen/USA-promote only if:** verified USA opcode/operand homology and a bounded source-original USA contact observation show matching state/order, or a concrete player-visible discrepancy requires investigation.

### Pilot D: two-human PAL pad gating and mode-7 latch

**Verdict: PAL original-game findings with two independent USA discriminators; no current USA issue proven.** Malmazuke's [R-0095](https://github.com/malmazuke/unirally-reconstruction/blob/962fb9ba3f728e1ea0e72bc0c623d1447c322891/docs/research/R-0095-two-human-stunts.md) (11 October 2026 integration) reconstructs two-human stunt races, VS results and original controller handoff. Normal 2P/VS pre-race screens accept either pad after selection, but the second rider's selection uses pad 2 and VS challenger continuation uses only that challenger's pad. For **controller-only 2P lifecycle** discrepancies, first compare USA original pad ownership and the Modern/Baldosa release candidate on the *same* mode and menu transition; the PAL $77:0742 gate is a lead, not a USA RAM fact.

The same R-0095 documents a more unusual bounded **PAL hardware-timing counterexample**: on two-view DOWNER, split HDMA writes the SNES $211B Mode 7 multiplier latch between the CPU's low/high writes, turning M7A from $0202 into $021C. PAL original rider 1 reaches -288 vertical velocity at frame 3558, versus -308 in the upstream native C++ run without cycle-accurate interleaving. This is **not** an observed Baldosa/UR bug. If a corresponding USA 2P event diverges, log *ordered original USA CPU/HDMA $211B accesses* and first multiplier consumer before touching physics or accepting PAL frame/scanline timing. Reopen only on a real USA source/trace contradiction or an exact-build two-human event mismatch. Full method and other source limits: [pinned October 11 intake](../reference/notes/malmazuke-pal-20261011-scenery-hdma-followup.md).

**Reuse:** specialize an existing QA-02/03/05 controller fixture or QA-01/07 2P oracle only when its live owner has a relevant blocker. No second renderer, guest-timing patch, additional CI job, research-ledger promotion, or gate change follows from this source alone.

### Pilot E: active-display OAM emulator implementations versus actual USA visible output

**Verdict: original USA write/table/target established; candidate native PPU/pixel mechanism only qualified.** The existing [active-display note](../reference/notes/oam-active-display.md), [historical emulator matrix](../reference/notes/emulator-compatibility-seams.md) and Research Ledger R-EXT-002/004 already fix the two-player `$2104 <- $A5/$5A` 112-line HDMA pair, mode-0 source `7E:206C` and resulting high-OAM byte `0x218`. jgenesis's `last_fetched_oam_idx` is imported and already studied. The [13 October search closeout](../reference/notes/github-uniracers-code-search-closeout-20261013.md) compares a newer RustySNES evaluation-phase redirect description against that jgenesis HBlank case. RustySNES explicitly leaves its *fetch-phase* index unfinished, so it does not prove the required HBlank target mechanism. Repeated emulator hacks at the same address are also correlated implementation evidence, not multiple independent hardware measurements.

**Reuse / stop rediscovery:** never spend another campaign finding the known scanline values or mirroring jgenesis. If the active QA-08 graphics owner has a remaining exact native failure after current OAM/beam PRs are reconciled, capture only source-backed scanline effective OAM, actual P1/P2 source pixel winners and BG/OBJ occlusion at the first difference. Stop if the present evidence already settles the bug's owning layer. This does not approve authored HD art or the Windows candidate.

## Application by agents

Consult these pilot conclusions only when their scope fits the current task; update the **existing** claim owner with new evidence, not this document as a running ledger. Use `docs/WORK-QUEUE.md` first, then `tools/select_three_project_reuse.py --lane <lane> --focus <term> --include-conditional` for live opportunities. A bounded investigation should end as soon as new evidence will not change a gameplay fix, acceptance decision or meaningful reference claim. Prefer delivering the Windows vertical slice over accumulating confirmations of already established mechanisms.
