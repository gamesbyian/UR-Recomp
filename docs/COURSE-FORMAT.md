# Course Format Investigation

Goal: produce a ROM-free technical description of Uniracers/Unirally course data and a parser that operates locally on a user-supplied ROM.

## Historical leads

Historical reports identified Rob Northen Compression for level/course data. The most useful historical course-layout observations are normalized in `references/notes/course-layout-history.md`. Local analysis confirmed 45 valid RNC Method 1 streams in the canonical USA retail ROM and 1994-11-29 PAL prototype, byte-identical at identical offsets. The newly acquired historical GoodSNES beta shares all 45 byte-for-byte as well. Europe retail also contains 45 streams, of which 38 are byte-identical by content; ordinal streams 4, 16, 20, 26, 27, 35 and 36 have changed packed/unpacked sizes and CRCs. The remaining question is what each decoded stream contains and how these seven final-PAL changes map to course or other semantics.

## Questions

1. Where is the course index/table?
2. How exactly does the game invoke RNC Method 1, and does its decoder structurally match the preserved ProPack SNES routine?
3. What constitutes a course record?
4. What are the dimensions and coordinate units?
5. How are track geometry and visuals related?
6. How are start, finish, checkpoints, hazards, boosts, jumps and stunt-relevant surfaces encoded?
7. Are palettes/themes separate from geometry?
8. Does each course contain metadata or use parallel tables?
9. Can original data be decompressed and losslessly recompressed?
10. Can custom course data be loaded without changing physics code?


## RNC reference implementation now preserved

The repository now contains a byte-preserved mirror of the public RNC ProPack 2.14 package at:

`references/imported/tools/rnc_propack-2.14/`

Most useful files for this investigation:

- `SOURCE/SUPERNES/RNC_1.S` — SNES Method 1 unpacker
- `SOURCE/SUPERNES/RNC_2.S` — SNES Method 2 unpacker
- `PROPACK.TXT` / `PROPACK.DOC` — original format/tool documentation
- `PPIBM.EXE` — original DOS packer

The manual describes Method 1 as prioritizing compressed size and Method 2 as prioritizing unpack speed, with Method 1 the packer's default.

### Current reproduction plan

1. [done] Extract and independently decompress all 45 confirmed Method 1 streams; all 180 streams across four preserved builds pass packed and unpacked CRC16 validation. Paired USA/PAL decoded differences are confirmed at streams 4, 16, 20, 26, 27, 35 and 36.
2. Generate a compact manifest with offsets, hashes, byte statistics and structural signatures.
3. [done] Identify the game's decompression routine and compare it structurally with preserved SNES `RNC_1.S`: USA/legacy-beta `01:B8F1`, Europe retail `01:B8E2`, 1994-11-29 PAL prototype `01:B8D1`. The distinctive entry and Huffman/bit-reader structure survives directly in the shipped code.
4. Test the historical 256-tile-width and 64x64-block claims against decoded bytes.
5. Associate decoded records with course loads and Halamantariel/VGMaps maps.
6. Identify course index/pointer tables and only then assign semantic names such as geometry, block dictionary, tilemap or metadata.


## Verified decoded corpus

Generated outputs:
- `analysis/generated/rnc-stream-manifest.json` — machine-readable stream offsets, sizes, CRC-derived verification, decoded SHA-256 hashes and basic structural metrics.
- `analysis/generated/rnc-stream-manifest.md` — compact human-readable summary.
- `tools/rnc_method1.py` — independent Method 1 decoder.
- `tools/analyze_rnc_streams.py` — deterministic corpus verifier/manifest generator.

All 45 USA decoded outputs are unique. Their unpacked sizes range from roughly 33.8 KiB to 65.4 KiB. None has a total size divisible by 256 or 4096, so the historical “256 wide” and “64×64 block” claims cannot be interpreted naively as the entire decoded stream being a raw rectangular byte array. A header, variable-length records, multiple planes/tables, or non-byte-sized units remain plausible and require direct structural testing.


## Shipped decompressor landmark

The canonical USA ROM's Method 1 unpacker begins at ROM offset `0x00B8F1` / LoROM `01:B8F1`. The legacy beta uses the same location. PAL builds move the routine slightly earlier: Europe retail to `01:B8E2`, and the November prototype to `01:B8D1`.

