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


### Reproduced VS active-display seam

A deterministic two-controller route now reaches active VS gameplay and locally reproduces the concrete behavior that historical emulator fixes were trying to preserve. In stable split-screen race checkpoints, the patched Snes9x write journal records:

- scanline 0: HDMA write `$2104 <- $A5`
- scanline 112: HDMA write `$2104 <- $5A`

The pair repeats at five sampled race checkpoints from guest frame 1140 through 1620. Earlier VS-selector captures contain only vblank-era OAM DMA around V=229-230, providing a local negative control.

This promotes the active-display OAM row from historical-only motivation to a locally reproduced fidelity seam. The exact downstream OAM-address/high-table consequences and sprites 96-99 still need reconstruction-level tracing, but authentic mode now has a concrete event-level regression target rather than a prose description of the old emulator workaround.

Durable inputs/assertion:

- `tests/input/vs-first-race.input`
- `tests/input/vs-first-race-observe.script`
- `tools/assert_uniracers_vs_oam_seam.py`


#### HDMA table source

The stable VS race captures also expose the driving HDMA configuration itself. At HDMA initialization, channel 1 is mode 0 with BBAD `$2104` and table source `$7E:206C`. The WRAM table is stable across the sampled race frames:

```text
7E:206C  70 A5 70 5A 00
```

For direct mode-0 HDMA this is two 112-line runs followed by the terminator: the first run supplies `$A5`, the second supplies `$5A`. This explains why the journal sees one `$2104` write at V=0 and the next at V=112.

That closes the immediate source/timing question. The remaining archaeology is the hardware consequence: map those active-display `$2104` writes through the effective OAM address/high-table semantics and confirm the historically implicated sprite range rather than inferring it from emulator workaround code.


### Empty-subscreen colour-addition historical discriminator

The preserved Snes9x 1.43 history makes this seam unusually testable rather than merely anecdotal.

Historical evidence records that Uniracers enables sub-screen addition on BG2 while nothing is present on the sub-screen, and explicitly asks whether the empty contribution should behave as fixed colour or backdrop. A later changelog entry says Snes9x temporarily switched to adding backdrop colour when sub-screen addition was enabled but nothing existed on the sub-screen because Uniracers seemed to require it, then disabled that change because it caused problems in other ROMs **and in later Uniracers screens**.

The corresponding preserved renderer source shows the relevant class of branch directly: when rendering colour addition/subtraction, it distinguishes a real sub-screen pixel from a clear sub-screen and separately handles the backdrop/fixed-colour fallback. Therefore this should be treated as a scene-dependent PPU semantic discriminator, not a title-specific patch to copy.

Local test strategy:

1. survey stable checkpoints using raw `TM`, `TS`, `CGWSEL`, `CGADSUB`, fixed RGB and framebuffer hashes;
2. identify at least one early checkpoint matching the historical empty-subscreen condition and one later checkpoint whose state differs;
3. reproduce the historical fallback perturbation in an isolated reference-core A/B;
4. require a candidate semantic rule to explain both scenes without merely moving the defect;
5. promote only the hardware/game-facing invariant, never the historical Snes9x workaround itself.

The first survey is implemented by `tools/summarize_color_math_state.py`; its one-shot canonical-ROM run is intentionally evidence acquisition only and will be retired after the measurements are preserved.


#### Canonical scene survey

Run `36659159802` surveyed the existing deterministic first-race route with the patched Snes9x register snapshot surface.

All stable frontend checkpoints from Main Menu through Now Playing share the same color-math configuration:

- `TM=13`
- `TS=10`
- `CGWSEL=02` (sub-screen math selected)
- `CGADSUB=7F` (addition with half flag and all layer/backdrop math bits set)
- fixed colour = black
- brightness 14

The first active race checkpoint changes regime materially:

- `TM=17`
- `TS=10`
- `CGWSEL=02`
- `CGADSUB=04`
- half flag off
- fixed colour = red 15, green/blue 0
- brightness 15
- `TMW=17`

This gives the historical fallback experiment a built-in scene pair. The frontend is the candidate regime where old Snes9x reported a backdrop-vs-fixed-colour ambiguity; the race is the later counterexample regime that must not be damaged by an overbroad rule.

The survey is preserved as `analysis/generated/color-math-scene-survey.json`.
