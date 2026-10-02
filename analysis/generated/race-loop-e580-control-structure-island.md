# Race-loop E580 control structural island

USA 83:E540..E7A4 is a seam-bounded race-loop support island between the merged E066/E53F control pair and the separate E7A5 routine. It contains a 64-byte table plus the direct race-frame target at E580.

| Region | Kind | Bytes | PAL prototype | Europe | Legacy beta |
|---|---|---:|---|---|---|
| race_control_lookup | data | 64 | 83:E536..83:E575 (-10; sim 1.000; op 0; other 64) | 83:E55C..83:E59B (+28; sim 1.000; op 0; other 64) | 83:E540..83:E57F (+0; sim 1.000; op 0; other 64) |
| race_loop_control | code | 549 | 83:E576..83:E79A (-10; sim 0.869; op 199; other 0) | 83:E59C..83:E7C0 (+28; sim 0.836; op 199; other 0) | 83:E580..83:E7A4 (+0; sim 1.000; op 199; other 0) |

## Accepted-census caller

- 83:CD47 JSR -> 83:E580 from race-frame-orchestrator / loop_body_after_sep_cleanup

The label is intentionally structural. The routine clearly participates in race-phase/control state and APU command selection, but exact higher-level semantics of $11F3/$11F5 are not asserted.
