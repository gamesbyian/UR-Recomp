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

