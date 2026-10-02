# 82:980D mirrored race-state bridge structural island

USA 82:980D..98BD is a compact long-entry helper called directly from race-frame orchestration. It derives mirrored $0FCB/$0FCD outputs from paired course/control state and terminates at 82:98BD; 82:98BE begins a separate routine and is excluded.

| Region | Bytes | PAL prototype | Europe | Legacy beta |
|---|---:|---|---|---|
| long_entry_wrapper | 4 | 82:9808..82:980B (-5; sim 0.750; op 2; other 0) | 82:981E..82:9821 (+17; sim 0.750; op 2; other 0) | 82:980D..82:9810 (+0; sim 1.000; op 2; other 0) |
| mirrored_state_bridge | 173 | 82:980C..82:98B8 (-5; sim 0.896; op 67; other 0) | 82:9822..82:98CE (+17; sim 0.890; op 67; other 0) | 82:9811..82:98BD (+0; sim 1.000; op 67; other 0) |

## Accepted-census caller

- 83:CD59 JSL -> 82:980D from race-frame-orchestrator / loop_body_after_sep_cleanup

The label remains structural: the mirrored-output behavior is clear, while exact higher-level gameplay naming for $0FCB/$0FCD is deferred.
