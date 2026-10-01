# Collision/contact resolution structural island

USA `81:8FB8..99D5` contains the per-racer collision/contact resolver plus its directly called geometry helper. Live trusted-entry code and instruction-bounded USA-dormant alternatives are represented separately so dormant paths are not given fabricated analyzer M/X context. The next wrapper begins at `81:99D6`.

| Region | Class | USA bytes | PAL prototype | Europe | Legacy beta |
|---|---|---:|---|---|---|
| resolver_prefix_before_europe_nops | live | 844 | 81:8F98..81:92E3 (-32; sim 0.922; op 348; other 0) | 81:8F98..81:92E3 (-32; sim 0.910; op 348; other 0) | 81:8FB8..81:9303 (+0; sim 1.000; op 348; other 0) |
| resolver_live_a | live | 384 | 81:92E4..81:9463 (-32; sim 0.917; op 161; other 0) | 81:92EA..81:9469 (-26; sim 0.914; op 161; other 0) | 81:9304..81:9483 (+0; sim 1.000; op 161; other 0) |
| resolver_usa_dormant_a | usa-dormant | 7 | 81:9464..81:946A (-32; sim 1.000; op 0; other 7) | 81:946A..81:9470 (-26; sim 0.857; op 0; other 7) | 81:9484..81:948A (+0; sim 1.000; op 0; other 7) |
| resolver_live_b | live | 443 | 81:946B..81:9625 (-32; sim 0.935; op 195; other 0) | 81:9471..81:962B (-26; sim 0.912; op 195; other 0) | 81:948B..81:9645 (+0; sim 1.000; op 195; other 0) |
| resolver_usa_dormant_b | usa-dormant | 36 | 81:9626..81:9649 (-32; sim 0.889; op 0; other 36) | 81:962C..81:964F (-26; sim 0.889; op 0; other 36) | 81:9646..81:9669 (+0; sim 1.000; op 0; other 36) |
| resolver_live_c | live | 67 | 81:964A..81:968C (-32; sim 0.821; op 30; other 0) | 81:9650..81:9692 (-26; sim 0.821; op 30; other 0) | 81:966A..81:96AC (+0; sim 1.000; op 30; other 0) |
| resolver_usa_dormant_c | usa-dormant | 3 | 81:968D..81:968F (-32; sim 0.667; op 0; other 3) | 81:9693..81:9695 (-26; sim 0.667; op 0; other 3) | 81:96AD..81:96AF (+0; sim 1.000; op 0; other 3) |
| resolver_live_d | live | 336 | 81:9690..81:97DF (-32; sim 0.952; op 165; other 0) | 81:9696..81:97E5 (-26; sim 0.949; op 165; other 0) | 81:96B0..81:97FF (+0; sim 1.000; op 165; other 0) |
| resolver_tail_after_europe_gate | live | 59 | 81:97E0..81:981A (-32; sim 0.966; op 31; other 0) | 81:97F1..81:982B (-15; sim 0.966; op 31; other 0) | 81:9800..81:983A (+0; sim 1.000; op 31; other 0) |
| geometry_helper_live_prefix | live | 311 | 81:981B..81:9951 (-32; sim 0.987; op 137; other 0) | 81:982C..81:9962 (-15; sim 0.977; op 137; other 0) | 81:983B..81:9971 (+0; sim 1.000; op 137; other 0) |
| geometry_helper_usa_dormant | usa-dormant | 7 | 81:9952..81:9958 (-32; sim 1.000; op 0; other 7) | 81:9963..81:9969 (-15; sim 0.857; op 0; other 7) | 81:9972..81:9978 (+0; sim 1.000; op 0; other 7) |
| geometry_helper_live_tail | live | 93 | 81:9959..81:99B5 (-32; sim 0.968; op 42; other 0) | 81:996A..81:99C6 (-15; sim 0.968; op 42; other 0) | 81:9979..81:99D5 (+0; sim 1.000; op 42; other 0) |

## Europe-only structural edits

- after 81:9303: Branch homolog of USA 81:9302 changes D0 09 to D0 0F and is followed by six NOPs; following shift changes -32 to -26.
- before 81:9800: Europe inserts LDA $0DE7; AND #$00FE; CMP #$0008; BEQ +8 before the shared tail; following shift changes -26 to -15.

USA-dormant regions are still instruction-bounded code from the recovered listing/control graph; their analyzer opcode counts are intentionally not promoted as trusted-entry measurements.
