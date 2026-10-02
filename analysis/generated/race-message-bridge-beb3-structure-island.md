# Race-message bridge BEB3 structural island

USA `81:BEB3..C0DC` is a race-frame message/state bridge called from `83:CD61`, ending immediately before the accepted stunt-message pipeline at `81:C0DD`. It contains the long-entry wrapper and three bounded executable helpers.

| Region | USA bytes | PAL prototype | Europe | Legacy beta |
|---|---:|---|---|---|
| long_entry_wrapper | 4 | 81:BE93..81:BE96 (-32; sim 0.750; op 2; other 0) | 81:BEA4..81:BEA7 (-15; sim 0.750; op 2; other 0) | 81:BEB3..81:BEB6 (+0; sim 1.000; op 2; other 0) |
| race_message_dispatch | 138 | 81:BE97..81:BF20 (-32; sim 0.942; op 53; other 0) | 81:BEA8..81:BF31 (-15; sim 0.877; op 53; other 0) | 81:BEB7..81:BF40 (+0; sim 1.000; op 53; other 0) |
| mirrored_commit_helper | 162 | 81:BF21..81:BFC2 (-32; sim 0.907; op 70; other 0) | 81:BF32..81:BFD3 (-15; sim 0.907; op 70; other 0) | 81:BF41..81:BFE2 (+0; sim 1.000; op 70; other 0) |
| mirrored_materialize_helper | 250 | 81:BFC3..81:C0BC (-32; sim 0.968; op 106; other 0) | 81:BFD4..81:C0CD (-15; sim 0.952; op 106; other 0) | 81:BFE3..81:C0DC (+0; sim 1.000; op 106; other 0) |

The bridge exposes a paired P1/P2 handoff into the already-recovered stunt-message queue: mirrored state/ready flags and mirrored 16-byte payload buffers are updated before `81:C0DD` consumes them.
