# Third-party source audit

This document records engineering review of imported executable/source artifacts.
The goal is not preservation for its own sake. Preserve originals for provenance;
promote only behavior that survives local verification into project-owned tools.

## Evidence hierarchy

For implementation decisions, prefer evidence in roughly this order:

1. canonical-ROM behavior reproduced in the project's deterministic harness;
2. hardware-oriented behavior independently corroborated by multiple modern implementations or hardware research;
3. period source that directly matches bytes/algorithms in the ROM;
4. modern emulator source with a generic hardware model;
5. emulator source with game-specific handling;
6. historical scripts, cheats, achievements and labels;
7. comments, filenames and folklore.

Agreement between multiple emulators is not automatically independent evidence if
they share the same historical workaround or uncertainty.

## Audited imports

### jgenesis SNES sprite/OAM implementation

Path: `references/imported/emulators/jgenesis/sprites.rs`

Assessment: **high-value implementation reference**.

The imported revision models sprite evaluation, tile fetch and mid-scanline OAM
writes through generic PPU state. Uniracers appears in a comment explaining a
dependency, not in a game-name conditional. That is the architecture closest to
what UR-Recomp should prefer if the behavior is reproduced locally.

Useful ideas to extract:

- explicit evaluation/fetch/idle sprite phases;
- progression of PPU sprite state to the current dot before active-display OAM writes;
- tracking the last fetched OAM index;
- deriving the effective OAM address from current sprite state rather than forcing a game-specific constant.

Do not copy implementation details blindly. Timing, scanline boundaries and the
exact effective OAM target still need deterministic validation against the ROM.

### Snes9x 1.43 snapshot

Paths:

- `references/imported/emulators/snes9x-1.43/dma.cpp`
- `references/imported/emulators/snes9x-1.43/problems.txt`
- `references/imported/emulators/snes9x-1.43/changes.txt`

Assessment: **excellent compatibility archaeology; poor implementation template**.

The DMA source contains an explicit `SNESGameFixes.Uniracers` branch that forces
`PPU.OAMAddr = 0x10c` and clears `PPU.OAMFlip`. The same file contains multiple
contemporaneous `XXX` comments describing incomplete DMA/HDMA behavior.

Use it to answer:

- what failure shape old emulators observed;
- which subsystem was implicated;
- which constant workaround happened to make the game work.

Do not port the branch into UR-Recomp.

### Pinned newer Snes9x snapshot

Paths:

- `references/imported/emulators/snes9x/dma.cpp`
- `references/imported/emulators/snes9x/memmap.cpp`

Assessment: **useful reference oracle, but still game-specific at this seam**.

The newer snapshot still contains explicit Uniracers handling. `memmap.cpp`
detects the internal title and sets `SNESGameFixes.Uniracers`; the HDMA path in
`dma.cpp` then applies an OAM-address workaround and comments that the emulator
does not fully understand OAM address invalidation.

Consequence: old and newer Snes9x are not two independent votes for the hardware
rule. They are two generations of the same acknowledged game-specific strategy.

### MAME SNES PPU snapshot

Path: `references/imported/emulators/mame/snes_ppu.cpp`

Assessment: **independent and useful, but explicitly approximate at this seam**.

The imported source documents Uniracers as the known game that performs active-
display OAM access and routes those accesses specially. The source itself calls
the treatment a hack and says exact behavior is not fully understood.

Use MAME as an independent discriminator and for candidate hardware semantics.
Do not treat the existence of a special route as proof that its chosen target is
the exact hardware behavior.

### RNC ProPack 2.14

Path: `references/imported/tools/rnc_propack-2.14/`

Assessment: **authoritative historical algorithm/format evidence**.

This is one of the strongest imports in the repository because period Super NES
Method-1 source can be matched directly to code and compressed streams in the
game. The DOS executables are retained as historical artifacts, not as preferred
runtime dependencies.

Project policy:

- keep `PPAMI.EXE` and `PPIBM.EXE` non-executable in Git;
- prefer project-owned decoders for automated analysis;
- use the period source to verify bitstream semantics, entry signatures and
  control-flow correspondence;
- differential-test project-owned decoding against all known streams and CRCs.

### Dessyreqt 2014 Tabletop bot

Path: `references/imported/tas-bots/uniracers-tabletop-bot-2014.lua`

Assessment: **high-value behavioral corpus; not safe as a direct API**.

Review has found at least two ordinary source defects/hazards:

- the player-1 byte table repeats named keys; Lua silently retains later values;
- `MakeWordSigned()` uses `word > 32768`, so raw `0x8000` is interpreted as
  +32768 rather than -32768.

The bot also embeds emulator-specific APIs, magic thresholds, track rectangles,
menu timings and historical RAM labels in one monolithic policy.

Use it as a source of hypotheses and controller-policy structure. Port useful
behavior into small project-owned state/policy/input layers after validating each
state field. Preserve the original file unchanged.

### Historical SMV movies

Paths:

- `references/imported/tas-bots/uniracers-2008-wip-microstorage.smv`
- `references/imported/tas-bots/dessyreqt-4250-submission.smv`

Assessment: **excellent deterministic input corpora**.

These are better treated as immutable data than as emulator-specific workflows.
Translate them into neutral controller streams and validate resulting state under
both the native runtime and a reference emulator. Embedded SRAM/reset semantics
must be preserved when present.

### Cheats and RetroAchievements

Paths:

- `references/imported/libretro/Uniracers (USA).cht`
- `references/imported/retroachievements/1295.json`

Assessment: **compact reverse-engineering leads**.

Addresses, patches and descriptions are hypotheses until reproduced locally.
Descriptions can be wrong while addresses remain useful. Never make a gameplay
or fidelity claim solely because a cheat/achievement label says what a byte does.

The libretro cheat mirror was found to have been normalized on import: upstream's
literal `&gt;` in one description had become `>`. PR #8 restores the exact
upstream bytes and now verifies the upstream Git blob hash.

## Promotion rule

An imported implementation detail may become project-owned infrastructure only
when all of the following are true:

- its purpose for UR-Recomp is explicit;
- source identity is pinned and integrity-checked;
- version/platform/emulator assumptions are identified;
- important semantics are reproduced locally;
- the project-owned interface is smaller and clearer than the historical one;
- a regression test protects the promoted invariant.

If the only reason to retain an awkward historical behavior is "the old tool did
it this way," leave it in `references/imported/`.
