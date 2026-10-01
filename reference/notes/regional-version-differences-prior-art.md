# Regional / Prototype Version-Difference Prior Art

This note records public third-party observations about differences between
`Uniracers` (USA), `Unirally` (Europe/PAL), and the surviving PAL prototype.
External claims remain leads until reproduced against the canonical ROM/runtime
corpus.

## High-value findings

### 1. PAL and NTSC input movies are not interchangeable

A 2008 TASVideos discussion records a user accidentally playing a USA Snes9x
movie against the PAL `Unirally` ROM. The run diverged almost immediately:
the unicycle moved left and failed to complete Dragster. The poster explicitly
connected the failure to using the wrong regional ROM and PAL/NTSC timing.

Source:
- https://tasvideos.org/Forum/Topics/979?CurrentPage=4&Highlight=39298&PageSize=25&Sort=CreateTimestamp

Project implication:
- Preserve this as an independent historical observation that deterministic
  input diverges across regions.
- Reproduce it more cleanly with one known USA input stream replayed against
  USA, PAL prototype, and Europe retail.
- Localize the first state divergence by frame/input tick. This may distinguish
  pure video-rate effects from changed timer, physics, input, or checkpoint
  logic.
- Do not assume a historical .smv remains suitable as the canonical fixture;
  use a project-owned deterministic input trace if cheaper.

### 2. PAL and NTSC players maintained separate record populations

GameFAQs preserved distinct NTSC and PAL high-score threads. Representative
Crawler/Dragster records are about 25.06 s NTSC versus 29.85 s PAL, close to
the expected 60 Hz / 50 Hz wall-clock ratio but not precise enough to establish
the game's timer formula from human records alone.

Sources:
- NTSC records:
  https://gamefaqs.gamespot.com/boards/588824-uniracers/41488930
- PAL records:
  https://gamefaqs.gamespot.com/boards/588824-uniracers/29406415

Project implication:
- Version-specific scoreboards are independent evidence that times are not
  directly comparable across USA/PAL.
- The historic record ratios are useful sanity checks for timer conversion,
  but canonical timer behavior should come from code/runtime evidence.
- This directly intersects the Europe-retail checkpoint timer-normalization
  contraction already identified in the multi-ROM atlas.

### 3. The surviving Nov-29-1994 build is explicitly a European PAL prototype

Hidden Palace identifies the surviving November 29, 1994 cartridge as a
European prototype. The public release dates place it before USA retail
(December 1994) and roughly five months before Europe retail (April 27, 1995).

Source:
- https://hiddenpalace.org/Uniracers_%28Nov_29%2C_1994_prototype%29

Project implication:
- The project's observed lineage is historically plausible: the prototype can
  contain PAL-oriented layout changes while retaining USA-like executable
  structure, with further changes entering Europe retail later.
- Keep using the prototype as a chronology discriminator rather than treating
  it as merely another regional ROM.

### 4. Uniracers depends on unusual active-display OAM behavior

Historical Snes9x carried an explicit Uniracers HDMA/OAM workaround. Later
bsnes/higan investigation described the underlying behavior more generally:
the game writes OAM during HBlank/active display and, on real hardware, the
internal OAM address happens to be around 0x0218 for the relevant scanline.
Near repeatedly noted that Uniracers is effectively the only known game to
depend on this behavior.

Sources:
- Snes9x historical game-specific workaround:
  https://sources.debian.org/src/libretro-snes9x/1.53%2Bgit20160522-1/memmap.cpp
  https://github.com/gocha/snes9x-rr/blob/master/dma.cpp
- bsnes analysis:
  https://bsnes.org/articles/state-of-emulation-2/
- NESdev active-display OAM discussion:
  https://forums.nesdev.org/viewtopic.php?f=12&hilit=Uniracers&t=15108
- NESdev DMA/HDMA discussion:
  https://forums.nesdev.org/viewtopic.php?start=15&t=14196

Project implication:
- This corroborates the existing OAM/fidelity research lane; it is not a newly
  discovered regional difference.
