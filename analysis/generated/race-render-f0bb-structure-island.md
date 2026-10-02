# Race-render F0BB structural island

USA `83:F0BB..F4D1` is a race-loop rendering/geometry service called from `83:CD7F`. It contains a 475-byte main body and two internal decode helpers, ending before the unrelated `F4D2` helper and `F4DA` text data.

| Region | USA bytes | PAL prototype | Europe | Legacy beta |
|---|---:|---|---|---|
| race_render_body | 475 | 83:F0DB..83:F2B5 (+32; sim 0.962; op 218; other 0) | 83:F0FF..83:F2D9 (+68; sim 0.937; op 218; other 0) | 83:F0BB..83:F295 (+0; sim 1.000; op 218; other 0) |
| address_decode_helper | 37 | 83:F2B6..83:F2DA (+32; sim 1.000; op 23; other 0) | 83:F2DA..83:F2FE (+68; sim 1.000; op 23; other 0) | 83:F296..83:F2BA (+0; sim 1.000; op 23; other 0) |
| tile_pair_decode_helper | 535 | 83:F2DB..83:F4F1 (+32; sim 1.000; op 331; other 0) | 83:F2FF..83:F515 (+68; sim 0.985; op 331; other 0) | 83:F2BB..83:F4D1 (+0; sim 1.000; op 331; other 0) |

All 1,047 bytes are analyzer-reached in all four ROMs. The three regions preserve all 572 aligned opcode positions with zero role disagreements. PAL prototype sits at `+32`, Europe at `+68`, and legacy beta is byte-identical to USA.
