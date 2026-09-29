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


## 2026-09-28 — Deterministic input harness reaches recovered main-menu state

The native smoke has been extended with a separate frame-synchronous `--script` route derived from Dessyreqt's recovered 2014 full-game bot rather than wall-clock key injection.

Observed so far:
- existing native build, boot and frame-300 visual validation remain green before the new input assertion;
- WRAM `7E:009F` reaches `0xD7` at simulated frame 446, independently reproducing the bot's historical `mainMenu = 215` label on the canonical USA ROM/runtime;
- the first simplified script then pressed A immediately, but did not reach the bot's `onePlayerSelect = 0x3C` state within the timeout;
- re-reading the bot shows that simplification omitted a real branch: on the main menu the bot reads `7E:009B` (`selectedOption`), pulses Up while it is nonzero, and presses A only after option 0 is selected.

Run 36504420741 resolved that diagnostic:

- at frame 446, `currentMenu = 0xD7`, `selectedOption = 0x00`, row `0x00`, column `0xFD`;
- after the one-frame A press plus 30 guest frames, `currentMenu` is still `0xD7` and `selectedOption` is still `0x00`, but the menu column byte has changed to `0x04`.

This rules out the bot's "move Up until option zero" branch for this clean boot and shows that the injected A reaches live guest/menu state. The remaining seam is acceptance timing: the historical bot continues to pulse A every other frame for as long as `mainMenu` remains active, whereas the first native test pressed it exactly once on the first frame where `0xD7` appeared.

The next committed test therefore leaves one second (60 guest frames) after first observing `0xD7`, captures a settled-menu snapshot, then sends a fresh one-frame A edge.

Interpretation: deterministic guest-observed menu navigation is now partly reproduced. The current blocker is one concrete input-ready transition, not generic controller delivery, wrong main-menu selection, or native execution.
