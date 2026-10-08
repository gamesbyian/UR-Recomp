# Course Format Investigation

Goal: produce a ROM-free technical description of Uniracers/Unirally course data and a parser that operates locally on a user-supplied ROM.

## Historical leads

Historical reports identified Rob Northen Compression for level/course data. The most useful historical course-layout observations are normalized in `reference/notes/course-layout-history.md`. Local analysis confirmed 45 valid RNC Method 1 streams in the canonical USA retail ROM and 1994-11-29 PAL prototype, byte-identical at identical offsets. The newly acquired historical GoodSNES beta shares all 45 byte-for-byte as well. Europe retail also contains 45 streams, of which 38 are byte-identical by content; ordinal streams 4, 16, 20, 26, 27, 35 and 36 have changed packed/unpacked sizes and CRCs. The remaining question is what each decoded stream contains and how these seven final-PAL changes map to course or other semantics.

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

`reference/imported/tools/rnc_propack-2.14/`

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


## Recovered 45-map and start/finish corpus

Dessyreqt's direct historical workspace supplies one PNG map for every shipped course under `reference/imported/reverse-engineering/dessyreqt/Maps/`, plus `Scripts/magicnumber.lua`, which records start/finish X coordinates for all 45 track IDs. This changes the validation posture:

- the project now has a complete local visual map corpus, so external VGMaps acquisition is comparison-only;
- the historical start/finish coordinates are cheap course-identity and race-finish probes, especially for distinguishing wraparound/circuit layouts;
- neither artifact overrides ROM/runtime evidence: the PNGs were produced by emulator-era tooling and `magicnumber.lua` is an optimization model, not a course-format specification;
- where provisional stream names are uncertain, prefer a low-cost coordinate/topology comparison against these artifacts before launching a broad trace.

The historical mapper scripts also show their method: freeze timers, move the racer through a grid, read camera position, and stitch emulator screenshots. That makes the maps independent visual observations of rendered courses rather than decoded RNC outputs, which is useful for validating a future ROM-derived renderer.

See `reference/notes/dessyreqt-workspace-mining.md`.


## Recovered historical ROM addresses independently confirm course identities

A retrospective semantic-propagation pass reconciled Nitrodon's recovered `ROM addresses.txt` against the canonical RNC manifest.

The historical values are SNES LoROM CPU addresses. Converting them to file offsets lands exactly on known packed RNC starts:

- `18:8000` → `0x0C0000` → stream 1 → **Dragster**;
- `18:8183` → `0x0C0183` → stream 2 → **Zoom Zoo**;
- recovered `18:94BA` does not land on a header, but `18:9B4A` → `0x0C1B4A` is exactly stream 3 → **Bowl**; this is strongly consistent with a transposition typo in the historical note;
- `18:A07E` → `0x0C207E` → stream 4 → **Switcher**;
- `1A:9678` → `0x0D1678` → stream 13 → **Jumps**.

These five names are therefore independently anchored by historical address evidence rather than only inferred from the modern stream-order reconstruction. The Bowl correction should be treated as a supported typo repair, not silently substituted into the preserved source file.

Practical rule: when mining historical ROM addresses, first test SNES LoROM CPU-address interpretation before treating the value as a raw file offset.

Full derivation: `analysis/generated/retrospective-semantic-propagation-2026-09-30.md`.

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

The provisional stream-to-name mapping is recorded in `reference/notes/course-order-and-stunt-timer.md`. Under that mapping, the seven PAL-retail content changes correspond to stream candidates:

- 4 Crawler / Switcher
- 16 Bounder / Last One
- 20 Bounder / Jumpover
- 26 Runner / Down+Up
- 27 Runner / Highroad
- 35 Hopper / Hairpin Hill
- 36 Sprinter / Vertical

Those names remain provisional until a runtime course-load trace or an in-ROM selector independently confirms stream ordinal identity.

Generated structural evidence: `analysis/generated/course-header-cadence.md`.


