# Course Format Investigation

Goal: produce a ROM-free technical description of Uniracers/Unirally course data and a parser that operates locally on a user-supplied ROM.

## Historical leads

Prior community reverse-engineering reportedly identified Rob Northen Compression for level/course data and successfully decompressed blocks. Treat those reports as leads until reproduced.

## Questions

1. Where is the course index/table?
2. Which RNC method/version is used?
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

### Immediate reproduction plan

1. Search the supported ROM for RNC packed-data headers/signatures and enumerate plausible records.
2. Identify the game's decompression routine(s) from callers, constants, bit-reading structure and output behavior.
3. Compare that routine structurally against both supplied SNES decoders rather than assuming a method.
4. Run candidate records through an independent decoder and verify packed/unpacked sizes and CRCs where present.
5. Associate decoded records with course loads by tracing their ROM source addresses into RAM/VRAM.
6. Only then assign semantic names such as course geometry, block dictionary or tilemap data.

This turns R-SEED-001 into a directly reproducible experiment instead of relying on the historical report.
