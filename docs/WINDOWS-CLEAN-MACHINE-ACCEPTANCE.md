# Clean-machine Windows portable-release verification

Status: manual/VM acceptance helper. Final-`main` Windows CI now also invokes
this same verifier **without** `-Launch` against its emitted ZIP and sidecar,
which checks PowerShell 5.1 execution and Windows-native extraction on the
hosted Windows runner. No claim of a verified clean end-user machine is made
until the full interactive procedure runs outside that development runner.

## Purpose

`tools/Test-URRecompPortable.ps1` accepts the exact private portable Windows
release ZIP and its adjacent `.sha256` sidecar. It needs only **Windows 10/11
with Windows PowerShell 5.1**, no Python, Visual Studio, Git, CMake or compiler.

It checks:

1. canonical lowercase release checksum and archive filename agreement;
2. archive SHA-256 before any extraction;
3. extraction through Windows `Expand-Archive` into a **new** directory,
   never overwriting an existing package or save tree;
4. the fixed Windows package format and manifest, payload file count/path,
   SHA-256 and byte length for every extracted executable/ROM/mod/resource,
   canonical package-relative `rom.cfg`, README provenance and no mutable
   saves/config in the package;
5. optionally, an actual launch through `run-uniracers.cmd` from an unrelated
   working directory, with mutable state directed to an isolated folder
   alongside (outside) the extracted package; after the game exits normally,
   verifies the expected user config/bindings/mod-state/saves and startup log
   exist and re-hashes all immutable package files.

## Run it on an actual clean Windows installation

The successful `ur-recomp-windows-x64-portable` workflow artifact includes
the ZIP, its `.sha256` and `Test-URRecompPortable.ps1` together. Copy all
three files to a throwaway Windows machine or clean VM. From Windows PowerShell:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\Test-URRecompPortable.ps1 `
  -Archive .\UR-Recomp-Windows-x64.zip `
  -Checksum .\UR-Recomp-Windows-x64.zip.sha256 `
  -Destination "$env:TEMP\UR-Recomp clean package probe"
```

The destination **must not already exist**. To also verify actual player
startup, repeat with a different destination and `-Launch`. The game will
open normally; reach the main menu, enter an ordinary race, check usable
video/audio/input, then exit from the game. The script checks that the game
exits successfully, that mutable state is isolated, and that its immutable
payload remains byte-identical. Pass `-InputScript <path>` instead of
`-Launch` to supply an existing deterministic guest-input script, but do
not confuse successful script exit with human visual/audio acceptance.

The output prints `UR_PORTABLE_ARCHIVE_VERIFIED`,
`UR_PORTABLE_MANIFEST_VERIFIED`, and on a successful run
`UR_PORTABLE_REAL_WINDOWS_LAUNCH_EXITED_OK`, ending in
`UR_PORTABLE_CLEAN_MACHINE_PACKAGE_OK`. Retain the full console transcript,
the build revision and archive hash, test Windows version, display adapter /
driver, audio and controller environment, and the isolated user root's
`diagnostics/startup.log` (review for personal paths before sharing).
These constitute the independent tester's evidence packet.

## Interpretation

This is deliberately an offline, self-contained consumer-artifact check.
It cannot prove the physical machine was clean merely because it ran, and
does not claim complete graphics/audio/controller coverage from a scripted
or headless invocation. A native window on an actual Windows desktop and
usable devices must be exercised before calling that environment accepted.
The final-`main` Windows gate independently covers deterministic race-result
behavior, representative injected startup failures, whole-folder upgrade and
legacy migration. Neither suite substitutes for the other.

Because this is a private preservation project, do not publish a packaged
ROM in public GitHub Releases or attach proprietary ROM bytes to support
reports. Keep release ZIP distribution private and lawful.