This is now a useful bridge between packed data and code archaeology. The immediate course-loader task is to find callers of this routine and the pointer/index structure that selects one of the 45 packed streams, then follow the destination buffer into the historical `7E:2080` tilemap breadcrumb or another verified runtime consumer.


## First decoded course-header field identified

The 45-stream corpus now aligns strongly with the shipped 45-track/tour structure.

External gameplay documentation gives a fixed five-track order for every tour: Race, Circuit, Stunt, Race, Circuit. The nine decoded streams at ordinal positions 3, 8, 13, 18, 23, 28, 33, 38 and 43 are exactly the nine streams whose decoded byte offset 2 is `0x2D`; all remaining 36 streams have `0x00` there. Independent gameplay documentation also describes stunt courses as 45-second events, and `0x2D` is decimal 45.

Current interpretation, with confidence separated:

- **Observed:** exactly 45 validated Method 1 payloads.
- **Observed:** byte 2 is 45 on exactly every third track position in each five-stream group and zero elsewhere.
- **External fact:** the game has 45 tracks grouped as nine tours of five in the order Race, Circuit, Stunt, Race, Circuit.
- **External fact:** stunt courses use a 45-second timer.
- **Supported interpretation:** one RNC payload corresponds to one shipped track, ordered by tour/slot.
- **Strong field identification:** decoded byte offset 2 is the stunt-course time limit in seconds, or a field whose shipped value directly supplies that 45-second limit. Runtime tracing can distinguish direct timer use from a semantically equivalent mode parameter.

The provisional stream-to-name mapping is recorded in `references/notes/course-order-and-stunt-timer.md`. Under that mapping, the seven PAL-retail content changes correspond to stream candidates:

- 4 Crawler / Switcher
- 16 Hopper / Wario Paint
- 20 Hopper / Hairpin Hill
- 26 Bounder / Last One
- 27 Bounder / Marathon
- 35 Runner / Fire Escape
- 36 Sprinter / Vertical

Those names remain provisional until a runtime course-load trace or an in-ROM selector independently confirms stream ordinal identity.

Generated structural evidence: `analysis/generated/course-header-cadence.md`.


## Runtime bridge: active decoded payload appears at 7F:0000

The deterministic Dragster race-entry WRAM dump provides the first direct bridge from decoded RNC bytes into live game memory.

Decoded stream 1 begins:

`00 00 00 44 00 32 00 44 00 32 00 0F 84 00 04 00 ...`

At settled first-race entry, WRAM `7F:0000` begins:

`00 00 00 44 00 32 00 44 00 32 00 16 84 00 04 00 ...`

The first 48 bytes otherwise match the decoded header pattern; byte offset 11 has changed from `0x0F` to `0x16` by the sampled runtime point. This strongly supports the active track payload being decompressed or copied directly into bank `7F` at offset `0000`, with at least some fields subsequently mutable in place.

A second correlation is especially suggestive. Stream 1's first 16-bit coordinate-like pair is `(68, 50)`, and the second pair is also `(68, 50)`. The verified race-entry player-1 and player-2 X positions are both 1088, exactly `68 × 16`. Their Y positions are 858/857 rather than `50 × 16`, so the Y mapping clearly has an additional anchor/offset or the field is not a direct center coordinate.

Current confidence separation:

- **Confirmed:** decoded stream 1 is resident at `7F:0000` during Dragster. Run 36514985916 compares all 33,815 decoded bytes and finds 33,814 exact matches; only decoded offset `0x000B` differs (`0x0F` decoded, `0x16` live).
- **Observed:** header X value 68 maps exactly to runtime start X 1088 at ×16.
- **Strongly supported hypothesis:** LE16 fields at decoded offsets 3/5 and 7/9 are two course-coordinate pairs, plausibly start/spawn positions for the two racer slots. On confirmed Dragster, both X values are 68 and both runtime racer X positions are exactly `68 × 16 = 1088`.
- **Open:** the meaning of decoded byte 11 and why it mutates `0x0F → 0x16`; the Y-coordinate anchor; whether the two pairs are racer starts, start/finish, or another paired course landmark.

Next discriminator: capture a different known stream/course at race entry, or causally perturb one decoded coordinate field, and test whether the corresponding runtime position moves by the predicted 16-unit scale.


### Whole-payload runtime match

