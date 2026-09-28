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


## Additional exact breadcrumbs from the archived thread

The first page preserves several concrete addresses and observations worth testing directly:

- ROM offset `0x108000` was called out because it contains repeated 8-byte structures such as `0F 04 1E 04 17 1E 00 00`, `10 04 1F 04 16 1E 00 00`, etc. Spinal initially suspected these might encode tile composition or palette-related structure. That interpretation was not established, but the address itself is a useful landmark.
- During emulator tracing, a DMA source around `7E:2080` was observed in connection with the level/background tilemap path. The original discussion identifies the destination/register context as BG tilemap-related. This is RAM, not a direct ROM address, so the recommended technique was to trace the writes that populate that RAM region back to ROM/decompression code.
- vSNES showed the level/background layer using an extended `64×64` tilemap in at least the inspected state.
- The thread explicitly distinguishes rendered tile graphics from collision/physics information after destructive ROM corruption produced visual and physics changes independently.

These are historical debugger breadcrumbs, not yet verified addresses for our supported ROM revision. They are good candidates for early trace labels once the recomp/disassembly environment is operational.
