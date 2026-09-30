# USJO v8 control/state model

This summarizes the optimizer itself. State labels describe recovered script behavior,
not game-internal semantics unless separately reproduced.

| Script state | Values | Meaning | Assignments |
|---|---|---|---:|
| `jumpstatus` | `0, 1, 2, 3, 4` | 0=idle; 1=trying to jump; 2=airborne/rising; 3=past peak; 4=landed | 21 |
| `twiststatus` | `0, 1, 2` | 0=idle/ready; 1=waiting for backward leg; 2=waiting for forward leg | 23 |
| `tabletopstatus` | `0, 1, 2, 6` | 0=idle/waiting; 1=first half; 2=second half; 6=complete | 12 |
| `zflipstatus` | `0, 1` | 0=idle/waiting; 1=active until counter advances | 10 |
| `rollstatus` | `0, 1` | 0=idle/waiting; 1=active until counter advances | 8 |
| `flipstatus` | `0, 1` | 0=idle/waiting; 1=active until counter advances | 8 |
| `mode` | `1, 2, 3, 4, 5` | 1=jump search; 2=first-twist timing search; 3=stunt-combination search; 4=best-candidate replay/evaluation; 5=done | 15 |
| `strategy` | `1, 3, 4` | 1=build up; 3=tear down from maxima; 4=replay best/finish | 7 |

## Controller translation

- `jumping` drives B.
- `xing` drives X.
- `flipping` and `rolling` choose opposite shoulder buttons based on travel direction.
- `reverse` temporarily swaps the held horizontal direction for twist execution.
- Outside a reverse interval, the bot continuously holds the current travel direction.

The important implementation consequence is that v8 is a feedback controller, not a fixed
movie: stunt-counter changes and air/rotation working state determine subsequent inputs.
