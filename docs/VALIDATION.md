# Validation Strategy

Fidelity should be falsifiable.

## Reference hierarchy

1. Original ROM on real hardware where practical.
2. Trusted mature/cycle-accurate emulator behavior.
3. `snesref` differential traces.
4. Recompiled execution.

Visual similarity alone does not establish simulation fidelity.

## Deterministic cases

The machine-readable fixture catalog is `tests/fixtures.json`. Each fixture names its controller script, purpose, execution engines, checkpoints, current comparison surfaces, and intended extensions. Add a fixture there when a replay becomes a durable regression workload.

Build short scripted cases covering boot, menus, race start, acceleration, jumping, rotation, landing, failed landing, stunt recognition, collision, finish, AI interaction and two-player behavior.

Useful comparison surfaces include full WRAM, WRAM write history, CPU state around first divergence, player position/velocity/orientation, camera, timer, RNG, active objects, PPU registers, OAM, VRAM, audio state and rendered frames.

The current `reach-first-race` fixture already runs unchanged through native recompilation and Snes9x/snesref and compares full 128 KiB WRAM checkpoints. Expand that same harness before creating parallel replay machinery.

## Controlled mutation

Use `tools/mutate_rom.py` for byte-level hypothesis experiments. It refuses in-place edits, bounds-checks and overlap-checks patches, writes a separate ROM copy, and emits a JSON record containing the original/output SHA-256 hashes and every before/after byte range.

Mutation outputs and bulk captures are scratch artifacts and should remain untracked unless deliberately promoted. A mutation result becomes evidence only when paired with a deterministic fixture and a recorded observable consequence.

## Widescreen invariant

Same initial state + same inputs + same elapsed frames should produce the same simulation state in 4:3 and widescreen unless a narrow, documented exception is intentional.

## Differential oracle

Use SNESRecomp's `tools/snesref` as the default interpreter-vs-recomp harness once deterministic comparison is needed. The repository toolchain pins a Snes9x libretro core as the default interpreter and can install it with:

```bash
python3 tools/bootstrap_toolchain.py
```

Prefer scripted inputs and bounded frame/WRAM/audio captures over manual replay. When the result may depend on emulator-specific PPU/OAM/timing behavior, confirm the observation with an independent high-accuracy implementation such as the pinned bsnes libretro source or ares before treating emulator behavior as hardware truth.
