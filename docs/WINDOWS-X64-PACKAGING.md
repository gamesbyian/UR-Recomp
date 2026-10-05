# Windows x64 Portable Packaging

Status: first consumer-package contract in progress. Windows x64 is the primary reference deliverable.

## Shipping format for the current milestone

The first supported consumer package is a **portable extracted folder / ZIP**, not an installer.

This is deliberate. The pinned desktop host currently anchors framework `config.ini`, `keybinds.ini` and cartridge save files to the executable directory. That is appropriate for a private portable build extracted somewhere writable, but it is not yet a safe basis for an installer under `Program Files`. A future installer must first redirect all mutable framework state to a per-user data root and prove migration/upgrade behavior.

The shipping artifact is a deterministic `UR-Recomp-Windows-x64.zip` with a single `UR-Recomp-Windows-x64/` root. The ZIP uses normalized timestamps/path metadata and is reproducible byte-for-byte from identical payload and source revision.

The portable package contains:

- `UniracersSNESRecomp.exe`;
- the canonical `Uniracers_USA.sfc` used by this private project;
- generated `rom.cfg`;
- the staged `mods/` tree;
- `run-uniracers.cmd`, which anchors launch to the extracted package directory, supplies the packaged ROM, checks the executable/ROM/`rom.cfg` are present, and returns a clear deterministic error if the package is incomplete;
- `README.txt` with the writable-extraction requirement;
- `PACKAGE-MANIFEST.json` with SHA-256 and size for every packaged payload file.

`tools/assemble_windows_package.py` is the canonical assembler/verifier/archive producer. It removes stale output before assembly, fails closed on missing required inputs, writes deterministic metadata apart from the explicitly supplied source revision, verifies exact package contents against the manifest, writes a deterministic ZIP, and independently verifies every archived payload hash/size/path against the embedded manifest.

## Clean-install acceptance

The Windows x64 workflow must validate the **assembled package**, not only the CMake build tree.

Acceptance is:

1. build the shipping Windows x64 product with the canonical SDL3/ClangCL lane;
2. assemble the portable package from the Release output;
3. verify the clean package manifest, create the deterministic ZIP, and verify the archive independently;
4. extract that ZIP to a fresh test directory and launch the extracted package from an unrelated working directory through `run-uniracers.cmd`;
5. reach the stock main menu using only files inside the package plus the external acceptance script;
6. prove first-run `config.ini` and `keybinds.ini` are created beside the packaged executable, not in the caller working directory;
7. deliberately remove the packaged ROM and prove the launcher exits with code 2 plus a clear missing-file diagnostic rather than falling through to a cryptic runtime failure;
8. re-verify the untouched clean source package and ZIP after the extracted test copy has generated runtime state, proving the shipping artifact was not contaminated by acceptance;
9. retain the deterministic ZIP as the consumer CI artifact for inspection.

The package must remain self-contained with respect to game/runtime payload. Build tools, repository source trees and checkout-relative paths are not allowed runtime dependencies.

## Save-location boundary

For this portable milestone, executable-directory framework state is accepted **only because the package explicitly requires extraction to a user-writable directory**. Modern host profile metadata/run history can continue using the platform preference directory according to the existing product contracts.

Do not call a Program Files installer supported until framework config/keybind/save placement has a proven per-user location and an upgrade/migration policy.

## Failure policy

Packaging failures are release failures. Missing executable, ROM, `rom.cfg`, staged mods, manifest mismatch, stale output contamination, or inability to boot the assembled package must fail CI rather than silently falling back to the build tree.
