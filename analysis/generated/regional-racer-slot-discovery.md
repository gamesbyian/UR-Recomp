# Regional racer persistent-slot discovery

Each row is recovered from bidirectional copy edges in the matched racer-update routine. The P2 address is the unique second persistent slot paired with the same shared working state after the already-confirmed P1 slot is identified.

| Build | Field | P1 | P2 recovered | Exact two-slot relation |
|---|---|---|---|---|
| usa-retail | xpos | `7E:0411` | `7E:0413` | yes |
| usa-retail | ypos | `7E:0415` | `7E:0417` | yes |
| usa-retail | xspeed | `7E:04B7` | `7E:04B9` | yes |
| usa-retail | yspeed | `7E:04BB` | `7E:04BD` | yes |
| usa-retail | boost | `7E:11CF` | `7E:11D1` | yes |
| pal-prototype-1994-11-29 | xpos | `7E:0411` | `7E:0413` | yes |
| pal-prototype-1994-11-29 | ypos | `7E:0415` | `7E:0417` | yes |
| pal-prototype-1994-11-29 | xspeed | `7E:04B7` | `7E:04B9` | yes |
| pal-prototype-1994-11-29 | yspeed | `7E:04BB` | `7E:04BD` | yes |
| pal-prototype-1994-11-29 | boost | `7E:11D3` | `7E:11D5` | yes |
| europe-retail | xpos | `7E:0415` | `7E:0417` | yes |
| europe-retail | ypos | `7E:0419` | `7E:041B` | yes |
| europe-retail | xspeed | `7E:04BB` | `7E:04BD` | yes |
| europe-retail | yspeed | `7E:04BF` | `7E:04C1` | yes |
| europe-retail | boost | `7E:11D9` | `7E:11DB` | yes |

This verifies structure membership and P1/P2 pairing, not equality of physics values between builds.