Workflow run 36514985916 decodes all 45 USA RNC streams and scores each against the 64 KiB live WRAM region beginning at `7F:0000` from the deterministic settled Dragster checkpoint.

Stream 1 is unambiguously the best match:

- stream: 1;
- packed ROM offset: `0x0C0000`;
- decoded size: 33,815 bytes;
- equal live bytes: 33,814 / 33,815;
- equal fraction: 0.999970;
- only mismatch: decoded offset `0x000B`, `0x0F → 0x16`.

No other decoded stream approaches this relationship. This directly confirms stream 1 as the active Dragster payload and `7F:0000` as its runtime decoded buffer.

The next format question is no longer "where does the course go?" It is:
1. when during frontend/race transition is the payload installed at `7F:0000`;
2. what writes decoded byte 11 from `0x0F` to `0x16`;
3. what the coordinate-like header pairs represent precisely.


### Course-load timing narrowed to Now Playing → race transition

Workflow run 36515555816 scores the decoded corpus against `7F:0000` at four deterministic frontend/race checkpoints:

- `tracks-ready`: stream 1 is not present as an installed payload;
- `after-track-confirm`: stream 1 is not present;
- `now-playing-ready`: stream 1 is still not present;
- `race-entered`: stream 1 is present at 33,814 / 33,815 exact bytes, with only offset `0x000B` changed to `0x16`.

The final Now Playing A pulse occurs after `now-playing-ready`; the race-active checkpoint is reached 151 guest frames later in the reference route. Therefore the active course payload is installed during that transition window, not while the track-select or settled Now Playing screens are displayed.

Caution: before the course is installed, the generic "best matching stream" metric can favor very sparse/zero-heavy decoded payloads (stream 23 scored about 97.4% against largely zero/unrelated live data). That is not evidence that stream 23 is loaded. The meaningful discriminator is the focused expected stream becoming essentially byte-identical across its full decoded length.

Next discriminator: sample `7F:0000` densely after the final Now Playing confirm to find the first frame where stream 1 appears, and track decoded byte 11 separately to determine whether `0x0F → 0x16` happens during decompression/load or in a later initialization pass.


### Dense transition trace: progressive install and exact spawn-coordinate scale

Run 36516395510 samples the course buffer after the final Now Playing confirm.

Key checkpoints:

- +0 through +16 frames: stream 1 is not installed; `7F:0000` still contains unrelated/mostly zero state and byte 11 is `0x00`.
- +32 frames: stream 1 has a **10,307-byte exact common prefix** at `7F:0000`; decoded byte 11 is present unchanged as `0x0F`. The rest of the stream is not yet fully installed.
- +64 frames: all 33,815 bytes are installed, with 33,814 exact matches; byte 11 has changed to `0x16`.
- +96/+128/+144/race-active: the same full-payload state persists.

This shows the course buffer being populated progressively during the transition rather than appearing only at race activation.

The same trace resolves the earlier Y-coordinate ambiguity. At +64 frames, when the decoded payload is fully resident, both racer slots are exactly `(1088, 800)`. Stream 1's two header pairs are both `(68, 50)`, and:

- `68 × 16 = 1088`;
- `50 × 16 = 800`.

Therefore the header coordinate-like fields use a ×16 scale into the runtime racer coordinate system at initialization. The later settled-race Y values around 858/857 are subsequent game/track state, not evidence against the header Y coordinate.

What remains unresolved is the assignment of the two identical Dragster pairs to racer slot 1 vs slot 2, because both pairs and both initial positions are identical on this course. A second course with unequal pairs or a controlled field mutation can separate them.

The next loader-timing discriminator is now narrow: sample densely from +32 to +64 frames to find (a) the first frame where all 33,815 bytes are resident and (b) the first frame where byte 11 changes `0x0F → 0x16`.


### Four-frame refinement: payload completion/mutation and racer initialization are separate phases

Run 36516675672 refines the critical post-confirm window:

- **+36 frames:** exact stream-1 prefix = 18,869 bytes; byte 11 still `0x0F`; racer slots `(0,0)`.
- **+40 frames:** exact prefix = 29,289 bytes; 33,220 / 33,815 bytes already equal; byte 11 still `0x0F`; racer slots still `(0,0)`.
- **+44 frames:** full payload is resident at 33,814 / 33,815 exact; byte 11 is already `0x16`; racer slots still `(0,0)`.
- **+48 frames:** payload remains complete and both racer slots have been initialized to `(1088,800)`.

