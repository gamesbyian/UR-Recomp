# Nintendo Switch Homebrew Port Plan

Last updated: 2026-10-02

## Goal

Prove that the final UR-Recomp product can run as a personal-use Nintendo Switch homebrew application while preserving the same authoritative simulation, Widescreen/HD presentation semantics, modern product-state boundaries and deterministic behavior used by desktop builds.

This is a portability lane, not a new implementation of Uniracers.

## Public toolchain baseline

Use the established public Switch homebrew stack:

- devkitPro package manager and `switch-dev` / devkitA64 toolchain;
- `libnx` for Switch userland APIs;
- `switch-examples` as the canonical usage-pattern reference;
- `switch-tools` for public helper tooling where needed;
- devkitPro Switch portlibs such as SDL2 where they materially reduce host divergence.

Pinned source references are recorded under `third_party/platform/switch/pins.json`.

Current pins:
- libnx: `feebd026ca0f5dcc2119f46ad8e0d16ad3dd4973`
- switch-examples: `669786898205b7beb25ff1731e72982e6d0397d3`
- switch-tools: `22756068dd0ed6ff9734c59cb4f99ebd3f62555b`

The devkitPro compiler/package installation remains package-manager supplied. Do not vendor an arbitrary local devkitPro installation into Git.

## Why SDL2 first

UR-Recomp already uses an SDL-shaped desktop host boundary. The official Switch examples include SDL2 examples, making SDL2 the cheapest first feasibility path.

First try to preserve:
- the existing semantic input layer;
- the existing host pause/retry command path;
- the existing audio abstraction;
- the modern compositor's platform-neutral logic.

Escalate to a Switch-specific renderer only if measured performance or unsupported features require it. Do not adopt deko3d merely because it is lower level.

## Portability gates

### Gate S0 — compile-only host probe

Create a minimal Switch target that:
- compiles with the pinned/current devkitPro Switch toolchain;
- links libnx and SDL2;
- emits a valid NRO;
- does not include Uniracers guest code yet.

Exit: deterministic CI/local cross-build recipe and retained compiler/link metadata.

### Gate S1 — runtime shell

On hardware, prove:
- app lifecycle enters/exits cleanly;
- 720p handheld and 1080p docked presentation surfaces;
- Pro Controller/Joy-Con/handheld input;
- audio initialization;
- writable application storage;
- suspend/resume behavior.

Exit: host capability report with no guest simulation dependency.

### Gate S2 — authoritative simulation

Link the same generated/recompiled simulation used by desktop.

Require:
- successful boot to deterministic fixture checkpoints;
- matching event-relative simulation digests for the finite stock-fidelity matrix;
- no Switch-only simulation patches.

### Gate S3 — modern product layer

Wire:
- semantic Pause/Resume;
- Restart Race rollback path;
- settings and profile persistence;
- controller mapping and vibration;
- focus/suspend policy.

Authentic mode must remain observationally stock and ignore modern policy exactly as on desktop.

### Gate S4 — Widescreen and HD

Prove:
- true-wide host composition at Switch output resolutions;
- accepted guest +8 Widescreen path remains unchanged;
- deeper host-owned materialization remains presentation-only;
- HD replacement lookup uses the same synchronized semantic composition contracts;
- Original mode remains an untouched fallback.

### Gate S5 — performance acceptance

Measure handheld and docked separately:
- stable 60 Hz guest simulation;
- frame-pacing behavior;
- compositor GPU/CPU cost;
- audio underrun rate;
- memory use;
- HD asset residency/streaming.

Optimization must not make simulation timing platform-dependent.

## Storage

Do not bind product state directly to libnx filesystem calls. Add or reuse a narrow host persistence interface supporting:
- atomic settings write;
- profile catalog;
- SRAM persistence;
- ghost/replay files;
- future custom content.

The desktop and Web implementations must implement the same semantic contract with platform-appropriate storage.

## Input

Map Switch physical controls into UR-Recomp semantic host inputs.

The title/product layer should receive concepts such as Accept, Back, Pause and Restart plus guest controller state. It should not receive Joy-Con-specific button enums.

Support eventually:
- handheld;
- paired Joy-Con;
- Pro Controller;
- two-player local controller assignment;
- rumble setting gated through the existing host-owned vibration policy.

## Graphics

Start with SDL2 because it minimizes host divergence. Keep the renderer boundary replaceable.

Do not assume that a 4K desktop-oriented internal render target is appropriate on Switch. The compositor must support native target sizes without changing simulation coordinates.

## CI

GitHub Actions may perform compile-only Switch feasibility checks if the required public devkitPro packages can be installed reproducibly and within CI cost limits.

Hardware acceptance remains a separate local step. Never mark a Switch behavior gate closed from cross-compilation alone.

## Security / repository boundaries

Do not commit:
- keys;
- device identifiers;
- NAND/system dumps;
- proprietary Nintendo SDK content;
- confidential developer materials;
- exploit payloads or circumvention material unrelated to ordinary homebrew application development.

The project only needs the ordinary public homebrew application toolchain.

## Immediate next work

This platform lane should remain low-disruption while core product work continues:

1. keep exact upstream pins current but deliberate;
2. add a compile-only NRO probe when a devkitPro-enabled runner/local machine is available;
3. inventory current SNESRecomp host dependencies for desktop-only assumptions;
4. add portable host interfaces where a real blocker is found;
5. do not fork simulation or presentation policy preemptively.
