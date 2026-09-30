# USJO v8 validation matrix

Generated from the recovered-source inventory and the canonical symbol map.
Priority 1 means unresolved semantic conflict/source-only evidence; priority 4 means
the USJO-specific claim is already causally confirmed in the current runtime evidence.

| Priority | Address | USJO variable | Canonical symbol | Confidence | Status | Next action |
|---:|---|---|---|---:|---|---|
| 3 | `7E:042B` | `numzflips` | `Player1_ZFlipCount` | 4 | strong-partial | Close any remaining semantic/unit ambiguity when convenient. |
| 3 | `7E:042F` | `numtabletops` | `Player1_TabletopCount` | 4 | strong-partial | Close any remaining semantic/unit ambiguity when convenient. |
| 3 | `7E:0DFD` | `zrotation` | `Player1_ZRotationState` | 4 | strong-partial | Close any remaining semantic/unit ambiguity when convenient. |
| 3 | `7E:0F57` | `zprerotation` | `CurrentPlayer_ZRotationWorking` | 4 | strong-partial | Close any remaining semantic/unit ambiguity when convenient. |
| 3 | `7E:0F61` | `numtwists` | `CurrentPlayer_TwistCountWorking` | 4 | strong-partial | Close any remaining semantic/unit ambiguity when convenient. |
| 3 | `7E:11CD` | `realboostmeter` | `Player1_BoostMeter` | 4 | strong-partial | Close any remaining semantic/unit ambiguity when convenient. |
| 3 | `7E:11F9` | `numrolls` | `Player1_RollCount` | 4 | strong-partial | Close any remaining semantic/unit ambiguity when convenient. |
| 3 | `7E:11FD` | `numflips` | `Player1_FlipCount` | 4 | strong-partial | Close any remaining semantic/unit ambiguity when convenient. |
| 4 | `7E:04B7` | `curspeed` | `Player1_XSpeed` | 5 | runtime-confirmed | No additional USJO-specific validation required unless new evidence conflicts. |
| 4 | `7E:04BB` | `yspeed` | `Player1_YSpeed` | 5 | runtime-confirmed | No additional USJO-specific validation required unless new evidence conflicts. |
| 4 | `7E:0545` | `airflag` | `Player1_AirState` | 5 | runtime-confirmed | No additional USJO-specific validation required unless new evidence conflicts. |

## Immediate queue

All eight formerly unresolved v8 read addresses now have strong static support or resolved storage roles.
The remaining work is dynamic/semantic closure: event-causal stunt-counter transitions, exact Z-state physical meaning, and exact game-facing boost units.
X speed, Y speed and air state are already runtime-confirmed and should not consume more USJO-validation effort unless conflicting evidence appears.
