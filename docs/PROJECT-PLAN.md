# UR-Recomp: product and architecture plan

**Current direction (2026-10-09):** Deliver the original Uniracers gameplay in a genuinely modern Windows x64 game: real wider world, 4K-capable output, faithful authored high-density art, controller-first Modern UI, profiles, records, ghosts, replays and multiplayer. **Baldosa native-core incorporation and cross-cutting release QA are the joint immediate priority.** Neither may declare the other complete: integrate the same authentic original/native gameplay, host/UI, visuals and data-integrity evidence into each playable candidate.

**This file owns durable product intent and system boundaries, not live PR status.** For current work and active owners, use [WORK-QUEUE.md](WORK-QUEUE.md); for source/asset reuse and measured Baldosa bridge, [BALDOSA-UR-RECOMP-REUSE-AUDIT-20261009.md](BALDOSA-UR-RECOMP-REUSE-AUDIT-20261009.md); for candidate quality, [QA-BOUNDED-RELEASE-CAMPAIGN.md](QA-BOUNDED-RELEASE-CAMPAIGN.md), [QA-PLAYER-JOURNEYS.md](QA-PLAYER-JOURNEYS.md) and the **sole release gate authority** [RELEASE-QUALITY-LEDGER.json](RELEASE-QUALITY-LEDGER.json). The complete earlier phase history and detail are preserved, unchanged, in [archive/PROJECT-PLAN-THROUGH-20261009.md](archive/PROJECT-PLAN-THROUGH-20261009.md). Do not execute its old linear phases as today's schedule.

## What we are building

**Uniracers itself, freed from cartridge-era presentation and administration.** The original ROM-driven game remains authoritative for physics, track contact and collision, stunts/landing/tricks, boosts, AI, RNG, timing, race rules, opponents and progression mechanics. Authentic mode preserves stock visual, audio, game and interaction behavior as a playable comparator.

Modern mode adds *host-owned* presentation and conveniences, without a second game simulator or silent rule changes:
- **Actual wider world**, not 4:3 stretch or crop. Original 256×224 logical pixels with 7:6 display PAR remain canonical; true Widescreen extends course/world visibility and respects camera, tile streaming, OAM, UI, split views and liveness.
- **HD Presentation** with faithful pose-registered 4× authored racers, high-resolution course/world art as coverage expands, and a correct Original fallback for unsupported source states. Stable rendering density and output resolution are separate from simulation and wider-world width. Real 3840×2160-capable output is a separate acceptance gate; a 1024×896 internal raster is not proof of 4K.
- **Modern frontend** with Play / Practice / Multiplayer / Records / Options, global Racer & Profiles identity, fully navigable physical controller and keyboard, options, pause/restart, onboarding, accessibility and clear results. Preserve Uniracers' original visual and audio language, not a generic engineering overlay.
- **Player convenience and integrity:** durable isolated profiles and SRAM, resumable tours, fast practice/rematch, verified personal bests and timing/splits, immutable completed-run records, real ghosts/replays, local 2P matches and multi-leg/round-robin tournaments. Reuse current versioned host files and authority; never synthesize completion or invent new persistence namespaces to suit a core.
- **Presentation options:** Original / Remastered / future Reimagined art layers; windowed/borderless/fullscreen, internal scale, resolution, VSync and host presentation FPS, plus legibility, remapping and reduced flashing. Higher display refresh must not alter 60 Hz guest simulation.

**Deferred until one complete Windows product journey is proven:** other OS/console/browser ports, online multiplayer, custom courses/editor, extravagant material/cosmetic variants, new replay editors and speculative original-code archaeology. These remain desirable later; they are not immediate QA gates. See [PLATFORM-TARGETS.md](PLATFORM-TARGETS.md), [MODERN-FRONTEND-MASTER-DESIGN.md](MODERN-FRONTEND-MASTER-DESIGN.md) and [MODERN-RACER-COSMETICS.md](MODERN-RACER-COSMETICS.md).

## One simulation, independent product layers

```text
Verified USA ROM → pinned Baldosa AOT native guest (candidate authoritative core)
                        ├→ Authentic PPU/audio/1P/2P path → independent original oracle
                        └→ read-only guest frame/PPU/OAM/time/input/result boundary
                             ├→ Widescreen: course-derived world margins, source OBJ and HUD
                             ├→ HD Presentation: guarded authored art + Original fallback
                             ├→ stable internal density → aspect/safe area → actual output resolution
                             └→ Modern host: lifecycle/input, profiles, progression,
                                            Records, replay/ghost, local 2P/tournaments
```

The current older patched SNESRecomp engine is the **existing shipping/rollback executor**, not a second gameplay authority to develop indefinitely. Baldosa-first is the **leading partially validated replacement path**, not yet the production executor. The already merged guest observer, human-input/acknowledged-pause, 4× HD and Original fallback, split-world +24 and Windows PE build are inputs to one integrated adapter. Preserve their actual code; do not build new generic implementations. If one measured fundamental incompatibility makes rehosting wasteful, revive the *bounded* selective old-core upgrade alternative at that precise seam. Read [BALDOSA-FIRST-CORE-MIGRATION-20261009.md](BALDOSA-FIRST-CORE-MIGRATION-20261009.md) for decision history and [BALDOSA-NATIVE-EXECUTION-EXPERIMENT-20261009.md](BALDOSA-NATIVE-EXECUTION-EXPERIMENT-20261009.md) for what was independently executed.

