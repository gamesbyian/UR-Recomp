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
