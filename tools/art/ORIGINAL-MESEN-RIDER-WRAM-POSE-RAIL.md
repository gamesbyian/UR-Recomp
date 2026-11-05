# ART-4K: optional original Mesen rider WRAM rail for 3D pose identifiability

**Consolidated implementation (2026-11-04):** Two independent options coexist on one original-Mesen capture: `--include-rider-wram` is the targeted executed CPU writer/queue probe from #3110, and `--include-rider-wram-full` is the entire 6 KiB *post-frame* WRAM snapshot described here from #3109. The manual workflow option for this full snapshot is `include_rider_wram_full`, false by default. Both options may be enabled together and have separate hashes and semantics, with no second original ROM replay. Historical original #3109 design sections below use the previous shared option name; use the consolidated flags for execution.

**Status: implementation proposed, not an executed capture.** This opt-in extends the existing pinned original-ROM Mesen PPU workflow. It adds no recurring work and leaves every default historical PPU/OAM/VRAM/CGRAM/P6 receipt unchanged. It is a narrowly scoped opportunity to validate *actual animation state* before another arbitrary 2026 GLB phase sweep.

## Why this is the next discriminating source observation

The already merged original 24 consecutive no-frame-skip Mesen observations (bridge ticks **1601–1624**, original-source ZIP SHA-256 `28dda3647fecb382fdbf824da7383a8116080df6ec8c98da0b3357a018986cf6`) show both racers' original OAM sprite **tile index, palette, size and flips unchanged**, while their underlying 4bpp VRAM tile contents change on all 23 observed adjacent transitions. The original sprite graphics producer or DMA writer PC has **not** been dynamically identified. The original 1994 3D skeletal/geometry source is likewise unverified.

The imported reference decompilation includes the following **static labels/hypotheses**. These are reverse-engineering aids, **not independently observed executed 1994 writer addresses**:

| Reference source label/address | Meaning as documented | Observation needed |
|---|---|---|
| `83:ED33` `Rider_UpdateAnimFrame` | Computes rider frame and wheel phase, with 24-state annotations | Repeated source working-RAM state at genuine adjacent Mesen bridge ticks |
| `83:EF10` `Rider_UpdateBodyLean` | Updates body lean/angle | Distinguish the current-rider workspace from P1/P2 persistent slots |
| `83:F0BB` `Gfx_QueueRiderTileDma` | Writes source address/bank/destination transfer-list arrays | Capture exact RAM array contents, remembering NMI may have already consumed them |
| `82:B8AB` `Nmi_FlushTileDmaList` | Flushes queued 32-byte VRAM tile transfers | A subsequent *execution breakpoint or write event*, if needed; do not infer execution from stale queue memory alone |

Known relevant original **7E:** WRAM offsets (imported `decomp/ram.txt` and existing `analysis/generated/mesen-symbols.mlb`):

- `0300` alternate render/buffer phase; `0306` pending tile-DMA request flag.
- `04C7` P1 persistent pitch/orientation; `04C9` P2 persistent pitch/orientation. `0F49` is a **current-player workspace**, so it cannot be casually assigned to P1.
- `0F83` current rider wheel rotation/presentation frame (candidate 24-state phase); `0F8F` signed wheel spin speed; `0F97` working presentation ID; `0F77` body/frame working selection; `0FD9` overlay selector. These labels are imported or historical, and may alias, be stale after a player pass, or be implementation-specific.
- `15A1` source-bank DMA table; `1645` source-address table; `16E9` VRAM destination table, each **162 bytes** by the imported reference. All fall within `0000..17FF`.

## Proposed bounded collection

The existing `.github/workflows/art4k-live-original-mesen-ppu-raw.yml` gains one optional manual `include_rider_wram_full` **boolean, default false**. When true, the existing source-verified `tools/art/capture_original_mesen_ppu_raw.py` reads `snesWorkRam` addresses `0x0000..0x17FF` (**6144 bytes**) once for each already-selected original Mesen bridge tick, after the held PPU state and optional P6 export, **without advancing the emulator in between**. This is six additional 1,024-byte read calls per snapshot and at most **24 × 6,144 = 147,456 extra raw WRAM bytes** in the one capture. Everything is SHA-256 pinned, under exact filenames `frame-NNNNNN-wram-0000-17ff.bin`, in the existing source artifact. The original 24-tick range remains capped by the preexisting workflow.

