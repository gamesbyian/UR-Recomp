# 2026-10-11 retained integration architecture and execution sequence

Transferred verbatim from the active product plan during #1320 documentation-size reconciliation. This records historic guidance; the active plan and live work queue remain authoritative.

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

