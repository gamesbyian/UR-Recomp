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


## Package caller and dormant-table reachability

A reusable canonical-ROM analysis now maps exact direct package callers by requiring the byte pattern `LDX #imm16 ; JSL $82:82A5`, and separately scans raw 16-bit table-seed occurrences as weak candidates.

Direct callers recovered:

| table | exact direct callers |
| --- | --- |
| `03:FAD5` | `02:E0CC`, `03:A63D` |
| `03:FB15` | `00:9459` |
| `03:FB55` | `03:CA22`, `03:CA67`, `03:CAAC`, `03:CAF1`, `03:CB36`, `03:CB7B` |
| `03:FB95` | **none** |
| `03:FBD5` | `00:A103`, `03:A757` |
| `03:FC15` | `03:A530` |

This reproduces the twelve direct callers while making their table ownership explicit.

A whole-ROM raw-word scan finds only three other occurrences of the `FB95` low-word seed, near `05:9C05`, `18:B111`, and `18:D84F`. Their surrounding bytes do not match the direct load/call form and are retained only as weak candidates. Therefore no obvious static code reference to `03:FB95` is currently known. This materially strengthens the dormant/unreferenced interpretation, but does **not** prove runtime unreachability: an address could still be computed indirectly.

The table relationship is exact and especially informative: `03:FB95` is a slot-preserving subset of `03:FAD5`, differing at exactly three positions. It replaces block IDs `$15`, `$29`, and `$07` with `$FF` at one-based selector slots 29, 33, and 49 respectively. It adds no blocks of its own.

That turns the next discriminator into a bounded question: determine what blocks `$07`, `$15`, and `$29` contribute to the loaded APU image/package, and compare those contributions with the Demo Race / Unused Song 1 and numbered-race / Unused Song 2 SPC-family differences. If one family is explained by exactly those omissions, `FB95` can be attributed much more strongly. If not, retain it as a dormant package variant without overclaiming song identity.

Durable machine-readable result:

- `analysis/generated/audio-package-map.json`
- `tools/analyze_audio_packages.py`


### Omitted-block SPC correlation

The three blocks omitted by `03:FB95` have now been compared directly against all ten preserved SPC APU-RAM snapshots. The SPC archive is acquired transiently and fingerprint-verified; only derived measurements are retained.

- **Block `$15`**: payload length 2,578. After four framing bytes, the remaining **2,574 bytes occur in every one of the ten SPC snapshots**. The numbered races and Unused Song 2 place that body at `$CA29`; Demo Race and Unused Song 1 place it at `$B9B5`; Title and Celebration use shifted locations. This is broadly shared package material, not a song-family discriminator by itself.
- **Block `$29`**: payload length 256. After one framing byte, **255 bytes occur at `$E3A3` in Demo Race and Unused Song 1**. Celebration has a related 252-byte suffix at `$CA83`. No corresponding substantial match was found in Title, any numbered race, or Unused Song 2. This is strong additional evidence tying block `$29` to the Demo/Unused Song 1 family.
- **Block `$07`**: payload length 10,894. After one framing byte, **10,893 bytes occur at `$CB7C` only in Celebration** among the ten snapshots. This gives block `$07` a strong Celebration-specific signature in the current corpus.

Therefore the dormant `FB95` variant removes three qualitatively different contributions from `FAD5`: one ubiquitous block (`$15`), one Demo/Unused Song 1-family block (`$29`), and one Celebration-specific block (`$07`). That makes it unlikely that `FB95` is simply a complete package for either currently tagged unused song. A more plausible interpretation is a deliberately reduced package variant whose game-facing selector/caller was removed or became unreachable. This remains provisional until caller-side selector semantics are decoded.

Durable result:

- `analysis/generated/audio-block-spc-correlation.json`
- `tools/correlate_audio_blocks_spc.py`


### Caller-side setup selector gaps

The repeated call immediately before each known package transfer has now been scanned independently. The exact form is `LDX #imm16 ; JSL $82:807E`.

Across the complete retail ROM, the observed setup-selector values are:

