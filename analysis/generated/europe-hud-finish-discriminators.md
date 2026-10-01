# Europe HUD / checkpoint structural discriminators

Two independent edges are used here: direct call references to the proposed HUD queue target, and the object-code dispatch-table entry that selects the checkpoint/finish handler.

## HUD queue call references

| Build | Candidate | JSR refs | JSL refs |
|---|---|---:|---:|
| usa-retail | `81:C5B3` | 2 | 0 |
| pal-prototype-1994-11-29 | `81:C590` | 2 | 0 |
| europe-retail | `81:C59C` | 2 | 0 |

## Object-code 0x14 dispatch

| Build | Matched dispatcher | Similarity | Dispatch table | 0x14 handler |
|---|---|---:|---|---|
| usa-retail | `81:82E6` | 1.000 | `81:8320` | `81:8050` |
| pal-prototype-1994-11-29 | `81:82C9` | 0.812 | `81:8303` | `81:8050` |
| europe-retail | `81:82BB` | 0.562 | `81:82F5` | `81:8050` |

If Europe object code 0x14 dispatches directly to `81:8042`, that independently corroborates the proposed Europe `Race_HandleCheckpointFinish` correspondence. Coherent call-reference counts and caller locations similarly strengthen the HUD queue candidate beyond byte similarity alone.
