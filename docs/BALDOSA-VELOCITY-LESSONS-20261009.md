# Velocity lessons from Baldosa: operating rules

Date: 2026-10-09. Source: `baldosa/uniracers-recomp@10b864b9`, 42 commit records between October 6 and October 9, 2026. Repository created October 7. These are observed chronology, not an estimated agent-hour denominator or evidence that a masked-checkpoint route is a complete game event. UR-Recomp is only in day 11 but has a substantially broader Modern remaster scope; raw calendar days are not comparable.

## Evidence-backed observations

- On October 6, Ema committed the scaffold, ROM-native boot baseline, routes and earliest state-checkpoint harness before expanding into more game modes. This established a runnable feedback loop before polishing.
- The project derives considerable leverage from the existing SNESRecomp framework and its upstream history. It is *not* evidence that all supporting technology was invented in three days.
- An automated pipeline extends compiled coverage, disassembles with M/X widths, reconstructs byte-exact Asar, partitions naming ownership, propagates named functions into generated C and repeats route oracles. It converts one recovered fact into multiple outputs, rather than demanding parallel manual notes.
- Nine short, deterministic, game-spanning route scripts provide broad smoke checks; the original project reports masked state parity and near-complete AOT route execution, but the scripts do **not** automatically satisfy our independent complete-result criteria.
- The project shipped an ordinary launcher, downloadable native binaries and web play while changing lower-level semantics. Reuse was heavy, including upstream framework changes and generic UI.
- Ema's one alternate release workflow appears inconsistent with committed `src/gen/*.c`. Speed did not remove the need for negative-path testing.

## Rules to apply to UR-Recomp today

**Rule 1: a user-visible journey is the unit of progress.** For most work, name which of these outcomes it advances: cold-start → choose a racer/profile → finish an authentic event → see a settled result → record/ghost/replay → repeat or quit; plus full two-pad multiplayer and real 16:9/4K HD composition. Report distance to the next successful journey and actual blockers; intermediate tests are supporting evidence, not the final deliverable.

**Rule 2: use the shortest route to a running reference.** Start from Ema's intact executable for the Baldosa-first spike. Make the stock Windows race and 2P work first, then pass guest snapshots into our presentation/product adapter. Stop trying to prove every ROM region before attempting a playable vertical slice.

**Rule 3: every investigative task has an exit.** An archaeology/graphics/timing investigation should end with (a) a specific fix merged and regression proven, (b) a small explicit discriminator, or (c) a documented closed negative with no more funding pending new evidence. Avoid unlimited exploratory continuations and recurrent rediscovery.

**Rule 4: one reproducible route runner, no competing frameworks.** Prefer existing `tests/routes`, our own `tests/input` and QA fixtures. Import Ema's effective input scripts and tools once, adapt them once, then share the same provenance/route specification across original/native and both migration spikes. Preserve unmasked discrepancies and genuine terminal game results.

**Rule 5: tools must be multiplicative.** Favor codegen, source/name crosswalks, symbol discovery, multi-course replay and automatic exact-runtime-state capture when they immediately remove several independent blockers. If a tool serves one hypothetical future study and cannot improve a named journey now, defer it.

**Rule 6: consume external solutions wholesale at stable boundaries.** Reuse the full independently working core if compatible; otherwise transplant a small compatible layer. Keep our Modern product, HD graphics, widescreen, replay/profiles and existing storage authorities rather than rewriting everything. Do not maintain two permanent guest authorities.

**Rule 7: keep CI focused.** Test each candidate at the smallest sufficient layer, then one native end-to-end acceptance. Do not create a new exhaustive suite for each individual fix, repeatedly trigger noisy all-platform GHA runs, or use CI babysitting as productive engineering. Deduplicate already proved checks.

**Rule 8: communicate proof and performance separately.** Each PR/agent handoff states: playable journey advanced; observed before/after; known failing end-to-end case; source and exact ROM identity; source/code/test links; negative remaining; and next irreversible decision. Count tests and assertions separately from terminal events and visible functionality.

## Bounded one-week operating trial

This is a *working protocol*, not a promised schedule or automatic seven-day recurring task.

- **First integration checkpoint:** a clean Baldosa game launch and independent stock Windows launch with identical verified USA ROM; choose the cheapest complete test route instead of further source inventory.
- **First gameplay checkpoint:** one actual non-Dragster Race/Circuit/Stunt result through the source runner. Favor a working paired live result over adding more static course descriptions. Remain at 0/45 until admission requirements are met.
- **First product checkpoint:** player-controller cold start, Modern visible root, one complete race, displayed result, persisted record and repeat/quit. Integrate into the selected engine path without a new frontend.
- **First visual checkpoint:** one coherent, moving real-widescreen HD race at a selectable 4K-capable output, with measured stock fallback and split-screen correctness; a static mockup alone is not evidence.
- **Migration decision checkpoint:** compare core replacement and selective upgrade under the same named route and Modern host tests. Stop the inferior branch rather than keeping parallel implementations alive.

## New anti-goals and stop signals

- No documentation-only follow-up unless it resolves a named integration or correctness decision.
- No further mass file-import rounds for Ema's pinned top-level repo: 210 Git entries are already classified and all 85 useful maintained/source-cache files retained.
- No broad 45-course replay campaign until a real native/original event has completed correctly at least once.
- No polishing internal correctness differences without a player-visible impact or a concrete determinism/data-integrity failure, while the vertical slice is blocked.
- No acceptance of an unverified upstream claim as our QA evidence.
- No new browser/mobile/console platform lane while Windows remains the primary unfinished product.
- Don't optimize agent-hours by skipping required crash recovery, fidelity or controller-ownership checks. Avoid expensive generality; never fake a passing result.

**Measure progress weekly:** number of complete user journeys, correctly played course/event families, visibly remastered moving scenes, real inputs correctly handled, bugs reproduced and closed, framework patches retired, CI minutes per accepted end-to-end case, and productive hours per *accepted outcome*. PR counts and lines of source are secondary.