`$32, $33, $34, $35, $36, $37, $38, $39, $3A, $3C, $3E, $3F, $40, $41, $42`.

Within the dense range `$38-$42`, **only `$3B` and `$3D` are absent entirely** from exact setup calls. Every other value in that range is present and pairs directly with a known package table:

- `$38 -> FB15`
- `$39 -> FBD5`
- `$3A -> FAD5`
- `$3C -> FC15`
- `$3E/$3F/$40/$41/$42 -> FB55`

No `$3B` or `$3D` setup call survives elsewhere in the ROM, so neither merely lost its immediately adjacent package transfer.

This is structurally interesting because the preserved SPC set contains exactly two tagged unused songs, but **that numerical coincidence is not yet evidence that selectors $3B/$3D are those songs**. The next discriminator is the semantics of routine `02:807E` and the surrounding selector sequences. If `$82:807E` is a song/program-selection primitive, the two holes become a strong unused-content lead; if it configures an unrelated resource type, the coincidence should be discarded.

Durable result:

- `analysis/generated/audio-setup-selector-map.json`
- `tools/scan_audio_setup_selectors.py`


### Setup routine decoded: direct block uploads

The bounded static extraction resolves the semantic class of the repeated `JSL $82:807E` setup calls.

- `02:807E` is a long-call wrapper: `JSR $8082; RTL`.
- `02:8082` saves caller state, begins the SPC handshake, calls `02:812A APU_ResolveBlockPointer` with the caller's X value, and transfers the resolved record through the APU ports.
- Therefore the observed immediates `$32-$42` are **audio block IDs**, continuing beyond the first 50 records (`$00-$31`) referenced by the six 64-byte package tables.

This materially changes the interpretation of the `$3B/$3D` gaps. They are not merely missing high-level selector numbers. They are missing direct calls to two block IDs inside a dense run of directly uploaded audio records. The next discriminator is to parse the physical block pool through `$42` and test whether records `$3B` and `$3D` exist and, if so, whether their payloads fingerprint either tagged unused-song SPC family.

The routine is promoted as `APU_UploadBlockById_Wrapper` at `02:807E`. The inner body at `02:8082` remains available for a later finer symbol split if useful.


### Retail unused-song blocks recovered

Extending the physical audio-record pool beyond the 50 package-table IDs (`$00-$31`) resolves the two tagged unused compositions directly.

The dense direct-upload family `$38-$42` maps as follows. In each matched record, the first four bytes are transfer framing and the remaining payload appears at APU RAM `$1D00`:

| block ID | retail exact setup call | SPC payload identity |
| --- | --- | --- |
| `$38` | yes | Demo Race, 2,899 bytes |
| `$39` | yes | Title Screen, 2,200 bytes |
| `$3A` | yes | Celebration, 1,592 bytes |
| **`$3B`** | **no** | **Unused Song 1, 532 bytes** |
| `$3C` | yes | no substantial match in the ten preserved snapshots |
| **`$3D`** | **no** | **Unused Song 2, 2,532 bytes** |
| `$3E` | yes | 1st Race, 2,457 bytes |
| `$3F` | yes | 2nd Race, 1,853 bytes |
| `$40` | yes | 5th Race, 1,981 bytes |
| `$41` | yes | 3rd Race, 2,623 bytes |
| `$42` | yes | 4th Race, 1,649 bytes |

The two holes previously observed in the exact `LDX #block ; JSL $82:807E` call sequence are therefore the two unused-song records themselves:

- **block `$3B` = Unused Song 1 program block**
- **block `$3D` = Unused Song 2 program block**

This establishes that both unused songs are physically present as ordinary members of the same retail audio-block family as the used title/demo/celebration/race programs. Their immediate upload callsites are absent from the exact retail setup-call corpus.

This is stronger than the earlier SPC-family clustering: it identifies the actual ROM-side records. It still does not by itself prove absolute runtime unreachability, because a computed/indirect invocation could theoretically select either ID. The next reachability check is therefore exhaustive direct-call accounting for `02:807E` plus targeted searches for non-immediate/computed selectors `$3B/$3D`.