So the transition has at least three observable phases:

1. progressive RNC output/copy through +40;
2. payload completion **and** header-byte-11 mutation sometime in +40→+44;
3. racer spawn-state initialization sometime in +44→+48.

This sequencing is especially useful for code archaeology: the course unpack/copy path can be distinguished from the later player initialization path rather than treating race setup as one monolithic routine.

Next discriminator: sample +41/+42/+43/+44, then +45/+46/+47/+48 if needed, to identify the first full-payload frame, first byte-11 mutation frame, and first spawn-state frame separately.


### Frame-exact Dragster setup chronology

Run 36517460851 resolves the critical setup sequence at one-guest-frame resolution:

| Frames after final Now Playing confirm | Stream-1 state at `7F:0000` | Header byte 11 | Racer slots |
|---:|---|---:|---|
| +42 | incomplete; exact prefix 33,359 / 33,815 | `0x0F` | `(0,0)`, `(0,0)` |
| +43 | **full payload complete**; 33,814 / 33,815 exact | `0x12` | `(0,0)`, `(0,0)` |
| +44 | full payload complete | `0x16` | `(0,0)`, `(0,0)` |
| +45 | full payload complete | `0x16` | **`(1088,800)`, `(1088,800)`** |

This gives a frame-exact ordering:

1. progressive decompression/copy is still underway at +42;
2. by +43 the complete decoded payload exists, and byte 11 has already been postprocessed from `0x0F` to `0x12`;
3. on the next guest frame (+44), byte 11 reaches `0x16`;
4. on +45, player/racer initialization consumes the course-space spawn coordinates and installs `(68,50) × 16 = (1088,800)` into both racer slots.

No finer frame sampling is needed for this chronology. The remaining question is **which guest routines perform the decompression write and the +43/+44 byte-11 updates**; the dedicated trace-course-buffer-writers workflow targets that next.


### Dynamic course-buffer writers identified

Trace run 36517696016 records writer history for the live Dragster buffer at `7F:0000` through race setup.

Observed writes:

- frame 867, `interp@$81BB73` writes the decoded stream bytes into the destination buffer, including:
  - `7F:0000 = 0x00`;
  - `7F:0003 = 0x44`;
  - `7F:0005 = 0x32`;
  - `7F:000B: 0x00 → 0x0F`.
- frame 879, `interp@$81BA96` writes the same byte seven times in succession:
  - `0x0F → 0x10 → 0x11 → 0x12 → 0x13 → 0x14 → 0x15 → 0x16`.

This directly explains the single runtime-mutated course byte. The first writer places the decoded `0x0F`; the second writer is responsible for the final `0x16` value.

Both PCs are in bank 81 near the already identified shipped RNC Method-1 unpacker region (entry `01:B8F1`). That proximity is not, by itself, enough to label `81BA96` as either part of the generic RNC algorithm or game-specific postprocessing. The next static step is to disassemble/map the exact shipped instructions at `01:BA96` and `01:BB73` against preserved `RNC_1.S` before naming either routine semantically.

Evidence:
- workflow run 36517696016;
- artifact 11011622806;
- `.github/workflows/trace-course-buffer-writers.yml`;
- `tools/trace_native_wram_writers.py`.


### Active writer static-classification probe

The existing RNC signature finder now includes a longer source-derived `MAKEHUFF` prologue signature and explicit build-relative byte context for the two dynamically observed USA writer PCs `01:BA96` and `01:BB73`. Workflow `.github/workflows/rnc-writer-static-classification.yml` regenerates the report from the preserved ROMs.

The classification rule is deliberately structural: compare each writer at the same displacement from that build's mechanically identified Method-1 entry, and only call a writer part of the generic RNC routine if the surrounding instruction sequence aligns with a specific preserved `RNC_1.S` block. Short-signature proximity alone is insufficient because the prior loose `MAKEHUFF` shape has two hits in the USA image.


### Authoritative decoder probe

