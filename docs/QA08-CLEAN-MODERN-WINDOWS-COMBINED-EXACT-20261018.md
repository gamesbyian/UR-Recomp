# QA08: current clean HDMA/V0 + Modern Win32 exact PE checkpoint

18 October 2026 | **real compiled Windows source evidence only, no independent QA admission**

The latest green **source-qualified integrated product** candidate at the time of this receipt comes from draft [graphics/Modern integration #1851](https://github.com/gamesbyian/UR-Recomp/pull/1851) and its exact 2014-USA Windows [Actions run 39168543664](https://github.com/gamesbyian/UR-Recomp/actions/runs/39168543664). Repository tooling [39168543631](https://github.com/gamesbyian/UR-Recomp/actions/runs/39168543631) and hygiene [39168543638](https://github.com/gamesbyian/UR-Recomp/actions/runs/39168543638) both passed.

## Immutable tested source and executable

The GitHub source-test merge commit `b498dc096649a128b34d0d03c7b0c4914460812a` has exact ordered parents **Modern #1713 `02214145f5e377302ab897ae0d69090971751d92`** and **graphics/Modern overlay `c7127e7cba0e7d5ed3039dc0480d90e2444890ac`**. The overlay adds 14 source-specific workflow lines and copies five files **byte-for-byte** from the clean production [#1780](https://github.com/gamesbyian/UR-Recomp/pull/1780), including the two source-qualified title-only first-line HDMA/V0 transformations and unit guards. All previously ordered Modern recovery work remains unchanged in the tested source. No #1807 brightness trial, read-only graphics research observer, source-frame offset or HD racer art is included.

Actual original Windows x64 binary and source binding have been separately downloaded, inspected, and rehashed:

| Actual Windows artifact | Immutable identity |
| --- | --- |
| Binding artifact 12152455037 | outer SHA256 `a315a1dc8655a34a212d53077bb7b7710e1757918bb924b0ccb4505c00eba5b0`; inner JSON SHA256 `79bfec6c939e5e6c54a3c389b0ddc0c53920cf50ad01a043c7ebe9753f6a52b8` |
| Package artifact 12151548147 | outer SHA256 `40efd28a42d2b29325f6ea5e4976f29465452f1dbe130e9d986d81fc4c9f4cd6` |
| ROM-free inner ZIP | 6,057,064 bytes; SHA256 `26beb351900c60347adb9c6fb900f6ca1bbc450391c43ca44d9b0a340fa5c276` |
| Exact executed/packaged PE32+ AMD64 | 20,332,544 bytes; SHA256 `516e406993805ce686e602ce3064c6fef2d0674050fda817944cb85c9a37aa6b` |
| Launcher | SHA256 `b61d6b3836e21da6dd91dc4bcbf5cff19a85df6f73f07ee2bcd29a377fc678c3` |

The full source ZIP has exactly four expected members (manifest, readme, executable and CMD launcher). Its embedded manifest's actual SHA, source revision, byte lengths and ROM-freedom were independently checked. Native PE DOS `MZ`, `PE\0\0`, x64 machine 0x8664 and PE32+ optional-header 0x20b signatures were read from the genuine executable, not inferred from a workflow name. The original USA ROM SHA256 is required externally and no ROM, SRAM or user profile is distributed.

### Actual tested product surface

That same Windows job compiled the two graphics source adjustments **after** RF017 regenerated/verified the original guest and **before** native AMD64 linkage. It executed the real 2,473-frame two-player guest CRC/pause test, **13/13** independent Windows player journeys through original Modern execution (including ten original Practice courses across two unlock states), real CMD Q/R/T/S recovery paths, named-profile cold boots, the actual NTFS-full VHDX save-failure scenario and post-raw typed fault. Each recorded job step succeeded.

### What this does not authorize

The original/native 263-source-frame clean PPU comparison still contains **890,205 RGB5 wrong pixels** in its *separately built* clean PE. This product PE did **not** itself run the 263-frame source P7 comparison, so it may not inherit that prior execution's graphics verdict merely because its source patch is similar. Source-original/native guest4016 forced-black, seven-field CGRAM writer chronology and medal-result remaining pixels are pending. Nor is this a physical 3840×2160/window output, 342×224 7:6 pixel-aspect, current-player-input, approved HD racer-likeness or independently accepted full USA course proof.

The Modern branch has already advanced beyond this tested parent. A further **same-source** product PE must be obtained for that newer Modern code. Draft [#1851](https://github.com/gamesbyian/UR-Recomp/pull/1851) has been rebuilt on that newer Modern head without altering either graphics transformation; its first successful run applies *only* to the older source above. Separate **nonshipping** diagnostic [#1857](https://github.com/gamesbyian/UR-Recomp/pull/1857) is set up to capture that newer exact integrated source's full 263-frame PPU raster using the already proven read-only observer. No independent release-acceptance result should be asserted until its genuine run is checked. All five changes in this report are evidence only; production #1780, Modern #1713, experimental brightness #1807, HD art #1826/#1840 and release ledger are untouched.

Machine-readable immutable receipt: [QA08 exact combined Windows source](../analysis/data/qa08-clean-modern-win32-combined-exact-20261018.json).
