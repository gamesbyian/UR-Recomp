# Stunt message / reward / display structural island

USA 81:C0DD..C604 connects queued stunt messages to score/boost rewards, message presentation, score-display digitization, embedded lookup data, and queue append helpers. The next code begins at 81:C605.

| Region | Kind | USA bytes | PAL prototype | Europe | Legacy beta |
|---|---|---:|---|---|---|
| message_consume_pre_cleanup | code | 366 | 81:C0BD..81:C22A (-32; sim 0.940; op 158; other 0) | 81:C0CE..81:C23B (-15; sim 0.915; op 158; other 0) | 81:C0DD..81:C24A (+0; sim 1.000; op 158; other 0) |
| pal_line_removed_nops | code | 3 | none | none | 81:C24B..81:C24D (+0; sim 1.000; op 3; other 0) |
| message_consume_post_cleanup | code | 283 | 81:C22B..81:C345 (-35; sim 0.940; op 120; other 0) | 81:C23C..81:C356 (-18; sim 0.943; op 120; other 0) | 81:C24E..81:C368 (+0; sim 1.000; op 120; other 0) |
| score_display_prefix | code | 9 | 81:C346..81:C34E (-35; sim 1.000; op 3; other 0) | 81:C357..81:C35F (-18; sim 1.000; op 3; other 0) | 81:C369..81:C371 (+0; sim 1.000; op 3; other 0) |
| score_display_usa_gate | code | 13 | 81:C34F..81:C35B (-35; sim 0.846; op 5; other 0) | none | 81:C372..81:C37E (+0; sim 1.000; op 5; other 0) |
| score_display_suffix | code | 217 | 81:C35C..81:C434 (-35; sim 0.871; op 88; other 0) | 81:C368..81:C440 (-23; sim 0.871; op 88; other 0) | 81:C37F..81:C457 (+0; sim 1.000; op 88; other 0) |
| message_reward_lookup_block | data | 282 | 81:C435..81:C54E (-35; sim 1.000; op 0; other 282) | 81:C441..81:C55A (-23; sim 1.000; op 0; other 282) | 81:C458..81:C571 (+0; sim 1.000; op 0; other 282) |
| queue_long_entry_and_helpers | code | 147 | 81:C54F..81:C5E1 (-35; sim 0.959; op 62; other 0) | 81:C55B..81:C5ED (-23; sim 0.810; op 62; other 0) | 81:C572..81:C604 (+0; sim 1.000; op 62; other 0) |

## Structural edits

- USA/beta C24B..C24D are three NOPs; both PAL-line builds omit them.
- Europe additionally contracts USA C372..C37E (13 bytes) to an 8-byte equivalent two-player display gate, net -5.
- The embedded data block ends at C571. C572..C575 is executable JSR $C576; RTL, not table data; its relocated JSR operand exposed the true seam.
