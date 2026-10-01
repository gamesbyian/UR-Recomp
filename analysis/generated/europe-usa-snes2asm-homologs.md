# Europe/USA selected snes2asm homolog comparison

Selected semantic homologs are compared only after relocation alignment and trusted entry seeding.

Executable subregions compared: **14**.
Aligned opcode pairs: **1152**.
Aligned opcode-byte disagreements: **0**.
Aligned operand-byte changes: **427**.
Aligned role disagreements: **0**.
Aligned M/X disagreements: **0**.

| Region | USA | Europe | Shift | Raw sim | Opcode Δ | Operand-byte Δ | Role Δ | M/X Δ |
|---|---|---|---:|---:|---:|---:|---:|---:|
| Text_TestCharacterMetadataBit7 | `80:8C41..80:8C4D` | `80:8C41..80:8C4D` | +0 | 0.846 | 0 | 2 | 0 | 0 |
| Player_ApplyVerticalAcceleration | `82:A968..82:A9AB` | `82:A96F..82:A9B2` | +7 | 0.897 | 0 | 7 | 0 | 0 |
| Input_DecodePlayer1Buttons:p1_decode | `82:AA6E..82:AB54` | `82:AA75..82:AB5B` | +7 | 0.848 | 0 | 35 | 0 | 0 |
| Input_DecodePlayer1Buttons:p2_decode | `82:AB55..82:AC52` | `82:AB5C..82:AC59` | +7 | 0.850 | 0 | 38 | 0 | 0 |
| Input_DecodePlayer1Buttons:postprocess | `82:AC53..82:ACA0` | `82:AC5A..82:ACA7` | +7 | 0.731 | 0 | 21 | 0 | 0 |
| Collision_TransformVelocity:matrix_apply | `81:9546..81:9624` | `81:952C..81:960A` | -26 | 0.915 | 0 | 19 | 0 | 0 |
| Collision_BuildContactShape | `81:9E2A..81:9FBE` | `81:9E1B..81:9FAF` | -15 | 0.990 | 0 | 4 | 0 | 0 |
| HUD_QueueMessage | `81:C5B3..81:C604` | `81:C59C..81:C5ED` | -23 | 0.805 | 0 | 16 | 0 | 0 |
| Race_UpdateRacersFrame:state_marshal_prefix | `82:89B9..82:8C26` | `82:89CC..82:8C39` | +19 | 0.674 | 0 | 203 | 0 | 0 |
| Stunt_FinalizeAndScoreAirTricks:air_entry | `82:9A42..82:9AA8` | `82:9A53..82:9AB9` | +17 | 0.816 | 0 | 19 | 0 | 0 |
| Stunt_FinalizeAndScoreAirTricks:rotation_progress | `82:9AAC..82:9B54` | `82:9ABD..82:9B65` | +17 | 0.864 | 0 | 23 | 0 | 0 |
| Course_LoadAndMaterialize:setup | `82:E165..82:E1CF` | `82:E12B..82:E195` | -58 | 0.944 | 0 | 6 | 0 | 0 |
| Course_LoadAndMaterialize:record_header | `82:E1D1..82:E213` | `82:E197..82:E1D9` | -58 | 0.896 | 0 | 7 | 0 | 0 |
| Course_LoadAndMaterialize:dma_row_loop | `82:E216..82:E2FF` | `82:E1DC..82:E2C5` | -58 | 0.885 | 0 | 27 | 0 | 0 |

## Interpretation

Across all **1,152** aligned opcode positions, USA retail and Europe retail use the same opcode byte. All **427** aligned byte differences occur in operands. Instruction boundaries and M/X state also agree exactly across the accepted corpus.

The accepted regions now span text metadata, vertical acceleration, the complete recovered input decoder in three pieces, collision velocity/contact-shape logic, HUD enqueue, the racer-frame state-marshal prefix, two stunt-finalizer blocks, and three course-loader/materializer blocks.

The racer-frame marshal prefix is particularly informative: raw byte similarity is only **0.674**, yet all **208** aligned opcode bytes are unchanged. Its 203 changed operand bytes are therefore direct evidence of regional state-layout retargeting inside preserved executable structure.

This remains a bounded conclusion about the selected homologs, not a claim that all Europe/USA executable code is opcode-identical.

## Reachability caveat

An earlier unseeded probe produced zero role disagreements because snes2asm marked the compared bank-81/bank-82 regions as unreached from its default vector walk. That result is rejected as vacuous. The accepted pass seeds only independently recovered function entries. For collision velocity, the seed begins at the independently visible local REP/SEP width setup immediately before the compared body. The tool fails if a region still contains zero aligned opcode pairs.

No bounded da65 or Ghidra escalation is warranted for these fourteen subregions because no role, M/X, or opcode disagreement survives homolog alignment and trusted entry seeding.