A second static-classification path now uses the pinned framework's own v2 65816 decoder rather than a project-local partial disassembler. `tools/probe_rnc_writer_decode.py` decodes the known USA RNC1 entry at `01:B8F1` with M/X state tracking and asks whether traced writer PCs `01:BA96` and `01:BB73` are members of that control-flow graph. If reachable, it records the exact decoded instruction and nearby M/X-qualified context. `.github/workflows/rnc-writer-decoder-probe.yml` persists the machine-readable result to `analysis/generated/rnc-writer-decode.json`; that generated path does not retrigger the workflow.

This probe is intentionally complementary to the source-signature report. A positive graph-membership result identifies the writer as part of the decoded RNC1 function under the recompiler's own control-flow model; a negative result means the writer requires a separately rooted helper/game-code decode and must not be classified from address proximity.


### Course stream pointer-table search

The 45 confirmed USA RNC payload offsets are now also searched mechanically as potential course-selection targets. `tools/find_course_stream_pointer_tables.py` scans the canonical ROM for consecutive runs of:

- 24-bit little-endian LoROM addresses;
- 24-bit little-endian file offsets;
- 16-bit LoROM addresses;
- common padded fixed-width records containing the 24-bit forms.

The scanner scores only consecutive stream-order runs of length three or greater, reducing isolated pointer-like byte coincidences. Workflow `.github/workflows/course-stream-pointer-search.yml` persists the result to `analysis/generated/course-stream-pointer-search.json`. A positive long run would expose a direct course pointer/index table; a negative result narrows the selector toward split-bank tables, relative offsets, transformed indices, or code-generated addresses.


## Header dimension-pair invariant

A corpus-wide invariant in decoded header bytes 13 and 14 strongly narrows the course-layout question. Across all 45 USA streams, interpreting encoded `0x00` as 256 gives a product of exactly **1024** for every pair. Observed forms include `256×4`, `128×8`, `64×16`, `32×32`, `16×64`, `8×128` and `4×256`.

This is too rigid to treat as incidental metadata. The leading interpretation is that bytes 13/14 are complementary dimensions or strides over a fixed 1024-unit course plane/table. The unit remains unresolved: it could be tiles, blocks, columns, lookup entries or another layout primitive. This also gives a concrete way to test the historical “256 wide” claim: streams encoded `00 04` or `04 00` are the natural first cases for runtime/memory-layout validation rather than assuming every course is literally 256 raw bytes wide.

The invariant is now generated mechanically by `tools/analyze_course_header_cadence.py`; `.github/workflows/course-header-cadence.yml` refreshes and persists the report.

Historical evidence now gives this a more specific, still provisional interpretation. OD-006 preserves Spinal's report that Mike Dailly said levels were 256 tiles wide; after decompressing the RNC data and overlaying hand-made maps, Spinal further reported that one byte in a level file corresponds to a 64×64 block. Combined with the local 45/45 product-1024 invariant, the smallest testable model is therefore a **1024-byte one-byte-per-64×64-block layout plane**, reshaped according to bytes 13/14. The provisional course-name alignment is suggestive: Dragster is `256×4`, Vertical is `16×64`, Little Dipper is `4×256`, while many circuit-like layouts are `64×16` or `32×32`. These names remain external/provisional until selector identity is closed.

`tools/analyze_course_layout_planes.py` now tests the first four 1024-byte regions after the header without assigning semantics, so the map-plane hypothesis can be accepted or rejected from corpus statistics rather than visual wishful thinking.


### Attribution correction: interpreter scope entries, not literal store PCs

Run 36517696016 remains valid evidence for the **timing, values, and attribution scopes** of the Dragster course-buffer writes, but its `interp@$...` labels were previously described too literally.

SNESRecomp's interpreter bridge documents `interp@$XXXXXX` as the **entry PC of an interpreter bridge run**. That synthesized name is pushed as the attribution scope for all still-interpreted writes during that run. It is not necessarily the guest instruction that performs each store.

Accordingly:

- the frame-867 payload-install writes occur under interpreter scope `interp@$81BB73`;
- the frame-879 seven-step `7F:000B` mutation `0x0F→...→0x16` occurs under interpreter scope `interp@$81BA96`;
- neither address should be named as the literal store opcode without narrower instruction-level evidence.

The static ROM context now independently confirms the distinction. `01:BA96` lies inside the preserved RNC Method-1 `GTBITS2` loop, with the surrounding byte sequence matching `LSR A / ROR BITBUFL / DEY / BEQ / DEX / ...` instruction-for-instruction. Thus `81BA96` is a genuine RNC bit-reader continuation/bridge entry, not itself the course-byte store instruction.