**Ownership invariants:** Baldosa owns only original guest execution; the host owns Modern UI and storage; original ROM/PPU owns true source state; the renderer owns pixels, density and widened observation only; the original/reference emulators remain independent fidelity oracles. Human input focus changes require native acknowledgement and physical release before guest resume. Profiles, SRAM, `.urrun`, `.urghost`, `.urmatch` and tournament receipt authority remain exactly once at the host. No arbitrary memory writes are granted to overlays.

## Integrated development and QA sequence

1. **Reconcile existing PRs rather than redoing them.** Refresh latest `main`, existing merged bridge steps and open ownership. Link one native Windows consumer candidate to actual Modern session APIs and controller-only root; reuse root/navigation work and source-output renderer. Original stock paths must still run.
2. **Pair each integration change with the cheapest relevant original/native and end-to-end QA witness.** Finish a legitimate Race, Circuit and timed Stunt with settled results before scaling the 45-USA course matrix. Include P2-only input, split-screen source-visible sprites, pause/resume/restart/audio, ghost timing and clean profile storage. A masked WRAM comparison or a smoke-script exit is not a completed event.
3. **Prove one compelling Windows vertical slice:** first launch → racer/profile → discoverable Play or Practice → moving Original/Remastered true-wide race → legitimate result → durable record/replay/ghost → repeat or quit. Verify its exact portable ZIP, ROM SHA, guest/core pin, output resolution, controller ownership and user data root. Run on real hardware when available; a PE build is not Windows runtime acceptance.
4. **Generalize only after the slice is real.** Extend event and graphic coverage, 2P/tournament process journeys and fullscreen/4K polish through reused acceptance routes. A QA blocker on a feature belongs to that feature's owner; QA independently verifies it, rather than creating another generic test harness.

The Baldosa and QA efforts **share build, route and player-journey evidence**; neither team should build its own wide harness, duplicate generated code, or reproduce already resolved archaeology. Match rigor to consequence, record exact candidate and artifacts, and prefer a single reusable native build feeding several isolated assertions. An upstream claim is not automatically a release pass. Full policy: [VALIDATION.md](VALIDATION.md), [ADVERSARIAL-QA-AND-RELEASE-READINESS.md](ADVERSARIAL-QA-AND-RELEASE-READINESS.md), [RECOMP-C-PRACTICES.md](RECOMP-C-PRACTICES.md).

## Acceptance and subsequent development

An internal research build can expose experiments and known limitations. An outward-facing alpha requires a controller-discoverable Windows package with an honest feature inventory and repeatable 1P/2P. A beta/release requires the applicable full gameplay content, recovery, controller/audio, renderer visibility, 4K/true Widescreen and physical-hardware gates from the release ledger. **No blanket claim that 45 courses pass**: current official count at the 2026-10-09 checkpoint is **0/45** complete independently admitted USA original/native event pairs.

Once the Baldosa/QA common candidate is established, prioritize expansion by measured player value: more actual HD poses and environmental art, Racer Studio and customization, track breadth and complete tournaments, cohesive visual/UI polish, accessibility, then secondary platforms and optional tools. Successful architecture disappears behind a game that is simply enjoyable to play.

## Authorities and terminology

- Current execution / live owners: [WORK-QUEUE.md](WORK-QUEUE.md).
- Implementation inventory / provenance: [BALDOSA-UR-RECOMP-REUSE-AUDIT-20261009.md](BALDOSA-UR-RECOMP-REUSE-AUDIT-20261009.md), [BALDOSA-SOURCE-CENSUS-20261009.md](BALDOSA-SOURCE-CENSUS-20261009.md).
- QA results and independent admission: [RELEASE-QUALITY-LEDGER.json](RELEASE-QUALITY-LEDGER.json), [ORIGINAL-COURSE-EVENT-CENSUS.md](ORIGINAL-COURSE-EVENT-CENSUS.md).
- UX / records / rendering: [MODERN-PRODUCT-LAYER.md](MODERN-PRODUCT-LAYER.md), [COMPLETED-RUN-RECORDS.md](COMPLETED-RUN-RECORDS.md), [DISPLAY-PRESENTATION-POLICY.md](DISPLAY-PRESENTATION-POLICY.md), [WIDESCREEN.md](WIDESCREEN.md), [HD-ART-DIRECTION.md](HD-ART-DIRECTION.md), [PRESENTATION-DENSITY-CONTRACT.md](PRESENTATION-DENSITY-CONTRACT.md).
- Packaging / platform: [WINDOWS-X64-PACKAGING.md](WINDOWS-X64-PACKAGING.md), [PLATFORM-TARGETS.md](PLATFORM-TARGETS.md).

Use **Widescreen** solely for expanded logical view, **HD Presentation** for source-faithful higher-density art/composition, and **4K output** for actual physical host presentation resolution. They are three distinct features, not synonyms for UR-Recomp.
