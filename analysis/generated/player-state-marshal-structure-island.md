# Player persistent-state marshal structural island

USA `81:8D14..8FB7` marshals P1/P2 persistent racer state into the shared current-player `0Fxx` workspace, runs the common per-racer helpers, and writes the workspace back before collision handling at `81:8FB8`.

All 676 USA bytes are executable. USA and legacy beta are byte-identical. PAL prototype and Europe both remain at shift -32 throughout. Both regional builds preserve all 234 aligned opcode positions with zero code/operand-role disagreements.

| Region | USA bytes | PAL prototype | Europe | Legacy beta |
|---|---:|---|---|---|
| long_entry_wrapper | 4 | 81:8CF4..81:8CF7 (-32; sim 0.500; op 2; other 0) | 81:8CF4..81:8CF7 (-32; sim 0.500; op 2; other 0) | 81:8D14..81:8D17 (+0; sim 1.000; op 2; other 0) |
| player1_marshal_and_sim_bridge | 331 | 81:8CF8..81:8E42 (-32; sim 0.822; op 114; other 0) | 81:8CF8..81:8E42 (-32; sim 0.692; op 114; other 0) | 81:8D18..81:8E62 (+0; sim 1.000; op 114; other 0) |
| player2_marshal_and_sim_bridge | 341 | 81:8E43..81:8F97 (-32; sim 0.824; op 118; other 0) | 81:8E43..81:8F97 (-32; sim 0.692; op 118; other 0) | 81:8E63..81:8FB7 (+0; sim 1.000; op 118; other 0) |

The P1 bridge copies persistent angle `7E:04C7` to shared `7E:0F49` and persistent angular velocity `7E:0BAD` to shared `7E:0F4B`; the P2 bridge performs the same mapping from `7E:04C9` and `7E:0BAF`. The writeback path returns shared angular velocity to each persistent slot after common simulation.
