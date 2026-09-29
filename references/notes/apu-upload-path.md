# CPU-to-APU upload path

Recovered: 2026-09-29

This note follows the SPC-family analysis in `references/notes/uniracers-spc-archaeology.md`.

## Result

The deterministic first-race route now exposes a concrete CPU-side audio transfer primitive.

A trace build armed only for SNES APU I/O writes at `$2140-$2143` recorded **6,691 writes across six guest frames, 957-962**, before `Race_ActiveState` became 1 at frame 984:

- `$2140`: 0 writes
- `$2141`: 0 writes
- `$2142`: 3,347 writes
- `$2143`: 3,344 writes

The traffic is therefore not an ordinary four-port command burst. It is a bulk-transfer protocol using `$2143` for payload bytes and `$2142` as a rolling echoed handshake/sequence byte.

The compact machine-readable result is:

- `analysis/generated/apu-upload-path-summary.json`

Reusable project-owned tools:

- `tools/find_mmio_access_sites.py`
- `tools/trace_apu_ports.py`
- `tools/analyze_audio_port_events.py`

## CPU routine

The static MMIO scan collapses the plausible executable accesses into a tight bank-02 cluster. The strongest transfer primitive begins at **`02:8298`**, named provisionally `APU_StreamTransfer`.

The decisive inner loop is visible directly in the candidate instruction neighborhoods:

- `02:82F0`: `LDA [$63],Y`
- `02:82F2`: `STA $2143`
- `02:82F5`: `XBA`
- `02:82F6`: `STA $2142`
- `02:8301`: `CMP $2142`
- `02:8304`: `BNE` back to the echo check
- `02:82F9`: `INY`
- `02:82FC`: `INC $65` when Y wraps, advancing the 24-bit source pointer rooted at direct-page `$63`
- `02:831C`: `LDA #$80`
- `02:831E`: `STA $2142`, followed by another echo wait

Immediately before the routine, `02:8294` is a JSR/RTL long-call wrapper. A small sibling helper at `02:8328` writes a paired value through `$2143/$2142` and waits for the `$2142` echo.

This is enough to call `02:8298` a CPU-to-APU byte-stream transfer routine with confidence 4. The exact higher-level packet/table semantics are still open.

## SPC byte-for-byte correlation

The traced `$2143` payload contains 3,344 bytes. Three `$2142`-only transitions split it into four chunks.

Those chunks correlate directly with the preserved SPC snapshots:

| Trace chunk | Trace bytes | Matching payload slice | APU RAM match |
| --- | ---: | --- | --- |
| 0 | 767 | all 767 bytes | `$B0E0-$B3DE` |
| 1 | 41 | bytes 2-40 | `$B3DC-$B402` |
| 2 | 2,120 | bytes 5-2,119 | `$B403-$BC45` |
| 3 | 416 | bytes 5-415 | `$BC46-$BDE0` |

Chunk 1 begins with two transfer-control/header bytes, `30 09`. Chunks 2 and 3 begin with five bytes each, `08 06 03 00 00` and `1F 33 03 00 00`. Chunk 1 intentionally/redundantly overlaps the prior data by three zero bytes.

After removing those 12 nonmatching control/header bytes and accounting for the 3-byte overlap, the runtime stream reconstructs **one continuous 3,329-byte APU-RAM region, `$B0E0-$BDE0`, exactly**.

SHA-256 of that recovered APU region:

`2574a4e8abb90cf8d6bc37763d967ef1c63246d0da7b28e4614187563c35c29d`

That full region is byte-identical at the same offsets in:

- 1st Race
- 2nd Race
- 3rd Race
- 4th Race
- 5th Race
- Unused Song 2

This materially strengthens the earlier classification of Unused Song 2 with the numbered-race family.

Related shared content also appears at shifted APU locations in other snapshots:

- Celebration carries the same matched chunks at shifted addresses.
- Title Screen shares the 2,115-byte middle chunk at `$8619`.
- Demo Race and Unused Song 1 share the final 411-byte chunk at `$7BA8`.

## What changed

The earlier SPC analysis established that large common APU ranges did not appear verbatim in the ROM. This trace explains part of that gap: the retail 65816 side actively streams audio-state bytes through the APU ports. The first-race transfer is not the already-mapped common BRR bank at `$3000-$5F87`; it reconstructs a high-RAM block at `$B0E0-$BDE0`.

That makes the next target much smaller and sharper: locate the caller and source-pointer/table setup for `02:8298`, rather than searching the entire ROM for APU snapshots.

## Next discriminator

1. Trace the caller/source pointer feeding `02:8298` and identify the ROM-side block/table that supplies `[$63],Y`.
2. Query SNESRecomp's already-existing `audio_events` ring around the same transition so request/apply/SPC-read traffic can classify the 12 control/header bytes.
3. Map the higher-level song/block selector table.
4. Test whether selectors for `Unused Song 1` and `Unused Song 2` are referenced by dormant retail code/data or are otherwise unreachable.
