# References

The maintained external-source corpus lives under `references/`.

- `references/catalog.yml` — provenance catalogue with source URLs, pinned revisions, rights notes, local copies/summaries and relevance.
- `references/README.md` — ingestion policy.
- `references/imported/` — third-party files copied into the repository when redistribution status is sufficiently clear.
- `references/notes/` — our own technical summaries of sources that should not simply be vendored.

## Recompilation and tooling

- SNESRecomp: https://github.com/RetroPortingToolKit/snesrecomp
- snesref: https://github.com/RetroPortingToolKit/snesrecomp/tree/main/tools/snesref
- Mega Man X SNES recomp: https://github.com/mstan/MegaManXSNESRecomp
- Donkey Kong Country recomp: https://github.com/elliotttate/DKC1Recomp
- Retro Studio: https://github.com/RetroPortingToolKit/Retro-Studio

## Uniracers-specific starting points

- Historical ROMhacking.net level-viewer reverse engineering: see `references/notes/course-reverse-engineering-history.md`.
- Snes9x/MAME active-display OAM behavior: see `references/notes/oam-active-display.md`.
- Public sprite-sheet references: see `references/notes/graphics-assets.md`.
- Libretro cheat data: `references/imported/libretro/Uniracers (USA).cht`.

## Rule

External references are leads. Concrete project claims should be reproduced locally where practical and entered in the research ledger with evidence. A source being copied into this repository does not by itself make its claims canonical.


## Harvest expansion

- Regional/search vocabulary: `references/notes/regional-search-vocabulary.md`.
- Mirrored emulator evidence: `references/imported/emulators/`.
- Hidden Palace prototype and DMA press-material leads are tracked in `references/catalog.yml`.