The next tracing task is therefore narrower: preserve the proven write timeline, but isolate the **actual interpreted instruction PC** responsible for the `7F:000B` stores rather than inferring it from the bridge-scope label.


### Preserved RNC body ends at 01:BB6E

The source-derived `MAKEHUFF` tail can be aligned directly in the already captured USA ROM context. The exact sequence `INY / INY / DEX / BNE / LSR HUFBSE / INC BITLEN / CMP #$0010 / BNE / RTS` begins at `01:BB60` and its final `RTS` is at `01:BB6E`. This establishes the preserved RNC Method-1 body as `01:B8F1..01:BB6E` in USA retail/legacy beta.

The byte stream immediately after that return begins a separate helper at `01:BB6F`. In that helper, `01:BB71` increments the input-pointer low word and `01:BB73` is the following conditional branch. Therefore the historical trace scope `interp@$81BB73` is **outside** the preserved RNC routine, while `interp@$81BA96` is **inside** generic RNC `GTBITS2`.

This gives the course-load write trace a cleaner interpretation: one write group is attributed to an interpreter bridge entered in game/integration helper code immediately following RNC, while the later mutation group is attributed to a bridge entered inside the RNC bit-reader. Neither scope entry is itself the literal store. The exact `IPC=` address-log probe remains the authority for store-opcode ownership.


### Static classification of the post-RNC helper

The helper immediately after the preserved generic RNC1 body is now understood well enough to name structurally. USA `01:BB6F` begins:

`LDA [IN]; INC IN; BNE ...`

and only takes its longer path when incrementing the low 16-bit input pointer wraps through zero. That path temporarily maps the pointer to the next LoROM bank at `$8000`, reads the replacement high byte, restores the original bank/pointer representation, and returns the assembled 16-bit word. The ordinary path simply restores the incremented pointer before returning.

This is therefore a **LoROM-safe packed-stream word reader** used by the shipped RNC integration, not a course-header mutation routine. The symbol is promoted to `RNC1_ReadWordLoROMSafe` at `01:BB6F`.

This also sharpens the dynamic-attribution interpretation: `interp@$81BB73` names an interpreter run that entered at the helper's wrap-test `BNE`. Writes attributed to that scope may happen later after control returns into the decoder/caller. The scope label cannot be read as “BB73 wrote this byte.” The same principle applies to the `interp@$81BA96` scope inside `GTBITS2`.

The dedicated exact-IPC write probe remains the correct discriminator for the literal instructions that write `7F:000B`.


### Near-end field and aligned pre-trailer cursor hypothesis

Treating decoded header bytes 11–12 as little-endian produces a field close to the end of every USA decoded course payload. Across all 45 streams, **`LE16@11 + 1` is 16-byte aligned**. The bytes after that cursor, `decoded_size - (LE16@11 + 1)`, range from **7 to 36 bytes**.

Dragster is the smallest-gap case:

- decoded size: `0x8417` (33,815 bytes);
- decoded `LE16@11`: `0x840F`;
- next offset: `0x8410`, exactly 16-byte aligned;
- bytes after the cursor through EOF: 7;
- observed runtime mutation: seven increments, `0x840F → 0x8416`;
- `0x8416` is exactly `decoded_size - 1`, the final valid payload byte offset.

This falsifies the tempting corpus-wide “size minus eight” interpretation, but suggests a stronger runtime model: **LE16@11 may be a mutable cursor initialized to the inclusive byte immediately before a 16-byte-aligned variable trailing region, then advanced while setup consumes that region**. Under that model, stream 11 has 21 bytes after its cursor and would need 21 increments to settle at EOF−1.

A deterministic second-tour route is now encoded in `tests/input/course-load-timeline-tour2.script`. It selects tour index 2 by moving the recovered tour-menu selection from `selectedOption=0` to `selectedOption=2`, then reuses the proven course-load timeline. The corresponding runtime workflow focuses stream 11 and persists `analysis/generated/course-runtime-tour2-tail-cursor.json` with the decoded cursor, live cursor, trailer length and whether the live cursor reaches EOF−1.

Until that capture lands, “variable trailer cursor” remains a testable hypothesis rather than a field name.
