# Original Baldosa and Malmazuke: pinned source census, 2026-11-09

**Research evidence, not instructions, imported code, or release acceptance.** Operational follow-up lives in [upstream intake plan](../../docs/UPSTREAM-BALDOSA-MALMAZUKE-INTAKE.md) and existing shared board. The [machine snapshot](../../analysis/upstream-baldosa-malmazuke-state-20261109.json) retains all Malmazuke PR numbers/titles/merge dates and original tree identities; GitHub's pinned trees are the canonical complete path inventories.

## Source census and scope actually checked

| | Baldosa USA | Malmazuke PAL |
| --- | --- | --- |
| Original | [baldosa/uniracers-recomp](https://github.com/baldosa/uniracers-recomp) | [malmazuke/unirally-reconstruction](https://github.com/malmazuke/unirally-reconstruction) |
| HEAD | [10b864b9d](https://github.com/baldosa/uniracers-recomp/commit/10b864b9d14a7b7416dd909eb7b054c88faef101) | [19ecb59fb](https://github.com/malmazuke/unirally-reconstruction/commit/19ecb59fb56bc9b3024a72ab9cba912586229769) |
| Last source push | 2026-10-09 | 2026-11-09 UTC |
| Full tree | [210 entries](https://api.github.com/repos/baldosa/uniracers-recomp/git/trees/10b864b9d14a7b7416dd909eb7b054c88faef101?recursive=1) | [1,138 entries](https://api.github.com/repos/malmazuke/unirally-reconstruction/git/trees/19ecb59fb56bc9b3024a72ab9cba912586229769?recursive=1) |
| Branches observed | main only | main only |
| PRs | 0 total | 99 PRs, all merged; #78 is an issue |
| Open issues | 0 | [#78](https://github.com/malmazuke/unirally-reconstruction/issues/78), "Hi! Working on a similar project." |
| Published GitHub releases | v0.1.0–v0.4.1 (5) | 0 |
| Root source rights | PolyForm Noncommercial 1.0.0 (Matthew Stanley) | MIT (Mark Feaver) |
| UR pinned research prior to this census | same HEAD | `42d444594641d23f5d3c15da7b7c454bb5180e43` (Oct 10) |

**Delta:** the current Malmazuke main is 260 commits ahead of UR's October 10 pinned research source, with 177 changed paths in the compare API. The old imported symbol/map set remains pinned intentionally. Baldosa is unchanged. Enumerated both full Git trees, all 99 Malmazuke PR metadata rows, upstream status/README/AGENT and current tasks, source/license/release/branch collections, and the most relevant new PR reports. **Not claimed:** line-by-line review of all 177 changed paths, reproducing uncommitted captures, verifying compiled output, independent USA game acceptance, or a definitive absence of useful details in older PR diffs. These remain explicit follow-ups rather than invisible assumptions.

## Source domains and research opportunities

| Surface | Upstream source evidence to inspect | Current interpretation / UR action |
| --- | --- | --- |
| AOT guest/codegen and symbols | Baldosa `recomp/`, `decomp/`, `src/gen/`, `framework_pins.txt`, `tools/regen.sh`; existing UR imported matching source | Stable original USA engine. Reuse pinned generated code/bridge; don't regenerate a competing engine. |
| Native host and exact routes | Baldosa `src/game_rtl.c`, `src/main.c`, `tools/routes.sh`, `tools/firstdiff.py`, `tests/routes/` | Compare actual current 2P sprite/visible pixels, persistence and game startup only when UR failure survives existing proof. |
| Web/networking/UI | Baldosa `src/web_netplay.c`, `web/netplay.js`, `web/settings.js`, launcher submodule and v0.4.1 | 3-frame lockstep delay and every-120-frame WRAM CRC are useful method references; browser WebRTC/signalling is not the intended infrastructure-independent Windows P2P architecture. Web port deferred. |
| Code-map census | Malmazuke [#96](https://github.com/malmazuke/unirally-reconstruction/pull/96), [#100](https://github.com/malmazuke/unirally-reconstruction/pull/100), `docs/map/static/`, `docs/research/R-0109`, `R-0112` | 919-run corpus and data reads give conditional PAL hypotheses. Unexplained code-bank headline 8,237→4,276 bytes only after classing 3,415 `unreferenced`; without assumption 7,691 remain. New data-bank read reach 86.7%; all 45 PAL track streams read. No USA completion claim. |
| SRAM, records, corrupted state | [#99](https://github.com/malmazuke/unirally-reconstruction/pull/99), `src/core/cartridge_ram.cpp`, `src/app/save_file.cpp`, `R-0111` | 919 routes / ~5.05M frames, 355,423→181,547 differing write frames, 207 routes still differing outside never-read bytes. Boot wipe timing, league cursor 16-bit wrapping, option words, multi-frame writes are good local test leads. |
| App-vs-runner divergence | [#97](https://github.com/malmazuke/unirally-reconstruction/pull/97), [#93](https://github.com/malmazuke/unirally-reconstruction/pull/93), `src/core/lab_outputs.cpp`, `src/app/frontend.cpp` | ScriptClock across notices, demo press, race loading frame count, default saves/audio; check exact Windows application vs scripted renderer/guest through existing UR tools. Upstream has **no Windows CI** for its app. |
| Rare branches and 2P HUD | [#94](https://github.com/malmazuke/unirally-reconstruction/pull/94), [#95](https://github.com/malmazuke/unirally-reconstruction/pull/95), `docs/map/race-*.map.json`, `R-0107/0108` | Purposeful original captures for arrows, looping, lift/push and high P2 stunt scores; surviving loop-facing-away and track-13 flag-table questions. Original USA replay/homolog proof required. |
| Locked tours, league, records, menu | [#81–#83](https://github.com/malmazuke/unirally-reconstruction/pull/83), [#87](https://github.com/malmazuke/unirally-reconstruction/pull/87), [#88](https://github.com/malmazuke/unirally-reconstruction/pull/88), [#91](https://github.com/malmazuke/unirally-reconstruction/pull/91), [#92](https://github.com/malmazuke/unirally-reconstruction/pull/92) | Expand existing PAL corroboration when actual supported USA menu/records/progression question appears; name rejection and option-bit semantics are already bounded by UR's current Modern/Auth split. |
| Split effects and rider placement | [#89](https://github.com/malmazuke/unirally-reconstruction/pull/89), [#90](https://github.com/malmazuke/unirally-reconstruction/pull/90), `src/core/presentation.cpp`, `src/core/rider_look.cpp` | Split HUNTER pictures, two-view power bounce and rider under-HUD differences can inform existing QA08 2P raster/OBJ analysis; not a substitute for actual original USA final pixels. |
| Audio/clock/PPU | `src/core/audio_*.cpp`, `tools/unirally_lab/reference/audio.py`, `docs/research/R-0074..R-0099`, queued timing tasks | Driver/port/cue studies may narrow QA01 CPU↔SPC causal discrepancy. Never copy PAL timings or treat output clock domains as aligned. |
| Selective CI and evidence retention | [#84](https://github.com/malmazuke/unirally-reconstruction/pull/84), [#85](https://github.com/malmazuke/unirally-reconstruction/pull/85), [#86](https://github.com/malmazuke/unirally-reconstruction/pull/86), [#98](https://github.com/malmazuke/unirally-reconstruction/pull/98); D-0011–D-0013 | Compare change-based dependency closure, main/candidate double verdict, adversarial mutation tests, zstd retention and pinned SDL mirror with existing UR collective-qualification plan. No second CI scheduler. |
| Replay/reference/architecture | Malmazuke earlier #1–#80, `tools/unirally_lab/{reference,replay,access,coverage,content,native,gates}/`, test manifests and freezes; existing 35-row UR matrix | Full early PR/title inventory captured, detailed diff-by-diff semantic reconciliation still incomplete. Reuse established U1/U2/conditional policy, not general code import. |
| Product/extended features | `docs/FUTURE_IDEAS.md`, Baldosa web addon | Malmazuke personal ghost/leaderboard ideas are deferred concepts; UR already has richer local records/ghost plans. No net-new implementation. |

## Upstream work still explicitly unfinished (as of this HEAD)

Malmazuke's `tasks/README.md` currently queues **OPEN-BRANCHES**, **SOUND-PROCESSOR-TIMING**, **CPU-CYCLE-TIMING**, **PICTURE-RESIDUALS**, **SAVE-IMAGE-REMAINDER** and **OPPONENT-POSE-BOUNDS**. The last exposes a hardened-build out-of-range opponent colour lookup (`presentation.cpp:243`, opponent `0x14`). `OPEN-BRANCHES` includes high HUD fields, sprite tile queue limits, 2P/VS locked tracks, race tie, final track wrap, 1000-point stunt, loop facing-away and rarely observed sounds. These are **upstream queued proposals or limitations**, not accepted fixes.

Malmazuke's `local/evidence/` raw captures are typically gitignored; the committed reports, recipes, maps and tests can be inspected, but the reported original recordings have not been imported or independently replayed here. The 919-run count is the upstream's assertion and needs scope-bound replication before UR promotes it to proof.

## Two practical first investigations

1. **SRAM applicability:** check existing UR Windows isolated profile/crash/record tests for missing exact cartridge write-frame and corrupt-cursor cases; document a minimal USA original/native discriminator where a real current blocker remains. Avoid modifying the host save format just to make PAL bytes match.
2. **App parity:** on one already qualified Windows source/PE, inspect scripted vs actual idle demo, notice and league transition timing. If current UR journeys already validate this, close as corroboration and move to the branch-coverage task.

The other 97 older Malmazuke PRs and all 177 changed paths are indexed or discoverable from the pinned tree, **not certified as semantically reviewed**. Continue explicitly through the shared work ID, with one bounded finding at a time and release credit unchanged.
