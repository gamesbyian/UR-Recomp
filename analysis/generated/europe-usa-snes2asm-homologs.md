# Europe/USA selected snes2asm homolog comparison

Selected semantic homologs are compared only after relocation alignment and trusted entry seeding.

Executable subregions compared: **8**.
Aligned opcode pairs: **656**.
Aligned role disagreements: **0**.
Aligned M/X disagreements: **0**.

| Region | USA | Europe | Shift | Raw sim | Role disagree | M/X disagree |
|---|---|---|---:|---:|---:|---:|
| Text_TestCharacterMetadataBit7 | `80:8C41..80:8C4D` | `80:8C41..80:8C4D` | +0 | 0.846 | 0 | 0 |
| Player_ApplyVerticalAcceleration | `82:A968..82:A9AB` | `82:A96F..82:A9B2` | +7 | 0.897 | 0 | 0 |
| Input_DecodePlayer1Buttons:p1_decode | `82:AA6E..82:AB54` | `82:AA75..82:AB5B` | +7 | 0.848 | 0 | 0 |
| Input_DecodePlayer1Buttons:p2_decode | `82:AB55..82:AC52` | `82:AB5C..82:AC59` | +7 | 0.850 | 0 | 0 |
| Input_DecodePlayer1Buttons:postprocess | `82:AC53..82:ACA0` | `82:AC5A..82:ACA7` | +7 | 0.731 | 0 | 0 |
| Collision_TransformVelocity:matrix_apply | `81:9546..81:9624` | `81:952C..81:960A` | -26 | 0.915 | 0 | 0 |
| Collision_BuildContactShape | `81:9E2A..81:9FBE` | `81:9E1B..81:9FAF` | -15 | 0.990 | 0 | 0 |
| HUD_QueueMessage | `81:C5B3..81:C604` | `81:C59C..81:C5ED` | -23 | 0.805 | 0 | 0 |

## Interpretation

All 656 aligned opcode positions preserve opcode/operand classification and M/X state across these selected USA/Europe executable homologs. Raw byte differences are therefore regional operand/layout variation inside the same instruction structure for this corpus, not snes2asm boundary disagreement.

Same-offset disagreement remains large in several moved routines and is retained in the JSON as negative evidence against literal-offset comparison.

## Reachability caveat

An earlier unseeded probe produced zero disagreements only because snes2asm marked these bank-81/bank-82 regions as unreached from its default vector walk. That result is explicitly rejected as vacuous. The accepted pass seeds only independently recovered function entries (and, for collision velocity, an independently visible local REP/SEP setup) before path discovery. The tool fails if a compared region still contains zero aligned opcode pairs.

No bounded da65 or Ghidra escalation is warranted for these eight regions because no analyzer disagreement survives homolog alignment and trusted entry seeding.
