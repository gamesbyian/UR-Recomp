# ROM reference set

This directory contains the preserved cartridge images used by the private UR-Recomp research project.

## Layout

- `retail/Uniracers_USA.sfc`
  - Canonical project input.
  - USA retail release.
  - All normal recompilation, validation, and CI work should use this ROM unless a task explicitly says otherwise.
  - Canonical fingerprints remain recorded in the root `rom_identity.txt`.

- `retail/Unirally_Europe.sfc`
  - Verified PAL retail release; comparative/regional research input, not the canonical runtime ROM.
  - 2,097,152 bytes.
  - CRC32: `d8583ed7`.
  - SHA-1: `d39ec113ef153ec9b7bacf12ed4a47f1a6d63a06`.
  - SHA-256: `a1105819d48c04d680c8292bbfa9abbce05224f1bc231afd66af43b7e0a1fd4e`.
  - Internal title `UNIRALLY`, PAL region byte 0x02, reset vector `$8858`.

- `prototypes/Uniracers_Beta_legacy.sfc`
  - Historical GoodSNES-listed `Uniracers (Beta)` image. Exact build date and original physical provenance are not established.
  - 2,097,152 bytes.
  - CRC32: `7ca23359`.
  - SHA-1: `c19a9239f56b0ccaaf0673d1fa9999c7727829d6`.
  - SHA-256: `450719206b1928287ac3bddbcacbba1907e38c0a1541825899d61df1a328c22d`.
  - Internal title `UNIRACERS`, NTSC/USA region byte 0x01, reset vector `$8858`.
  - Header checksum/complement match the USA retail image, but this does not establish the semantic relationship between the builds.

- `prototypes/Unirally_1994-11-29_PAL_prototype.sfc`
  - Preserved PAL development prototype dated 1994-11-29.
  - 2,097,152 bytes.
  - Git blob SHA: `53c4446921ca716d195533de3e0843e464704394`.
  - Preservation provenance is recorded in `docs/original-development/ACQUISITION-LEDGER.md`.
  - This is a comparative/differential research input, not the canonical runtime ROM.

## Rules

1. Never silently substitute a prototype or regional ROM for the canonical USA retail input.
2. Identify every ROM by exact hashes before using it as evidence.
3. Keep provenance for prototypes, betas, review builds, and other acquired images.
4. Code/data differences between builds are evidence, not automatically bugs or intended final behavior.
5. Before any public release or repository-visibility change, apply the proprietary-material policy in `docs/ROM-SAFETY.md`.

## Machine-readable inventory

Run `python tools/inventory_reference_roms.py` to regenerate `analysis/generated/reference-rom-inventory.md`. The inventory is authoritative for exact local hashes and basic header/RNC observations.

## Next technical use

Use all four verified images as differential oracles. Highest-value pairings are USA retail vs the historical GoodSNES beta, PAL retail vs the 1994-11-29 PAL prototype, and USA vs PAL retail. Compare raw blocks, vectors, executable regions, pointer/data tables, RNC streams and disassembly structure before assigning semantic meaning to any difference.
