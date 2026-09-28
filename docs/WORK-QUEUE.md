# Work Queue

Work in dependency order. Later visual work is intentionally gated on a trustworthy stock baseline.

## Phase 0 — Evidence floor

- [x] Create private GitHub repository.
- [x] Select a pinned SNESRecomp revision.
- [ ] Add SNESRecomp gitlink/submodule at the pinned revision.
- [ ] Identify exact ROM revision(s) to support first.
- [ ] Record ROM identity only as hashes, size, mapping/header facts and version metadata.
- [ ] Add local ROM verification.
- [ ] Confirm no proprietary blobs are tracked.
- [ ] Record baseline behavior in trusted emulators where useful.

**Exit:** target ROM can be reproducibly identified without storing it.

## Phase 1 — Analyzer reconnaissance

- [ ] Run current SNESRecomp analyzer against target ROM.
- [ ] Record cartridge mapping, banks, AOT/static coverage, unresolved indirect dispatch, interpreter fallback, warnings, crashes and likely framework gaps.
- [ ] Classify blockers as configuration, analyzer, runtime/hardware, or unknown.
- [ ] Keep human-authored summaries and configs; do not commit giant generated code dumps.

**Exit:** we know what blocks or permits execution.

## Phase 2 — First boot

- [ ] Native window opens.
- [ ] Reset vector executes.
- [ ] DMA/HDMA initialization survives.
- [ ] Title/logo sequence appears.
- [ ] Input reaches menus.
- [ ] A mode can be selected.

**Exit:** title/menu operation is reproducible.

## Phase 3 — First playable race

- [ ] Reach one-player race.
- [ ] Track/player/background render plausibly.
- [ ] Audio runs.
- [ ] Start, accelerate, jump, rotate, land and finish.
- [ ] No simulation modifications.

**Exit:** complete a stock race in 4:3.

## Phase 4 — Uniracers hardware oddity

Investigate the historical Snes9x game-specific OAM/HDMA behavior.

- [ ] Test whether current runtime already handles it.
- [ ] Reproduce the failure if not.
- [ ] Determine affected modes.
- [ ] Reduce to smallest deterministic case.
- [ ] Prefer a correct general SNES behavior fix to a game-specific hack.

## Phase 5 — Differential validation

Use `snesref` or another trustworthy reference route.

- [ ] Deterministic input sequences.
- [ ] WRAM/state comparison.
- [ ] First-divergence workflow.
- [ ] Regression cases for race start, acceleration, jump, rotation, landing, stunt, collision, finish and two-player.

**Exit:** fidelity is objectively testable.

## Phase 6 — Reverse-engineering map

Prioritize: main loop, input, race state, player physics, camera, course loader, RNC decompression, course representation, sprite/OAM construction, culling, HUD and audio hooks.

Maintain `SYMBOLS.md` and `RESEARCH-LEDGER.md`.

## Phase 7 — Course format

- [ ] Locate compressed blocks and pointer/index tables.
- [ ] Verify RNC variant/path.
- [ ] Reconstruct dimensions and primitives.
- [ ] Produce ROM-free structural documentation.
- [ ] Build local parser from a user-supplied ROM.

## Phase 8 — Widescreen

Only after deterministic stock behavior is established.

- [ ] Separate viewport width from gameplay/collision semantics.
- [ ] Widen render/culling paths deliberately.
- [ ] Test object activation and opponent behavior.
- [ ] Preserve 4:3 regression mode.

## Phase 9 — Modern presentation

Optional authentic scaling, arbitrary windows, 16:9/ultrawide, high-resolution UI and replacement presentation layers.

## Phase 10 — Editor/custom courses

Design only after the real course representation is understood. Prefer a documented custom-course format loaded without altering core physics.
