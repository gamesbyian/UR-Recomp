# Bring-up Log

Chronological record of attempts to execute Uniracers/Unirally under the recompilation stack. Keep this empirical: what happened, what changed, and what evidence supports the conclusion.

## 2026-09-28 — Project scaffold

- Repository created as `gamesbyian/UR-Recomp`.
- Current SNESRecomp bootstrap pin selected: `cd5875cbdaf19f5e324272b1f8051d671fce9215`.
- No ROM committed.
- No compatibility claim yet.
- First technical objective: analyzer reconnaissance, then first boot.

### Known prospective compatibility concern

Uniracers has historically required special emulator handling around OAM/HDMA behavior. Treat this as a test target, not as proof the recomp runtime will fail.

### Working rule

Generated C is disposable. Permanent fixes belong in configuration, hand-authored integration code, or the underlying runtime/framework.

## 2026-09-28 — ROM baseline established

GitHub Actions run 36479306630 fingerprinted the tracked canonical ROM and ran the pinned framework's cartridge probe.

Observed:

- file size: 2,097,152 bytes (2 MiB)
- CRC32: `383858c7`
- SHA-1: `cb249cf7301bdd985e6fe4bc4c942bf4f86d7d83`
- SHA-256: `859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478`
- MD5: `1066cfd0c6be4dbdfede796751e801c5`
- mapping: LoROM
- region: USA
- coprocessor: none
- SRAM: 8 KiB
- reset vector: `$8858`
- SNES header checksum: valid

This clears the basic cartridge-compatibility gate for SNESRecomp's documented standard LoROM support. It does not yet establish game execution compatibility.


## 2026-09-28 — Native smoke result reclassified as harness error

The latest native-build-smoke run successfully completed ROM verification, project scaffolding/generation, and the build step. However, inspection of the workflow log shows the "Locate executable" fallback selected:

`build/CMakeFiles/3.31.6/CompilerIdCXX/a.out`

That is CMake's compiler-identification test binary, not the generated Uniracers executable. The subsequent exit status 164 therefore does **not** establish a game-runtime failure.

Evidence:
- workflow run 36484477962;
- steps "Scaffold, generate and build" and "Locate executable" succeeded;
- the log explicitly prints the selected CompilerId binary before the smoke step.

Immediate correction:
1. make executable discovery target the actual project output;
2. remove the permissive "first executable in build tree" fallback;
3. fail the workflow if the expected game executable cannot be found;
4. rerun the smoke test before drawing any runtime conclusions.

Current interpretation: build viability is promising, but first boot has not yet genuinely been tested.


## 2026-09-28 — Strict executable discovery exposes an earlier build dependency failure

Workflow run 36490913616 removed the permissive executable fallback and required the scaffold's expected game target, `build/UniracersSNESRecomp`.

Observed:
- ROM verification succeeded.
- Code generation succeeded and emitted eight generated C files.
- the scaffold's internal build wrapper reported a warning rather than propagating configure failure;
- CMake failed while configuring SDL3 because the Ubuntu runner lacked the XScreenSaver development package: `Couldn't find dependency package for XSCRNSAVER`;
- consequently no game executable existed, and strict discovery failed as designed;
- no native Uniracers code was launched, so there is still no genuine runtime result.

Interpretation: this is a CI/toolchain dependency failure, not a game or SNESRecomp compatibility failure. The workflow now installs `libxss-dev` and has been rerun. Keep strict target discovery in place.


## 2026-09-28 — First genuine native execution

Workflow run 36491383506 installed the remaining SDL/X11 build dependencies (`libxss-dev` and `libxtst-dev`), built the generated native target, selected the exact executable `build/UniracersSNESRecomp`, and launched it against the canonical USA ROM under Xvfb.

Observed host milestones:
- canonical 2 MiB ROM resolved and loaded;
- internal cartridge name reported as `UNIRACERS`;
- `SnesInit: ok`;
- SDL/X11 window created at 960×720;
- renderer initialized;
- 32 kHz stereo audio device opened;
- main loop entered;
- first frame simulated;
- first audio callback serviced;
- process remained alive until the intentional 12-second timeout, yielding `SMOKE_RESULT=alive_after_12s`.

