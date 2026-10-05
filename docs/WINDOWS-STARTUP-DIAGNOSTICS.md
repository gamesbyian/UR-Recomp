# Windows Startup Diagnostics Contract

Status: package-bootstrap subset implemented and acceptance-covered; video/audio/log presentation remains deferred.

## Implemented portable-package subset

The assembled Windows x64 package now classifies four high-value startup failures without adding a second launcher or persistence authority:

- `UR-STARTUP-ROM-MISSING`: the packaged ROM is absent;
- `UR-STARTUP-ROM-INVALID`: the explicit packaged ROM fails the framework's generated ROM-identity check;
- `UR-STARTUP-SAVE-ROOT`: the shared per-user root cannot be created/written or the framework cannot adopt it;
- `UR-STARTUP-RUNTIME-DATA`: required executable, `rom.cfg` or staged mod payload is absent.

`run-uniracers.cmd` owns package-presence and user-root checks. The pinned desktop host owns the ROM-identity and final mutable-root adoption checks. Windows package acceptance deliberately breaks each representative prerequisite and requires the corresponding stable code.

`UR-STARTUP-VIDEO`, `UR-STARTUP-AUDIO`, optional retained startup-log presentation, and a generic `UR-STARTUP-UNKNOWN` catch-all remain open. Existing host breadcrumbs/crash reporting continue to own those failures until a similarly narrow implementation is available.

## Purpose

The Windows consumer build must fail usefully when host-owned startup prerequisites are unavailable or invalid, without turning diagnostics into another gameplay state model. This contract owns only host/bootstrap failures before authoritative guest execution is established.

## Ownership boundary

Startup diagnostics may observe and report:

- executable/build identity;
- host product-state/save root resolution;
- SDL/video/audio/controller initialization;
- required runtime/data-file presence;
- user-supplied ROM discovery and validation status;
- creation/read/write failures for host-owned profile/settings/run directories.

They must not repair, rewrite, or synthesize guest SRAM, progression, replay, ghost, physics, timing, or course state. Existing fail-closed codecs remain authoritative for those surfaces.

## Player-facing behavior

For a recoverable startup failure, emit one concise message containing:

1. a stable machine-readable error code;
2. a plain-English explanation;
3. the exact path or subsystem involved when safe and useful;
4. one actionable recovery instruction.

Do not expose stack dumps as the primary UI. Detailed diagnostics belong in a retained text log.

The initial stable codes are:

- `UR-STARTUP-ROM-MISSING`
- `UR-STARTUP-ROM-INVALID`
- `UR-STARTUP-SAVE-ROOT`
- `UR-STARTUP-VIDEO`
- `UR-STARTUP-AUDIO`
- `UR-STARTUP-RUNTIME-DATA`
- `UR-STARTUP-UNKNOWN`

Codes are product API: tests and future support material may depend on them, so renaming requires an explicit compatibility decision.

## Diagnostic log

Create at most one startup log per process in the resolved host diagnostics directory. If that directory itself cannot be created, fall back to stderr and the player-facing error surface rather than recursively attempting alternate persistence.

The log should contain deterministic fields where available:

- product/build revision;
- Windows architecture;
- startup error code;
- failing subsystem;
- relevant resolved paths;
- ROM validation result without embedding ROM bytes;
- SDL initialization result;
- final fatal/recoverable disposition.

Do not log controller input streams, SRAM contents, profile names, run artifacts, ROM bytes, or unrelated filesystem inventory.

## Acceptance

A Windows release candidate is not startup-diagnostics-complete until automated acceptance covers at least these fresh-process cases:

1. valid normal startup reaches the established playable frontend/race baseline with no startup error;
2. missing ROM exits cleanly with `UR-STARTUP-ROM-MISSING`;
3. wrong ROM bytes exit cleanly with `UR-STARTUP-ROM-INVALID`;
4. unwritable host save root exits cleanly with `UR-STARTUP-SAVE-ROOT`;
5. deliberately missing required runtime data exits cleanly with `UR-STARTUP-RUNTIME-DATA`;
6. every failure produces exactly one stable player-facing diagnosis and, where writable, one bounded diagnostic log;
7. Authentic and Modern modes share the same bootstrap/error contract because no guest simulation has started yet.

The acceptance harness must use temporary directories and synthetic invalid data. It must never require committing or uploading proprietary ROM bytes.

## Implementation seam

Prefer a small typed result returned by the existing Windows/native bootstrap boundary and rendered by the current host UI/error path. Do not add a second process launcher, product-state store, or logging framework merely for this feature. The first implementation should wire only failures already observable at startup; add codes later only when a concrete new failure class is demonstrated.

## Exit condition

This lane closes when the packaged Windows x64 build has fresh-process acceptance for the cases above and the same stable codes are emitted by the real consumer startup path. Packaging itself remains separately owned by the release/package lane.
