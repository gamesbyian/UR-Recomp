# Europe/USA selected snes2asm homolog comparison

Selected semantic homologs are compared only after relocation alignment and trusted entry seeding.

Executable subregions compared: **8**.
Aligned opcode pairs: **656**.
Aligned opcode-byte disagreements: **0**.
Aligned operand-byte changes: **142**.
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

## Interpretation

Across all **656** aligned opcode positions, USA retail and Europe retail use the same opcode byte. All **142** aligned byte differences occur in operands. Instruction boundaries and M/X state also agree exactly across the accepted corpus.

This supports a narrow conclusion: for these selected text, vertical-acceleration, input, collision and HUD routines, regional divergence is address/constant/layout motion inside preserved instruction structure. It is not evidence that all Europe/USA code is opcode-identical.

Same-offset disagreement is retained in the JSON as negative evidence against literal-offset comparison.

## Reachability caveat

An earlier unseeded probe produced zero role disagreements because snes2asm marked the compared bank-81/bank-82 regions as unreached from its default vector walk. That result is rejected as vacuous. The accepted pass seeds only independently recovered function entries. For collision velocity, the seed begins at the independently visible local REP/SEP width setup immediately before the compared body. The tool fails if a region still contains zero aligned opcode pairs.

No bounded da65 or Ghidra escalation is warranted for these eight regions because no role, M/X, or opcode disagreement survives homolog alignment and trusted entry seeding.
