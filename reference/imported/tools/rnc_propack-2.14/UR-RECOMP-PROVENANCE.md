# RNC ProPack 2.14 research mirror

Source mirror: https://github.com/tobiasvl/rnc_propack
Pinned revision: `08406a33e700aa33936e4c4800cd0887a468a31b`
Retrieved: 2026-09-28

This directory preserves the original ProPack 2.14 package files from the public mirror byte-for-byte, excluding only the mirror maintainer's GitHub README. It includes the packer executables, original manual/listing, and supplied decompressor assembly for every platform in the archived package, including SNES.

The upstream mirror describes this as the official RNC 2.14 package. The original manual identifies Rob Northen Computing and states Copyright (c) 1991,92, All Rights Reserved. These files are preserved as third-party historical/reverse-engineering evidence.

## Uniracers relevance

Historical Uniracers reverse engineering records Mike Dailly identifying the game's course/level compression as Rob Northen Compression. The package includes period SNES reference implementations for both methods:

- `SOURCE/SUPERNES/RNC_1.S`
- `SOURCE/SUPERNES/RNC_2.S`

These give us code signatures and format behavior to compare directly with the Uniracers ROM decompression routine and compressed data.

## Integrity

Files copied from the source mirror were transferred via their Git blob contents, using base64 for byte-preserving import. Original relative names are retained.
