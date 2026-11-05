# ART-4K: targeted original rider graphics WRAM and queue writer witness

The exact original USA ROM bytecode in [#3107](https://github.com/gamesbyian/UR-Recomp/pull/3107) exposes an ordinary 24-state × 64-orientation rider graphics lookup and a 32-byte-at-a-time DMA transfer queue. The original 24-tick no-skip Mesen PPU archive already merged in [#3103](https://github.com/gamesbyian/UR-Recomp/pull/3103) shows original 8×8 tile bytes changing under stable OAM references, with a byte-exact VRAM tile census in [#3104](https://github.com/gamesbyian/UR-Recomp/pull/3104). What remains unresolved is which *executed ROM instruction* and current rider state produced those pixels at the two actual source upper-region events.

**Small additive probe:** Reuse the existing, SHA-pinned `tools/art/capture_original_mesen_ppu_raw.py` and `third_party/src/mesen-for-ai/bridge.lua` Mesen execution and original input replay, with optional `--include-rider-wram`. It reads **eleven exactly bounded 16-bit little-endian SNES WRAM words** at each selected original held PPU snapshot: `0F77` (candidate orientation), `0F83` (candidate phase), `0F69` (recent motion delta), `0F49` (angle), `0F97` (selected graphics), `0FE9/0FEB` (two queued player graphic IDs), `0306` (queue pending), plus first queued DMA source bank `15A1`, address `1645` and VRAM destination `16E9`. Every read must report the exact requested `snesWorkRam` type/address/length, two true bytes and a stable emulator bridge frame; a SHA-256 over the exact eleven word pairs is written into the normal source manifest.

Use the *existing* `watch.create` / `watch.list` bridge API to record bounded CPU **write callbacks with actual PC, source callback frame and cycle counts** for precisely seven queue/graphics words. These callbacks are installed just before the first requested original source event, with the bridge's existing 2,048-event ring and a max 128 selected events per captured boundary; overflow fails closed, never silently truncates. The callback frame and the held PPU snapshot may belong to different intra-frame phases, and a NMI may already have cleared the queue by the read. The current temporary orientation/phase registers may reflect the last processed rider, **not independently identified P1/P2 state**. Those limitations remain explicit in the evidence schema.

The existing original-Mesen Actions workflow gains an opt-in manual `include_rider_wram` boolean and one automated bounded PR qualification: original bridge ticks **1601,1602,1603,1605,1606,1609,1610,1624**. This executes only one 1,624-tick replay with existing Mesen cache and original ROM. It does **not** capture new geometry, invent a separate emulator harness, run a broad search, automatically modify shipping art or add a recurring workflow. The normal workflow outputs remain unchanged when the option is off.

The original response manifest retains hashes for all co-timed OAM/VRAM/CGRAM and held framebuffer files; the new WRAM/CPU-write callback records are tied to their exact original bridge tick and included in the manifest, plus concise, machine-parseable `ART4K_ORIGINAL_RIDER_BOUNDARY` lines in the Actions log. This lets an agent review the actual selected graphics IDs and event PC metadata **without** downloading or re-running a transient binary artifact. A future interpretation must correlate those registers with the source index-to-ROM-pointer audit, and keep source 1994 3D mesh, articulated joint angles, final PPU ownership and owner visual acceptance **unverified**.

**Stop criterion:** If the first exact-head original replay produces no appropriate watch PC events, or if temporary selected-rider values cannot be associated with either player or the observed tile updates, record `unresolved` and inspect callback timing/queue consumers before any further emulator run. Never multiply the captured phase by 15° or the orientation by 5.625° and declare a physical 3D rig recovered.

This probe is optional research evidence. No Windows release QA or artwork acceptance gate is awarded.

## Original emulator execution: bounded source WRAM and CPU writer results

The exact-head original-Mesen job **[run #41773225199](https://github.com/gamesbyian/UR-Recomp/actions/runs/41773225199)**, job `126387503637`, successfully executed on PR head `58952694a712338f39c63d19aac4614f400e2119`. It used the existing source-built original MesenCE and original controller replay; no separate emulator or Desktop Commander access was involved. The eight chosen original bridge snapshots were **1601,1602,1603,1605,1606,1609,1610,1624**, intentionally including both previously observed upper-silhouette source changes. The machine-readable log's eight `ART4K_ORIGINAL_RIDER_BOUNDARY` records and **160 CPU WRAM-write callbacks** are preserved verbatim in `analysis/data/racer-original-mesen-rider-wram-queue-writers-eight-20261103.json`, Git blob `95daf2e1f11ffbe1e8f4e37dc73cd91e17a0bdcc`.

| Original bridge tick | Current $0F83 phase | Current $0F77 orientation | $0F97 selected graphics | Queued P1 $0FE9 | Queued P2 $0FEB |
|---|---:|---:|---:|---:|---:|
| 1601 | 5 | 61 | 381 | 1401 | 381 |
| 1602 | 8 | 60 | 572 | 121 | 572 |
| 1603 | 11 | 60 | 764 | 441 | 764 |
| 1605 | 16 | 60 | 1084 | 1018 | 1084 |
| 1606 | 19 | 60 | 1276 | 1338 | 1276 |
| 1609 | 4 | 60 | 316 | 698 | 316 |
| 1610 | 7 | 60 | 508 | 954 | 508 |
| 1624 | 22 | 60 | 1468 | 442 | 1468 |

**All eight actual original source states satisfy the static ROM-verified ordinary presentation equation** `selected ID = 64×phase + orientation` exactly. In these eight held-boundary samples, selected graphics ID equals **queued P2 graphics ID**. This makes current WRAM state consistent with the last-processed rider being P2, but the current selected state alone cannot establish which original source OAM slot or anatomical part uses that graphics ID. The P1 IDs also change, and their low six bits are 57 or 58 rather than current selected P2's 60 or 61. This is a major advance over retrospective best-of-five 2026 GLB poses: source presentation values are now tied to *actual executed original frames*.

**Executed original CPU callback PCs**, sampled on callback frame `tick−1` at each selected held snapshot:
- `$82:8E72` writes the P1 graphic ID and `$82:9360` writes P2;
- `$83:EF0F` writes the selected graphics register;
- `$83:F21D` writes first queued graphics DMA source address; `$83:F22A` writes bank, `$83:F26E` writes VRAM destination;
- `$83:F295` sets the queue pending flag and `$82:B8BA` clears it during NMI.

These PC values are the **emulator's callback program-counter readings**, often the *instruction immediately following* the corresponding store: compare the byte-exact static 65816 disassembly in #3107 to identify the store's opcode address, typically a few bytes earlier. Every sampled held state reported pending flag 1 and first queue destination `$6020` with first source bank `$27`; first source address `$D440` at ticks 1601–1603 and `$D5C0` at later selected ticks. These are **the first queue entry**, not independent proof of which player's original 64×64 sprite region they address. The held PPU timing and callback frame numbering remain explicitly unaligned until separately verified; the eight samples are not a prospective blind holdout.

**Next discriminating reconstruction step:** use exact ROM graphics pointer/queue architecture and the observed source phase/graphic IDs to map the queue's multiple VRAM destinations against the *specific* 64 source 8×8 tiles of OAM96/OAM97, including timing and source 4bpp colours. Confirm player/OAM assignments with original PPU tile-byte differences, then determine whether any source-aligned phase sequence meaningfully constrains wheel, fork, crank or saddle geometry. Preserve **source-original 2D tile-generation** as a competing hypothesis; don't convert a source 24-state integer into physical wheel degrees without proof. The unapproved 2026 GLB, viewer, owner visual likeness and Windows release remain separate.

The four focused, ROM-free receipt tests recheck immutable Git blob bytes, original SHA/baseline, all eight actual `64×phase+orientation` relations, both queued graphics values, per-boundary 22-byte SHA-256, callback PC/address/frame data and no-3D claims. The prior exact-head real-Mesen run passed; a later docs/data commit does not claim a new emulator execution.

## Executed full graphics queue: 233 original sprite-tile destinations

Second exact original Mesen run [#41774019061](https://github.com/gamesbyian/UR-Recomp/actions/runs/41774019061), job `126390044838`, passed at implementation head `23a82d36c514347fae0e3d32844927a575b184c8`. It captured the three original 82-word DMA queue arrays (source bank WRAM `$15A1`, source address `$1645`, destination `$16E9`) at the same eight selected original game ticks. Each array's source `$FFFF` terminating bank word gives 27–30 entries, each representing a queued 32-byte original graphics transfer.

**Crucial source address correction.** The original ROM's NMI transfer routine checks destination bit `$0080` and adds **`$0800` words** to the queued VRAM destination in that case, before writing `$2116`. Using that actual flag rule and the previously authenticated 64 tile addresses from each original 64×64 source OBJ produces the following exact address-region partition:

| Original bridge tick | Queued tile transfers | Red OAM97 addresses | Blue OAM96 addresses | Unclassified |
|---|---:|---:|---:|---:|
| 1601 | 27 | 13 | 14 | 0 |
| 1602 | 28 | 13 | 15 | 0 |
| 1603 | 28 | 13 | 15 | 0 |
| 1605 | 30 | 15 | 15 | 0 |
| 1606 | 30 | 15 | 15 | 0 |
| 1609 | 30 | 15 | 15 | 0 |
| 1610 | 30 | 15 | 15 | 0 |
| 1624 | 30 | 15 | 15 | 0 |

**All 233/233 source queue destinations map into exactly one of the independently authenticated red or blue racer source sprite tile sets.** The first three observations show slightly shorter groups, while the last five have exactly five repetitions of the original red/red/red/blue/blue/blue interleaving. This is a strong executed linkage between game graphics selection, actual SNES DMA queue contents, and original sprite tiles. It does not prove that all 233 queued transfers were executed *before* the PPU image held at that same bridge tick. The source callback frame reported `tick−1`, and intra-frame PPU DMA/scanout timing is not independently aligned. The individual player graphic index to individual queued ROM source tile bytes is still to be verified; original 1994 3D geometry is not identified.

Complete 233-entry *derived* receipt: `analysis/data/racer-original-mesen-rider-queue-vram-tile-mapping-eight-20261103.json`, Git blob `e1102a691ac6e5da738187ac83fb69afed6f1497`. It includes every original source bank/address, raw destination, NMI-adjusted destination, sprite colour role, queue terminator, source ROM hash, source 24-tick PPU hash and exact Mesen workflow/head provenance. The independent ROM-free test `tests.unit.test_original_mesen_rider_full_dma_queue_receipt` freezes 233 transfers, the 64+64 genuine OBJ tile-word address sets, every NMI flag adjustment, the exact interleaving, and the unproven 3D/scanout flags. No additional emulator work is required to reproduce the original queued *destination* classification.

**Next actual geometry discriminator:** map the source ROM tile bytes referenced by each queued `source_bank_word:source_address_word` into exact 4bpp tiles and compare them to the authentic captured original VRAM tile payloads, with an explicit possible 1-frame/scanout timing offset. Only after assigning the graphics ID to source tile content should a source-aligned pose sampler drive or evaluate the experimental 2026 articulated GLB. The source's 24 phase states and 64 orientation indices are graphics-selection labels, not independently proved 15° wheel or 5.625° physical angle steps.

## Original ROM source-byte transfer timing: exact next-frame match

The existing `tools/art/audit_original_mesen_dma_source_tile_timing.py` executed successfully under the exact original-ROM/Mesen workflow in [run #41775009525](https://github.com/gamesbyian/UR-Recomp/actions/runs/41775009525), job `126393219592`, at implementation head `0841e1a97280eb5d39653f8730dc39547358ba4b`. The job's machine-generated `ART4K_ORIGINAL_ROM_SOURCE_DMA_BYTE_MATCHES` JSON compared every queued LoROM 32-byte source tile to the original SHA-locked 24-tick PPU VRAM snapshot at `tick-1`, `tick` and `tick+1`, using each queued effective destination after the original NMI address adjustment.

**All 203 transfers with an available next snapshot match all 32 ROM source bytes at `tick+1`, exactly 6,496/6,496 bytes.** This holds across ticks 1601 (27), 1602 (28), 1603 (28), 1605 (30), 1606 (30), 1609 (30) and 1610 (30), covering both racers' already-classified queue destinations. Tick 1624's 30 queued entries have no tick 1625 in the authenticated source archive and therefore **no next-frame test**; they are not failures, nor inferred matches. Current/same-tick matches vary (16/27, 8/28, 18/28, 10/30, 20/30, 18/30, 20/30, 19/30); this sharp delta is evidence that the queued source data is reflected in the next held PPU tick under the tested replay conventions.

The unit regression `test_actual_original_input_identity_and_all_233_source_entries` now also requires the exact seven-sample 203/203 next-frame match and excludes the missing 1625 boundary. This new test is a *subsequent commit* and needs its own exact-head CI qualification; the executed original-Mesen run above predates the stronger assertion. Do not assert a retroactively rerun emulator, actual PPU scanline start, exact intra-frame CPU/NMI timing, a physical wheel-angle mapping or a reconstructed original 1994 camera/mesh. The original 24×64 values remain **source graphics indices**.

**Next geometry discriminator:** treat 32-byte sprite tiles as identified source products, then determine whether *visible pixels* in successive authenticated source sprites can be explained by one shared projected articulated 3D mesh better than source-only palette/content changes and 2D translation/deformation nulls. Count only transitions with changed alpha/material boundaries, not tile updates whose visible alpha is unchanged. Preserve fixed geometry/camera, explicit red reflection, source timestamp and holdout declarations.