Each optional frame carries only the declared `source_original_rider_work_ram_0000_17ff` file receipt, offset, memory type, capture order, byte length and hash. The top-level manifest explicitly records three *nonclaims*: the queue may be **post-NMI and emptied**, the actual CPU/DMA graphics writer PC is **unidentified**, and the original 1994 3D pose is **not recovered**. Validation rejects incomplete, corrupted, symlinked, misaddressed or unclaimed WRAM files, nonboolean opt-in values and premature emulator advances during reading. Old captures continue to pass unchanged without any WRAM keys.

**Predeclared prospective use, only once qualified and explicitly dispatched:** one run using genuine original bridge ticks `1601,1602,...,1624`, with frame skip disabled. Require old/new overlap at original 1601/1607/1618 in OAM, VRAM, CGRAM and P6 against the previously merged SHA-locked original source before interpreting any WRAM phase. Read the fixed P1/P2 persistent slots and current-player workspace separately; compare candidate original wheel phase/animation state against actual original 4bpp tile-content transitions. Interpret each offset with signedness and field-lifetime qualifications. Do **not** pick a wheel period by circularly choosing the GLB's best-fitting rendered frame. If the frame-boundary queue has already been consumed, an exact execution breakpoint at the annotated writer is the next **separate** experiment, rather than trying to infer the writer PC from a zero queue.

**No new capture has been executed by this change.** In particular, no authenticated original 1994 model, rig, bone hierarchy, 3D camera, artwork likeness, source-to-2026 material semantics, original wheel rate, or shipping acceptance follows from merely implementing a WRAM sidecar. The current 2026 five-parent GLB remains experimental and draft #2832 remains unapproved.

## Offline decoded candidate-word reader

The proposed optional source rail is paired with `tools/art/audit_original_mesen_rider_wram_fields.py`, a standard-library-only post-processing tool. It first invokes the existing **entire PPU + optional WRAM original-capture manifest verifier**, including all SHA-bound OAM/VRAM/CGRAM/P6/WRAM files and exact original ROM/replay/Mesen source identities. It refuses legacy captures without the explicitly opted-in WRAM sidecar. It then emits the raw little-endian unsigned/signed 16-bit values at the documented candidate offsets, and independently SHA-pins the three 162-byte DMA list array slices. The first four raw u16 values and first sentinel `FFFF` position are reported as *potential queue memory*, never as a proven transfer. Source bytes, emulator frame-step, controller masks and executable SHA stay bound to each record.

```sh
python3 -m tools.art.audit_original_mesen_rider_wram_fields \\
  --source-dir /private/new/mesen-original-ppu-plus-rider-wram/ \\
  --out /private/new/original-rider-raw-candidate-words.json
```

This reader must **not** interpret the current-player scratch field `0F49` as persistent P1 orientation, claim queue entries are still pending post-NMI or identify a physical wheel angle from the raw 0F83 word. Four additional ROM-free tests cover signed little-endian interpretation, complete candidate field/queue slices, a same-tick synthetic live-capture roundtrip, tampering and correct refusal of default PPU-only archives. The offline reader produces no new source observation until an actual original emulator run has been performed.

## Qualification

The opt-in must preserve existing regular Mesen raw PPU semantics. **Qualification enhancement:** the existing PR-triggered original-emulator proof explicitly enables the 6KiB WRAM sidecar for its already scheduled two-frame Mesen capture, checking the actual Mesen `snesWorkRam` namespace, same-emulator-tick snapshot, original PPU-plus-WRAM SHA manifest and complete output. No additional workflow job or scheduled replay is added. When `workflow_dispatch` is used manually, `include_rider_wram_full` remains default **false**, so the historical original capture behavior does not change. The source WRAM proof on PR is only two frames and therefore **does not** constitute an observed 24-tick original animation phase rail; that still requires a deliberately selected future 1601–1624 one-off run.

The opt-in must preserve existing regular Mesen raw PPU semantics. ROM-free synthetic tests require the exact 6144-byte read schedule, unchanged default selection, correct same-tick binding, SHA/metadata verification and refusal to overclaim CPU writer or 1994 pose, invalid boolean types, and emulator advancement during WRAM read. The existing Mesen workflow is the only integration point; no new hosted cron or recurring source-ROM workflow.

Run `python3 -m unittest tests.unit.test_capture_original_mesen_ppu_raw` and the existing tooling-unit/hygiene jobs. An **independent source review and exact-head CI** remain necessary before merging or dispatching the optional original evidence run.
