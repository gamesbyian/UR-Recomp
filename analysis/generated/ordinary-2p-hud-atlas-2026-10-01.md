# Ordinary 2P HUD atlas evidence — 2026-10-01

Source: GitHub Actions ordinary 2P reference regression run `36943103609`, artifact `ordinary-2p-reference`.

This capture promotes the existing ordinary-two-player deterministic fixture into a visual/HUD evidence surface. Six named gameplay checkpoints were captured independently from the native recomp host and the patched Snes9x reference path. Both fixture-scoped UI-atlas reports completed with 6/6 captures `ok`; every capture is 256x224 and remains in `in_race = 1`.

## Stable semantic/visual observations

Across both runtimes:

- split-screen camera mode remains enabled (`$0DDB = 1`) at every sampled gameplay checkpoint;
- both cameras begin at X=`0x03D8`;
- after the P1-only movement interval, camera 1 advances to `0x05AF` while camera 2 remains at `0x03D8`;
- at that same checkpoint, the opposite-screen racer staging uses the recovered culling sentinels: screen 2 / P1 X = `0x30`, screen 1 / P2 X = `0x70`;
- those sentinels persist through the P2-only and simultaneous movement samples;
- the rendered split-screen course, checker bands, player-name HUD placement, mode label and timing HUD occupy the same overall presentation structure in both runtimes.

The camera-2 values reproduce the already-bounded post-intervention timing drift rather than introducing a new ownership error: at the P2-only checkpoint native reports X=`0x043A` and Snes9x X=`0x0441`; at the simultaneous checkpoint native reports `0x040B` and Snes9x `0x040F`. Camera 1 matches exactly at those sampled checkpoints.

## Framebuffer interpretation

The native and Snes9x framebuffer hashes are intentionally **not** promoted as an exact cross-runtime parity gate. Direct inspection shows why:

- at the settled baseline around frame 1420, the course/HUD composition is aligned while racer sprite animation/placement is slightly phase-shifted;
- after causal movement, moving racer sprites and stunt text can differ in presentation phase;
- at frame 1520 the displayed race timer differs by one tenth (`0:02:9` vs `0:03:0`) even though the event-relative gameplay fixture has already established the host-frame-boundary offset between runtimes.

This is consistent with the closed absolute-frame anchoring result in `docs/TWO-PLAYER-FIXTURE-PLAN.md`. A raw same-ordinal framebuffer hash would therefore conflate presentation timing with semantic fidelity. Use these captures as a durable visual atlas and as seeds for event-relative presentation checks, not as a demand for byte-identical same-host-frame output.

## Captures

| Checkpoint | Native framebuffer SHA-256 (prefix) | Snes9x framebuffer SHA-256 (prefix) |
|---|---|---|
| `two-player-race-1220` | `2e6dcb8615a8` | `4320585331ed` |
| `two-player-race-1420` | `4b83fba6e691` | `2835c6d99c9c` |
| `two-player-p1-pre-1470` | `4ac50bdece20` | `337bec1ea0c4` |
| `two-player-p1-post-1520` | `64e4b685e30c` | `1c76741c04f6` |
| `two-player-p2-post-1570` | `0c6b16644ef3` | `a24e3072d39d` |
| `two-player-both-post-1620` | `443f371e878c` | `ae7306c4d6cf` |

## Disposition

The richer split-screen/HUD atlas obligation is complete for the current ordinary-2P fidelity gate: stable gameplay, isolated P1 movement, isolated P2 movement, simultaneous opposed movement, dual-camera ownership, opposite-screen culling, and the rendered HUD/course composition are now represented by durable named captures.

Do not spend additional time expanding this atlas merely for more screenshots. Reopen visual sampling when a concrete renderer/Widescreen decision needs a state that this six-card set does not exercise. Mesen/MesenCE runtime promotion and gameplay-object activation remain separate open obligations.
