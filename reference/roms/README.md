# ROM reference set

This directory contains the preserved cartridge images used by the private UR-Recomp research project.

## Layout

- `retail/Uniracers_USA.sfc`
  - Canonical project input.
  - USA retail release.
  - All normal recompilation, validation, and CI work should use this ROM unless a task explicitly says otherwise.
  - Canonical fingerprints remain recorded in the root `rom_identity.txt`.

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

## Next technical use

The PAL prototype should be fingerprinted beyond its Git blob SHA and compared against the USA retail ROM at several levels: raw blocks, SNES header/vectors, executable regions, pointer/data tables, compressed streams, and disassembly/function structure. The comparison is expected to be especially useful for identifying late tuning changes and separating code from packed assets.
