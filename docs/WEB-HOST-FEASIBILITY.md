# Web Host Feasibility Contract

Last updated: 2026-10-03

This document turns the Web feasibility target in `PLATFORM-TARGETS.md` into a bounded engineering contract. It does not create a browser fork of Uniracers. The browser host must run the same authoritative recompiled simulation and consume the same platform-neutral product/presentation contracts as desktop hosts.

## Goal

Prove that the current native architecture can support an Emscripten/WebAssembly host without moving browser constraints into guest simulation or creating browser-specific game semantics.

The first milestone is deliberately small: compile and boot the authoritative runtime in a browser harness, advance deterministic guest frames, accept semantic host input, and persist/reload a small host-owned settings payload. HD art, Widescreen polish, packaging, and full audio UX are later consumers of the same host seams.

## Authority boundary

The browser may own:

- canvas/WebGL or WebGPU presentation plumbing;
- browser frame scheduling;
- Web Audio device/output plumbing;
- Gamepad API and keyboard event translation;
- IndexedDB/OPFS-backed persistence adapters;
- focus, visibility, fullscreen, pointer and lifecycle events;
- browser-specific packaging and asset delivery.

It may not own or reinterpret:

- guest physics, timers, AI, RNG, collision, stunt windows or progression;
- SRAM semantics;
- Widescreen materialization semantics;
- Racer-HD semantic replacement identity;
- modern product-state schema meanings;
- Restart/Retry snapshot semantics;
- simulation cadence.

`requestAnimationFrame` is a presentation scheduler, not the game clock. Browser throttling or a 120/144 Hz display must never change the number or timing of authoritative guest simulation steps.

## Portability seams to prove

### 1. Bootstrap and main loop

The host must be able to initialize the recompiled runtime without `fork`, `exec`, subprocesses, or a blocking desktop event loop. A browser entry point should expose an explicit initialize/tick/present lifecycle suitable for Emscripten's main-loop integration.

Acceptance:
- runtime initializes in a browser build;
- a deterministic fixed number of guest frames can be advanced;
- presentation callbacks may occur at a different rate without changing the guest-frame count or deterministic semantic digest.

### 2. Persistence

All required writes must pass through an adapter rather than assuming an immediately durable POSIX filesystem.

The browser adapter may use Emscripten FS backed by IndexedDB initially, with OPFS as a later implementation option. The shared product/SRAM layer must not know which backing store is used.

Acceptance:
- write a host-owned settings payload;
- explicitly flush/synchronize browser persistence;
- recreate the host/runtime and recover the identical payload;
- perform the same round trip for cartridge SRAM without changing its bytes or checksum semantics.

### 3. Input

DOM keyboard and Gamepad API state must translate into the existing semantic host-input layer. Browser key codes and gamepad indices must not leak into simulation or product policy.

Acceptance:
- one keyboard route and one gamepad route produce the same semantic P1 action;
- focus loss clears transient physical input so a held browser event cannot become a stuck guest control;
- Authentic and Modern modes consume the same semantic gameplay input.

### 4. Audio

Web Audio scheduling must remain downstream of authoritative emulation/audio production. Browser autoplay policy may delay device activation, but it may not stall or retime guest simulation.

Acceptance:
- boot with audio unavailable or suspended;
- advance deterministic guest state;
- activate/resume browser audio later without changing the semantic digest.

### 5. Display and fullscreen

Browser fullscreen and canvas sizing implement the shared display-presentation policy where the platform permits it. Unsupported desktop concepts must fail closed or map to documented browser behavior rather than acquiring new product semantics.

Initial mapping:
- Windowed: canvas embedded at selected presentation size;
- Borderless: not a distinct browser capability; treat as unsupported/inapplicable;
- Fullscreen: Fullscreen API when granted;
- output resolution: canvas/output backing size, bounded by browser/device capability;
- internal render scale: independent presentation input;
- VSync: browser compositor controlled; expose no false promise of disabling it;
- presentation FPS: scheduler target/best effort only, with simulation cadence fixed.

### 6. Assets

Required runtime assets must be addressable without arbitrary host filesystem discovery. Build-time packaging or explicit fetched assets are acceptable. Runtime correctness may not depend on directory enumeration outside the packaged/browser storage contract.

## First spike

Create a minimal Emscripten target only after the seams above are represented by interfaces in current native code. The spike should avoid product polish and answer four questions:

1. Does the authoritative runtime compile to wasm32 with the current dependency set?
2. Can it boot and advance a deterministic fixed-frame fixture?
3. Which unresolved native APIs remain in the transitive link surface?
4. Can settings and SRAM survive an explicit browser persistence round trip?

Retain the compiler/linker diagnostics and a machine-readable dependency/blocker inventory. Do not paper over unsupported APIs with no-op stubs unless the stub is semantically correct and explicitly documented.

## Fail-closed rule

A browser limitation is evidence about a host adapter, not permission to weaken cross-platform contracts. If a shared dependency cannot support WebAssembly, record the exact dependency/API and isolate it behind a host seam. If an essential authoritative subsystem itself requires an unavailable facility, stop the Web feasibility lane and promote that as an architectural blocker.

## Completion criterion

Web moves from `feasibility target` to `host bring-up in progress` only when a retained browser build proves deterministic fixed-frame execution plus persistence round trips without browser APIs entering authoritative simulation state.
