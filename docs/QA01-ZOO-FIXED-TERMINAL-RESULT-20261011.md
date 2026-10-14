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
