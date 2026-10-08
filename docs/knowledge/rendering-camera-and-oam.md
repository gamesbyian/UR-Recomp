# Rendering, camera and OAM

## The unusual split-screen mechanism

Uniracers intentionally changes sprite-related state during active display.

This is supported independently by developer testimony and multiple emulator investigations.

Mike Dailly described the technique as a SNES application of C64-style **sprite ripping** and said Nintendo R&D had to verify the behavior.

Modern emulator evidence makes the mechanism concrete:

- jgenesis reports OAMDATA writes on scanlines 0 and 112;
- values are `0xA5` and `0x5A`;
- both are expected to target high-OAM byte `$18`;
- that byte affects sprites 96 through 99;
- top and bottom screen halves alternately move sprite pairs on/off screen.

Snes9x's title-specific workaround forces OAM word address `0x10C`.

MAME describes the equivalent byte offset as `0x0218`.

These are two representations of the same effective location.

## What this means architecturally

The split-screen racer presentation is not simply "draw two normal scenes."

At least part of the original visual result depends on raster-time mutation of OAM-related state.

Therefore:

- authentic 4:3 mode must preserve or accurately model the original effect;
- two-player and Vs. modes deserve dedicated validation;
- a later host compositor may render equivalent logical sprites without needing to reproduce the trick in final presentation, but game state must remain authoritative.

The current optional Remastered racer compositor removes the stock racer OBJ range and draws four host replacements. Even though those replacements are host-owned, they must obey the same scanline-112 switch: slots 98/99 belong to output rows 0..111 and slots 97/96 to rows 112..223. `racer_split_viewport_contains_row()` enforces this independently of 1x–4x Internal Render Scale so an oversized sprite near the split cannot draw into a viewport where its original OAM slot is inactive. This affects only the enabled HD replacement path; it does not change guest OAM, the Original framebuffer or simulation.

Within each split viewport, the original SNES OBJ engine also gives the smaller OAM slot precedence where sprites overlap. The Remastered host painter therefore draws its four registered instances in descending slot order: slot 99 behind 98 in the top half, slot 97 behind 96 in the bottom half. The OAM attribute priority bits resolve OBJ versus BG priority, not racer-versus-racer overlap; this order is limited to the established non-rotating four-slot racer presentation.

The stock SNES line evaluator uses `(scanline - OBJ_Y) & 0xFF`, so a sprite whose raw Y lies below the visible 224 lines may wrap across the 256-line OBJ coordinate period and still paint valid rows near output row 0. The Remastered host now wraps source rows modulo 256 before applying the 224-line visible crop and the independent scanline-112 viewport check. The supplied native boundary assertions cover `Y=250` and `Y=255` at each display density. The Original PPU image remains the oracle; this corrects only host-owned replacement pixels.

## Other historical rendering seams

Older Snes9x history shows Uniracers also exposed unrelated emulator correctness problems:

- LoROM SRAM mapping;
- XOR/window-area logic;
- color addition / empty-subscreen behavior;
- active-display OAM behavior.

These should be separate tests. A visual failure in Uniracers should not automatically be blamed on the famous OAM quirk.

## Recovered multiplayer camera-to-render bridge

Recent structural recovery turns the split-screen camera path into a concrete chain rather than a generic widescreen risk.

The game maintains two camera positions and velocity pairs:

- camera 1: `$0419/$041D`, velocity `$04F5/$04F9`;
- camera 2: `$041B/$041F`, velocity `$04F7/$04FB`.

Bank 81's recovered camera-control island updates camera 1 every active race pass and conditionally updates camera 2 when `$0DDB != 0`. The same island converts camera position into coarse/fine map-window indices and feeds `81:ADB6`, `81:B27F` and `81:B375`, which derive track-data windows from `$7F000F` into working buffers. This is evidence that camera state participates in world/course sampling, not only PPU scroll.

The per-camera raw window-update state is now exposed by the paired-player summarizer: `$0505/$0507` are the movement-derived edge values, `$052B/$052D` are their associated update spans, and `$0509/$050B` retain the fine/index component. The code sets inactive edges to `$FFFF` and zero span, while active camera motion drives additional strip fetches through `B27F/B375`. Treat these names as structural/raw until runtime evidence further narrows whether they represent rendering-only streaming, collision/object activation, or a shared world-window primitive.