## Decoded payload tail resource list identified

The previously unexplained Dragster mutation at decoded offsets `0x000B..0x000C` is now resolved.

Those two bytes are the little-endian word `0x840F`, not an isolated byte-sized field. `Course_LoadAndMaterialize` reads this word as an offset into the active decoded payload, increments it after each read, and consumes one-byte resource IDs until it encounters `0xFF`.

For Dragster:

- decoded size = `0x8417` bytes;
- initial resource cursor = `0x840F`;
- observed settled cursor = `0x8416`;
- therefore the loader consumed offsets `0x840F..0x8415`;
- `0x8415` is the terminating `0xFF`;
- the span contains six resource IDs plus the terminator.

This exactly explains the long-observed low-byte mutation `0x0F → 0x16`: the loader advances the 16-bit cursor from `0x840F` to `0x8416`.

Each resource ID then indexes two related structures: a five-byte descriptor table used by the generic resource-transfer path and a four-byte bank-17 pointer table. The latter feeds paired materialization into runtime planes at `7E:A000` and `7E:C000`. The C000 plane is the one later queried by the course object/collision dispatcher.

Current structural model:

`decoded header → tail resource-ID list → reusable bank-17 resources/templates → runtime A000 + C000 planes → object/collision behavior`

This means checkpoint/finish object code `0x14` should be traced backward through the owning materialized resource span, not searched for as a naive raw byte in the RNC payload.

Full derivation: `analysis/generated/course-resource-list-materialization-2026-09-30.md`.

## Dragster checkpoint resource attributed structurally

The frame-exact course-load artifact plus the five-byte resource descriptors now partition Dragster's complete 20-byte `7E:C000` behavior plane by owning resource.

Recovered Dragster tail list:

`01 02 14 24 16 18 FF`

Descriptor sizes imply C000 spans of `1, 1, 4, 9, 4, 1` bytes respectively. Those sum exactly to the observed 20-byte runtime behavior plane:

`00 00 | 12 1C 00 00 | 14 14 14 14 14 14 14 14 14 | 02 02 02 02 | 02`

Therefore resource ID **`0x24`** owns C000 offsets 6–14, and its entire nine-byte behavior contribution is object code `0x14`, the confirmed checkpoint/finish dispatcher code.

This is an important methodological counterexample: resource ID `0x14` is **not** the checkpoint resource. It materializes `12 1C 00 00`. Matching numeric IDs/addresses alone would have produced the wrong conclusion; the correct attribution comes from descriptor size, cumulative materialization spans, runtime behavior distribution, and loader chronology.

Use structural fingerprints for future resource equivalence: course incidence, list position, track-slot context, descriptor shape, output spans, pointer relationships, behavior-code distribution, and content signatures. Numeric IDs and absolute addresses are supporting evidence only.

Full derivation: `analysis/generated/dragster-resource-span-attribution-2026-09-30.md`.

## Checkpoint/finish resource family generalized across all 45 courses

The full 45-course resource-list corpus now turns Dragster resource `0x24` from a course-specific attribution into a game-wide structural family.

`tools/analyze_course_resource_lists.py` decodes every course in all four preserved builds and fingerprints each resource by course incidence, tour slot, and list position. The result for resource `0x24` is exact and unusually clean:

- it occurs in **36 / 45** courses;
- those 36 are **every Race A, Circuit A, Race B, and Circuit B slot in all nine tours**;
- it occurs in **0 / 9 Stunt** courses;
- the same `0x24` ID and the same incidence/list-position fingerprint are preserved in USA retail, Europe retail, the legacy beta, and the 1994-11-29 PAL prototype;
- Dragster independently proves that this resource contributes nine runtime `0x14` object cells, and `0x14` dispatches to `Race_HandleCheckpointFinish`.

Taken together, the supported semantic label is now:

`resource 0x24 = race/circuit checkpoint-finish resource family`

