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

## Differential oracle

Use SNESRecomp's `tools/snesref` as the default interpreter-vs-recomp harness once deterministic comparison is needed. The repository toolchain pins a Snes9x libretro core as the default interpreter and can install it with:

```bash
python3 tools/bootstrap_toolchain.py
```

Prefer scripted inputs and bounded frame/WRAM/audio captures over manual replay. When the result may depend on emulator-specific PPU/OAM/timing behavior, confirm the observation with an independent high-accuracy implementation such as the pinned bsnes libretro source or ares before treating emulator behavior as hardware truth.
