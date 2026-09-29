# Historical course-layout reverse-engineering notes

Retrieved/rechecked: 2026-09-28

Purpose: preserve concrete historical observations that can discriminate local course-format hypotheses. These are external observations until reproduced against the canonical ROM.

## RHDN Unirally/Uniracers level-viewer thread

Archive:
https://ximwix.net/mirrors/rhdn-old/index.php%40topic%3D6940.15.html

Earlier page:
https://ximwix.net/mirrors/rhdn/index.php%40topic%3D6940.0.html

Relevant observations reported by Spinal:

- Mike Dailly told him the level/course data used Rob Northen Compression and described levels as 256 tiles wide.
- After extracting and decompressing the RNC payloads, Spinal wrote a viewer and reported that its output aligned with track maps he had made manually.
- He later reported that one byte in the decompressed level corresponds to one 64x64 course block.
- He distinguished that stored representation from the live SNES background tilemap: the visible BG used 16x16 SNES tiles and a conventional VRAM tilemap, so the game appears to expand/translate its course representation before display.
- The thread reports 1280 available 8x8 graphics tiles while discussing the still-unresolved composition of the larger course blocks.

These observations are especially relevant to the local header discovery that decoded bytes 13/14 form complementary dimensions with constant product 1024 when encoded zero is treated as 256. The smallest combined hypothesis is therefore a 1024-entry, one-byte-per-64x64-block stored course plane whose shape is described by bytes 13/14. This remains a hypothesis until the corresponding decoded region and runtime consumer are identified.

## VGMaps corpus

Map index:
https://vgmaps.de/maps/snes/uniracers

VGMaps credits Halamantariel with a broad set of full-course maps. These are useful as an independent visual oracle for later parser/viewer work, but their PNG bounds are stitched/cropped presentation bounds rather than presumed raw storage dimensions.

A VGMaps site-statistics post records, for example:

- Crawler / Dragster: 28,128 x 152 pixels, exceptionally wide;
- Hopper / Downer: 36,864 x 16,111 pixels, exceptionally large.

Those image dimensions should not be equated directly to header dimensions. Use topology/orientation and recognizable block sequences as comparison evidence after a local stored-layout plane is reconstructed.

## Local next tests

1. Characterize successive 1024-byte regions immediately after the 16-byte decoded header across all 45 streams.
2. Identify which region has one-byte index/map-like statistics and changes coherently with the 13/14 shape pair.
3. Reshape candidate regions by the encoded dimensions and compare topology/orientation against Halamantariel maps, starting with extreme aspect cases such as Dragster, Vertical and Little Dipper.
4. Trace the candidate region into the game's runtime course-to-VRAM/background generation path.
5. Only after the consumer relationship is verified, assign semantic names and build a durable viewer/parser.