This does **not** imply every byte or every materialized cell from `0x24` is identical on every course. It identifies the reusable resource family selected by every shipped lap/checkpoint-bearing race/circuit course and omitted by every timed Stunt course.

The negative evidence is especially useful: Stunt courses do not use the ordinary checkpoint/finish resource family, which matches their timer/score mode and gives the future editor/runtime model a clean mode-dependent structural distinction.

Generated corpus:
- `analysis/generated/course-resource-list-manifest.json`
- `analysis/generated/course-resource-list-manifest.md`

Regenerate both artifacts with `python3 tools/analyze_course_resource_lists.py`.
Use `python3 tools/analyze_course_resource_lists.py --check` for a read-only
corpus-to-artifact consistency check; parser, fingerprint, renumbering, and
preserved-ROM regression coverage lives in
`tests/unit/test_analyze_course_resource_lists.py`.

The same manifest is also the single machine-readable owner for tracked
course-header and resource-list differences relative to USA retail. It records
no tracked-field differences for the legacy beta or PAL prototype; Europe
retail changes Switcher's first coordinate pair and appends resource `0x22` to
Down+Up and Vertical. `build_consolidated_knowledge.py` derives the normalized
resource-catalog summary from these exact deltas and the decoded-stream hashes
in `rnc-stream-manifest.json`, rather than restating stream numbers or expected
edit forms as independent mutable facts.

Derived closeout:
- `analysis/generated/checkpoint-resource-family-2026-10-01.md`


## Runtime object map: checkpoint/finish code identified

A retrospective propagation pass through the race object dispatcher at `81:82E6` identifies one concrete runtime course-object code.

The dispatcher reads a byte from the materialized runtime map at `7E:C000,X`, clears bit 0, and uses the resulting even value as a jump-table offset into `81:8320`. Object code `0x14` selects `81:8050`, the confirmed checkpoint/finish handler.

Therefore `0x14` is a supported runtime **checkpoint/finish course-object code**.

This gives the course-format investigation a direct semantic bridge:

`decoded course payload → materialized 7E:C000 object map → object code 0x14 → checkpoint/finish race-state mutation`

Next high-value discriminator: locate `0x14` cells in the active Dragster object map, map their runtime grid positions to known finish/checkpoint coordinates, then trace those bytes backward into the decoded RNC payload. Do not decode the rest of the object jump table uniformly; promote additional codes only when a gameplay/editor/fidelity question needs them.

Full derivation: `analysis/generated/semantic-propagation-finish-collision-2026-09-30.md`.

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
- **Resolved:** decoded offsets `0x000B..0x000C` are a mutable 16-bit resource-list cursor (`0x840F → 0x8416` on Dragster); the apparent byte-11 mutation is simply its low byte advancing. **Open:** whether the two coordinate pairs are racer starts, start/finish, or another paired course landmark.

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
2. which six resource IDs occupy Dragster's tail list and what A000/C000 spans each materializes;
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


### Dynamic course-buffer write scopes identified

Trace run 36517696016 records write history for the live Dragster buffer at `7F:0000` through race setup.

Observed write groups:

- frame 867, writes attributed to interpreter scope `interp@$81BB73` install decoded stream bytes, including `7F:000B: 0x00 → 0x0F`;
- frame 879, writes attributed to interpreter scope `interp@$81BA96` update that byte seven times: `0x0F → 0x10 → ... → 0x16`.

SNESRecomp's `interp@$XXXXXX` label is the **entry PC of an interpreter bridge run**, not the exact opcode responsible for every write in that scope. Static classification now resolves both landmarks: `01:BA96` is inside generic RNC `GTBITS2`, and `01:BB73` is the wrap-test `BNE` inside `RNC1_ReadWordLoROMSafe`. Neither is the literal course-buffer store instruction.

The trace therefore proves two distinct interpreted execution scopes own the payload-install and later mutation write groups, while the exact WRAM store PCs remain the target of the dedicated `SNESRECOMP_WLOG_STATE` exact-IPC probe.