- Two-player rendering failures in historical emulators should be interpreted
  first through this hardware seam before attributing them to game-code
  regionalization.
- Keep the game-specific emulator hack distinct from the actual hardware model.

### 5. Historical emulator compatibility failures cluster around real hardware seams

Dorando's compatibility archive records multiple independent emulators with
Unirally failures: title-screen stops, major in-race graphics failure, sound
errors, and two-player errors. Snes9x 1.41 explicitly announced a “working
Uniracers hack” in DMA handling. Older Snes9x-derived changelogs also record
PAL scanline-count corrections and Uniracers-sensitive window/subscreen fixes.

Sources:
- https://dorando.emuverse.com/html/uniracers.html
- https://www.snes9x.com/journal.asp?PageNo=2
- https://github.com/OpenEmu/SNES9x-Core/blob/master/src/docs/changes.txt
- https://github.com/esmjanus/snes9xTYL/blob/mecm/CHANGES%20%28snes9x%29.TXT

Project implication:
- Preserve these as a failure-mode matrix, not proof of regional code changes.
- The reports provide cheap regression scenes for PPU/OAM/audio correctness.

### 6. Andrew Innes independently described the cartridge-detection protection

In a 2010 retrospective, programmer Andrew Innes said DMA accidentally
discovered a way to distinguish real cartridges from their development copy
device, then deliberately turned it into anti-piracy protection. He also
recalled the final ROM having only a few bytes free.

Source:
- https://www.nintendolife.com/news/2010/03/feature_the_making_of_unirally

A 1995 Game Doctor review independently listed Uniracers among cartridges whose
copy protection required special handling.

Source:
- https://groups.google.com/g/net.games.video/c/XLlkirOViQE

Project implication:
- This is strong historical provenance for the protection behavior already
  visible in emulator history.
- Search version diffs around protection-related code only when the four-ROM
  atlas shows executable or operand changes there; do not assume protection
  itself changed by region.

## Lower-value but real differences

### Branding / title presentation

The TASVideos discussion explicitly notes visibly different `Uniracers` and
`Unirally` title typography. This is obvious localization evidence and useful
for asset provenance, but low-value for core behavioral reconstruction.

### Manual differences

The same TASVideos thread records at least one content/layout difference between
the USA and UK manuals: a handwritten “tabletop” hint present in the US manual
was reportedly absent from the corresponding UK location, while other copy was
shared verbatim.

This is documentation/localization evidence, not ROM evidence.

## Search result: what was *not* found

No public source found so far provides a trustworthy comprehensive list of
USA-vs-Europe executable/gameplay changes.

No public source found so far documents:
- the Europe-retail-only checkpoint timer contraction identified locally;
- the post-prototype +4 and +2 WRAM insertion brackets;
- an explanation for the inserted WRAM bytes;
- a full prototype-to-retail change log.

This makes the local multi-ROM atlas genuinely additive rather than a
rediscovery of a known public diff.

## Recommended external-evidence experiments

1. **Cross-region deterministic-input divergence**
   - replay one fixed USA trace against USA / PAL prototype / Europe;
   - record first divergent frame and state fields;
   - separate video-rate divergence from actual code/data changes.

2. **Timer sanity model**
   - derive timer conversion from code/runtime;
   - compare expected PAL/NTSC ratios against the historical record tables;
   - use player records only as coarse validation.

3. **OAM two-player regression**
   - keep the existing active-display OAM fixture lane;
   - use the emulator-history sources as independent failure expectations.

4. **Continue targeted historical search**
   - TASVideos pages 1–7 and linked artifacts;
   - old Snes9x/bsnes/higan source history and forum discussions;
   - archived GameFAQs PAL/NTSC threads;
   - preservation/prototype release notes;
   - old copier/backup-device compatibility discussions.

Do not turn this into general game-history collection. The acceptance test for
new sources is whether they yield a specific version difference, a reproducible
hardware seam, or an experiment that can sharpen the multi-ROM atlas.
