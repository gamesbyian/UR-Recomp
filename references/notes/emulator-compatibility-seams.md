# Uniracers emulator compatibility seams

This note turns historical emulator failures into candidate fidelity seams. A historical symptom is evidence that a subsystem was difficult to emulate, **not** proof of the root cause. Every row stays provisional until reproduced against the project's canonical ROM/runtime.

Primary source registry entries:

- `dorando-compatibility`
- `snes9x-143-changelog`
- `snes9x-143-historical-uniracers`
- `zsnes-uniracers-history`
- `snes9x-uniracers-oam`
- `mame-uniracers-oam`
- `jgenesis-uniracers-oam`
- `nesdev-oam-2016`

## Fault families

| Seam | Historical evidence | What it can discriminate | Cheapest useful local scene | Relationship to other seams |
|---|---|---|---|---|
| LoROM SRAM mapping | Historical Snes9x changelog explicitly says a LoROM SRAM map bug was fixed and "now Uniracers works." | Cartridge mapping / SRAM address decode, save/progression access, possible boot/frontend side effects. | Cold boot plus deterministic save/load/progression probe using known SRAM anchors. | Independent of active-display OAM. Do not explain a startup failure as rendering until SRAM access is ruled out. |
| Window XOR / inversion | Historical Snes9x changelog records XOR window combination fixes making Uniracers look correct. | Window masks, area inversion, main/sub-screen clipping. | Scene with the known window effect, compared as raw frame/layer state. | Distinct from OAM sprite-addressing even when both appear as graphics corruption. |
| Empty-subscreen colour addition | Historical Snes9x notes say switching the fallback from fixed colour to backdrop seemed necessary for Uniracers, then caused trouble on later screens and was disabled. | Main/sub-screen colour math when the sub-screen contributes no layer pixel; backdrop/fixed-colour semantics. | Capture an affected early screen and a later screen in the same fixture so a fix cannot merely move the defect. | Closely related to window logic, but should remain a separate assertion because the historical experiment affected later screens differently. |
| Active-display OAM addressing | Snes9x, MAME, jgenesis, NESdev discussion and the Canoe workaround all converge on Uniracers writing OAM during active display; jgenesis gives concrete Vs.-mode HBlank events. | Internal/external OAM address behavior, HBlank/active-display access, split-screen sprite selection. | Deterministic Vs. fixture around scanlines 0 and 112 with writes to $2104/OAM captured. | Strongly associated with 2P/Vs. disappearing/ghost racers, but should not absorb unrelated 2P logic/input failures. |
| Two-player general | Dorando reports 2P errors in bsnes 0.015, MESS 0.120 and SNEeSe 0.842; ZSNES history records a release where Uniracers 2P became functional. | Split-screen presentation, P1/P2 input ownership, race-state handoff, per-player viewport/state, OAM-sensitive sprite switching. | Canonical P1/P2 route through racer selection into a Vs./2P race, with semantic checkpoints plus raw frame/OAM evidence. | Partition failures after observation: OAM-specific, input/handoff, viewport/window, or game-state. |
| APU / sound startup | Dorando records minor sound errors in multiple emulators and no sound in Super Sleuth 1.03. | SPC700 boot/upload handshake, DSP state, sequence/sample transfer, timing. | Title music startup followed by first-race music transition; compare APU state and audible/capture hashes only after deterministic state is available. | Independent from PPU/OAM. Repeated cross-emulator reports make it worth a dedicated audio discriminator. |
| Title-to-frontend transition / early execution | NLKE, SNESGT, SNEmul and YAME are reported to stop after the title; SNEmul also shows a screen-change error. | CPU/interrupt/timing, mapper/SRAM, DMA/HDMA, or PPU state transition. Root cause unknown. | Deterministic title -> main menu route with checkpointed CPU/WRAM/PPU state at the last matching frame. | Treat as a first-divergence problem. Historical symptom alone does not justify assigning it to graphics or timing. |
| Bottom-border / missing effects | SNEeSe reports a bottom-border error and missing effects. | Overscan/border geometry, windowing, colour math, layer enable/clip behavior. | Raw 4:3 frame plus PPU register/layer capture on the exact scene if recoverable. | May overlap window/colour-math semantics; retain separately until reproduction proves identity. |
| Race-start/post-start graphics | Xe is reported to develop major graphics errors shortly after a race begins. | Race renderer transition, sprite/tile updates, DMA/HDMA cadence, OAM, window/colour math. | First-race fixture from countdown through early acceleration, with first differing frame reducer. | Likely a convergence point for several subsystems. Use it as a scene discriminator, not a causal diagnosis. |

## Test-order guidance

The matrix is useful only if it prevents broad, expensive tracing.

1. Reuse existing deterministic frontend and first-race fixtures wherever they already cover the scene.
2. Add the smallest missing P1/P2 route for multiplayer-specific seams.
3. Compare semantic state first; add PPU/OAM/APU capture only when the symptom requires it.
4. When a historical failure is broad ("stops after title", "major graphics errors"), reduce it to the first differing frame/event before assigning subsystem ownership.
5. Keep independent failure classes independent until a local reproduction demonstrates a shared cause.

## Negative-space warning

A modern emulator running the game correctly does not erase these seams. The value of old compatibility reports is that different incomplete implementations accidentally performed perturbation experiments on the game. Conversely, an old emulator failure is not evidence that the original game is doing something undocumented in every affected subsystem; several failures may simply be ordinary emulator bugs that Uniracers happened to expose.

The project should promote only locally reproduced behavior into fidelity requirements.


### Active-display OAM local capture status

The project now has a locally reproducible detailed OAM/PPU observation path rather than relying only on historical emulator reports.

- The upstream `snesref` Snes9x debug-export patch was preserved verbatim as `tools/patches/snes9x-snesref-debug-exports.patch`.
- It applies cleanly to UR-Recomp's pinned Snes9x revision `1bcc369e89f08243e0a462882fb1f3e42e51de3a`.
- The patch is now part of the normal Snes9x toolchain build contract and exposes 544-byte OAM snapshots, decoded PPU register state, and an always-on per-write journal with frame/V/H/address/value/source.
- A deterministic VS-selector smoke successfully produced `.oam.bin`, `.regs.json`, and `.ppuw.tsv` artifacts through the repository-built patched core.

The selector-screen capture is a useful **negative discriminator**: its observed `$2104` traffic is ordinary DMA around V=229-230, not the historically reported active-display split-screen seam around scanlines 0/112. Therefore frontend VS selection is too early to reproduce the compatibility bug. The next fixture must advance through a P2-causal route into actual two-player/VS gameplay before judging the historical OAM behavior.

This closes the observability blocker. Remaining work is now scene reachability and cross-oracle comparison, not missing instrumentation.
