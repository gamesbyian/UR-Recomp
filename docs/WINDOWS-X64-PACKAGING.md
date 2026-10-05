# Windows x64 Portable Packaging

Status: portable consumer-package lifecycle is shippable and acceptance-covered. Windows x64 is the primary reference deliverable; an installer remains deferred.

## Shipping format for the current milestone

The first supported consumer package is a **portable extracted folder / ZIP**, not an installer.

This is deliberate. The portable package now separates immutable package payload from mutable user state without introducing installer semantics. `run-uniracers.cmd` selects one user-data root, defaulting to `%APPDATA%\\gamesbyian\\UR-Recomp` and overridable with `UR_RECOMP_USER_DATA_ROOT`. The pinned framework consumes the same root through `SNESRECOMP_USER_DATA_DIR`, so framework config, keyboard bindings and relative cartridge/profile saves move together. The mod catalog/resources remain package-relative while `SNESRECOMP_MOD_STATE_PATH` places mutable mod selections in the same user root. Modern host settings, profile catalog/onboarding data, practice helpers and completed-run history consume the same product root. ROM and mod payload lookup remains executable/package-relative.

Older portable folders are migrated deterministically on launch: package-local `config.ini`, `keybinds.ini`, `saves/` and legacy `mods/preloaded/state.toml` are copied only when the corresponding destination does not exist. Existing per-user state always wins, making migration idempotent and preventing an old extracted folder from overwriting newer settings or progress.

The shipping artifact is a deterministic `UR-Recomp-Windows-x64.zip` with a single `UR-Recomp-Windows-x64/` root. The ZIP uses normalized timestamps/path metadata and is reproducible byte-for-byte from identical payload and source revision.

The portable package contains:

- `UniracersSNESRecomp.exe`;
- the canonical `Uniracers_USA.sfc` used by this private project;
- generated `rom.cfg`;
- the staged `mods/` tree;
- `run-uniracers.cmd`, which keeps package payload lookup anchored to the extracted directory, resolves/probes the shared per-user mutable root, performs destination-wins legacy migration, supplies the packaged ROM, and emits stable startup diagnostic codes for package/root failures;
- `README.txt` documenting the per-user root, override and migration contract;
- `PACKAGE-MANIFEST.json` with SHA-256 and size for every packaged payload file.

`tools/assemble_windows_package.py` is the canonical assembler/verifier/archive producer. It removes stale output before assembly, fails closed on missing required inputs, writes deterministic metadata apart from the explicitly supplied source revision, verifies exact package contents against the manifest, writes a deterministic ZIP, and independently verifies every archived payload hash/size/path against the embedded manifest.

## Clean-install and upgrade acceptance

The Windows x64 workflow validates the **assembled package**, not only the CMake build tree.

Acceptance now covers:

1. build the shipping Windows x64 product with the canonical SDL3/ClangCL lane;
2. assemble and independently verify the clean package manifest and deterministic ZIP;
3. extract the ZIP to a fresh directory and launch it from an unrelated working directory through `run-uniracers.cmd`;
4. reach the stock main menu and the authoritative race-result checkpoint from the extracted consumer package;
5. prove fresh-run `config.ini`, `keybinds.ini` and `saves/` are created under an isolated user-data root, with no mutable state appearing in either the package directory or caller working directory;
6. seed representative framework settings, mod selections, Modern settings, bindings, profile catalog/profile state and completed-run data under that user root, replace the extracted package from the clean ZIP, and prove every seeded user-data artifact remains byte-identical;
7. construct a legacy portable folder containing package-local config, bindings and save data, launch against an empty user root, and prove all three migrate successfully while the legacy source remains untouched;
8. launch that legacy folder again after changing the migrated destination and prove destination-wins/idempotent migration does not overwrite newer user data;
9. exercise representative startup failures for missing ROM, missing runtime payload, unusable user-data root and invalid ROM, requiring the stable diagnostic codes documented in `WINDOWS-STARTUP-DIAGNOSTICS.md`;
10. re-verify the clean source package/archive and retain the deterministic ZIP as the consumer CI artifact.

The package remains self-contained with respect to immutable game/runtime payload. Build tools, repository source trees and checkout-relative paths are not runtime dependencies.

## Save-location boundary

The portable package no longer requires a writable extraction directory for ordinary mutable state. The default Windows root is `%APPDATA%\\gamesbyian\\UR-Recomp`; `UR_RECOMP_USER_DATA_ROOT` exists as an explicit portable/testing override. The launcher exports that resolved root to the framework and Modern host rather than maintaining feature-specific locations.

Package-owned executable, ROM, `rom.cfg`, mod payload and manifest files remain immutable inputs. User-owned config, bindings, cartridge/profile saves, mod selections, Modern settings/profile metadata, onboarding state, practice helper files and completed-run history remain outside the package. Replacing or deleting the extracted package therefore does not delete normal user progress.

An installer is still deferred. The storage/migration prerequisite is now satisfied, but installer selection, registration/uninstall behavior, signed release policy and installer-specific upgrade/rollback acceptance are separate work and must not be implied by the portable ZIP.

## Failure policy

Packaging failures are release failures. Missing executable, ROM, `rom.cfg`, staged mods, manifest mismatch, stale output contamination, or inability to boot the assembled package must fail CI rather than silently falling back to the build tree.