Evidence:
- workflow run 36517696016;
- artifact 11011622806;
- `.github/workflows/trace-course-buffer-writers.yml`;
- `tools/trace_native_wram_writers.py`.


### Active RNC scope static-classification probe

The RNC signature finder includes source-derived entry/`MAKEHUFF` signatures, explicit context for the two dynamically observed USA interpreter-scope entries `01:BA96` and `01:BB73`, the exact generic-RNC end, and the LoROM-safe word-reader helper. Workflow `.github/workflows/rnc-writer-static-classification.yml` regenerates and now persists the report from the preserved ROMs.

The classification rule is deliberately structural: compare each scope landmark at the same displacement from that build's mechanically identified Method-1 entry, and only classify code as generic RNC when the surrounding instruction sequence aligns with a specific preserved `RNC_1.S` block. Short-signature proximity alone is insufficient because the loose `MAKEHUFF` shape has two hits in the USA image.


### Authoritative decoder probe

A second static-classification path uses the pinned framework's own v2 65816 decoder rather than a project-local partial disassembler. `tools/probe_rnc_writer_decode.py` decodes the known USA RNC1 entry at `01:B8F1` with M/X state tracking, follows local JSR callees, and asks whether scope-entry PCs `01:BA96` and `01:BB73` belong to that decoded call tree. It also mechanically scans direct JSR/JSL callers of the shipped RNC entry. `.github/workflows/rnc-writer-decoder-probe.yml` persists the machine-readable result to `analysis/generated/rnc-writer-decode.json`.

This probe is complementary to the source-signature report: graph membership classifies the **code containing the attribution landmark**, not the exact WRAM store responsible for a write observed under that scope. Literal store ownership remains an instruction-level tracing question.


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


### Dragster presentation spatial/resource contract

The representative Dragster runtime path now resolves the dimension unit and the two-level spatial indirection far enough for Widescreen work. This supersedes the provisional "1024-byte one-byte-per-64x64-block plane" interpretation for the active runtime representation while preserving the corpus-wide header invariant.

At runtime, `81:A313..A51F` reads decoded byte 13 and expands the zero-as-256 header dimension by a factor of four into `7E:04F1`, the X count of 64-world-unit coarse sectors. Dragster's raw `00 04` header therefore becomes a `1024 x 16` coarse grid. The same setup writes camera/world masks `0D49=FFFF` and `0D47=03FF`, giving a Dragster spatial domain of **65536 x 1024 world units**. This domain contains both the runtime-confirmed spawn `(1088,800)` and the historical finish-X probe `25278`.

The decoded payload then has an exact two-level layout:

- `0x000F..0x800E` / runtime `7F:000F`: **16,384 little-endian u16 coarse-sector entries**. `81:8A4A..8B94` indexes them as `(y >> 6) * 04F1 + (x >> 6)`.
- `0x800F..0x840E` / runtime `7F:800F`: **32 records x 32 bytes**. Each coarse entry is multiplied by 32 to select one record.
- each 32-byte record is a **4 x 4 grid of u16 packed surface words**, with coordinate bits 4..5 selecting a 16x16 fine cell inside the 64x64 coarse sector;
- Dragster's resource list begins immediately afterward at `0x840F`.

For a normal packed surface word, `81:8C11..8C2C` derives the `C000` slot as
`((word & 0x000F) >> 1) + ((word & 0x03F0) >> 2)`. The same slot owns a paired 32-byte block in `A000`. Because the six Dragster resource descriptors append their A000/C000 spans in resource-list order, every normal 16x16 world cell can therefore be mapped mechanically to its owning resource without decoding unrelated control bits.