No crash or unsupported-hardware failure was observed in this smoke interval. The workflow does not yet prove that the title/logo is visually correct because Xvfb output was not captured or compared.

Evidence: GitHub Actions run 36491383506.

Interpretation: native execution is now real and stable enough to advance from “can the game target launch?” to visible-frame and input milestones. The first observable failure, if any, lies after initialization/first-frame execution rather than in build/scaffold startup.


## 2026-09-28 — Native title screen visually verified

Workflow run 36493358927 extended the strict native smoke with the pinned runtime's diagnostic presented-frame capture.

Observed:
- the exact generated `UniracersSNESRecomp` executable again remained alive for the intentional 12-second timeout;
- the host produced 477 presents spanning simulated frames 1–477;
- presented output is black through frame 123, then begins a visible transition at frame 124;
- a diagnostic capture at simulated frame 300 is a 256×224 RGB frame with 250 distinct RGB colors and 57,193/57,344 non-black pixels;
- the captured PPM SHA-256 is `d5c5afd0259d632773bb33c6106d377d2ce1f6a6bf140140b6e1e13e1cd5424b`;
- direct visual inspection shows a coherent stock Uniracers title screen: UNIRACERS logo, rendered unicycle/rider artwork, rainbow track, trademark and Nintendo copyright are all present rather than corrupted or blank.

Evidence:
- GitHub Actions run 36493358927;
- temporary workflow artifact `uniracers-native-frame` (artifact 11001868327, seven-day retention);
- artifact archive digest `sha256:e2d066e765dce16f420df3b31044dd3c4dcb5fd4965ce9739d2dcb5c70a196bc`;
- deterministic screenshot capture is encoded in `.github/workflows/native-build-smoke.yml`.

Interpretation: basic native CPU/PPU/DMA/audio bring-up reaches recognizable stock presentation. This does not yet establish pixel-accuracy against a reference emulator, controller/menu progression, race simulation, or the two-player active-display OAM path.

Next milestone: add deterministic input and/or reference-frame comparison to reach title/menu selection and actual race gameplay without guest-state edits.


## 2026-09-28 — Screenshot smoke timing hardened after branch reconciliation

While reconciling the repository-hygiene/tooling branch, native run 36493652126 again built and launched the correct `UniracersSNESRecomp` executable, but the 12-second wall-clock timeout expired before simulated frame 300 on the slower CI run, so the screenshot validator found no file. The boot step itself remained alive and successful.

The smoke timeout was increased to 20 seconds without changing the requested capture frame or validation criteria. Run 36495039455 then completed successfully.

Interpretation: the branch run exposed harness timing sensitivity rather than a game/runtime regression. Frame 300 remains the visual assertion; the extra wall-clock budget only gives CI enough time to reach it reliably.


## 2026-09-28 — Deterministic menu input reaches one-player rider select

The native smoke has been extended with a separate frame-synchronous `--script` route derived from Dessyreqt's recovered 2014 full-game bot rather than wall-clock key injection.

Verified observations:
- existing native build, boot and frame-300 visual validation remain green before the new input assertion;
- WRAM `7E:009F` reaches `0xD7` at simulated frame 446, reproducing the bot's historical `mainMenu = 215` label on the canonical USA ROM/runtime;
- run 36504420741 captured `7E:009B = 0x00` at that state, matching the bot's condition for selecting the one-player entry;
- a one-frame A pulse sent immediately on first observing `0xD7` was ignored: 30 frames later the menu remained `0xD7`;
- run 36504768959 instead waited 60 guest frames after first observing `0xD7`, then sent the same one-frame A pulse;
- that delayed pulse succeeded: after the pulse `7E:009F = 0x3C`, reproducing the bot's `onePlayerSelect = 60` state.

Interpretation: SNESRecomp scripted controller delivery works. The important nuance is that the historical menu-state byte becomes visible before the corresponding scene is ready to accept its first confirmation edge. The recovered bot tolerated this naturally because it reevaluated state and retried inputs every frame; a linear deterministic script needs an explicit readiness delay or equivalent stateful retry policy.

