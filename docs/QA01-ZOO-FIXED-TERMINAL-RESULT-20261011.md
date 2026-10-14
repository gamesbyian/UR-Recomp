# QA-01 Zoom Zoo: executed fixed terminal frame/host discriminator (2026-10-11)

**Evidence:** [green original/native single-case campaign run 38173454680](https://github.com/gamesbyian/UR-Recomp/actions/runs/38173454680), source checkout `8c5b7d1583c741d1a64c6ab4468639c075971aa2`, case artifact `11714967334` (`producer-report.json`, `case-result.json`, both auxiliary emulator logs). This run used `selected=zoom-zoo`, `zoo_terminal_phase=true`, the pinned original Snes9x/reference and historical Baldosa research binary, canonical USA retail ROM, source-verified original 2014 controller movie and independent fresh guest entries. **It is not the integrated Windows shipping candidate.**

## Decision

**The one-frame terminal disparity is not introduced by the original script's `until 009F == BC` polling.** The independent fixed-frame (wait/dump only) probe found the first four-frame-stable Circuit result at **original guest +5163 / host 6180** and **native guest +5162 / host 6181**. Both fixed-vs-`until` result deltas are **zero**. The primary comparison remains a genuine **strict divergence**; evidence transport and case aggregation succeeded, zero producer errors.

The two guest course-entry hosts differ by **two**: original **1017**, native **1019**. Thus native is one frame *early on its guest-relative course clock*, but one frame *late on the absolute host clock*. Do not conflate the clocks or apply a whole-movie input rebase (already experimentally falsified by earlier Zoo lap failures).

## Narrow actual-guest transition evidence

All numbers below come from **independently replayed, source-qualified, full 131072-byte guest WRAM snapshots**, not fabricated timing or extrapolated emulator state. Named field equivalence is weaker than full WRAM equality.

| Clock axis / host | Original menu/track/7E:0313 | Native menu/track/7E:0313 | Interpretation |
| --- | --- | --- | --- |
| Same host **6178** (original +5161, native +5159) | `16/01/01` | `16/01/01` | Both active on Zoo; selected named fields equal |
| Same host **6179** (original +5162, native +5160) | `16/01/00` | `16/01/01` | **First terminal exit offset:** original leaves active racing; native still active. Contact/clock fields also differ |
| Same host **6180** (original +5163, native +5161) | `BC/01/3D` | `16/01/00` | Original result visible, native has just exited active racing |
| Same host **6181** (original +5164, native +5162) | `BC/01/3D` | `BC/01/3D` | Both show authentic Circuit result; named fields agree, full-WRAM hashes still differ |

On the **same guest-relative clock**, original +5157 remains `84/00/01` while native +5157 is already `16/01/01` (the native course-ID-zero prelude ends earlier relative to its entry); relative +5161 original is active, native inactive; at relative +5162 original is inactive and native shows `BC/01/3D`; both show `BC/01/3D` by +5163. Relative +5170 onward also contains post-result contact discrepancies. **None of the sampled full-WRAM SHA-256 pairs is equal**. Do not infer CPU/NMI equivalence or harmlessness from the named fields.

The independent phase probe captured **18 snapshots per guest (+5156..+5173)**, with **16 overlapping absolute host frames** (6175..6190). Fixed versus primary `until` onset offsets are zero for each engine. The settled PPU race times/laps already match, but these boundary differences are not an admitted event.

## Next causal discriminator

**Trace actual writers and their scheduling/consumer context for `7E:0313` (active-race flag) and `7E:009F` (menu/result) across absolute hosts 6178–6181, independently in original and native, using the existing execution/trace adapters.** Qualify the original code bank:PC, NMI/VBlank or host tick phase, the triggering condition and adjacent P1 finish/lap state. Compare exactly corresponding instruction boundaries where possible, not guessed frame normalization. If writers occur at different CPU/beam phases, determine whether an original/native scheduling defect or different legitimate host-frame sampling causes it. Do not start with another full movie run when existing artifacts suffice to choose the target.

Stop once the first causally material instruction boundary is identified or a specific missing observer prevents conclusion. Preserve strict `+5163/+5162` rejection, original input, official QA-01 **0/45**, and ownership separation from the active Switcher NMI stack investigation (PRs #1376/#1370). No release-ledger changes.

**Limit:** Fixed host snapshots prove concrete timing of observed menu/race-flag state at host boundaries, not identical CPU instruction phase or player-visible persistence/next-event progression.

## Source-executable 0313 writer discriminator (2026-10-13 continuation)

The existing original/native `.github/workflows/baldosa-2014-zoo-scene.yml` already executes original Snes9x opcode-change instrumentation at the source 2014 movie's active→result boundary. Its prior **native** helper-write range was `7E:008B..00CE`; this excluded **`7E:0313`**, the raw race-state word whose transition was independently shown one guest-relative frame early in native. Thus a negative native writer count there could never distinguish an absence of guest writes from the logger never watching the target.

The QA-01 experiment now extends that already-frame-bounded native logger to `7E:0313`, retaining the old interstitial menu/track gate untouched. A **single source/native crosswalk** consumes the existing replays: separate original CPU `ZOOPCWRITE` opcode/PC scope logs, native `SNESRECOMP_WLOG_ADDR` CPU-helper via scopes, the unchanged 128-KiB original/native `boundary-05160..05163` guest dumps and the two host script's independently reported actual frame receipts. The crosswalk checks the actual source-observed transitions:

| Guest-relative fixed ticks | Original Snes9x `7E:0313` | Native `7E:0313` |
| --- | --- | --- |
| +5160 | 01 (racing) | 01 (racing) |
| +5161 | 01 (racing) | 00 |
| +5162 | 00 | 3D (result-side state reuse) |
| +5163 | 3D (result-side state reuse) | 3D |

These rows restate **previously executed fixed-frame evidence**, not a claimed new emulator run. The new machine-readable `zoo-terminal-writer-crosswalk.json` reports observed source/native writer candidate scopes for transitions `01→00` and `00→3D`. A native write logger is not a complete bus trace; a source opcode pre/post delta is not automatically an identified direct store. Their frames are **separate axes**: source `ICPU.Frame`, native pre-`RtlRunFrame` `snes_frame_counter`, and zero-frame host script snapshots. A matching PC/value or a one-frame apparent offset alone does **not** establish NMI/beam-cycle correspondence, a native gameplay defect or full-course acceptance.

For static investigation only, Nitrodon's archived annotated bank disassembly contains literal `$0313` writes at `82:AC0C/AC1B/AC22` (`STY`) and `83:E073/E3FE` (`STA`), and dynamic routing can write via indirect addressing. These are **historical candidate PCs, not a proven set of executed USA original or native transition writers**; confirm against the new source execution trace and USA homolog/ROM before attribution. The experiment never patches ROM, gameplay, controller masks, release-ledger authority or event comparator. Existing strict Zoo terminal +5163/+5162 disparity and USA **0/45** acceptance remain unchanged.


## Executed native/source overlap finding (2026-10-14)

**Real guest execution, already recovered:** [PR #1436 experimental run 38499115188](https://github.com/gamesbyian/UR-Recomp/actions/runs/38499115188) completed the original and native gameplay replays, observed the expected independent scene entries **1604/1606**, and produced full WRAM at all target frames. Its existing original CPU opcode-scoped witness succeeded with 69/69 attributed scratch offsets in the earlier transition window. The newly added crosswalk step returned red for a **tooling-only receipt grammar error**: original Snes9x writes `script f=6766 dump boundary-05162 fb=256x224 RGB565 sram=8192 ppuw=3190`, whereas native writes `script f=6768 dump boundary-05162 ok`. The original files and host ticks were valid. The real job nevertheless retained artifact **11865327185** (ZIP SHA-256 `90a1e52592d1d7097daaa60ac5cc7131a4182a1f9e58647c828d8120a8aa7a8e`), and the parser has since been updated to accept **both exact source-native log grammars** while independently requiring complete WRAM. **The failed crosswalk must not be called an overall green integration run.**

Recovery of that genuine artifact produced [machine-readable, hash-pinned source and native writer evidence](../analysis/data/zoo-original-native-0313-overlapping-writers-20261014.json):

| Actual executing guest scope | Emulator frame | Byte at `7E:0313` | What the source actually did |
| --- | ---: | --- | --- |
| Original Snes9x `83:8B85`, V=9 | original CPU **6765** | **01→00** | Indexed `STA $0000,X` inside `83:8B79..` buffer-clear loop, with `A=$004C`; observed changing byte is the high half of the overwritten word |
| Native `Vram_ClearRegions_M1X0` | native pre-run **6766** | **00** | Executed 16-bit `80:0312=004C`, upper byte `00` |
| Original Snes9x `80:C585`, V=79 | original CPU **6766** | **00→3D** | Indexed `STA $0040,X` inside original text drawing loop, destination overlaps `0312/0313` |
| Native `Text_DrawLoop_C3F7_M1X0` | native pre-run **6767** | **3D** | Executed 16-bit `00:0312=3D0A`, upper byte `3D` |

The original writer PCs were **seen executing in the real original emulator**, not guessed by searching for literal `STA $0313` instructions. Nitrodon's historical disassembly independently shows their **indexed instructions** at `83:8B85` and `80:C585`. The native profiler recorded the two real word stores starting one byte **before** the observed `0313` field. Thus the fixed-frame `0313` transition is demonstrably at least partly a **presentation/work-buffer overwrite**, not an independently identified logical instruction telling gameplay to leave the race. It was legitimate to observe `0313=1` in active racing, but **not legitimate to treat the subsequent `0` and `3D` as causal evidence of finish/lap physics without tracing the earlier owner of the completion condition**.

Both sides make the same byte-level changes through corresponding buffer-clearing and text-generation routines, yet their host and guest-relative clocks are separate: source guest-relative **+5162/+5163**, native **+5161/+5162**; original result menu `BC` appears at +5163, native at +5162. Matching write *functions* does not prove the same instruction/beam phase, source routine call-site scheduling or complete-event parity. The decisive next investigation is **what schedules the original `83:8B85` clear and `80:C585` text pass relative to each independently measured scene entry**. A subsequent measured call/producer transition could distinguish timing policy from guest execution ordering. No experimental change to input timing or result comparator follows from this observation. **QA-01 0/45 unchanged.**


## Exact result-text cursor mutation stream (executed original/native, 2026-10-14)

After #1436 merged, the **fully green** original/native Zoom Zoo replay [run 38500427634](https://github.com/gamesbyian/UR-Recomp/actions/runs/38500427634), [artifact 11866136501](https://github.com/gamesbyian/UR-Recomp/actions/runs/38500427634/artifacts/11866136501) (ZIP SHA-256 `d5ec65c672736fa45f01214134db8598baa840f106729bd2c04ffb8949f1d039`) independently confirmed the source opcode and native helper stores. Its actual source/original `7E:009F` writer log shows a text cursor, not a unique logical circuit-result flag:

- Original `83:988A` changed `009F=84→16` in original `ICPU.Frame=6760`, V=240, beginning the interstitial text state. The **new narrower run's** native text helper journal does not include that earlier reset. Crucially, a **previous genuine paired run 38018081196 already executed and identified the native restore**: `Sram_RestoreDirectPage_FastRom_M1X0` writes 16-bit `80:009E` whose high byte updates `7E:009F` to `16`, at native pre-run frame **6762**. The original CPU `83:988A` is `STA $0000,X` inside `83:987D` direct-page restore, and writes the same high byte at source original CPU frame **6760**. The [earlier source-owner witness](../analysis/data/zoo-original-native-sram-restore-source-owner-20261009.json) already establishes both owners; **do not call a narrow-log absence an unexecuted native restore**.
- Original Snes9x then emitted **167 changed-byte `009F` painting instructions** across original CPU frames 6765–6766: `80:C49E` 23 changes, `80:C5B2` 134, plus ten `80:C432/C434` text writes. With the earlier reset, there are **168 original 009F changes**.
- Native Baldosa's CPU-helper logger emitted **169 text-cursor write attempts** in its own pre-run frame 6767: `Text_CmdSetPos_M0X0` 25, `Text_DrawLoop_C3F7_M1X0` 134 and `Text_DrawLoop_C40D_M1X0` 10. **Two** extra native attempts simply rewrite the unchanged cursor values `6A` and `AA`, at zero-based attempt indices 122 and 150. They cannot show up in Snes9x's opcode **change-only** journal.
- Removing **only those two idempotent native attempts** leaves exactly **167 mutating native values matching all 167 original changed bytes in the same order**, with identical SHA-256 of their hex-encoded byte streams `03513446fb0071a2b1377588dc0aad1c77830410c246246a4811a1b0c7d0fe14`. Both end `009F=BC`. The [independent narrow report](../analysis/data/zoo-original-native-result-text-cursor-stream-20261014.json) retains immutable source hashes and exact source/native counters; `tools/qa01_zoo_text_cursor_crosswalk.py` replays this comparison on the retained logs, requiring the original host dump receipt and native dump receipt for +5160..+5163.

This is **new positive evidence of source/native result-text cursor *value-order* agreement**, not an admission of clock, physics, record or completed-course parity. Original `ICPU.Frame` and native pre-run `snes_frame_counter` are distinct clocks, and source `009F=BC` appears at guest-relative +5163 whereas native does so at +5162. The matched text cursor is a presentation-buffer update, so a complete-event validator must **not rely on `009F==BC` alone**. Preserve the existing independent guest-course and lap observations, genuine result PPU text, source input identity and strict complete-event timing checks. This evidence provides *zero* new complete-event credit and USA remains **0/45**.

**Next causal discriminator:** capture the original *caller/scheduling* boundary for the `83:988A` cursor reset and `80:C49E/C5B2` text pass, plus their native equivalents, on the same independently measured guest entry. Specifically distinguish the first result-presentation work scheduled one absolute host tick later from an earlier course-completion decision. The **new** native text-writer journal did not re-capture the initial `84→16` reset; the **earlier executed native source-owner witness did**. The causal open question is the source/restored scene timing versus independently measured active course entry, not existence of the restoration. Do not globally rebase controller input or turn matching text into a proof of correct gameplay result timing.


## Completed source/native post-restore cadence crosswalk (2026-10-14)

An **independent artifact replay**, not another emulator build, reuses the genuinely green original Snes9x/native [run 38500427634](https://github.com/gamesbyian/UR-Recomp/actions/runs/38500427634) and hash-pinned artifact **11866136501**. New `tools/qa01_zoo_restore_anchored_phase.py` consumes the unmodified ZIP (SHA-256 `d5ec65c672736fa45f01214134db8598baa840f106729bd2c04ffb8949f1d039`), checks actual script-frame receipts, complete 128-KiB guest memory for each sampled frame, course/laps/checkpoint/gate, and **specific actually executed original opcode changes AND native CPU-helper stores**. It does not waive a frame, replay different controls or modify the game.

| Verified guest milestone | Original scene-relative (absolute host) | Native scene-relative (absolute host) | Host frames since respective restored state |
| --- | --- | --- | --- |
| Independently observed active scene entry | 0 (1604) | 0 (1606) | Not a restoration anchor |
| `83:988A` / `Sram_RestoreDirectPage`: `009F=16`, course 1 | +5158 (**6762**) | +5157 (**6763**) | 0 / 0 |
| `83:8B85` / `Vram_ClearRegions`: upper byte `0313=00` | +5162 (**6766**) | +5161 (**6767**) | **4 / 4** |
| `80:C585/C5B2` / `Text_DrawLoop`: `0313=3D`, cursor `009F=BC` | +5163 (**6767**) | +5162 (**6768**) | **5 / 5** |

**Result:** all three *independently observed* original/native presentation milestones retain an absolute host offset of **native +1**, while the **initial scene-entry receipts** retain native +2. Thus the apparent one-frame guest-relative Zoo result lead was **already present at the first recovered direct-page restore**; **nothing adds another frame between restore and result text** in the sampled schedule. Original/native cursor writes are additionally proven to have the same 167 actual changed values in order by merged #1450.

This narrows the next causal question to **the source race's finish/return decision and the integrity of the `0313==01` scene-entry anchor before `Sram_RestoreDirectPage`**. The restore-anchored schedule is a bounded presentation finding, not proof that the source/native gameplay completion decision occurs at the same CPU instruction, beam position or update. Original `ICPU.Frame` and native pre-`RtlRunFrame` counters also cannot be interchanged by subtracting their printed numbers. The recorded `0313` terminal values are word-buffer overlap, and `009F==BC` at this stage is a text cursor, **not dedicated finish flag certification**.

[Immutable machine witness](../analysis/data/zoo-original-native-restore-anchored-cadence-20261014.json) retains separate full-WRAM SHA-256 for each of the six milestone snapshots. The comparison explicitly refuses changed ROM/session fingerprints, malformed actual host receipts, missing/duplicated opcode/writer evidence, altered lap/checkpoint/finish-gate fields and unqualified terminal-state bytes; synthetic unit fixtures confer no gameplay credit. **Strict original/native guest-relative result remains mismatched, full USA event count remains 0/45.** Investigate the entry/return scheduler; do not retime the entire controller stream or relax the course admission comparator.


## Source-executed race-to-menu handoff bracket (next reproducible QA-01 run)

**Existing authentic evidence**, from executed fixed-frame [run 38500427634](https://github.com/gamesbyian/UR-Recomp/actions/runs/38500427634), artifact 11866136501 (ZIP SHA-256 `d5ec65c672736fa45f01214134db8598baa840f106729bd2c04ffb8949f1d039`), independently establishes:

- At original/native **guest-relative +5000**, both original Snes9x `$2100 INIDISP=0F` and native Baldosa `inidisp=15`, normal brightness.
- At original/native **+5100**, both have `INIDISP=80`, forced blank; these are genuine original/native PPU register witnesses, not a decoded menu label.
- P1 laps remaining has already reached 0, checkpoint and finish latch 1 in both guests by **+4800**. The race-completion bookkeeping therefore predates the observed forced-blank return transition, but the *source CPU instruction that schedules it* is **not yet observed**.
- The actual direct-page restore stage is later still: original **+5158/host6762**, native **+5157/host6763**. From each restore to result text, both retain exactly five sampled frames (#1460).

The historical PAL reconstruction documents `$83:C8E0` as a race-return path and `$80:A09A` as early menu setup, with `$83:987D` as SRAM direct-page restoration and `$80:951C` as result construction. **These are hypotheses for the USA ROM**, not independently accepted USA homologs. In particular, inferring a USA host clock by subtracting PAL's `r+101` restoration interval would be unjustified before observing the source code.

Executed [PR #1484's first genuine Zoo run 38510127487](https://github.com/gamesbyian/UR-Recomp/actions/runs/38510127487) (source/native artifact 11869299294, ZIP SHA-256 `84d83422e98ce4bbd725f5b9b01bd3a113b493c373d87a6fdcf3f7114d58e235`) passed the entire original/native replay and all fail-closed checks, **but every new +5048..+5072 frame already had `INIDISP=80` in BOTH guests**. The restricted original CPU window +5047..+5074 observed **zero** candidate historical PAL return PCs. This result narrows the onset to somewhere between the independently observed **+5000 lit** and **+5048 already blank**, rather than proving any historical PC is absent from USA execution.

The follow-up original/native Zoo workflow therefore takes **49 fixed, source-input-neutral guest-relative dumps, +5001..+5049** (all `wait` / zero-frame `dump`, no input change) and injects a **cheap source-only CPU execution marker** for historical candidate PCs and, independently, **the actual original CPU opcode that changes PPU `$2100 INIDISP`**, inside +4999..+5051. This captures even an unanticipated USA return-writer PC. The earlier +5152..+5165 69-address original WRAM opcode-change trace stays at its original restricted window; it is *not* stretched across another hundred frames. Native read-only full WRAM and PPU snapshots use the same unchanged source 2014 movie and independent guest entries. A new `tools/qa01_zoo_return_bracket.py` validates original framebuffer/PPU script receipts against native `ok` receipts for all 25 intermediate ticks plus the original +5000 lit and +5100 blank observations, intact 128-KiB WRAM, real PPU registers, source candidate executed PCs (if any), and actual course lap/checkpoint/finish bookkeeping.

**What it can decide:** actual first sampled original and native forced-blank transitions on each independent scene/absolute host clock, whether those transitions have a repeatable one-frame shift, and whether any **real source USA opcode execution** supports the historical return-PC leads. **What it cannot decide:** which instruction internally authored the finish decision, exact native AOT opcode PC, or NMI/beam equivalence from a PPU brightness boundary alone. Missing candidate PCs are preserved as nonconfirmations, not fabricated findings, and all outputs explicitly report **0/45 release acceptance**. No native guest runtime rules, controller phase, result comparator, Modern frontend, release authority or graphic-presentation code is changed.

