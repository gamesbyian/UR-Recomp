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

The original #44 note placed the transfer boundary at `02:8298`. Static bytes and a follow-up first-race WRAM trace correct that boundary.

- `02:8294`: `JSR $8298; RTL`, a long-call wrapper around a short initializer.
- `02:8298-02:82A4`: `PHP; SEP #$20; STZ $68; REP #$20; STZ $6C; STZ $6A; PLP; RTS`. This is now `APU_TransferStateInit`.
- `02:82A5`: `JSR $82A9; RTL`, the public long-call wrapper `APU_StreamTransfer_Wrapper`.
- `02:82A9`: the actual `APU_StreamTransfer` body.

The transfer body begins by setting `$6F=$40`, preserving the caller's X in direct page `$83`, and reading `LDA $030000,X`. It then flows into the already runtime-proven transport loop:

- `02:82F0`: `LDA [$63],Y`
- `02:82F2`: `STA $2143`
- `02:82F5`: `XBA`
- `02:82F6`: `STA $2142`
- `02:8301`: `CMP $2142`
- `02:8304`: `BNE` back to the echo check
- `02:82F9`: `INY`
- `02:82FC`: `INC $65` when Y wraps, advancing the 24-bit working pointer rooted at `$63`
- `02:831C`: `LDA #$80`
- `02:831E`: `STA $2142`, followed by another echo wait

A small sibling helper at `02:8328` writes a paired value through `$2143/$2142` and waits for the `$2142` echo.

### ROM-side source seed

A static scan finds 12 long calls to `02:82A5`. Several are immediately preceded by `LDX #imm16`, yielding a compact family of bank-03 source seeds:

- `$FAD5`
- `$FB15`
- `$FB55`
- `$FBD5`
- `$FC15`

Six bank-83 callers use `LDX #$FB55` immediately before `JSL $82:82A5`.

The deterministic first-race WRAM trace independently confirms that seed. SNESRecomp records the transfer body's 16-bit `STX $83` state as paired byte writes sharing one block index. At frame 906 the first live pair is exactly `$83=$55`, `$84=$FB`, reconstructing **X=`$FB55`**. Subsequent pairs advance through `$FB56`, `$FB57`, and onward. Therefore the first-race transfer enters the bank-03 source at **`03:FB55`**, LoROM file offset **`0x01FB55`**.

This also explains why the earlier attempt to identify a standard stream solely through direct-page `D+$00` was too aggressive: the retail routine has its own directly observed bank-03 selector/cursor path, while `$63-$65` is a working pointer inside the transport.

The recovered `03:FB55` bytes settle the immediate format question. The first 64 bytes are not a `length16,target16,payload` stream; interpreted that way they would begin with an implausible 6,144-byte block targeting `$0627`, then run off the bounded window on the next header. Instead they match the control flow exactly: **64 one-byte selector slots**, containing unique IDs `$00-$30` sparsely among `$FF` sentinels. The live X cursor visits exactly `$FB55-$FB94` once while `$6F` counts down from `$40`. `$FF` slots are normally skipped within the same guest frame, while populated IDs consume transfer time.

The surrounding ROM contains a contiguous six-table ladder at 64-byte spacing:

| table | direct caller found | non-`FF` IDs | SHA-256 |
| --- | --- | ---: | --- |
| `03:FAD5` | yes | 25 | `8d4e4bfa27d9e3471fabdce635dfd21ff8ce39ae7aea9a8dc9180533d5e0e4c3` |
| `03:FB15` | yes | 19 | `960fd76d62a9b985ca50c1d1504aa98e8ec746ebfec7dd6cd71039bef6e32d2f` |
| `03:FB55` | yes; first-race live | 24 | `85c0973c8e26803e411b6e87cf350ea1c56300427097ff7cd5009296ca52febf` |
| `03:FB95` | **no direct `JSL $82:82A5` caller found** | 22 | `ba06845292e028a708c216703526c0d30c4a0ada66cf7eab332035c025408b74` |
| `03:FBD5` | yes | 21 | `12dd26f1219b3688b75139b8e349ae328395741a3dc2e713f98683d0f87a44f1` |
| `03:FC15` | yes | 23 | `e4479b21aad06acd4f26749ab30842f5ae2bc746fcc5fc8ce60f1866c06a2ba0` |

`03:FB95` is therefore a concrete dormant/unreferenced **audio package selector-table candidate** in retail data. It is not yet identified with either tagged unused song; that requires mapping selector IDs through the block resolver and associating the table callers with song/package states.

Across all six tables, the populated IDs have an exact union of **50 values, `$00-$31`**, with no gaps and no values outside that range. Within each table every populated ID is unique. This establishes a 50-block selector namespace. The 64-byte table controls an ordered/subset package selection over those 50 blocks, with `$FF` meaning “skip this slot.”

The uncalled `03:FB95` table is particularly structured: it preserves the order/positions of `03:FAD5` and differs only by replacing three IDs, `$07`, `$15`, and `$29`, with `$FF`. That is strong evidence that it is an intentional package variant rather than unused padding, though its game-facing meaning remains unassigned.

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

That target is now narrower still: the first-race caller/source seed is `03:FB55`, with a small cluster of sibling seeds nearby. The next task is to decode that ROM-side serialization and determine how those seeds correspond to audio packages/song selectors.

## Next discriminator

1. Decode the bytes beginning at first-race source `03:FB55` and compare sibling seeds `03:FAD5`, `03:FB15`, `03:FBD5`, and `03:FC15`.
2. Correlate the ROM serialization with the already-established `$2143` chunks and the retained SNESRecomp `audio_events` request/apply/SPC-read chains.
3. Map the higher-level package/song selector relationships represented by the clustered seeds and their callers.
4. Test whether selectors/data for `Unused Song 1` and `Unused Song 2` are referenced by dormant retail code/data or are otherwise unreachable.