The current committed route applies the same 60-frame settle after reaching `0x3C`, confirms the default rider, then waits only for `currentMenu != 0x3C` and captures the resulting state. This deliberately avoids assuming whether a clean SRAM route next enters the bot's `onePlayerTours1 = 0x6D` or `onePlayerTours2 = 0x10`.

Evidence:
- workflow run 36504420741;
- workflow run 36504768959;
- `tests/input/reach-first-race.script`;
- `.github/workflows/native-build-smoke.yml`;
- recovered bot source `references/imported/tas-bots/uniracers-tabletop-bot-2014.lua`.

Next milestone: classify the post-rider menu state, then extend the settled state-driven route through tour, track and now-playing selection to `7E:0313 == 1` race state.


### Follow-up — native frontend chain reaches track selection

Run 36505156490 extended the settled route through rider confirmation. Run 36505588585 then extended it through the first tour selection. Both completed the deterministic route step successfully.

Observed settled chain on the canonical USA ROM:

- `main-menu-ready`: `currentMenu = 0xD7`, `selectedOption = 0x00`;
- `rider-select-ready`: `currentMenu = 0x3C`, row `0x00`, column `0x06`;
- `tours-ready`: `currentMenu = 0x6D`, `selectedOption = 0x00`, row `0x00`, column `0x07`;
- after confirming the current first tour and allowing the destination to settle: `currentMenu = 0xF6`, `selectedOption = 0x00`, row `0x00`, column `0x01`.

These independently reproduce four Dessyreqt frontend labels under native execution: `mainMenu = 0xD7`, `onePlayerSelect = 0x3C`, `onePlayerTours1 = 0x6D`, and `onePlayerTracks = 0xF6`.

The route uses only controller input plus guest-observed WRAM conditions. No menu/game state is poked. The conservative 60-guest-frame settle remains in place before the first confirm in a newly reached scene because first visibility of the menu byte is not equivalent to input readiness.

Evidence:
- GitHub Actions run 36505156490, artifact 11006149797;
- GitHub Actions run 36505588585, artifact 11007410671;
- `tests/input/reach-first-race.script`;
- recovered bot source `references/imported/tas-bots/uniracers-tabletop-bot-2014.lua`.

Next milestone: settle at `0xF6`, confirm the default first track, and capture the resulting state before treating the bot's `onePlayerNowPlaying = 0x16` label as locally verified.


### Follow-up — native race entry and reference replay are green

Run 36506120930 completed the full native deterministic route with controller input only.

Native checkpoints:
- frame 506: main menu settled, `7E:009F = 0xD7`;
- frame 569: rider select settled, `0x3C`;
- frame 639: first tours page settled, `0x6D`;
- frame 703: track select settled, `0xF6`;
- frame 769: post-track screen is `0x16`, confirming Dessyreqt's `onePlayerNowPlaying` label;
- frame 984: `7E:0313 = 0x01`, confirming active race state;
- frame 1044: settled `race-entered` dump produced and the route exited cleanly.

The same script was then replayed unmodified through `snesref` using the pinned Snes9x libretro core in run 36506281320. That reference run also reached every checkpoint and race state successfully:

- main menu settled at frame 500;
- rider select at 563;
- tours at 633;
- tracks at 696;
- now-playing at 761;
- `inRace = 1` at frame 975;
- settled race dump at frame 1035.

All checkpoint fields printed by the workflows agree across native and reference execution: current menu, selected option, row, column, track byte and race-active byte. The reference path reports Snes9x's existing `Applied Uniracers hack.`, so this successful replay establishes a useful oracle path but does not by itself prove the native runtime reproduces the historical active-display OAM behavior correctly.

Interpretation:
- Phase 2's title/menu operation gate is cleared;
- Phase 3's "reach one-player race" milestone is cleared;
- Dessyreqt's `onePlayerNowPlaying = 0x16` and `inRace = 1` labels are now locally verified;
- native/reference frontend timing differs by several frames while the observed state sequence agrees.

Next milestone: compare the complete WRAM checkpoint dumps byte-for-byte in one differential job, record the first differing offsets at each scene, and then extend deterministic control into actual race movement/physics.


### Follow-up — first full WRAM differential narrows race-entry mismatch to seven bytes

