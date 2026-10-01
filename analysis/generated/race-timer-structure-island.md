# Race / stunt timer lifecycle structural island

USA `81:C697..C906` contains the timer long-entry wrapper, mode dispatcher, count-up race timer, stunt countdown timer, digit refresh, timeout handling, and warning-sound threshold. The next code begins at `81:C907`.

All 624 USA bytes are executable. USA and legacy beta are byte-identical. PAL prototype stays at shift -35 and Europe at -19 throughout. Both regional builds preserve all 244 aligned opcode positions with zero code/operand-role disagreements.

| Region | USA bytes | PAL prototype | Europe | Legacy beta |
|---|---:|---|---|---|
| long_entry_and_dispatch_live | 13 | 81:C674..81:C680 (-35; sim 0.769; op 6; other 0) | 81:C684..81:C690 (-19; sim 0.769; op 6; other 0) | 81:C697..81:C6A3 (+0; sim 1.000; op 6; other 0) |
| dormant_cb37_call | 3 | 81:C681..81:C683 (-35; sim 0.667; op 1; other 0) | 81:C691..81:C693 (-19; sim 0.667; op 1; other 0) | 81:C6A4..81:C6A6 (+0; sim 1.000; op 1; other 0) |
| mode_dispatch_tail | 44 | 81:C684..81:C6AF (-35; sim 0.795; op 17; other 0) | 81:C694..81:C6BF (-19; sim 0.773; op 17; other 0) | 81:C6A7..81:C6D2 (+0; sim 1.000; op 17; other 0) |
| count_up_timer | 270 | 81:C6B0..81:C7BD (-35; sim 0.844; op 104; other 0) | 81:C6C0..81:C7CD (-19; sim 0.815; op 104; other 0) | 81:C6D3..81:C7E0 (+0; sim 1.000; op 104; other 0) |
| stunt_countdown_timer | 294 | 81:C7BE..81:C8E3 (-35; sim 0.850; op 116; other 0) | 81:C7CE..81:C8F3 (-19; sim 0.806; op 116; other 0) | 81:C7E1..81:C906 (+0; sim 1.000; op 116; other 0) |

`81:C6A4..C6A6` is a valid `JSR $CB37` intentionally bypassed by the unconditional `BRA` at `C6A2`; it is retained as a dormant code slot, not reclassified as data.

The live timer representation is split across `7E:0E0F` (minutes), `0E13` (tens of seconds), `0E17` (seconds), `0E1B` (tenths), and `0E1F` (six-step sub-tick/frame phase). The count-up and countdown routines share the same display-digit refresh path.