For Dragster the materialized totals are **A000 = 0x280 bytes** and **C000 = 0x14 bytes**. Resource `0x24` owns C000 slots `6..14`; all nine contain behavior code `0x14`, already tied to `Race_HandleCheckpointFinish`. The generated contract consequently locates checkpoint/finish-bearing fine cells and their containing coarse sectors in world space.

The machine-readable hand-off is `analysis/generated/dragster-presentation-spatial-contract.json`, generated by `tools/build_course_presentation_contract.py`. A caller can query a world rectangle and receive every touched 16x16 cell with its coarse sector, fine-record ID, packed surface word, C000 slot, paired A000 range, and owning tail resource. The companion Markdown report is `analysis/generated/dragster-presentation-spatial-contract.md`.

This is the current **presentation-complete** boundary for one representative course. It deliberately does not name every packed control bit, infer gameplay activation, decode graphics assets, or define an editor schema. Generalization should first test the same table boundaries, dimension transform, and packed-word/resource-ownership invariant on a small cross-course sample; do not mechanically census all 45 courses unless a product question demands it.

That small cross-course check is now complete. `tools/analyze_course_presentation_contract_sample.py` samples four distinct header shapes: stream 1 (`256x4`), stream 9 (`128x8`), stream 5 (`32x32`) and stream 6 (`16x64`). All four satisfy the same presentation-facing invariants:

- runtime expansion produces exactly 16,384 coarse 64x64 sectors, hence the same fixed `0x8000`-byte u16 coarse table;
- the region from `0x800F` to the course resource cursor is an integral number of 32-byte fine records;
- every coarse-table record reference stays inside that fine-record table;
- every normal packed surface word resolves to a C000 slot inside the materialized resource span;
- total A000 materialization is exactly 32 bytes per C000 slot.

The sample spans 32, 736, 607 and 463 fine-record tables respectively, so the Dragster result is not an artifact of its unusually small 32-record second stage. Generated evidence is preserved in `analysis/generated/course-presentation-contract-sample.{json,md}`.

**Promotion:** the two-level coarse-sector → 32-byte fine-record → packed surface word → materialized resource shape is now a reusable course-family presentation contract. Per-course record counts, resource lists and world aspect vary; packed control-bit semantics beyond the proven resource selector remain intentionally unresolved. This is sufficient for Widescreen-facing spatial/resource queries without an editor-complete format.



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


### Cross-corpus spawn-pair strengthening — 2026-10-02

The corrected 45-course identity map plus Dessyreqt landmarks strengthens the two header coordinate pairs substantially.

For Dragster, dense loader evidence already proves both header pairs `(68,50)` initialize the two racer slots to `(1088,800)`, exactly ×16 in both axes.

Across the full course corpus:

- all 36 non-stunt courses have equal A/B X coordinates;
- non-stunt A/B Y coordinates are either equal or differ by small offsets;
- four stunt courses use distinct A/B X coordinates;
- historical start X matches header pair A.x ×16 on 43/45 courses.

The strongest current interpretation is therefore that decoded offsets 3/5 and 7/9 are the two racer spawn coordinate pairs, with pair-to-player assignment still requiring one unequal-pair runtime discriminator. Keep Zoom Zoo and Jumps as explicit historical-coordinate exceptions rather than weakening the broader relation.


### Targeted checkpoint/finish resource placement probe (2026-10-08)

The new tools/probe_course_checkpoint_placements.py exposes a ROM-derived
world-cell lookup for resource family 0x24 on a selected course, rather than
extending the Dragster-only presentation artifact or guessing which cells
activated the finish handler. It requires the exact canonical USA retail ROM
hash because its descriptor table address is anchored at USA 82:B7DA.

The probe decodes the selected RNC stream, applies the 16,384-entry coarse table
and 32-byte/4x4 fine-record lookup, and resolves each normal packed word's
C000 slot to the cumulative descriptor-owned resource span. Repeated resource
IDs remain distinct spans. Example invocations:

    python3 tools/probe_course_checkpoint_placements.py --stream-index 1
    python3 tools/probe_course_checkpoint_placements.py --stream-index 1 --observed-c000-slot 8
    python3 tools/probe_course_checkpoint_placements.py --stream-index 5 --query-rect 0 0 1023 1023

