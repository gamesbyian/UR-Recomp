# Race input decode / normalization structural island

USA `82:AA6E..ACA0` decodes both controllers into normalized race-state fields, applies controller-disable fallbacks, tracks activity, and optionally remaps controls. The next code begins at `82:ACA1`.

All 563 USA bytes are executable. USA and legacy beta are byte-identical. PAL prototype stays at shift -15 and Europe at +7 across all three subregions. Independent aligned-opcode adjudication reports 100% opcode consensus, zero role disagreements, and zero M/X disagreements in both regional builds; Europe's lower raw byte similarity is operand relocation rather than changed instruction structure.

| Region | USA bytes | PAL prototype | Europe | Legacy beta |
|---|---:|---|---|---|
| player1_decode_and_fallback | 231 | 82:AA5F..82:AB45 (-15; sim 0.991; op 98; other 0) | 82:AA75..82:AB5B (+7; sim 0.848; op 98; other 0) | 82:AA6E..82:AB54 (+0; sim 1.000; op 98; other 0) |
| player2_decode_and_activity | 254 | 82:AB46..82:AC43 (-15; sim 0.988; op 107; other 0) | 82:AB5C..82:AC59 (+7; sim 0.850; op 107; other 0) | 82:AB55..82:AC52 (+0; sim 1.000; op 107; other 0) |
| reverse_controls_remap | 78 | 82:AC44..82:AC91 (-15; sim 0.987; op 32; other 0) | 82:AC5A..82:ACA7 (+7; sim 0.731; op 32; other 0) | 82:AC53..82:ACA0 (+0; sim 1.000; op 32; other 0) |

Europe's operand deltas include the already-established controller-state relocation family such as `030D→0311`; this island therefore provides direct structure for translating raw SNES button words into the regional normalized race-control workspace.
