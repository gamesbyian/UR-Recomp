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
3. Identify the game's decompression routine and compare it structurally with the preserved SNES `RNC_1.S` implementation.
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