The output includes exact candidate 16x16 world rectangles, fine-record IDs,
coarse sectors, per-slot counts, and a bounded set of candidate positions for a
guest-observed C000 slot (such as Dragster index 8 at frame 2903). The automatic historical finish-X probe comes
from Dessyreqt's magicnumber.lua corpus. It is an **X-only optimizer lead**,
not confirmation of a finish-line position, active cell, checkpoint order,
lap semantics, or collision trigger. Stunt courses without resource 0x24
produce an empty candidate set, not inferred checkpoints.

The integration regression pins Dragster resource slots 6..14, its 31 coarse
sector placements, and its 65536x1024 extent to the accepted spatial contract.
The next semantic discriminator is an emulator event trace overlaying actual
C000 collision indices and checkpoint/finish state transitions on candidate
cells in a circuit and a non-Dragster race. Static X proximity cannot replace
that dynamic evidence.


### Historical start-X evidence calibration (2026-10-08)

A direct cross-check of all 45 normalized course headers against Dessyreqt's
preserved magicnumber.lua gives 43 exact matches between the script's startX
constant and decoded header coordinate A.X multiplied by 16. The two exceptions
are Zoom Zoo (historical 8961 versus header 575*16 = 9200) and Jumps
(historical zero versus header 262*16 = 4192). All 45 historical finish-X
values fit inside the corresponding decoded course's derived world X extent.

Crucial source-level limitation: magicnumber.lua **assigns startX but does not
read it in its calculations**. Its calculations use the script's finishX and
the live racer X from 7E:0411 instead. Therefore the 43 matches are strong
evidence of transcription/association between the course header and the
historical workspace, but are **not an independent emulator measurement of
race spawn X**. Jumps' zero may be a placeholder, and Zoom Zoo's nonaligned
8961 may be a historical error or a different author-selected marker. Neither
case should be silently "corrected" in the historical artifact. The first
actual discriminator is a deterministic Zoom Zoo/Jumps race-entry WRAM trace
against both header coordinate pairs, with exact selected course ID and
frame-relative spawn state, not a guess based on the script's labels.


**Cheap next live header discriminator:** Switcher (stream 4) has an exact
USA-to-Europe retail header change confined to coordinate pair A's Y:
USA A=(99,26), Europe A=(99,22), while pair B=(99,34) in both.
If those are world-position units multiplied by 16 as the Dragster reference
shows, the candidate A spawn moves by 64 world Y units between retail builds.
A paired frame-exact Switcher race-entry observation in both ROMs can establish
whether A drives P1, P2, or another landmark; do not infer the player binding
from the header labels alone. This is a cheaper falsifier than decoding
unrelated checkpoint handlers or conducting a broad 45-course runtime sweep.


### Dragster finish-column triangulation from independent runtime evidence (2026-10-08)

The established Dragster object-activation reference fixture records the first
semantic finish transition at guest frame 2903: **postframe** P1 X=25256,
**newly sampled** contact word 0x2020, C000 index 8, behavior code 0x14.
The ROM-proven USA main-race call order dispatches course objects before
sampling new contact. The prior frame-2902 stored word 0x2024/slot 10 is
therefore the stronger **pre-dispatch input candidate**, not a proven
finish trigger. Never use the frame-2903 postframe slot-8 value as proof
that slot 8 activated the *same-frame* finish transition. The published ROM-derived
Dragster spatial contract independently places packed word 0x2020 (C000
slot 8) at world X 25280 in three 16x16 cells at world Y 800, 832 and 864.
The historical optimizer finish-X lead is 25278, two world units before
those candidate cells; the observed P1 X is 24 units before their left edge.

