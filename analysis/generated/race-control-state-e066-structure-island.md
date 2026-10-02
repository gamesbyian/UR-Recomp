# Race-control/state paired structural island

USA `83:E066..E53F` contains two race-loop control/state routines called independently from the recovered race-frame orchestrator. The first spans `83:E066..E237`; the companion spans `83:E238..E53F` and ends before table/data at `83:E540`.

| Region | USA bytes | PAL prototype | Europe | Legacy beta |
|---|---:|---|---|---|
| race_control_state_primary | 466 | 83:E05C..83:E22D (-10; sim 0.916; op 176; other 0) | 83:E082..83:E253 (+28; sim 0.830; op 176; other 0) | 83:E066..83:E237 (+0; sim 1.000; op 176; other 0) |
| race_control_state_companion | 776 | 83:E22E..83:E535 (-10; sim 0.927; op 287; other 0) | 83:E254..83:E55B (+28; sim 0.807; op 287; other 0) | 83:E238..83:E53F (+0; sim 1.000; op 287; other 0) |

## Accepted callers

- 83:CD3A -> 83:E066 from race-frame-orchestrator
- 83:CD32 -> 83:E238 from race-frame-orchestrator

Both routines are fully analyzer-reached in all four ROMs. PAL prototype preserves both at shift `-10`; Europe preserves both at `+28`. Across the pair, all 463 aligned opcode positions match in every non-USA build with zero analyzer role disagreements.
