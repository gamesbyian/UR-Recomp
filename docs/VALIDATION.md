# Validation Strategy

Fidelity should be falsifiable.

## Reference hierarchy

1. Original ROM on real hardware where practical.
2. Trusted mature/cycle-accurate emulator behavior.
3. `snesref` differential traces.
4. Recompiled execution.

Visual similarity alone does not establish simulation fidelity.

## Deterministic cases

Build short scripted cases covering boot, menus, race start, acceleration, jumping, rotation, landing, failed landing, stunt recognition, collision, finish, AI interaction and two-player behavior.

Useful comparison surfaces include WRAM writes, CPU state around first divergence, player position/velocity/orientation, camera, timer, RNG, active objects and relevant PPU/OAM state.

## Widescreen invariant

Same initial state + same inputs + same elapsed frames should produce the same simulation state in 4:3 and widescreen unless a narrow, documented exception is intentional.
