# Course Format Investigation

Goal: produce a ROM-free technical description of Uniracers/Unirally course data and a parser that operates locally on a user-supplied ROM.

## Historical leads

Historical reports identified Rob Northen Compression for level/course data. Local analysis has now confirmed 45 valid RNC Method 1 streams in both the canonical USA retail ROM and the 1994-11-29 PAL prototype, at identical offsets with matching packed/unpacked sizes and CRCs. The remaining question is what each decoded stream contains and how it maps to course semantics.

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

1. Extract and independently decompress all 45 confirmed Method 1 streams; verify unpacked sizes and CRCs.
2. Generate a compact manifest with offsets, hashes, byte statistics and structural signatures.
3. Identify the game's decompression routine and compare it structurally with the preserved SNES `RNC_1.S` implementation.
4. Test the historical 256-tile-width and 64x64-block claims against decoded bytes.
5. Associate decoded records with course loads and Halamantariel/VGMaps maps.
6. Identify course index/pointer tables and only then assign semantic names such as geometry, block dictionary, tilemap or metadata.