Immediately before the DMA/update-descriptor construction, `81:AA40..AB87` uses those same camera-derived edge bands to filter two compact 16-entry structures. Counts live at `$0DCD/$0DCF`, byte flags at `$0D6D/$0D7D`, and encoded coordinate words at `$0D8D/$0DAD`. Matching entries have their flag byte cleared as camera 1 or camera 2 crosses the encoded edge bands. Bank 82 resolves their role: `82:D383..D3C4` loads each encoded word into `$2116` as a VRAM address, selects a value from `$7E2132` using the flag byte, and writes it through `$2118`. These are therefore camera-filtered VRAM update lists, not gameplay-object activation state.

Bank 82 then computes per-racer, per-screen coordinates in `$1501..$150E` from racer positions relative to camera 1/2. Off-screen branches substitute sentinel coordinates and update visibility bits in `$1599`. Routine `82:D2D8..` subsequently writes `$1501..$1510` directly to OAMDATA.

For later widescreen work, keep these layers distinct:

1. camera simulation/follow state;
2. camera-derived course/window sampling;
3. racer screen-space projection and culling;
4. OAM emission and the active-display split-screen seam.

Expanding only the final render rectangle would therefore be insufficient and could expose objects or course sectors outside the original simulation/activation window.

## Camera and future Widescreen feature

The project should recover and distinguish:

- world/camera state;
- PPU scroll state actually rendered;
- object culling bounds;
- sprite/OAM emission bounds;
- stage/stream activation boundaries;
- HUD/UI layers.

SNESRecomp's existing Widescreen patterns warn that widening only one of those layers is insufficient. In particular, culling and OAM emission form separate gates.

The permanent rule is:

**4:3 authentic behavior is the regression oracle. Widescreen extends presentation without silently changing simulation or progression.**

See `docs/WIDESCREEN.md` for implementation-specific rules.


### Remastered racer capture must follow final host geometry (2026-10-08)

The pinned desktop runner's `CaptureSimulationFrame()` first executes
`PreparePpuFrame()`, resolving `prepare_frame()` output into
`snesrecomp_desktop_frame_width()/height()`, **then** invokes the game
`begin_sim_frame()` callback, and only afterward scans the PPU. A widescreen
WorldExpand scene may set logical width above 256 in that first step.

The optional Racer HD presenter strips OAM slots 96–99 from the PPU image with
`kPpuOverlayFlag_RemoveFromGame` only when both racer semantic registrations
and placements are known. Its actual host draw callback still supports only a
256×224 logical field. Therefore starting an OBJ extraction for a 342×224
field and declining the host draw afterward is not a harmless Original
fallback: the captured raster can already **lack the original racers**.

`racer_hd_begin_sim_frame()` now calls
`racer_hd_can_capture_frame_geometry()` with the finalized desktop dimensions
**before** selecting art, binding overlays or requesting OBJ removal. Only the
exact 256×224 field may promote the four slots. All other frame geometries
preserve stock OBJ rendering; the Modern presentation layer may still apply
its independently configured integer-density scale to that complete stock
field. This is intentionally conservative until the independently governed
widescreen compositor can present HD art in shifted world coordinates while
preserving background/foreground priority. It does not alter WRAM/VRAM/OAM,
the split-scanline policy, or stock/Original PPU raster geometry.

Regression coverage checks both the pure geometry admission policy and the
real native PPU presenter link path. A comparative real Windows capture
at a fully registered pose, once each in Original width and WorldExpand, is
still needed for pixel-level evidence. Never infer that the pure helper unit
test alone proves the final widened picture.


#### Pixel-level Native 342px stock-fallback acceptance

The graphics-owned native presentation probe now enables the pinned desktop
host's native-wide mode and supports a diagnostic-only
`UR_RACER_HD_PROBE_WIDE=1` switch. It fixes the probe's logical width to 342
(43 side columns) and height to 224 *before* `begin_sim_frame`. The probe
asserts that no OBJ `RemoveFromGame` capture is armed on any such frame,
including frame 1220 of the deterministic two-player race.

The native presentation acceptance reuses its existing generated binary, ROM,
controller input and script to take **two independent** 342×224 PPM captures
at that same frame: `UR_RACER_HD=0` and `UR_RACER_HD=1`. It requires
identical full screenshot bytes (and validates dimensions and nontrivial
colors), emits `UR_RACER_HD_WIDE_PARITY PASS`, and archives both PPMs and
logs. This validates a true desktop-runner widened PPU scan and final host
presentation without touching the Modern frontend. It is a geometry/fallback
guard acceptance, **not** a claim that independently authored HD sprites now
render in widened scenes.
