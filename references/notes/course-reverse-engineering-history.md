# Historical course reverse engineering

Source: ROMhacking.net forum thread **“Unirally/Uniracers level viewer”**, preserved by the ximwix mirror.

Primary:
https://ximwix.net/mirrors/rhdn/index.php@topic=6940.0.html

Continuation:
https://ximwix.net/mirrors/rhdn-old/index.php@topic=6940.15.html

Retrieved: 2026-09-28

## What the historical work established or strongly suggested

The investigator “spinal” began by locating palettes and 8×8 graphics in the ROM and using emulator/debugger tooling to connect ROM data, VRAM state, DMA transfers and displayed tilemaps.

The thread documents the practical progression from raw graphics to a course viewer:

- track graphics use 8×8 SNES tiles, with displayed course structures assembled at larger granularities;
- VRAM/tilemap inspection and DMA tracing were used to work backward toward source data;
- destructive ROM edits were used to identify title graphics, logos, palettes, music and apparent physics/collision-related regions;
- visual track representation and collision/physics data were observed to be separable;
- Mike Dailly was contacted and reportedly identified the level data as Rob Northen Compression (RNC), allowing compressed files to be extracted and decompressed;
- Dailly reportedly stated that levels are 256 tiles wide;
- the resulting viewer output was reported to align with independently hand-made maps;
- later discussion described levels as apparently composed from 64×64 blocks, with unresolved mapping down to 8×8 tile graphics.

## Why this matters to UR-Recomp

This is not just historical trivia. It gives us several concrete hypotheses to reproduce:

1. Find the RNC signatures / decompression path in the supported US ROM.
2. Locate the course index and compressed records.
3. Determine which “tile” unit the historical 256-wide statement refers to.
4. Reconstruct the block hierarchy without inheriting ambiguous old terminology.
5. Separate collision/physics geometry from rendered track graphics.
6. Produce a deterministic extractor and compare it with known visual course layouts.

Until reproduced locally, these remain historical leads rather than canonical facts.

See also: `docs/COURSE-FORMAT.md` and `docs/RESEARCH-LEDGER.md`.
