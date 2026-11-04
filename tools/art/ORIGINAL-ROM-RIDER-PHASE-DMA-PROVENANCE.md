# ART-4K: retail-ROM rider state and graphics DMA, machine-code verified

**Original retail code evidence, 2026-11-03 local / 2026-11-04 UTC.** This note links actual, directly verified original USA ROM instructions to the independently executed 24-tick original Mesen source-OBJ sprite capture. The objective is to replace arbitrary experimental wheel angular speeds and frame-lean timing with the game's authentic **discrete representation state** as soon as those internal state values are instrumented. No 1994 3D model, camera, joints, geometry or drawing algorithm has been recovered here.

## Sources and exact identity

The 2,097,152-byte headerless USA retail ROM is already in the repository at `reference/roms/retail/Uniracers_USA.sfc`, SHA-256 `859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478`. This is exactly the ROM SHA held by the original Mesen capture, not an imported prototype, disassembler-generated pseudo-ROM or experimental GLB. Its Git blob SHA is `2b208c3f80f6c9549dd73d2a64cf79a8b178aa71`. The original **24 truly consecutive executed ticks 1601–1624** remain the byte-validated no-frame-skip archive merged through [#3103](https://github.com/gamesbyian/UR-Recomp/pull/3103), SHA-256 `28dda3647fecb382fdbf824da7383a8116080df6ec8c98da0b3357a018986cf6`. The Mesen PPU archive proves original OAM/VRAM/CGRAM and completed-screen bytes; **it does not contain sampled game WRAM phase/angle registers or executed CPU program counters**.

The imported reverse engineering symbols, from `reference/imported/reverse-engineering/baldosa-uniracers-recomp/`, provided **candidate** code locations. They were checked directly against **fourteen exact machine-code byte sequences** from the actual retail ROM. PC addresses below are SNES LoROM `bank:address`; the verified mapping is `(bank & 0x7f)*0x8000 + (address & 0x7fff)` for original high code banks 82/83, with no copier header. Source instructions have now been verified independently of symbol names.

## What the original machine code actually establishes

| Original SNES program counter | ROM-verifiable effect | Reconstruction relevance |
|---|---|---|
| `83:ED33` | Calls original per-rider state update at `83:EF10` before subsequent presentation bookkeeping | Current rider state is produced by code, not an editorial sprite strip |
| `83:EE53` | Adds to RAM `$0F83`, wraps below 0 and above/equal `0x18` (24) | **24-state source presentation phase**, not 24 physical degrees |
| `83:EED9` | Loads `$0F83`, shifts left **six** and adds `$0F77` for an indexed lookup | Rider presentation lookup combines phase and a secondary state; phase ×64 is a **table-addressing scale**, not a recovered 3D transform |
| `83:F054` | Masks and stores RAM `$0F49` with `0x003F` | **64-value rider angle index**; its geometric meaning, origin and camera mapping remain unverified |
| `83:F0D7` | Reads the two rider presentation IDs `$0FE9 / $0FEB`, staging them in RAM `$0200 / $0204` | Shared graphics composition receives per-rider frame selection |
| `83:F296` | Computes `id*3 + 0x8000` and reads a packed entry from bank `$20` | Original graphics source is selected by **three-byte table entries**; this is a real ROM-addressed data path |
| `83:F188` | Initializes tile destination cursor `$26` to VRAM word `$6000` | Queue starts in the source-observed racer OBJ VRAM region |
| `83:F21A` | Writes computed source addr to `$1645,Y` and bank to `$15A1,Y` | Explicit actual DMA queue fields in WRAM |
| `83:F26B` | Writes destination word to `$16E9,Y`, advances queue index; loops tile-grid columns/rows | Explicit destination field, 16-word increments and row stride |
| `83:F282` | Stores negative source-bank sentinel at `$15A1,Y` and sets `$0306` nonzero | Producer marks DMA transfer list ready |
| `82:B8AB` | NMI consumes pending `$0306`, sets VRAM increment and DMA channel-0 mode/destination register | Real original SNES VRAM upload pathway |
| `82:B8E3` | Reads `$15A1` source bank and `$1645` source address, writes DMA registers `$4304/$4302` | Queue is consumed by NMI |
| `82:B8F4` | Reads `$16E9`; when destination bit `0x0080` is set, adds VRAM word `0x0800`, then writes `$2116` | Two candidate OBJ VRAM banks from one queued address representation |
| `82:B902` | Triggers DMA with `$420B = 1` and prepares `$4305 = 0x0020` for 32-byte tile transfers | One 8×8 4bpp tile per normal list entry |

The bank `$20:8000` 3-byte pointer table is not to be confused with the bank used by an unrelated `$8008,Y` lookup. CPU data-bank identity and the *executed* intermediate lookup results are **not established** by this static audit. No reverse engineering symbol string is treated as proof of its author's semantic naming.

## Independent source graphics connection

The held Mesen original 2D sprites use source OAM slots 96 (blue) and 97 (red). For **every one of 24** original captured ticks, both keep fixed OAM tile number, relevant palette and H/V flip flags; their **64 original 8×8 backing VRAM tile word addresses** also remain fixed. The original VRAM tile payload changes across **all 23 real adjacent transitions** per racer, not only when OAM positions move. The verified source addresses are:

| Source original rider | First observed 4bpp tile word | Last observed tile word | Source fixed OAM tile |
|---|---:|---:|---:|
| Red, slot 97 | `0x6000` | `0x6780` | 0 |
| Blue, slot 96 | `0x6880` | `0x6FF0` | 136 (`0x88`) |

The ROM-verified NMI destination-bit rule maps example queued word `0x6000` to actual VRAM `0x6000`, and queued word `0x6080` to actual VRAM `0x6880`, matching the **start words of the two observed source-racer regions**. This is a strong structural connection from original code to original PPU evidence. It does **not** yet show the queue entry `0x6080` occurring on any captured tick, identify the entire actual DMA-list contents, prove every observed changed 8×8 tile came from this precise queue, or rule out other runtime writing paths.

The earlier source-only VRAM audit [#3104](https://github.com/gamesbyian/UR-Recomp/pull/3104) measured **1,457 blue / 1,565 red changed tile-byte instances** across 23 adjacent transitions, with a **15-tile burst** at blue tick 1602→1603 and red tick 1605→1606. This narrower original-code proof makes direct verification of those two bursts' queue provenance an economical next step.

## Concrete next experiment for 3D identifiability

**First reuse existing instrumentation.** The target is a *single bounded* original-run observation of the actual values and provenance at **ticks 1602/1603 and 1605/1606**, plus one ordinary adjacent edge 1609/1610. Preserve original ROM SHA, exact Mesen binary and controller replay, no skipping, source OAM/VRAM/CGRAM and completed-screen identity. Record enough original *work RAM* and CPU/DMA state to determine whether:

1. `7E:0F83` (24-state phase), `7E:0F49` (64-value angle index), `7E:0F77` (lookup offset), and `7E:0F97` (shared presentation ID) are the *actual* state used to select the observed rider sprites. These are shared working state addresses and require per-player call-boundary attribution, **not** arbitrary per-frame fixed player labels.
2. Persistent player presentation IDs `7E:0FE9` / `7E:0FEB` and DMA queue `7E:15A1 / 1645 / 16E9`, pending `7E:0306` and frame-bank selector `7E:12EB` agree at a defined CPU/NMI point. An end-of-frame WRAM value by itself might be too late or belong to the other player.
3. The original execution actually reaches `83:ED33`, `83:F0BB`, and `82:B8AB` for these transitions; record queue source bank/address/destination **before NMI consumes and clears it**, and verify the destination addresses intersect the independently observed changed VRAM tile addresses.

The correct next experiment should use **one** carefully chosen, bounded original-emulator replay or existing equivalent trace, never add a recurring capture workflow. First check the current Mesen bridge debugger callback/WRAM read capabilities; if it cannot trace actual execution, document that blocker before modifying an emulator. Predeclare capture semantics, output SHA, old overlap checkpoints, and a clear negative condition. Do not try to infer wheel angular degrees by fitting these code indices to the already examined 2D sprites.

Only *after* runtime state aligns with original source and individual racer ownership can the 2026 five-parent rig receive **frame-index-conditioned** poses as an experimental mapping. It must preserve one fixed 3D geometry and camera, no per-frame source-pixel translations or material remappings, and separate actual PPU source colours from 2026 model part/material IDs. The current +24° per tick was arbitrary; 24-state and 64-state **code domains** provide a physically more plausible experiment protocol but do **not** establish any 1:1 angle or 3D geometry.

## Reproduce, validate and gates

```sh
python3 -m unittest tests.unit.test_audit_original_rom_rider_phase_dma
python3 -m tools.art.audit_original_rom_rider_phase_dma \
  --rom reference/roms/retail/Uniracers_USA.sfc \
  --source-zip analysis/data/racer-original-mesen-consecutive-1601-1624-20261103.zip \
  --out /private/new/original-rom-rider-phase-dma-proof.json
```

The tool authenticates the retail ROM, the complete Mesen source archive and fourteen code instruction windows, then verifies all 64 observed tile target words for both original players throughout 24 real executed frames. The canonical JSON receipt is `analysis/data/racer-original-usa-rom-phase-dma-source-witness-20261103.json`, SHA-256 `538fe21cac2dd5b0e627e75136cda31c451e459ceb6f789ad046d35deb53eeab`, LF-only, atomic exclusive no-overwrite. All **6 focused stdlib tests** passed against actual original ROM and original PPU archive on the HP in under one second. Separate source review and exact-head hosted qualification remain mandatory; no original game CPU writer PC has been recorded in motion, 1994 3D source mesh recovered, owner likeness approved or Windows release gate changed.
