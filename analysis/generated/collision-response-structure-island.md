# Per-racer collision / contact-response structural island

USA `81:8FB8..99D5` consumes sampled course/contact state, reduces collision candidates, classifies landing/air state, corrects velocity and position, and includes the contact-direction quantizer at `81:983B`. The next independent long-entry wrapper begins at `81:99D6`.

| Region | USA bytes | PAL prototype | Europe | Legacy beta |
|---|---:|---|---|---|
| candidate_reduction_and_surface_classification | 569 | 81:8F98..81:91D0 (-32; sim 0.938; op 231; other 0) | 81:8F98..81:91D0 (-32; sim 0.924; op 231; other 0) | 81:8FB8..81:91F0 (+0; sim 1.000; op 231; other 0) |
| landing_air_and_velocity_gates | 275 | 81:91D1..81:92E3 (-32; sim 0.887; op 117; other 0) | 81:91D1..81:92E3 (-32; sim 0.880; op 117; other 0) | 81:91F1..81:9303 (+0; sim 1.000; op 117; other 0) |
| contact_response_after_europe_nops | 1276 | 81:92E4..81:97DF (-32; sim 0.926; op 551; other 46) | 81:92EA..81:97E5 (-26; sim 0.916; op 551; other 46) | 81:9304..81:97FF (+0; sim 1.000; op 551; other 46) |
| final_position_correction_and_return | 59 | 81:97E0..81:981A (-32; sim 0.966; op 31; other 0) | 81:97F1..81:982B (-15; sim 0.966; op 31; other 0) | 81:9800..81:983A (+0; sim 1.000; op 31; other 0) |
| contact_direction_quantizer | 411 | 81:981B..81:99B5 (-32; sim 0.983; op 179; other 7) | 81:982C..81:99C6 (-15; sim 0.973; op 179; other 7) | 81:983B..81:99D5 (+0; sim 1.000; op 179; other 7) |

## Europe-retail insertions

- Before USA 81:9304: Europe 81:92E4 inserts 6 bytes: NOP; NOP; NOP; NOP; NOP; NOP.
- Before USA 81:9800: Europe 81:97E6 inserts 11 bytes: LDA $0DE7; AND #$00FE; CMP #$0008; BEQ +8.

## Dormant USA code

- 81:9484..81:948A (7 bytes): LDA #$0764; STA $A3; BRA $94AF — bypassed alternative reward/contact selector.
- 81:9646..81:9669 (36 bytes): decay $0F4B/$0F4D toward zero — alternate angular-state decay block bypassed by the live BRA at 81:9644.
- 81:96AD..81:96AF (3 bytes): JMP $9728 — orphaned alternate jump with no recovered predecessor.
- 81:9972..81:9978 (7 bytes): LDA #$056C; STA $A3; BRA $997E — bypassed contact-direction selector alternative.

Trusted-entry tracing from the real subsystem entry preserves accumulator/index context and gives 100% aligned opcode consensus in every accepted homolog region. The dormant blocks remain explicit code but are not counted as live reached bytes.
