# Europe/USA selected snes2asm homolog comparison

Selected semantic homologs are compared only after relocation alignment and trusted entry seeding.

Total regions represented: **21**.
Comparable homolog regions: **20**.
Explicit structural-delta regions: **1**.
Aligned opcode pairs across comparable homologs: **1455**.
Aligned opcode-byte disagreements: **0**.
Aligned operand-byte changes: **510**.
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
| Race_HandleCheckpointFinish:entry_and_time_prefix | `81:8050..81:8101` | `81:8050..81:8101` | +0 | 0.904 | 0 | 17 | 0 | 0 |
| Race_HandleCheckpointFinish:time_suffix | `81:8118..81:8122` | `81:810A..81:8114` | -14 | 0.909 | 0 | 1 | 0 | 0 |
| Race_HandleCheckpointFinish:player_records | `81:8123..81:8194` | `81:8115..81:8186` | -14 | 0.947 | 0 | 6 | 0 | 0 |
| Race_HandleCheckpointFinish:lap_hud | `81:8195..81:81D3` | `81:8187..81:81C5` | -14 | 0.825 | 0 | 11 | 0 | 0 |
| Race_BuildRacerOAMState:p1_projection | `82:ACF3..82:ADA7` | `82:ACFA..82:ADAE` | +7 | 0.856 | 0 | 26 | 0 | 0 |
| Race_BuildRacerOAMState:p2_projection | `82:ADC1..82:AE57` | `82:ADC8..82:AE5E` | +7 | 0.854 | 0 | 22 | 0 | 0 |

## Genuine structural delta

The checkpoint/finish handler is dispatch-confirmed at `81:8050` in both USA and Europe. The function is same-layout through `81:8101`, then differs only in a bounded timer-frame normalization block before rejoining at Europe `81:810A` / USA `81:8118` with a persistent `-14` shift.

- USA `81:8102..81:8117`: 22 bytes, opcodes `AD C9 30 3A 0A 18 6D C9 30 A9`.
- Europe `81:8102..81:8109`: 8 bytes, opcodes `AD 0A 18 6D`.
- Net Europe contraction: **14 bytes**.
- USA logic reads the frame field, conditionally decrements it when `>=4`, doubles it, adds `$0300`, then clamps the result to 9.
- Europe reads its relocated frame field, doubles it, and adds `$0300`, omitting both adjustment/clamp branches.

### Four-ROM lineage

- USA retail: **usa-style-22-byte**
- Legacy beta: **usa-style-22-byte**
- PAL prototype 1994-11-29: **usa-style-22-byte**
- Europe retail: **europe-style-8-byte**

The PAL prototype has the USA-style instruction shape with its expected relocated frame-counter operand. Therefore the 8-byte contraction is a later Europe-retail change, not a general PAL/prototype characteristic.

## OAM result

`Race_BuildRacerOAMState` adds two clean bounded Europe homologs at shift `+7`: the player-1 and player-2 world/camera-to-screen projection blocks. Across them there are 141 aligned opcode pairs, zero opcode substitutions, zero role disagreements, zero M/X disagreements, and 48 changed operand bytes.

## Reachability caveat

An earlier unseeded probe produced zero role disagreements because snes2asm marked the compared bank-81/bank-82 regions as unreached from its default vector walk. That result is rejected as vacuous. Accepted comparisons seed only independently recovered function entries or local REP/SEP state. `unreached→unreached` is never counted as analyzer consensus.

No da65/Ghidra escalation is needed for the 20 comparable homolog regions because no opcode, role, or M/X disagreement survives. The checkpoint timer block is preserved separately as a genuine regional executable delta.