tools/correlate_dragster_finish_spatial_event.py makes this triangulation a
regression against the retained generated spatial contract. It accepts the
documented event or an explicitly supplied JSON report from the existing
object-activation analyzer, verifies the word-to-C000 selector relation,
and enumerates *exact-word* candidate cells and their X distances. This
is narrower than choosing all resource 0x24 placements and safer than naming
the nearby cells as an authoritative collision plane.

The three matching Y bands remain distinct. Neither P1 center X nor the
historical finish-X optimizer constant establishes the actual contact point,
the size of the collision footprint, which band the racer contacted, or
how the checkpoint order state maps to each course feature. Do not infer
those from a static 16x16 cell rectangle. The next high-value runtime
discriminator is a frame-exact contact-point Y / selected fine-cell trace
of this already accepted finish transition.

### Full-payload identity guard for spawn assignment (2026-10-08)

The optional course-entry WRAM spawn-assignment probe must not evaluate header
A/B against arbitrary best-scoring RNC content. Earlier frontend checkpoints
showed a sparse unrelated stream scoring about 97.4% against mostly empty WRAM
before the selected course was installed. The first-race entry witness instead
establishes near-total equality across the **full** decoded stream, with only
resource-list cursor bytes 0x0B..0x0C mutable.

tools/probe_runtime_course_payload.py now reports the complete course identity
criterion separately from a generic similarity ranking: decoded bytes must
match the entire decoded payload extent in the 7F course buffer except offsets
0x0B and 0x0C. The racer-slot A/B discriminator runs only when exactly one
full stream meets that criterion, or an explicitly focused stream itself
meets it. The --limit diagnostic-excerpt option cannot weaken the identity
requirement. Partial decompression, wrong sparse streams and nonmatching
focus streams produce a machine-readable not_evaluable result, not a
promoted spawn-slot assignment.


### Native Dragster checkpoint/finish transition: slot ordering witness (2026-10-08)

The original native deterministic object-activation workflow artifact
(run 36954104693, artifact 11204794758) has been re-opened and its
seven-frame guest-WRAM contact sequence preserved in
analysis/data/dragster-finish-contact-transition.json. This is **native
SNESRecomp guest-state evidence**, not an independent Snes9x/bsnes result.
The selected words and course placements can be independently checked
against the ROM-derived spatial contract.

Relevant consecutive observations at fixed P1 Y=857:

- frame 2902, P1 X=25248: collision word 0x2024 -> C000 slot 10,
  object code 0x14, checkpoint/finish/lap state 3/0/1;
- frame 2903, P1 X=25256: word 0x2020 -> slot 8, **same object
  code 0x14**, state changes to 1/1/0;
- frame 2904, P1 X=25264: word 0x2020 -> slot 8, state stays 1/1/0;
- frames 2905 through 2907: word 0x0022 -> slot 9, code remains 0x14
  and state stays 1/1/0.

The decoded Dragster resource placement at coarse X sector 395 contains
alternating 16x16 cells: 0x2020 / slot 8 in the left column at
X=25280, Y=800/832/864; 0x2024 / slot 10 in that column at
Y=816/848/880; and 0x0022 / slot 9 in the adjacent column X=25296
at Y=800/832/864. This contact word/slot sequence is therefore
consistent with exact course-local packed cells at the finish stripe.

**Semantic consequence:** merely observing a 0x14 checkpoint/finish
object code cannot be equated to a finish event. The preceding **postframe observation** already contained the same handler
family while checkpoint, finish-gate and lap state had not changed. This
is not evidence that the word was dispatched during that same frame;
actual dispatch order places it earlier than the new contact sample. The next decoder/runtime experiment must
correlate the state of the handler, selected slot and active contact
point rather than assuming all cells of resource 0x24 are equivalent.

The observed P1 center Y=857 is seven world units above the nearest
slot-8 candidate cell band Y=864..879, ten below the Y=832..847 band,
and 42 below Y=800..815. The world-cell correlation tool now reports
this center-to-cell proximity explicitly as a *ranking* only, never as
a claimed contact-point location.

