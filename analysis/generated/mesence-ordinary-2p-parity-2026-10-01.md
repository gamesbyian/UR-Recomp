# MesenCE ordinary 2P semantic parity — 2026-10-01

Run `36948109734` promoted the ordinary two-player fixture through pinned MesenCE revision `a60e79feb4d6dcced5922d636f9211837d01e381`, using the repository's `mesen-for-ai` adapter and the Lua input-port compatibility patch already carried under `third_party/src/mesen-for-ai/patches/`.

The run successfully built MesenCE, replayed the canonical neutral two-controller stream, dumped all nine named checkpoints, summarized the six promoted race checkpoints, and passed the split-screen route assertions.

## Three-runtime result

The MesenCE semantic summary matches Snes9x **exactly** at all six promoted race/movement checkpoints for the recovered racer slots, race-progress state, camera/viewport state, culling sentinels, and observed update-list state.

The important discriminator is the already-known P2 movement seam:

| checkpoint | runtime | P2 x | P2 vx | camera 2 x | camera 2 vx |
|---|---|---:|---:|---:|---:|
| `two-player-p2-post-1570` | native | 1180 | 306 | 1082 | 11 |
|  | Snes9x | 1187 | 305 | 1089 | 10 |
|  | MesenCE | 1187 | 305 | 1089 | 10 |
| `two-player-both-post-1620` | native | 1137 | -263 | 1035 | -9 |
|  | Snes9x | 1141 | -266 | 1039 | -9 |
|  | MesenCE | 1141 | -266 | 1039 | -9 |

Before P2 intervention, all three runtimes agree exactly at `1220`, `1420`, `1470`, and `1520` for the promoted semantic surfaces.

This independently confirms that the small post-P2 difference is a native-host timing slice rather than a Snes9x-specific behavior. It is consistent with the separately closed absolute-frame anchoring investigation and gives the project a second emulator oracle for the same causal route.

## Durable gate

The MesenCE workflow now asserts the Snes9x-established semantic tuple at all six promoted checkpoints: racer X/X-speed, per-camera X/X-velocity, and both players' checkpoint/finish/lap progress. It deliberately does not require MesenCE to reproduce the native host's post-P2 coordinates.

The Mesen/MesenCE runtime-promotion item in `docs/TWO-PLAYER-FIXTURE-PLAN.md` is therefore complete. Future expansion should be driven by a concrete need such as object activation or widescreen validation, not by adding more emulator checkpoints for their own sake.
