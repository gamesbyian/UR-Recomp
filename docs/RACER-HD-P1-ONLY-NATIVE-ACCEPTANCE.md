# Native P1-HD + stock-P2 pixel preservation acceptance

Status: **experimental acceptance in PR**. A passing test does not by itself
promote the optional P1-only renderer to a player-facing default.

The source-level admission contract is in
`native/presentation/racer_oam_placement.hpp` and
`docs/RACER-HD-PAIR-GATE-COVERAGE.md`. It is explicitly disabled unless
`UR_RACER_HD=1 UR_RACER_HD_P1_ONLY=1` is set.

## Same-frame discriminator

The generated native graphics acceptance runner uses the pinned SnesRecomp
desktop renderer with an actual deterministic two-player race. During the
diagnostic-only `UR_RACER_HD_P1_NATIVE_TEST=1` route:

- The internal density is set to 1× for a direct same-frame logical-pixel
  comparison. Stock input and final host output therefore share 256×224
  coordinates without resampling.
- When PPU OBJ capture is armed for exactly slots **97/98**, the final
  renderer must actually return success; the raster geometry remains 256×224.
- The probe reads the **live OAM** bottom P2 slot96 and constructs its exact
  signed-X / 8-bit wrapped-Y, 64×64 visible rectangle, clipped to scanlines
  112–223.
- Every output pixel in that entire rectangle must equal the same pixel in
  the original PPU field used by the host composer, byte-for-byte. A single
  changed byte aborts the native process with offending `x,y`.
- The same frame must also contain at least one actual HD-changed output
  pixel, proving that the test is not passing because nothing was drawn.
- The native job must find at least one visible P2 rectangle under admitted
  P1-only capture along the unmodified long 2P input route. Its
  `UR_RACER_HD_P1_NATIVE_SUMMARY` logs total capture admissions.

This addresses the most immediate mixed-render depth risk: lower P2 OAM 96
is in front of P1 OAM 97, so a one-player replacement may not paint over
stock P2. It compares **the exact same guest raster in one process**,
avoiding the present/simulation frame skew encountered in early widened
screenshots (see merged #876).

The test intentionally does not assert that all possible P1-only frames are
safe, nor does it prove foreground BG color-math priority in every track.
The opt-in remains diagnostic until real gameplay image review and sufficient
scene coverage establish those independent properties. Widened output stays
stock and the full two-player HD pathway remains unchanged.
