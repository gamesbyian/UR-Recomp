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

## Owner decision: public research repository and runner availability

**Recorded 2026-10-21:** The project owner has deliberately kept this repository **public** because available GitHub Actions runner capacity is more constrained for their private repositories. They understand and explicitly accept the exposure risk associated with canonical ROM bytes in present and historical Git objects. **Do not silently change repository visibility or repeatedly raise this already-decided tradeoff as a blocker to ordinary project work.** This is the owner's current operational choice, not an assertion that hosting or redistribution rights have been granted.

**Narrow safety boundary:** This decision does **not** authorize publishing additional ROM dumps or ROM-bearing build/artifact ZIPs through Actions, releases, PR attachments or the recovery vault. Review and restrict those independently; avoid adding new copies. Agents should continue ROM-free unit tests and source-provenance checks where suitable.

## Future distribution and visibility hygiene

If the owner revisits publication/distribution policy or plans to remove proprietary ROM material from the repository, deleting a file in a later commit is not sufficient. Before claiming a ROM-free public distribution:

1. remove proprietary ROM/game-derived material from the working tree;
2. audit the entire Git history;
3. rewrite history where necessary;
4. verify release artifacts do not embed the ROM;
5. re-check generated source/assets for redistributable game content.

Private-repo storage is a deliberate convenience for this research project, not a claim about redistribution rights.