The dormant `03:FB95` 64-byte package table should now be treated as a separate question. It is no longer needed to explain the existence of either unused song.

Durable result:

- `analysis/generated/audio-extended-block-correlation.json`
- `tools/correlate_audio_blocks_spc.py`


### Unused-song direct reachability closeout

A complete direct-call accounting was run after identifying blocks `$3B` and `$3D` as the retail records for Unused Song 1 and Unused Song 2.

Results:

- there are **36** direct `JSL $82:807E` calls in the complete retail ROM;
- **all 36** are immediately preceded by an `LDX #imm16` block ID;
- there are **zero** unbound direct wrapper calls;
- there are **zero** raw `LDX #$003B` or `LDX #$003D` instruction byte patterns anywhere in the ROM;
- the only direct call to inner upload body `02:8082` is the wrapper's own `JSR $8082` at `02:807E`;
- no direct `JSL $82:8082` bypass exists.

Within the direct static call graph, the two unused-song records therefore have no selection path. This is strong retail unreachability evidence for ordinary direct invocation. It does not mathematically exclude a computed X value followed by an indirect/code-generated transfer path, but no such path is currently evidenced and the normal block-upload primitive is exhaustively accounted for.

The two unused songs can now be described precisely as **retained retail audio records with their ordinary direct selection callsites absent**.

Durable result:

- `analysis/generated/audio-unused-reachability.json`
- `tools/scan_audio_setup_selectors.py`

### Full package signatures close the likely unused-song packages

The earlier three-block comparison has now been expanded to the complete package-table
block universe. Workflow run `36777071311` correlates all records `$00-$31` against
all ten preserved SPC snapshots. Its transient SPC archive is the same pinned public
artifact used earlier (491,821 bytes; SHA-256
`85a3f00cfe46cddd18caa714374ef54da6835f0d293557ce499de352b8d4fdb0`).

Block `$00` is the only record shorter than the correlator's 32-byte minimum
(`22` payload bytes), so it is the sole mechanically untestable package member.
Excluding only that record, the method first reproduces every known reachable package
mapping exactly:

- Title Screen -> `03:FBD5`;
- Demo Race -> `03:FB15`;
- Celebration -> `03:FAD5`;
- all five numbered races -> `03:FB55`.

That successful calibration makes the two unused results substantially stronger:

- **Unused Song 1 has the exact same 18-block correlatable package signature as
  Demo Race -> `03:FB15`.**
- **Unused Song 2 has the exact same 23-block correlatable package signature as
  every numbered race -> `03:FB55`.**

The latter is independently corroborated by the earlier live first-race transfer, whose
3,329-byte APU region at `$B0E0-$BDE0` is byte-identical at the same offsets in
Unused Song 2.

Compact durable evidence:

- `analysis/generated/audio-package-spc-signatures.json`
- `analysis/generated/audio-unused-path-analysis.{json,md}`
- `analysis/generated/audio-record-pool-reconciliation.md`

This means `03:FB95` should remain classified as an intentional dormant/reduced package
variant, not the likely complete package for either preserved unused song.

### Song record 3B/3C relationship and causal test

A canonical pairwise comparison also found that unused record `$3B` and reachable
record `$3C` are exceptional near-duplicates: both payloads are 536 bytes, they share
a 165-byte prefix and 10-byte suffix, and only 16 byte positions differ. The reachable
`$3C` path uses package `03:FC15`, so that package remains a useful sequence-sibling
control even though the full SPC signature identifies `03:FB15` for Unused Song 1.

The project now has two fail-closed causal-test helpers:

- `tools/patch_unused_audio_counterfactual.py` changes only the verified selector byte
  inside a known-good setup/package pair;
- `tools/verify_unused_audio_trace.py` requires the complete post-header song body to
  appear contiguously in the captured `$2143` transfer stream.

Primary counterfactuals are therefore:

1. Demo path `$38 -> $3B` while retaining package `03:FB15`;
2. first-race path `$3E -> $3D` while retaining package `03:FB55`.

The normal direct selection callsites for `$3B/$3D` remain absent in retail; these
counterfactuals are research fixtures, not claims of surviving retail reachability.

