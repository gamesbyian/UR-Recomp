# ROM and Copyright Policy

## Current private-research policy

This repository intentionally tracks one canonical project input:

- `Uniracers (USA).sfc`

The reason is operational: GitHub Actions and repository-based tooling can analyze the exact same input without an out-of-band ROM handoff.

This differs from SNESRecomp's recommended public-distribution model, which expects users to supply their own ROM.

## Still keep out of Git by default

- duplicate or alternate ROM dumps unless deliberately admitted;
- bulk extracted graphics, music, sound samples, maps or other copyrighted assets;
- saves/states containing substantial proprietary data unless needed for a specific experiment;
- bulk generated source that effectively reproduces proprietary ROM code;
- distributable builds that embed the ROM;
- temporary dumps and analyzer output that can be regenerated cheaply.

## Appropriate project material

- hashes and cartridge metadata;
- verification/build scripts;
- reverse-engineering notes;
- symbols and addresses;
- reproducible analysis configuration;
- independently authored runtime/integration code;
- tests expressed as inputs, addresses, assertions or small factual state values;
- structural format documentation;
- transformation logic;
- concise generated evidence needed to reproduce a finding.

## Visibility gate

**Do not make this repository public while the ROM remains in current or historical Git objects.**

Deleting the file in a later commit is not sufficient. Before any public release or visibility change:

1. remove proprietary ROM/game-derived material from the working tree;
2. audit the entire Git history;
3. rewrite history where necessary;
4. verify release artifacts do not embed the ROM;
5. re-check generated source/assets for redistributable game content.

Private-repo storage is a deliberate convenience for this research project, not a claim about redistribution rights.
