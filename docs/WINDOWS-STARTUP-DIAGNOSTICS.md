# Windows Startup Diagnostics Contract

Status: the portable Windows x64 startup-diagnostics contract is implemented at every currently observable release-facing bootstrap seam. Final-main assembled-package acceptance owns the end-to-end regression. Installer/signing/uninstall behavior remains outside this lane.

## Implemented consumer-package contract

The assembled Windows x64 package and pinned desktop host classify these startup failures without adding another launcher, persistence authority or logging framework:

- `UR-STARTUP-ROM-MISSING`: the packaged ROM is absent;
- `UR-STARTUP-ROM-INVALID`: the explicit packaged ROM fails the framework's generated ROM-identity check;
- `UR-STARTUP-SAVE-ROOT`: the shared per-user root is invalid, unavailable, inside the extracted package, has a required path type conflict, cannot be created/written, cannot complete legacy migration, or cannot be adopted by the host;
- `UR-STARTUP-RUNTIME-DATA`: the executable, `rom.cfg`, staged mod payload, or a non-empty `mods/` payload is missing;
- `UR-STARTUP-VIDEO`: SDL video initialization, window creation, or the selected renderer initialization fails;
- `UR-STARTUP-AUDIO`: SDL audio initialization or audio-device open fails;
- `UR-STARTUP-CONTROLLER`: SDL controller-subsystem initialization fails after video and audio initialization have already succeeded.

`UR-STARTUP-CONTROLLER` owns that remaining fatal SDL controller-init seam and cannot swallow ROM, save-root, runtime-data, video or audio failures. No currently classified consumer-package bootstrap path uses `UR-STARTUP-UNKNOWN`; other later crashes continue to use the existing breadcrumb/crash-reporting pipeline until a concrete release-facing startup class justifies another stable code.

`run-uniracers.cmd` owns package-presence, resolved user-root, migration and startup-log setup. The pinned desktop host owns ROM identity plus the real SDL/video/audio/controller initialization seams. Modern and Authentic modes use the same bootstrap because mode-specific guest/product behavior has not started yet.

## Purpose and ownership boundary

The Windows consumer build must fail usefully when host-owned startup prerequisites are unavailable or invalid without turning diagnostics into another gameplay state model.

Startup diagnostics may observe and report executable/build identity, Windows architecture, the resolved package/user-data paths, ROM validation status, SDL/video/audio/controller initialization, required runtime/data-file presence, host-owned persistence creation/read/write failures, and legacy migration stage/commit failures.

They must not repair, rewrite or synthesize guest SRAM, progression, replay, ghost, physics, timing or course state. They must never record ROM bytes, SRAM contents, profile names, controller input streams or run-artifact payloads.

## Player-facing behavior

Each classified fatal failure emits exactly one concise diagnosis containing the stable `UR-STARTUP-*` code, a plain-English explanation, the relevant path/subsystem when safe and useful, and one recovery action. Stack traces and low-level SDL text remain supporting diagnostics rather than the primary player-facing message.

Codes are product API. Tests and future support material may depend on them, so renaming requires an explicit compatibility decision.

## Retained startup log

After the user-data root has been validated as writable, the launcher creates one bounded log for the process at:

`<user-data-root>/diagnostics/startup.log`

The file is overwritten once at process launch rather than accumulated indefinitely. The launcher seeds deterministic fields:

- `schema=ur-startup-log-v1`;
- packaged source/build revision;
- `architecture=x64`;
- bootstrap subsystem;
- resolved package root;
- resolved user-data root;
- initial result.

A classified launcher or host failure appends only its stable code, subsystem and fatal result. Host startup uses the same path through `SNESRECOMP_STARTUP_LOG`. A normal host exit appends the process exit status.

If the user-data root or diagnostics directory cannot be created, diagnostics fall back to the one player-facing/stderr diagnosis rather than trying alternate log locations recursively. Failures that occur before a writable root exists therefore legitimately have no retained log.

## Acceptance

Final-main Windows package acceptance uses temporary directories and synthetic failure conditions only. It covers:

1. valid normal startup reaching the established frontend/race baseline;
2. missing packaged ROM -> `UR-STARTUP-ROM-MISSING`;
3. synthetically modified ROM bytes -> `UR-STARTUP-ROM-INVALID`;
4. unavailable/relative/package-local/unwritable user-data roots and required-path type conflicts -> `UR-STARTUP-SAVE-ROOT`;
5. deliberately missing or empty runtime payload -> `UR-STARTUP-RUNTIME-DATA`;
6. a deliberately invalid SDL video driver -> `UR-STARTUP-VIDEO`;
7. a deliberately invalid SDL audio driver -> `UR-STARTUP-AUDIO`;
8. the controller-initialization classification remains pinned by the focused package/unit contract to `UR-STARTUP-CONTROLLER` / `subsystem=controller` through the same `StartupFail` log path; the assembled-package lane does not invent an unstable Windows/SDL fault-injection knob solely to force that subsystem to fail;
9. exactly one player-facing stable diagnosis for each runtime-injected classified failure;
10. where the user-data root is writable, one `diagnostics/startup.log` containing deterministic build/subsystem/path/result fields and exactly one matching fatal code entry.

The harness never needs to add proprietary ROM material beyond the repository's existing private canonical package input, and synthetic invalid-ROM acceptance mutates only a temporary copy.

## Closure boundary

This diagnostics lane is closed at the currently observable bootstrap seams. Reopen it only when a new real initialization failure class reaches the consumer package without a useful stable diagnosis, or when final-main package acceptance demonstrates that one of the implemented classifications/log guarantees is incorrect.

Installer selection, signing, registration, uninstall, installer rollback, telemetry, generalized crash handling and later in-session device-loss UX are separate work.
