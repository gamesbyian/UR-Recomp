# Course Format Investigation

Goal: produce a ROM-free technical description of Uniracers/Unirally course data and a parser that operates locally on a user-supplied ROM.

## Historical leads

Historical reports identified Rob Northen Compression for level/course data. Local analysis confirmed 45 valid RNC Method 1 streams in the canonical USA retail ROM and 1994-11-29 PAL prototype, byte-identical at identical offsets. The newly acquired historical GoodSNES beta shares all 45 byte-for-byte as well. Europe retail also contains 45 streams, of which 38 are byte-identical by content; ordinal streams 4, 16, 20, 26, 27, 35 and 36 have changed packed/unpacked sizes and CRCs. The remaining question is what each decoded stream contains and how these seven final-PAL changes map to course or other semantics.

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
