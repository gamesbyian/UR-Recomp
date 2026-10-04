# Nintendo Switch Homebrew Port Plan

Last updated: 2026-10-04

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

The devkitPro compiler/package installation remains package-manager supplied. Gate S0 CI uses the dated public `devkitpro/devkita64:20260219` container recorded in `third_party/platform/switch/pins.json`; each run records the actual compiler, libnx and SDL2 package versions alongside the NRO digest. Do not vendor an arbitrary local devkitPro installation into Git.

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

**Closed for compile/link/package feasibility.** Run `37238310723` passed the repository contract, toolchain discovery, libnx+SDL2 compile/link, ELF/NACP/NRO packaging, metadata capture and artifact upload in the pinned devkitPro container. The repository-owned probe lives under `platform/switch/s0_probe/`, with its machine-readable scope in `analysis/switch-s0-contract.json` and validator in `tools/check_switch_s0_probe.py`.

The probe:
- compiles with the dated devkitPro Switch toolchain container;
- includes and links both libnx and SDL2 through actual symbols (`appletGetOperationMode` and `SDL_GetVersion`);
- emits an ELF, NACP and NRO through the public `libnx/switch_rules` path;
- contains no Uniracers ROM, generated guest code, SNESRecomp runtime or modern-product implementation;
- retains compiler/package versions, NRO size/digest and linker map metadata as bounded CI evidence.

The workflow is `.github/workflows/switch-s0-compile-probe.yml`. It runs automatically only when the S0 contract itself changes and remains manually dispatchable. That green cross-build closes S0's compile/link/package requirement only; it makes no hardware-runtime claim. Reopen S0 only if the pinned public toolchain or probe contract regresses.

Exit: deterministic CI/local cross-build recipe and retained compiler/link metadata.

### Gate S0.5 — shared modern-core portability

**Closed.** Run `37238705878` cross-compiled 20 platform-neutral modern product/title translation units into Switch AArch64 objects with devkitA64 and `__SWITCH__` defined. The retained contract is `analysis/switch-shared-core-contract.json`; `tools/build_switch_shared_core_probe.py` validates the boundary and performs the cross-build.

The first pass exposed one useful boundary defect: `native/title/uniracers_ws_margins.c` contains reusable course/materialization logic but also binds directly to generated runtime state through `common_rtl.h`. It is therefore classified with the runtime adapters rather than falsely counted as shared core. `native/product/uniracers_modern_host.cpp` remains explicitly desktop-owned because it binds SDL lifecycle/pref-path/focus/quit behavior and SNESRecomp desktop display APIs.

Current result: profile/state persistence, pause/options/session policy, restart lifecycle, output-resolution policy, Widescreen composition policy, run-data decoding and tour-resume logic all compile for the Switch target without a platform-specific simulation fork. Reopen this gate only if a shared-core file gains a direct desktop/runtime dependency or the devkitA64 cross-build regresses.

### Gate S1 — runtime shell

**Software shell implemented and cross-build accepted; hardware acceptance still open.** Run `37239380410` validates the repository-owned S1 shell in the pinned devkitA64 environment: the scope validator and hardware-report evaluator pass, and the SDL2/libnx application compiles, links, packages as an NRO and retains build metadata. The first link attempt exposed a real Switch static-link requirement for libm through SDL2/Mesa/EGL; the Makefile now retains that dependency explicitly.

The hardware shell under `platform/switch/s1_runtime_shell/` is deliberately guest-free and records observations to `ur-recomp-s1-capability-report.txt`. It probes:
- clean applet-loop lifecycle and explicit exit;
- 1280×720 handheld and 1920×1080 console targets using live operation mode;
- standard libnx controller styles, retaining the styles actually observed;
- SDL2 audio-device initialization;
- a write/read/delete round trip in the SD-backed application working directory;
- SDL background/foreground lifecycle events as suspend/resume evidence.

`tools/evaluate_switch_s1_report.py` provides the retained hardware gate. Multiple sessions may be combined so handheld, docked, Pro Controller and Joy-Con coverage need not occur simultaneously, but each session must still initialize display/audio/storage and exit cleanly. CI explicitly records `hardware_acceptance=not_run_in_ci`; it cannot close S1.

On hardware, still prove:
- both handheld and console operation modes;
- Pro Controller, Joy-Con and handheld input;
- audio initialization;
- writable application storage;
- background then foreground lifecycle events across suspend/resume;
- clean exit.

Exit: evaluator passes retained on-device capability report(s) with no guest simulation dependency.

### Gate S1.5 — generated guest AOT portability

**Closed.** Run `37239842625` verifies the canonical USA ROM, stages the repository-owned patched SNESRecomp framework, generates fresh Uniracers AOT C, transfers that exact source bundle into the pinned devkitA64 container, and cross-compiles the title driver plus all generated guest translation units for Switch AArch64.

The accepted bundle contains 11 C translation units: `game_rtl.c`, `host_contract.c`, `gen_stubs.c`, and 8 generated `src/gen/*.c` banks. All 11 emitted AArch64 objects successfully (391,848 bytes total in the retained run). The desktop `main.c` and desktop runner sources are explicitly excluded.

The first pass exposed only an evidence-packaging defect: scaffold headers were omitted from the cross-job bundle. After carrying the actual project headers, the same compile gate passed without simulation-source modifications.

