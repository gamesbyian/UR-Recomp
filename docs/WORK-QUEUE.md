# Work Queue

Work in dependency order. Later visual work is intentionally gated on a trustworthy stock baseline.

## Phase 0 — Evidence floor

- [x] Create private GitHub repository.
- [x] Select a pinned SNESRecomp revision.
- [x] Add SNESRecomp gitlink/submodule at the pinned revision.
- [x] Place canonical project ROM in the private repository for repository-hosted tooling.
- [ ] Fingerprint exact ROM revision: SHA-256, CRC32, size, header/mapping, region and vectors.
- [ ] Record ROM identity in project-readable form.
- [ ] Make verification tooling accept only the canonical fingerprint.
- [ ] Record baseline behavior in trusted emulators where useful.

**Exit:** the canonical input is fingerprinted and machine-verifiable.

## Phase 1 — Analyzer reconnaissance

- [ ] Run the pinned SNESRecomp cartridge probe against the canonical ROM.
- [ ] Run analyzer/code-discovery reconnaissance.
- [ ] Record cartridge mapping, banks, AOT/static coverage, unresolved indirect dispatch, interpreter fallback, warnings, crashes and likely framework gaps.
- [ ] Classify blockers as configuration, analyzer limitation, runtime/hardware, or unknown.
- [ ] Keep human-authored summaries and configs; avoid committing giant generated code dumps without a reason.

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
- [ ] Produce structural documentation.
- [ ] Build parser/tooling around the canonical ROM.

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


## Original-development archaeology workstream

See docs/original-development/.

- [x] Establish confidence-labelled developer technical history.
- [x] Create source index and acquisition ledger.
- [x] Acquire and place the 1994-11-29 PAL prototype in `reference/roms/prototypes/`.
- [ ] Fingerprint the PAL prototype and record header/mapping/vector metadata.
- [ ] Diff PAL prototype against canonical USA retail.
- [ ] Acquire DMA press-material archive locally; inventory and extract only Uniracers-relevant assets.
- [ ] Continue hunt for Mike Dailly's historical SNES framework source.
- [ ] Search for binaries/source/screenshots of SNasm, Unicycle Compression, level editor, A0 plotter, graphics/MIDI converters and Amiga/SNES link.
- [ ] Convert historical predictions into local ROM tests: RNC streams, 256-wide course interpretation, OAM/raster behavior, copier protection, animation indexing and audio-driver identity.
