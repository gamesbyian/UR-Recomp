# USA / 1994-11-29 PAL prototype snes2asm homolog comparison

Trusted semantic/control-flow subregions reused from the Europe/USA corpus are aligned independently against the PAL prototype and analyzed with trusted-entry-seeded snes2asm.

Regions compared: **19**.
Aligned opcode pairs: **1465**.
Opcode substitutions: **0**.
Operand-byte changes: **296**.
Role disagreements: **0**.
M/X disagreements: **0**.

| Region | USA | PAL prototype | Shift | Raw sim | Opcode Δ | Operand Δ | Role Δ | M/X Δ |
|---|---|---|---:|---:|---:|---:|---:|---:|
| Text_TestCharacterMetadataBit7 | `80:8C41..80:8C4D` | `80:8C3C..80:8C48` | -5 | 0.923 | 0 | 1 | 0 | 0 |
| Player_ApplyVerticalAcceleration | `82:A968..82:A9AB` | `82:A959..82:A99C` | -15 | 0.912 | 0 | 6 | 0 | 0 |
| Input_DecodePlayer1Buttons:p1_decode | `82:AA6E..82:AB54` | `82:AA5F..82:AB45` | -15 | 0.991 | 0 | 2 | 0 | 0 |
| Input_DecodePlayer1Buttons:p2_decode | `82:AB55..82:AC52` | `82:AB46..82:AC43` | -15 | 0.988 | 0 | 3 | 0 | 0 |
| Input_DecodePlayer1Buttons:postprocess | `82:AC53..82:ACA0` | `82:AC44..82:AC91` | -15 | 0.987 | 0 | 1 | 0 | 0 |
| Collision_TransformVelocity:matrix_apply | `81:9546..81:9624` | `81:9526..81:9604` | -32 | 0.951 | 0 | 11 | 0 | 0 |
| Collision_BuildContactShape | `81:9E2A..81:9FBE` | `81:9E0A..81:9F9E` | -32 | 0.990 | 0 | 4 | 0 | 0 |
| HUD_QueueMessage | `81:C5B3..81:C604` | `81:C590..81:C5E1` | -35 | 0.951 | 0 | 4 | 0 | 0 |
| Race_UpdateRacersFrame:state_marshal_prefix | `82:89B9..82:8C26` | `82:89B6..82:8C23` | -3 | 0.785 | 0 | 134 | 0 | 0 |
| Stunt_FinalizeAndScoreAirTricks:air_entry | `82:9A42..82:9AA8` | `82:9A3D..82:9AA3` | -5 | 0.835 | 0 | 17 | 0 | 0 |
| Stunt_FinalizeAndScoreAirTricks:rotation_progress | `82:9AAC..82:9B54` | `82:9AA7..82:9B4F` | -5 | 0.876 | 0 | 21 | 0 | 0 |
| Course_LoadAndMaterialize:setup | `82:E165..82:E1CF` | `82:E101..82:E16B` | -100 | 0.944 | 0 | 6 | 0 | 0 |
| Course_LoadAndMaterialize:record_header | `82:E1D1..82:E213` | `82:E16D..82:E1AF` | -100 | 0.896 | 0 | 7 | 0 | 0 |
| Course_LoadAndMaterialize:dma_row_loop | `82:E216..82:E2FF` | `82:E1B2..82:E29B` | -100 | 0.885 | 0 | 27 | 0 | 0 |
| Race_HandleCheckpointFinish:entry_and_time | `81:8050..81:8122` | `81:8050..81:8122` | +0 | 0.910 | 0 | 19 | 0 | 0 |
| Race_HandleCheckpointFinish:player_records | `81:8123..81:8194` | `81:8123..81:8194` | +0 | 0.982 | 0 | 2 | 0 | 0 |
| Race_HandleCheckpointFinish:lap_hud | `81:8195..81:81D3` | `81:8195..81:81D3` | +0 | 0.857 | 0 | 9 | 0 | 0 |
| Race_BuildRacerOAMState:p1_projection | `82:ACF3..82:ADA7` | `82:ACE4..82:AD98` | -15 | 0.934 | 0 | 12 | 0 | 0 |
| Race_BuildRacerOAMState:p2_projection | `82:ADC1..82:AE57` | `82:ADB2..82:AE48` | -15 | 0.934 | 0 | 10 | 0 | 0 |

## Interpretation

All **1,465** aligned opcode positions are identical between USA retail and the 1994-11-29 PAL prototype. All **296** changed aligned bytes are operands. No opcode/operand role or M/X disagreement survives homolog alignment and trusted entry seeding.

The prototype therefore preserves the same instruction stream throughout this selected corpus while exposing an earlier stage of regional address/constant/layout motion. Compared with Europe retail's 510 operand-byte changes across the comparable corpus, the prototype is materially closer to USA at the operand/layout level.

The checkpoint/finish handler remains USA-shaped in the prototype, including the 22-byte frame-normalization block. Europe retail's later 8-byte contraction is therefore a post-prototype executable change rather than a generic PAL characteristic.

No da65/Ghidra escalation is warranted for these prototype regions.