The retained snapshot has P1 Y=857 but does not preserve the exact
selected collision probe/contact Y or the footprint of the contacting
racer. It therefore does not resolve which of the repeated Y cells
was touched. Avoid promoting a unique cell or causal slot ordering
without that additional runtime witness.


One additional byte-level caveat comes from the original 128 KiB WRAM binaries.
The object-activation analyzer reads P1's sampled word at 7E:0E95:
it advances 0x1804 -> 0x2024 -> 0x2020 -> 0x0022 during this
transition. The postframe snapshot at 7E:0F09, the current-player
collision-state source named in the dispatcher disassembly, remains
0x1804 in all seven frames. These observations have separate fields
in the preserved witness and cannot be conflated. The apparent discrepancy is now resolved structurally by the byte-verified
P1/P2 handoff: shared 0F09 is overwritten by the subsequent P2 update
path before the frame-end dump, so it cannot be interpreted as
permanent P1 state. Whether every expected instruction executed on each
retained frame still requires a CPU trace. Resolve it
with an instruction-time read/write trace around 81:82E6 and the P1/P2
marshal, not by assigning stable frame-end memory an in-flight value.


The same archived snapshots add a narrower observation: per-player P2's
stored collision word at 7E:0E97 is exactly 0x1804 on all seven frames,
matching the settled 7E:0F09 scratch value byte-for-byte; the P1 word
at 7E:0E95 changes independently. This is consistent with 0F09 holding
the last marshalled/current-player collision word after the frame
finishes, potentially P2's. The per-player entry/exit marshal and bank-82 course-dispatch inputs are
now ROM-byte-verified, as documented in docs/COURSE-CONTACT-MARSHAL.md;
the precise instruction-time contents during a specific recorded event
remain unobserved. It is nevertheless enough
to reject using a postframe 0F09 snapshot as the observed P1 collision
selector for this trace.


### Validate placed course cells directly in native WRAM (2026-10-08)

tools/probe_live_course_world_cells.py resolves the same 64x64 coarse sector
-> 32-byte fine record -> packed 16x16 cell -> C000 behavior code contract
**from a 128 KiB native WRAM snapshot**, without relying on a pre-generated
course JSON file. It is a read-only diagnostic for course reconstruction.
For example, given a saved native frame from the established Dragster
object-activation probe:

    python3 tools/probe_live_course_world_cells.py frame.wram.bin \
      --rect 25280 784 25311 911 \
      --rom reference/roms/retail/Uniracers_USA.sfc \
      --stream-index 1

Supplying both ROM and stream index verifies that the entire selected
decoded course is actually resident at 7F:0000, except for the two
known mutable resource-list cursor bytes. This validation bounds the
fine-record indices to the selected decoded course, not merely to
physical WRAM. Without a ROM the tool explicitly labels course identity
unverified and constrains record reads only to the WRAM buffer.

The first independent live evidence is retained in
analysis/data/dragster-finish-live-course-cells.json. Those 16 placed
cells come from the original native guest-frame-2903 WRAM dump in Actions
run 36954104693 (artifact 11204794758), rather than being copied
from the generated static Dragster spatial contract. On the finish
stripe at X=25280/25296 and Y=784..911 the live coarse grid selects
fine records 19, 22 and 31. The exact word/slot pairings agree with the
separately decoded ROM spatial contract: e.g. 0x2020 selects C000 slot 8,
0x2024 slot 10, and 0x0022 slot 9, all with runtime behavior code 0x14.
Regression tests assert both cross-authority parity and correct live
coordinate indexing.

**Limits:** a live C000 value describes the materialized object behavior
at a placed world cell. It does not by itself prove that the cell was
actually contacted in a given frame, nor that its checkpoint/finish
handler changed race progress. The fine-cell lookup is also separate
from collision-footprint selection and guest execution timing.