Combined differential workflow run 36508095522 built both native SNESRecomp and pinned Snes9x/snesref, ran the same `reach-first-race.script`, and compared all seven complete 128 KiB WRAM dumps.

Differing-byte counts:
- `main-menu-ready`: 19 / 131072;
- `rider-select-ready`: 252;
- `tours-ready`: 250;
- `tracks-ready`: 254;
- `after-track-confirm`: 258;
- `now-playing-ready`: 255;
- `race-entered`: **7**.

The settled race-entry differences are:
- `0x00C6`: native `04`, Snes9x `1D`;
- `0x00C8`: native `03`, Snes9x `01`;
- `0x00C9`: native `02`, Snes9x `03`;
- `0x01D1–0x01D4`: native `90 13 20 80`, Snes9x `00 00 00 00`.

The contiguous `0x01D1–0x01D4` block first becomes visibly divergent by rider-select and remains present through later captured frontend states and race entry. The three `0x00C6/0x00C8/0x00C9` bytes vary across checkpoints and are plausible timing/animation state, but their semantics are not yet assigned.

Interpretation: native/reference semantic race entry is extremely close in WRAM after the 60-frame race settle despite the nine-frame route timing offset. The next high-value discriminator is the origin and meaning of writes to `0x01D1–0x01D4`, followed by characterization of the three remaining low-WRAM differences.

Evidence:
- workflow run 36508095522;
- artifact 11007769197;
- `tools/compare_wram_checkpoints.py`;
- `.github/workflows/deterministic-differential.yml`.


### Follow-up — seven-byte race-entry differential explained

Trace workflow run 36511207129 completed successfully and reached `7E:0313 = 1` at native frame 984 while preserving the shared controller-only route.

At that point:
- CPU native mode: `E = false`;
- stack pointer: `SP = $01FF`;
- `$01D1–$01D4 = 90 13 20 80`;
- reverse-debug writer history reports zero ordinary WRAM writes to `$01D1–$01D4`.

The four-byte block sits far below the live top of the native-mode stack. Earlier full-WRAM checkpoints also showed many transient differences elsewhere in page `$01xx` that disappeared once race entry settled. This combination resolves `$01D1–$01D4` as stale stack history rather than live game state.

The other three final differences are active timing/phase counters:
- `$00C6` is decremented once per frame by `bank_80_FADF_M1X0`; the trace records 253 writes before race entry.
- `$00C8` cycles through a short per-frame countdown in interpreted code at `$00:8588`; 286 writes are recorded.
- `$00C9` advances on a seven-frame cadence through the same interpreted routine; 45 writes are recorded.

Their differing values at the settled checkpoint are consistent with the previously measured native/reference route timing offset, not a semantic gameplay-state split.

Interpretation: the first-race native/reference comparison now has no unexplained persistent gameplay-state divergence in WRAM. Full-WRAM equality should not be required across runtimes for stack residue and free-running phase counters; future regression assertions should target confirmed semantic invariants and event-relative behavior.

Evidence:
- GitHub Actions run 36511207129;
- artifact 11009305157;
- `tools/trace_native_wram_writers.py`;
- `docs/RESEARCH-LEDGER.md` entries R-SEED-014 and R-SEED-015.

Next milestone: extend the shared fixture into controlled race behavior and validate the recovered player-state labels for acceleration, jump, rotation, landing, collision and finish.


## 2026-09-28 — Trace harness failure lessons promoted

The race-entry writer investigation exposed two repeatable harness hazards before succeeding in run 36511207129.

1. **Debug-server handshake assumption.** The Python probe initially waited for a greeting line after TCP connect. SNESRecomp's trace server sends no greeting; it is command/response only. The wait caused repeated client timeouts/reconnects and made the server repeatedly drop the previous connection.
2. **Wall-clock budgeting under trace instrumentation.** After the handshake fix, the traced game followed the deterministic route correctly through frame 829 but the workflow's 90-second outer timeout killed the healthy host before race entry. The final probe batches early stepping, respects the server's bounded synchronous `step N` wait, and gives the host 240 seconds of wall-clock headroom.

These are harness/tooling failure modes, not game-runtime failures. Agent-facing guardrails are now in `AGENTS.md`; operational guidance is in `docs/VALIDATION.md`.
