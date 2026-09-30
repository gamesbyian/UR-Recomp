# USJO v8 validation matrix

Generated from the recovered-source inventory and the canonical symbol map.
Priority 1 means unresolved semantic conflict/source-only evidence; priority 4 means
the USJO-specific claim is already causally confirmed in the current runtime evidence.

| Priority | Address | USJO variable | Canonical symbol | Confidence | Status | Next action |
|---:|---|---|---|---:|---|---|
| 1 | `7E:0DFD` | `zrotation` | `Player1_ZRotationState` | 2 | source-lead | Reproduce the claimed semantic transition locally before promotion. |
| 1 | `7E:0F57` | `zprerotation` | `Player1_ZPreRotationState` | 2 | source-lead | Reproduce the claimed semantic transition locally before promotion. |
| 1 | `7E:11CD` | `realboostmeter` | `Player1_BoostMeter` | 3 | width-or-units-conflict | Resolve runtime width/units and byte-vs-word behavior. |
| 2 | `7E:042B` | `numzflips` | `Player1_ZFlipCount` | 3 | corroborated-unreproduced | Trigger the claimed state change and verify this field causally. |
| 2 | `7E:042F` | `numtabletops` | `Player1_TabletopCount` | 3 | corroborated-unreproduced | Trigger the claimed state change and verify this field causally. |
| 2 | `7E:0F61` | `numtwists` | `Player1_TwistCount` | 3 | corroborated-unreproduced | Trigger the claimed state change and verify this field causally. |
| 2 | `7E:11F9` | `numrolls` | `Player1_RollCount` | 3 | corroborated-unreproduced | Trigger the claimed state change and verify this field causally. |
| 2 | `7E:11FD` | `numflips` | `Player1_FlipCount` | 3 | corroborated-unreproduced | Trigger the claimed state change and verify this field causally. |
| 4 | `7E:04B7` | `curspeed` | `Player1_XSpeed` | 5 | runtime-confirmed | No additional USJO-specific validation required unless new evidence conflicts. |
| 4 | `7E:04BB` | `yspeed` | `Player1_YSpeed` | 5 | runtime-confirmed | No additional USJO-specific validation required unless new evidence conflicts. |
| 4 | `7E:0545` | `airflag` | `Player1_AirState` | 5 | runtime-confirmed | No additional USJO-specific validation required unless new evidence conflicts. |

## Immediate queue

The narrowest unresolved targets are the boost-meter width/units question at `7E:11CD`
and the source-only Z-rotation working fields `7E:0DFD` / `7E:0F57`.
The five stunt counters are independently corroborated but still need causal transition fixtures.
X speed, Y speed and air state are already runtime-confirmed and should not consume more
USJO-validation effort unless conflicting evidence appears.
