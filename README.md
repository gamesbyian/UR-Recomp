# UR-Recomp

Private technical reconstruction and modern-port project for **Uniracers / Unirally** (SNES, 1994). The goal is **original gameplay, faithfully preserved, presented as a genuinely modern 4K-capable Widescreen game** with authored high-density art, a coherent controller-first frontend, profiles, records, replays/ghosts and local multiplayer. Authentic stock presentation remains available.

**Current integration priority (October 2026): incorporate Ema Guillén's Baldosa native recompilation and complete the remaining adversarial QA as one integrated effort.** The existing first-party Modern product, authored racer art, world-margin compositor, data formats and original-reference evidence are assets to **reuse**, not rewrite.

**Dual enduring goal:** deliver a faithful modern game **and** a definitive, independently reproducible technical reference for every recoverable aspect of Uniracers. Complete original understanding, evidence-backed behavior, lossless recoverable structures, clean interfaces and newcomer usability are permanent project objectives. Product alpha can progress before the entire technical reference or release QA finishes. See the [technical-reference charter](docs/DEFINITIVE-UNIRACERS-TECHNICAL-REFERENCE.md).

## Start here

- **Coding agent:** [AGENTS.md](AGENTS.md) → [live work queue](docs/WORK-QUEUE.md) → one lane-specific authority.
- **Cross-project leverage:** run `python3 tools/select_three_project_reuse.py --lane all --include-conditional` before substantive work; this consults the pinned [three-project capability matrix](analysis/data/three-project-apparatus-capability-matrix-20261010.json) without overriding the live queue.
- **Product architecture:** [project plan](docs/PROJECT-PLAN.md); feature-status and provenance are distinguished from implementation and release proof.
- **Baldosa reuse:** [UR-Recomp/Baldosa code and asset audit](docs/BALDOSA-UR-RECOMP-REUSE-AUDIT-20261009.md), [measured native bridge](docs/BALDOSA-NATIVE-EXECUTION-EXPERIMENT-20261009.md), [migration runbook](docs/BALDOSA-FIRST-CORE-MIGRATION-20261009.md).
- **Independent QA:** [bounded shared campaign](docs/QA-BOUNDED-RELEASE-CAMPAIGN.md), [player journeys](docs/QA-PLAYER-JOURNEYS.md), [authoritative release ledger](docs/RELEASE-QUALITY-LEDGER.json). A smoke route or guest WRAM checksum is not a settled original/native event.
- **Document ownership:** [docs/README.md](docs/README.md). Dated prior phase narratives are retained under `docs/archive/` and are **not active work instructions**.

## What is actually established

Our original Windows host already has substantial separate Modern product, replay/ghost/profile/tournament code and a deterministic portable ZIP path. The **Baldosa-first candidate** now has a real pinned native guest, read-only racer observer, 2P input authority, native pause handling, 4× authored-racer rendering plus stable 4× Original fallback, calibrated extra world margins and a Windows native build/execution experiment. These are **separate verified components**, not yet a released Modern Baldosa Windows product.

As of the 2026-10-09 status checkpoint, **0/45 USA courses** have been independently admitted as matching complete original/native events. Windows full-player journeys, source-visible 2P HD, physical 4K output, user-data migration and hardware acceptance retain their specific gates. Refer to the live ledger rather than treating this README as updated CI status.

## Runtime and presentation invariants

The verified original game is the gameplay authority (physics, track contact, stunt/scoring, AI, timers, RNG, collision and progression mechanics). Baldosa is the leading candidate *execution backend*; our patched legacy runtime remains a rollback until the Baldosa Modern player journey passes. Host-managed preferences, profiles, saves, records, modern menus and graphics **never form a second simulation**.

**Widescreen** expands original world visibility; **HD Presentation** supplies faithful higher-density art and fallback; **4K output** is a separate physical display-resolution goal. Original 256×224 and validated 7:6 display PAR retain their independent reference path. Do not silently stretch/crop, substitute guessed graphics or alter guest physics to fill a wider view.

Windows x64 is the first supported consumer build. Other platforms are explicitly deferred until the Windows product works. See [PLATFORM-TARGETS.md](docs/PLATFORM-TARGETS.md).

## Private ROM and distribution boundary

The repository currently includes the canonical original USA retail ROM under `reference/roms/retail/Uniracers_USA.sfc` for exact research/CI, as well as preserved comparative material. **Do not make this repository or its accumulated history public** on the assumption that code and game assets are redistributable. A separate audited public-source/ROM-user-supplied packaging decision would be required. [ROM-SAFETY.md](docs/ROM-SAFETY.md) owns this boundary.

Build/runtime bootstrap: [TOOLCHAIN.md](docs/TOOLCHAIN.md), [BRINGUP.md](docs/BRINGUP.md), [VALIDATION.md](docs/VALIDATION.md) and [WINDOWS-X64-PACKAGING.md](docs/WINDOWS-X64-PACKAGING.md). Do not choose a build recipe from an old dated experiment without checking today's pinned source and toolchain.