This establishes that the generated authoritative guest/title code itself is architecture-portable to Switch. It does **not** yet link the SNES hardware/runtime model, run on hardware, prove deterministic parity, or close S2. The next S2 task is therefore the runtime-model link boundary, not rewriting generated guest code.

### Gate S1.75 — authoritative runtime-floor portability

**Closed.** Run `37240684525` cross-compiled the pinned non-desktop SNES runtime floor with devkitA64 and `__SWITCH__` defined. The accepted contract covers 32 framework translation units: common CPU/RTL infrastructure, CPU state/dispatch, the SNES CPU/DMA/PPU/APU/DSP hardware model, cartridge/joypad/coprocessor support, interpreter fallback and the AOT/LLE bridge.

All 32 emitted AArch64 objects successfully, totaling 892,704 bytes in the retained run. Desktop host, launcher, save-state/rewind UI, debug server/oracle, mod UI/runtime, network/co-simulation and SDL/OpenGL presentation sources remain explicitly outside this floor.

The first runtime pass exposed two boundary-header dependencies rather than implementation blockers:
- `variables.h` is a scaffold-required title header and is empty until a title names WRAM variables;
- `common_rtl.c` includes `config.h` but references no desktop `Config` fields.

The probe therefore supplies only those narrow compile contracts rather than importing `runner/src/desktop` into the Switch runtime. It also stages the patched framework on a normal Ubuntu job before entering the devkitPro container, avoiding the older Python `TarFile.extractall(filter=...)` incompatibility in that image.

Together with S1.5, this establishes source-level Switch portability for both the generated Uniracers guest/title code and the authoritative non-desktop runtime floor. The next S2 boundary is an actual guest + runtime link with explicit Switch host contracts, followed by hardware execution and deterministic parity.

### Gate S1.9 — combined guest/runtime link surface

**Closed as a first-pass inventory.** Run `37240878730` regenerated the canonical guest, cross-compiled the accepted 11 guest/title and 32 runtime-floor translation units, and collapsed all 43 AArch64 objects with a relocatable link. The combined object is 1,212,472 bytes.

After internal guest/runtime references were resolved, 101 external symbols remained. That count is intentionally conservative: it contains ordinary libc/POSIX/libm/toolchain symbols plus framework support modules that were outside the first runtime-floor set. Examples of the latter include `audio_trace_*`, `ppudma_*`, `sha256_compute`, `snes_mod_audio_*`, `snes_runahead_active`, `host_report_breadcrumb`, and `g_framedump_callback`.

The next reduction step is therefore to add the required non-desktop framework support translation units to the collapse before designing a Switch host adapter. Do not treat the raw 101-symbol list as 101 Switch APIs.

### Gate S1.95 — full guest/runtime Switch executable link

**Closed.** Run `37242319162` produced the first Nintendo Switch NRO that contains the freshly generated canonical Uniracers guest, the accepted authoritative SNES runtime floor, required portable framework support modules, and a Switch-owned host contract. The final AArch64 executable link has zero undefined symbols and `elf2nro` packaged it successfully.

Accepted NRO SHA-256: `884e25ddcc12acb2ca761e0b129a676336b6e30a5a07f040d2741602693626fc`.

The host is intentionally a non-simulating skeleton. It owns the framework's true host seams (fatal handling, APU serialization contract, optional SPC interception, frame-present hook, save-directory creation, window-scale no-op, Widescreen globals and breadcrumb logging) but does not call `SnesInit` or `RtlRunFrame`. It opens no audio thread; therefore its no-op APU lock is valid only for this single-threaded link/boot probe and must be replaced before simulation + audio are enabled.

This result closes the executable-link question: no Switch-only simulation fork is needed to combine the canonical guest and authoritative runtime into a real NRO. Gate S2 remains open for the materially harder proof: initialize the canonical ROM/runtime on Switch, execute deterministic fixture checkpoints, and match the retained event-relative simulation digests.

### Gate S1.97 — canonical initialization/execution hardware probe

**Build closed; hardware execution pending.** Run `37243544919` successfully regenerated the canonical Uniracers guest, embedded the verified USA ROM, linked the authoritative runtime + digest support with zero undefined symbols, and packaged the bounded S2 execution probe as a real NRO.

Accepted probe NRO SHA-256: `ed68209641fe117be0f5ecc5a6aaa70ed8e8639c4bd929e8e87ec4c5c56c1c3d`.

On hardware the probe calls `RtlRegisterGame(&kGameInfo)`, then `SnesInit`, then runs exactly 120 no-input frames through `RtlRunFrame(0)`. It records the framework's existing partitioned simulation digests at frames 0, 1, 60 and 120 into `ur-recomp-s2-execution-report.txt`.

CI proves generation, compilation, ROM embedding, complete link and packaging only. It does **not** prove that initialization or frame execution succeeded on Switch hardware, and it makes no deterministic-parity claim until a hardware report is compared with the retained desktop reference.

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

1. keep exact upstream/toolchain pins current but deliberate and keep the S0 NRO cross-build green;
2. inventory current SNESRecomp host dependencies for desktop-only assumptions before attempting to link guest code;
3. design S1 as a hardware-only capability report for lifecycle, display, input, audio, storage and suspend/resume, without promoting those checks to CI claims;
4. add portable host interfaces only where the inventory or S1 finds a real blocker;
5. do not fork simulation or presentation policy preemptively.
