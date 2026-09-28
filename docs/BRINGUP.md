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
