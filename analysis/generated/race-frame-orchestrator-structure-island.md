# Race-frame orchestration structural island: USA 83:CBCC..CD9F

The corridor begins at an explicit SEP #$30, includes the main race-loop header at 83:CC62, and reaches the JMP $CC62 back-edge at 83:CD9D.

| Region | USA bytes | PAL prototype | Europe | Legacy beta |
|---|---:|---|---|---|
| setup_loop_prefix | 187 | 83:CBCC..83:CC84 (+0; size 185; sim 0.882; op 75) | 83:CBF2..83:CCAA (+38; size 185; sim 0.872; op 75) | 83:CBCC..83:CC86 (+0; size 187; sim 1.000; op 76) |
| loop_body_after_sep_cleanup | 281 | 83:CC85..83:CD9D (-2; size 281; sim 0.833; op 108) | 83:CCAB..83:CDC3 (+36; size 281; sim 0.790; op 106) | 83:CC87..83:CD9F (+0; size 281; sim 1.000; op 109) |

## Lineage edit

USA retail and the legacy beta contain consecutive SEP #$20 instructions at 83:CC83..CC86. The PAL prototype and Europe retail omit the second instruction (USA 83:CC85..CC86), contracting the remaining loop body by two bytes. The edit is already present in the 1994-11-29 PAL prototype.

The corridor directly orchestrates input decode, racer simulation, player-state marshaling, racer OAM construction, and additional HUD/race services. This artifact records control-flow structure without assigning semantics to every callee.
