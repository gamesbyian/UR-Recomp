# RF049 bank-qualified original indexed sound operand full source-window census

**Status: instrument and analysis only until a genuine original/native 2014 USA Zoo case finishes and exact identity-bound case archive is independently checked.** Full event admission stays **0/45**; this work only owns original/native CPU/APU research.

## Source question

The merged [RF048 original consumer research](RF048-ZOO-SOUND-FIRST-CONSUMER-20261018.md) has genuine original 82:82F0 LDA [$63],Y execution but selected only 278 of over 42,000 opcodes, revealing original physical 11:C770..11:C779. Genuine native host6057 and host6062 helper operations read DP63=C774 / D0B4 with separate DP65=13, yielding native base addresses **13:C774** and **13:D0B4**. The source operand 11:C774 does not prove same physical address as native 13:C774. Missing full-bank 13:C774 in *sparse samples* does not prove absence.

RF049 determines whether the original full-bank target appears **anywhere inside the complete source-original qualified 82:82F0 execution window** rather than extrapolating from the first four instructions per source frame. Original 2014 Snes9x executes 82:82CC LDY $63; 82:82CE/D0 STZ $63/$64; 82:82F0 LDA [$63],Y. The original pointer bank plus indexed Y must be interpreted as a full 24-bit operand. The per-bank extrema are independently useful even if neither target occurs.

## Narrow observer, not a game patch

`tools/qa01_rf049_sound_operand_census.py` stages strictly **after existing RF035 and RF048 source probes** in the disposable pinned original Snes9x `cpuexec.cpp`. It never adds a guest memory bus access or invokes an extra opcode. At each actual bank82 82F0 within original internal frames6000..6150 it derives the effective 24-bit operand from original D/three raw pointer bytes and source pre-opcode Y, increments an uncapped integer census, and updates the exact count and low-address extrema for banks10/11/12/13. Exact low-word C774/D0B4 hits are retained *independently* of exact full-address **13:C774 / 13:D0B4** hits. Only actual target LDA instructions, and their subsequent true 82:82F2 STA $2143 and 82:82F6 STA $2142 opcode completions, produce per-instruction rows. A single final census is emitted upon genuine source CPU frame6151+, avoiding incomplete missing-frame evidence. Any target row overflow, lack of final sentinel, unclosed LDA->STA followthrough, impossible bank sums or mismatched original effective address causes the analyzer to fail closed.

`tools/qa01_rf049_sound_operand_report.py` additionally verifies the same unchanged Zoo case against the RF047 entire `zoo_race_mesh`, `zoo_next_bowl_handoff`, and `source_terminal_followthrough` control objects, and reuses the RF048 analyzer requiring **native real DP63 plus DP65 actual helper reads**. Original internal frames and native host times are never equated without independent proof.

Use the existing one-shot RF047 campaign composite (same USA 2014 ROM/movie/SRAM/input, source-signature pins, RF015–019/026 and historical RF030–048 observers, unchanged 78 unmasked 128-KiB WRAM checkpoints, Zoo +5163, Bowl +267, full earned SRAM pairs and cold ranked-record reload). The one-shot Actions trigger must be removed immediately after enqueue and the shared campaign restored byte-for-byte to main. A green build or unit suite alone is not evidence of an original executed first consumer.

## Interpretation

If 13:C774 or 13:D0B4 is observed, require the genuine subsequent STA port3/port2 instruction completions and the actual RF037 original CPU port publication logs, then register their source-SPC-age/CPU clock against the independently matched native writer ordinal. A match in low 16 bits alone is never enough. If both are absent across the **complete bounded original 6072..6150 execution window**, classify that *within-window absence*, not global sound-upload absence, zero audio effects or any reason for an automatic native clock patch. Source/content equivalence and the original/native instruction-frame registration remain separate evidence requirements. Never mask WRAM bytes or credit QA-01/QA-07 without a full independently accepted original USA event.
