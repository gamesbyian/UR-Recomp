# Baldosa native execution and read-only presentation bridge: measured experiment

Status: October 9, 2026, experimental CI PR #1068. Sources pinned to Baldosa game 10b864b9d14a7b7416dd909eb7b054c88faef101 and framework 075fbe4c8e0d97b0013be541795c39cb644a9709. Exact USA ROM SHA256 859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478. Ubuntu 22.04 / SDL2 / Xvfb. No official course acceptance gate promoted.

## Actually executed

GitHub Actions run 37987324413 proves:

- Ema's unmodified native generated game compiles and links, with 92 generated C translation units reported at configure time.
- One-player Dragster script completes its own route after **5,447 guest frames**, with final WRAM/OAM/SRAM checkpoint, exit 0. This is **not** yet an independently verified original/native result comparison.
- Two-player split-screen script exits 0 after **2,473 frames**, with go, t060, t120, t240 and t480 guest WRAM/OAM/SRAM checkpoints. This is **not** independently verified original/native P2 pixel parity.
- Unmodified Zoom Zoo script enters active gameplay at frame **1,812** but remains active through **17,390** frames and times out, exit 124, after 95 seconds. An earlier 180-second attempt also timed out. Precise repro and bounded next discriminator: **issue #1071** at https://github.com/gamesbyian/UR-Recomp/issues/1071. DO NOT count it as a complete Circuit.
- The same CI run builds a second Baldosa executable with an external C-ABI after_run_frame hook that links **the actual UR-Recomp racer_guest_snapshot.cpp and racer_replacement_selector.cpp** from native/presentation/. The hook observes both racers' 128 KiB guest WRAM without guest writes. The two-player script again exits 0 and **every one of the 2,473 guest frame WRAM CRCs is identical** to unmodified Baldosa. This is a non-invasive state-consumption and integration proof, not a full host or graphics transfer.

Full logs: https://github.com/gamesbyian/UR-Recomp/actions/runs/37987324413

## Engineering outcome

The Ema-first native guest is an independently reproducible working baseline for 1P and split-screen input. We have proved our own racer-state reader can link into its host and observe a full 2P route without changing observed WRAM execution. That is an important piece of a future 4K/HD/Modern remaster foundation.

However, none of the full Modern root, controller-ownership hooks, 4K real world extension, 2P source-visible HD composition, storage/records/ghosts, or the full event-family original/native settled-result checks have been carried across. Do **not** select a production engine solely on this evidence.

## Efficient follow-up

1. Keep the upstream native 1P and 2P smoke cases. The automated Zoom Zoo route has a known unbounded *terminal menu* wait; the ordinary PR smoke now runs a **bounded, nonterminal** copy of the same route with original menus/movement preserved, plus after-drive WRAM/OAM dumps. It explicitly earns 0 release event completions.
2. Narrow the injected C++ include path to the one bridge source. The initial experiment accidentally rebuilt 219 objects when adding a target-wide include flag; source-local includes avoid unnecessary recompilation on subsequent probes.
3. Validate actual P1/P2 OAM sprite source-visibility against pinned Snes9x evidence and our current QA-08 material.
4. Attempt one existing source-derived HD fallback renderer or +24 native widening presenter on top of the proven after_run_frame/prepare_frame/draw_frame host seams. Do not rebuild the Modern host or invent guest rules.
5. Run a separate narrow B path test against the existing patched UR-Recomp runtime; select the path by an actual controller-first, playable, persistent Modern race and cost of maintaining host hooks.

Original/native complete-event denominator remains **0/45 USA** until independently admitted result parity.
