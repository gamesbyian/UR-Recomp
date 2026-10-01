# References

The maintained external-source corpus lives under `reference/`.

- `reference/catalog.yml` — provenance catalogue with source URLs, pinned revisions, rights notes, local copies/summaries and relevance.
- `reference/README.md` — ingestion policy.
- `reference/imported/` — third-party files copied into the repository when redistribution status is sufficiently clear.
- `reference/notes/` — our own technical summaries of sources that should not simply be vendored.

## Recompilation and tooling

- SNESRecomp: https://github.com/RetroPortingToolKit/snesrecomp
- snesref: https://github.com/RetroPortingToolKit/snesrecomp/tree/main/tools/snesref
- Mega Man X SNES recomp: https://github.com/mstan/MegaManXSNESRecomp
- Donkey Kong Country recomp: https://github.com/elliotttate/DKC1Recomp
- Retro Studio: https://github.com/RetroPortingToolKit/Retro-Studio

## Uniracers-specific starting points

- Historical ROMhacking.net level-viewer reverse engineering: see `reference/notes/course-reverse-engineering-history.md`.
- Snes9x/MAME active-display OAM behavior: see `reference/notes/oam-active-display.md`.
- Public sprite-sheet references: see `reference/notes/graphics-assets.md`.
- Libretro cheat data: `reference/imported/libretro/Uniracers (USA).cht`.

## Rule

External references are leads. Concrete project claims should be reproduced locally where practical and entered in the research ledger with evidence. A source being copied into this repository does not by itself make its claims canonical.


## Harvest expansion

- Regional/search vocabulary: `reference/notes/regional-search-vocabulary.md`.
- Mirrored emulator evidence: `reference/imported/emulators/`.
- Hidden Palace prototype and DMA press-material leads are tracked in `reference/catalog.yml`.


- Recovered Canoe patch and byte-level analysis: `reference/imported/patches/uniracers_canoe.md`.
- TAS/SRAM/bot/course-map archaeology: `reference/notes/tas-and-sram-research.md`.

- RetroAchievements RAM-address evidence: `reference/notes/retroachievements-ram.md` and mirrored `reference/imported/retroachievements/1295.json`.
- Widescreen/modern-renderer prior art: `reference/notes/widescreen-and-modern-presentation-prior-art.md` (pinned wide-snes and Zelda64Recomp references; bsnes-hd diagnostic taxonomy).
- Historical Snes9x 1.43-era source/problem snapshots: `reference/imported/emulators/snes9x-1.43/`.
- Manual and PAL course-map scan sources are tracked in `reference/catalog.yml`.

- RNC ProPack 2.14 historical toolchain, including original DOS packers and SNES Method 1/2 decoders: `reference/imported/tools/rnc_propack-2.14/`.

- Stalled-session recovery/state note: `reference/notes/recovery-2026-09-28.md`.
- Complete GameDB-SNES prototype metadata snapshot: `reference/imported/metadata/GameDB-SNES/c362c7b1/`.

## Original-development archaeology

Detailed technical history, source provenance, and acquisition status:

- docs/original-development/DEVELOPER-TECHNICAL-HISTORY.md
- docs/original-development/SOURCE-INDEX.md
- docs/original-development/ACQUISITION-LEDGER.md

High-value sources include Mike Dailly's own SNES tool/hardware notes, the 2010 developer retrospective, the archived level-viewer thread reporting Dailly correspondence, the 1994-11-29 PAL prototype record, and the DMA press-material archive. See SOURCE-INDEX.md for confidence labels and exact URLs.

- External decomp/recomp/ROM reverse-engineering practice archaeology, including multilingual sources: `reference/notes/external-reverse-engineering-practices.md`.
