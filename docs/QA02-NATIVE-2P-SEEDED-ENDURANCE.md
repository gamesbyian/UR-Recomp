# QA-02 native two-controller seeded gameplay endurance

**Status:** manual reliability research, not original/native course acceptance, a settled multiplayer event, a Baldosa Windows release or physical gamepad test. One new randomized workload; no second emulator, controller interpreter, game host, storage model or gameplay oracle. Entry: [QA-02 native 2P seeded gameplay endurance](../.github/workflows/qa02-native-2p-seeded-endurance.yml). Depends on the existing [Shared Modern native acceptance](../.github/workflows/modern-shared-native-acceptance.yml) for the *same exact* Linux candidate build and existing 2P input grammar.

## Problem and scientific question

The short CI routes execute a finite fixed stream of controller actions and stop; replaying that stream thousands of times is limited coverage. This campaign asks a narrower but important new question: **Can the current authentic native 2P guest withstand many different legal two-seat frame-input trajectories, remaining deterministic on a fresh replay and observably responsive to each rider independently?** A same-binary repeatability comparison is not an independent SNES original oracle, a course-completion proof or a 1P/2P Modern product proof.

## Construction

The source-owned fixtures [ordinary 2P input](../tests/input/two-player-first-race.input) and [race observation](../tests/input/two-player-first-race-observe.script) establish a known genuine stock menu-to-race entry and source WRAM checkpoint at frame 1620. The campaign reuses the maintained `tools/controller_input.py` parser to validate the fixture and all its generated input files, preserving the **entire original prefix byte-for-byte**. No WRAM patching, scripted fake results, forced guest event outcome or alternate game logic.

Each seed makes a unique two-seat action stream after the source entry, with a simultaneous P1 Right/P2 Left probe at frame 1650 and varying later movements and A combinations in distinct non-overlapping frame slots. One trial is **four fresh real native guest processes** with separate mutable directories:

1. **Treatment:** varied P1 + P2 frame inputs.
2. **Exact repeat:** identical input stream. Every actual captured full 128-KiB WRAM checkpoint must match the treatment's SHA-256; one different sample is a red determinism failure.
3. **P1 ablated:** same P2 inputs but remove only new P1 controls after the source entry.
4. **P2 ablated:** same P1 inputs but remove only new P2 controls.

All four must share the original first-race active WRAM checkpoint before new actions. Both ablations must show a different real guest WRAM state after the controlled simultaneous input pulse. This proves the two-seat test did not silently become a menu-only or one-pad no-op. The later source guest checkpoints capture the effect of hundreds of different actions, without asserting each action should produce a particular race result or fabricated original-game equality.

**Dimensions intentionally exercised:** varied legal masks (left, right, A, combined movement/A), durations, neutral gaps, simultaneous opposing inputs, repeated state evolution after legitimate source race entry, deterministic independent process replay, and independently ablated P1/P2 inputs. This is currently one ordinary 2P event family, not a 45-course sweep, source-visible graphics or a screen/controller test.

## First live-run diagnosis, 2026-10-11

[First manual workflow run 38182883707](https://github.com/gamesbyian/UR-Recomp/actions/runs/38182883707) **failed before a single stress guest process could execute**. The existing native producer and all its source-owned acceptance jobs passed, but both downstream stress shards ran on Ubuntu **22.04**, while the shared executable built under `ubuntu-latest` requires `GLIBC_2.38`. Both shard receipts faithfully recorded zero accepted cases and native process startup errors; the aggregate correctly failed. This is runner ABI skew, not evidence of a native gameplay determinism or dual-seat bug.

The stress job now matches its producing workflow's `ubuntu-latest` runner family, with an explicit ELF/linkage check (`ldd`) and minimum GLIBC 2.38 guard **before the case loop**. The workflow regression asserts the producer/consumer compatibility boundary. This repair does not change any input, guest WRAM, case acceptance, source identity, or missing-shard assertion. Re-dispatch **15 minutes** after the fix merges; no campaign execution pass has yet been established by this incident.

## Runtime and dispatch

The manual workflow runs the existing production native build once via a reusable workflow, then two independent Linux stress shards with at most two simultaneous runner jobs. Choose 15, 60 or 120 **wall minutes of actual trial work per shard**. The default is **15**, deliberately an initial smoke; after demonstrated run correctness, choose **120** for the extended workload. Each shard tests distinct seeds, starting with `base_seed + shard*1000003 + case_index`. Up to 3,000 unique trials per shard keep the campaign bounded even on unexpectedly fast hardware; each process has a 120-second watchdog and each shard a 145-minute hard runner limit. Every trial performs four native guest sessions, not four synthetic predictions.

The runner checks the wall deadline before starting a **new** trial. It does not sleep, idle or fabricate duration to fill the budget. It may finish earlier if 3,000 distinct trajectories are exhausted or if a material invariant failure is detected. **The report always lists actual elapsed seconds, actual unique streams, four-process count, and stop reason.** Do not call it a two-hour test unless those wall seconds demonstrate two hours of real activity. The underlying production acceptance workflow is allowed to finish its own source-owned QA tests before fan-out, which is useful but adds up-front time not counted as stress minutes.

Any two failures terminate a shard early, preserving the failing seed/index and bounded error text; private guest memory dumps remain on the ephemeral runner, not uploaded with possible personal state. Positive trials delete their private roots. One aggregate demands both named shard receipts, identical native executable and source/ROM/input hashes, complete and uniquely seeded surviving cases, true dual-seat and deterministic assertions, and absence of false release credit. Missing or failed witnesses go red. Results have 14-day retention. This is not an account-level scheduled self-runner: every launch remains explicit, avoids collisions with the four product/graphics/gameplay agents, and has no automatic trigger.

## Reproduction and advancement

For a failure, use the exact source revision, compiled native executable hash, shard, base seed and trial-index-derived seed. `tools/qa02_native_2p_seeded_endurance.py input_plan(seed)` and the same original input fixture recreate the control stream; the first divergent named dump identifies the failure window. Do not weaken the same-input SHA match or accept an ablated nonresponse just because a long campaign previously passed. Unit regressions in `tests/unit/test_qa02_native_2p_seeded_endurance.py` deliberately include fake stream/missing/invalid source and counterfactual negative outcomes; those tests are contract-only and cannot certify an actual native run.

Once a real 15-minute run completes, review throughput and output. The next investment should be genuine wider event and result-to-Records input generators owned by their respective gameplay and Modern lanes. **Do not infer QA-01 45-event acceptance, Windows/physical L5 certification, or complete-event scoring from native deterministic WRAM equality.**
