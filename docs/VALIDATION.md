# Validation Strategy

Fidelity should be falsifiable.

## Reference hierarchy

1. Original ROM on real hardware where practical.
2. Trusted mature/cycle-accurate emulator behavior.
3. `snesref` differential traces.
4. Recompiled execution.

Visual similarity alone does not establish simulation fidelity.

## Evidence proportionality

Validation exists to decide whether the port is faithful enough to proceed, not to maximize the amount of evidence collected.

Before adding a capture, trace, second emulator, manual frame review, or bespoke workflow, name:

1. the specific decision or uncertainty;
2. the cheapest observable that can discriminate the plausible explanations;
3. what result would change the next action;
4. the stopping condition.

Use the minimum sufficient surface. A player-position question does not automatically require full WRAM + VRAM + OAM + audio + screenshots; a PPU/OAM question does not automatically require instruction tracing. Escalate only after a cheaper surface fails to distinguish the hypotheses.

For temporal/video divergences, first localize with machine-friendly methods: frame/state hashes, coarse checkpoints, binary search over time, or event-relative anchors. Inspect individual frames or short frame windows only after the interval is bounded. Frame-by-frame manual review of a long run is a last resort, not a default fidelity ritual.

Rigor should scale with downstream consequence. A claim that changes authoritative simulation or a hardware-compatibility rule deserves stronger independent corroboration than a cosmetic/layout observation or an archival inference. Once additional evidence is unlikely to change implementation, a gate, or the confidence class, stop.


## Deterministic cases

The machine-readable fixture catalog is `tests/fixtures.json`. Each fixture names its controller script, purpose, execution engines, checkpoints, current comparison surfaces, and intended extensions. Add a fixture there when a replay becomes a durable regression workload.

Build short scripted cases covering boot, menus, race start, acceleration, jumping, rotation, landing, failed landing, stunt recognition, collision, finish, AI interaction and two-player behavior.

For two-player cases, use the shared neutral controller stream `start:duration:p1-mask[:p2-mask]`. The three-field legacy form remains P1-only. Native Lua and Mesen adapters consume the same format directly; the pinned `snesref` source is patched at build time by `tools/patches/snesrecomp-dual-controller-input.patch` until equivalent support is upstream. Do not validate 2P merely by observing the second racer: require at least one P2-only causal input, one simultaneous-input case, and paired player-state checkpoints.

Useful comparison surfaces include full WRAM, WRAM write history, CPU state around first divergence, player position/velocity/orientation, camera, timer, RNG, active objects, PPU registers, OAM, VRAM, audio state and rendered frames.

The current `reach-first-race` fixture already runs unchanged through native recompilation and Snes9x/snesref and compares full 128 KiB WRAM checkpoints. Expand that same harness before creating parallel replay machinery.

### Two-player atlas/fidelity completion gate

`docs/TWO-PLAYER-FIXTURE-PLAN.md` owns the behavioral acceptance route for the shared P2 transport. Before menu/gameplay/OAM/split-screen fidelity is considered complete, preserve deterministic evidence for P1-to-P2 rider-selection handoff, VS challenger/challenge-track progression, first two-player race entry, simultaneous P1/P2 input, paired player-state checkpoints, and split-screen framebuffer/OAM behavior. One-player coverage must not silently stand in for multiplayer coverage.

## Controlled mutation

Use `tools/mutate_rom.py` for byte-level hypothesis experiments. It refuses in-place edits, bounds-checks and overlap-checks patches, writes a separate ROM copy, and emits a JSON record containing the original/output SHA-256 hashes and every before/after byte range.

Mutation outputs and bulk captures are scratch artifacts and should remain untracked unless deliberately promoted. A mutation result becomes evidence only when paired with a deterministic fixture and a recorded observable consequence.

## First-party C semantic safety

For handwritten C/C ABI code that observes guest state or models machine-shaped values, fidelity validation has two independent layers.

First, the host-language implementation must stay within explicit portable C semantics. Follow `RECOMP-C-PRACTICES.md`: fixed-width guest values, explicit byte order, range-checked narrowing, bounds-before-dereference address derivation, and no reliance on signed overflow or implementation-defined negative shifts. Portable first-party C seams compile as C11 under both GCC and Clang with the documented strict warning floor and run their pure/testable paths under ASan/UBSan.

Second, the resulting behavior must still satisfy the owning game-fidelity oracle. Sanitizers cannot prove SNES behavior, and a matching deterministic fixture does not excuse undefined host-C behavior. Use both layers where the seam can affect guest-derived behavior.

Do not extend these warning requirements mechanically into vendored or imported C. Generated recompilation output remains disposable; recurring generated-code issues belong in the generator/runtime or a narrow project-owned seam.

## Windows release artifact identity

The portable Windows x64 release path verifies the assembled package tree, verifies the final ZIP, and boots the extracted ZIP rather than the build tree. Package files remain read-only; mutable state lives outside the extracted package.

The ZIP constructor normalizes archive entry order, timestamp, compression metadata, and file mode. Release acceptance rebuilds a second ZIP from the same verified package tree and requires byte-for-byte equality before upload. It also retains a canonical .sha256 sidecar for the uploaded ZIP so the exact distribution artifact can be identified before extraction. The internal PACKAGE-MANIFEST.json remains the per-file integrity authority after extraction.

## Widescreen invariant

Same initial state + same inputs + same elapsed frames should produce the same simulation state in 4:3 and widescreen unless a narrow, documented exception is intentional.

## Differential oracle

Use SNESRecomp's `tools/snesref` as the default interpreter-vs-recomp harness once deterministic comparison is needed. The repository toolchain pins a Snes9x libretro core as the default interpreter and can install it with:

```bash
python3 tools/bootstrap_toolchain.py
```

Prefer scripted inputs and bounded frame/WRAM/audio captures over manual replay. Snes9x is a convenient default interpreter, not hardware truth: the pinned source still contains an explicit Uniracers OAM workaround. Therefore Snes9x cannot independently validate the exact active-display OAM behavior it special-cases.\n\n`.github/workflows/independent-reference-route.yml` runs the same durable first-race fixture through pinned Snes9x and the pinned Beetle/bsnes-derived libretro core via `snesref` and compares their WRAM checkpoints. The ordinary bsnes-libretro core is useful for manual/frame-level cross-checks but does not expose `RETRO_MEMORY_SYSTEM_RAM`, so it cannot drive `snesref`'s WRAM-keyed fixture grammar without adapter work. Use the Beetle route as the cheap second-oracle floor. The pinned Beetle core currently completes the first-race fixture and writes the required WRAM checkpoints, then aborts during libretro teardown after scripted quit. The workflow accepts exit 134 only when the terminal checkpoint already exists, emits a warning, and still compares the completed evidence; any earlier failure remains fatal. The first successful cross-core run found checkpoint differences of 22 bytes at `main-menu-ready`, 237 at `rider-select-ready`, 28 at `tours-ready`, 33 at `tracks-ready`, 59 at `after-track-confirm`, 53 at `now-playing-ready`, and 120 at `race-entered` out of 131,072 WRAM bytes. Treat these counts as an emulator-variance baseline, not as bugs or tolerances by themselves; classify addresses before promoting any difference into an invariant. For claims that specifically depend on PPU/OAM/timing behavior, add the relevant PPU/OAM/frame capture and, where practical, corroborate with ares or hardware-level evidence before promoting a rule as SNES behavior.


## Native trace / CI failure classification

Before treating a failed native or trace workflow as a game/runtime regression:

- require the exact generated game executable; never fall back to the first executable found under a CMake build tree;
- separate build/configuration failures, workflow timeouts, client/protocol failures and guest/runtime failures;
- inspect the preserved host log before changing SNES behavior;
- remember that trace instrumentation can make wall-clock execution dramatically slower without changing guest-frame behavior.

The pinned SNESRecomp trace debug server is line-oriented **command/response** TCP. It does not send a greeting banner. Clients should connect and immediately issue a supported command. Prefer extending `tools/trace_native_wram_writers.py` or another established client rather than duplicating protocol assumptions.

The server's synchronous `step N` command has its own bounded wait. Keep trace batches small enough to finish comfortably inside that deadline; the current race-entry probe uses 25-frame batches, then switches to frame-by-frame observation near the target. Give the outer workflow timeout substantially more wall-clock budget than an ordinary native run.

When a trace probe fails, preserve both the host log and structured probe output even on failure. A successful host that is later killed by the workflow timeout is a harness-budget failure, not evidence of a guest crash.

## Interpreting WRAM differentials

Full-WRAM comparison is intentionally broad and will include non-semantic state. Do not require byte-for-byte equality until differences are classified.

For each persistent difference, prefer this order:

1. inspect its behavior across checkpoints;
2. attribute writes dynamically where possible;
3. inspect relevant CPU state such as SP/DP/DB and execution mode;
4. decide whether the byte is semantic game state, stack/scratch residue, or a free-running timing/presentation counter;
5. promote only confirmed semantic invariants into regression assertions.

The first-race investigation is the reference example: `$01D1–$01D4` differed because of stale stack history, while `$00C6/$00C8/$00C9` were phase counters. Treating all seven as simulation bugs would have sent the investigation in the wrong direction.
