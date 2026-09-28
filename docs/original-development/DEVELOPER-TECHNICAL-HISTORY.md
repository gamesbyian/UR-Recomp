# Original Development Archaeology

Last updated: 2026-09-28

This document records technical facts and leads about the original development of Uniracers / Unirally / 1x1 that may guide reverse engineering and recompilation. It deliberately separates first-hand developer statements from later reverse engineering and inference.

## Confidence labels

- Developer-confirmed: stated by a credited DMA developer.
- Contemporary: stated in period material.
- Reported correspondence: a researcher reports a direct exchange with a developer, but the original exchange is not presently preserved here.
- Independent reverse engineering: discovered by later researchers/emulator developers.
- Inference: project interpretation built from evidence above.

## Credited technical team

Mike Dailly's 2008 retrospective identifies the working responsibilities as follows:

- Malcolm Scott Maxwell: game coder and project leader.
- Andrew Innes: front end, statistics, and general coding.
- Martin Good: CG artist responsible for the unicycle renders.
- Robbie Graham: artist.
- Mike Dailly: level editor, unicycle compression, SNES framework and tools.
- Colin Anderson: music and effects.
- Craig Arbuthnott and other testers: testing; retail credits also identify level design work.

Sources:
- https://dailly.blogspot.com/2008/10/uniracerscredits.html
- https://www.mobygames.com/game/8085/uniracers/credits/snes/

## CPU, assembler, framework, and host tooling

### SNasm

Developer-confirmed. Dailly's project inventory lists SNasm as a 65816 macro assembler written for Amiga in Pascal/68000 work, dated 1993. He separately says his later SNasm retained the core of the assembler he wrote in 1992.

Sources:
- https://lemmings.info/things-ive-done/
- https://lemmings.info/museum-donations/

Implication: reconstructed source should not assume ca65/WLA/official Nintendo assembler conventions. Macro-generated idioms, calling conventions, data declarations, alignment, and bank layout may reflect a bespoke DMA tool.

### Surviving SNES framework source

Developer-confirmed existence in 2008. Dailly wrote that he had found his old 65816 SNES framework source and was considering cleaning it up and releasing it. The same developer separately credits himself with the SNES framework used on Uniracers.

Source:
- https://dailly.blogspot.com/2008/10/past-tools.html

Status: no public copy has yet been located in this investigation.

Priority: very high. A surviving framework could reveal initialization, IRQ/NMI handling, controller input, DMA helpers, memory conventions, macros, math routines, sprite/OAM management, and source terminology that can be matched against the retail binary.

### Other Dailly tools contemporaneous with Uniracers

Developer-confirmed. His inventory lists:

- SNES Graphics converter, DOS/Pascal, 1994.
- SNES MIDI converter, DOS/Pascal, 1994.
- Uniracers "Unicycle Compression, Editor", Amiga/DOS/SNES, C/68000, 1994.
- Uniracers A0 plotter, DOS/C, 1994.
- Amiga/SNES link, Amiga/Pascal/68000, 1994.

Source:
- https://lemmings.info/things-ive-done/

The A0 plotter is particularly useful corroboration for developer recollections that the huge animation set was managed on large printed sheets.

## SNES development hardware and iteration loop

Developer-confirmed. Dailly states that his SN Systems 65816 developer kit was first used for SNES Lemmings 2 and then "used to write Unirally." He also identifies a Super Magicom cartridge copier used for testing to avoid repeatedly burning EPROMs. A genuine cartridge was plugged into the Magicom/devkit as a protection cartridge.

He also describes building an Amiga-to-SNES devkit using a Magicom and parallel cable to download and run programs.

Source:
- https://lemmings.info/museum-donations/

Implications:
1. The game was repeatedly exercised from copier/dev hardware, not just final cartridge hardware.
2. Hardware-dependent copier detection is historically plausible and directly corroborated by Andrew Innes's later description of the game's copy protection.
3. Development artifacts may contain Magicom-format images, maps, or transfer-tool assumptions.

## Copy protection / copier detection

Developer-confirmed. Andrew Innes recalls DMA normally testing builds using a disk-based copy device rather than repeatedly burning EEPROMs. A development image sent to Nintendo behaved differently from a proper cartridge. Innes used the discovered distinction to implement anti-piracy logic, and later described Unirally as unusually troublesome to run correctly under emulation.

Source:
- https://www.nintendolife.com/news/2010/03/feature_the_making_of_unirally

Reverse-engineering warning: unusual cartridge-sensitive or timing-sensitive paths should not be dismissed as dead code until the anti-copy path is identified.

## Graphics and animation pipeline

Developer-confirmed. Robbie Graham describes the unicycle as a highly detailed 3D source model rendered down into very small 2D game frames. Animation dimensions included stunt rotations, tilt/stretch behavior, saddle movement, and many pedal/wheel phases. Martin Good is identified by Dailly as the CG artist responsible for the unicycles.

Sources:
- https://www.nintendolife.com/news/2010/03/feature_the_making_of_unirally
- https://dailly.blogspot.com/2008/10/uniracerscredits.html

Dailly's tool inventory independently identifies dedicated Unicycle Compression and an A0 plotter.

Inference: the ROM likely contains a highly indexed/packed multidimensional animation corpus rather than a simple sequential sprite strip. Recovering its indexing dimensions may be as important as extracting the graphics.

## Split-screen / sprite hardware behavior

Developer-confirmed concept; implementation to verify locally. Dailly has described Uniracers as applying a raster-era sprite trick for the unusually tight split-screen presentation. Later emulator/reverse-engineering discussions associate Uniracers with unusual OAM behavior during active display / HBlank.

Useful external lead:
- https://forums.nesdev.org/viewtopic.php?t=24932

Project rule: prove the exact ROM implementation with traces before documenting exact register behavior as fact.

## Course compression and structure

### RNC compression

Reported direct correspondence. In a 2009 ROM-hacking thread, researcher "Spinal" says he contacted Mike Dailly and was told that Unirally levels use Rob Northen Compression, recognizable by the bytes "RNC". He reports extracting and successfully decompressing level streams.

The same post says Dailly told him levels are 256 tiles wide.

Source:
- https://ximwix.net/mirrors/rhdn-old/index.php%40topic%3D6940.15.html

This is highly actionable but is not equivalent to an archived first-hand Dailly post. Verify both claims in the canonical ROM.

### Later structural observations

Independent reverse engineering. The same researcher reports that a decompressed map aligned with manually reconstructed maps and revised his model toward 64x64 blocks composed from an 8x8 SNES tile map.

These dimensions are hypotheses for local verification, not project truth.

## Physics / gameplay tuning

Developer recollection. The 2010 making-of describes an earlier, more simulation-like unicycle prototype and the later racing design. Colin Anderson recalls the team reducing testing to a flat straight race as an acid test for fairness and feel before relying on stunts and elaborate track geometry.

Source:
- https://www.nintendolife.com/news/2010/03/feature_the_making_of_unirally

Implication: a flat-track deterministic scenario is an excellent golden test for reconstructed acceleration, speed, collision/contact, stunt boost, and two-player fairness.

## Cartridge capacity

Developer recollection. Andrew Innes recalled that the finished cartridge had only a handful of unused bytes.

Source:
- https://www.nintendolife.com/news/2010/03/feature_the_making_of_unirally

Treat the exact byte count as recollection, but expect aggressive packing and avoid assuming gaps are intentionally unused.

## Audio

Retail credits and preservation sets identify Colin Anderson as composer/SFX author. A preserved SPC set contains eight normal tracks plus two unused pieces.

Sources:
- https://www.snesmusic.org/v2/profile.php?profile=set&selected=3149
- https://www.mobygames.com/game/8085/uniracers/credits/snes/

A secondary preservation source associates Anderson's SNES work with assembly-macro music entry and the Software Creations driver family:
- https://www.vgmpf.com/Wiki/index.php?title=Colin_Anderson

Status: driver-family attribution for this exact ROM should be verified from the binary before being considered confirmed.

## Development prototype

A public preservation record exists for a 1994-11-29 European prototype:

- origin: four-EPROM development cartridge;
- board: SHVC-4PV5B-01;
- label: UNIRALLY PAL;
- public release of dump: 2022-07-28.

Source:
- https://hiddenpalace.org/Uniracers_%28Nov_29%2C_1994_prototype%29

Priority: obtain a local copy, hash it, preserve provenance, and binary-diff against canonical USA retail.

## DMA press-material archive

Hidden Palace / Internet Archive preserve a 638.6 MB DMA Design miscellaneous press-material collection assembled from electronic press kits and scans. Uniracers/Unirally is explicitly represented.

Sources:
- https://hiddenpalace.org/Assets/DMA_Design_Miscellaneous_Press_Material
- https://archive.org/details/dma_press_material

Priority: acquire externally, inventory it, and commit only useful Uniracers-specific files whose size/licensing/provenance make repository storage sensible. Record hashes for every retained artifact.

## Search aliases

Use all of these in archival searches:

- Uniracers
- Unirally
- Uni Racers / Uni Rally
- 1x1 (development codename)
- DMA Design
- Malcolm Scott Maxwell / Malcolm Maxwell
- Andrew Innes
- Mike Dailly / Michael Dailly
- Robbie Graham
- Martin Good
- Colin Anderson
- Craig Arbuthnott
- Steve Hammond

## Multilingual search status

Searches have been run using English plus translated/locale-specific queries in French, German, Spanish, Italian, Polish, Russian, Swedish, and Japanese. Thus far the strongest technical evidence resolves to English-language developer interviews, Dailly's own sites, preservation archives, and English ROM-hacking material. Non-English results remain useful as pointers to scans or interviews but should not be treated as independent corroboration when they translate an English source.

## Concrete ROM predictions

These are tests, not assumed facts:

1. Find RNC magic/signatures and identify all candidate compressed streams.
2. Locate the decompressor and classify the RNC variant.
3. Test a 256-tile-wide interpretation of decompressed course data.
4. Search for structures consistent with 64x64 blocks backed by 8x8 SNES tiles.
5. Identify active-display/HBlank OAM manipulation and determine exactly how split-screen sprites are recycled.
6. Identify cartridge/copier-sensitive protection logic.
7. Recover the unicycle animation index dimensions and compression/decompression path.
8. Identify the audio driver and distinguish used from unused music.
9. Compare the 1994-11-29 PAL prototype against USA retail at function/data-block granularity.
10. Compare reconstructed startup/framework patterns with any recovered Dailly SNES framework source.


## Second-pass archival leads

### Dailly Flickr / YouTube preservation corpus

Developer-confirmed. In September 2007 Mike Dailly said he had been looking out Uniracers pictures for an article, that he had far too much old DMA material for his planned DMA website, and that he was uploading old images to Flickr and DMA videos to YouTube. A later post says he still had "a stack of level building graphics" even after uploading much of the material.

Sources:
- https://dailly.blogspot.com/2007/
- https://dailly.blogspot.com/2007/09/?m=0
- historical Flickr account: https://www.flickr.com/photos/mikedailly/

Implication: archived Flickr set IDs, image descriptions, original filenames, comments, and Wayback captures are a high-value search surface. "Level building graphics" may refer to multiple DMA games, so attribution must be verified per asset.

### Steve Hammond as a second preservation node

Developer-confirmed general DMA archive, not yet Uniracers-specific. In a 2016 interview Steve Hammond says he still has old graphics and photos, a number of game design/proposal documents, and complete source/assets for an unfinished DMA project. This demonstrates that his personal archive survived long after DMA.

Source:
- https://www.retrovideogamer.co.uk/rvg-interviews-steve-hammond/
- Spanish mirror/transcription: https://www.elotrolado.net/hilo_entrevista-a-steve-hammond-programador-en-dma-design-lemmings-unirally-body-harvest_2184097

Implication: search Hammond's published archive/blog material for Uniracers-era scans, filenames, faxes, design paperwork, or photos. Do not assume possession of Uniracers source.

### Modern SNasm and SNES archaeology tools

Mike Dailly currently distributes a modern SNasm supporting 65816. He describes it as his personal macro cross-assembler and elsewhere says the modern assembler descends from his older work. This is useful syntax/convention evidence but is not assumed source-compatible with the 1993 tool.

- https://mdf200.itch.io/snasm

Dailly also has a public fork of the DisPel 65816/SNES disassembler:
- https://github.com/mikedailly/SNES-Disassembler

This is not original DMA tooling, but may reveal his later preferred SNES-analysis workflow and is worth keeping as a reference rather than treating it as historical evidence about the 1994 build.


## Third-pass technical evidence

### Direct 2008 scanline statement from Dailly

In a 2008 Lemon64 discussion, Mike Dailly explicitly says that on SNES Nintendo was not keen on developers changing things "on a scanline basis", that DMA did exactly that for Uniracers, and that the technique had to be verified by Nintendo R&D.

Source:
- https://www.lemon64.com/forum/viewtopic.php?sid=36bb321ef89b54d4d24309d3388276a0&start=30&t=27153

This is stronger than a later emulator inference because it directly establishes intentional per-scanline state changes in the shipped technique.

### Dailly identifies the technique as sprite ripping

In a September 2008 blog post, Dailly says the Uniracers split-screen system used an old C64 trick of "ripping sprites" to achieve perfect splits and that Nintendo R&D had to verify it.

Source:
- https://dailly.blogspot.com/2008/09/

In a later technical article about C64 emulation, Dailly explains sprite ripping more concretely: change a sprite's position while the raster is drawing it so different portions of the sprite are effectively rendered at different positions. He says Uniracers used the same trick on SNES, that Nintendo had not seen it before, and that the two black separator lines were aesthetic rather than required.

Source:
- https://lemmings.info/creating-a-commodore-64-emulator-in-gamemaker-part-6/

Implication for reverse engineering: the target is not merely generic HDMA usage. Instrument scanline-timed writes to OAM-related state / sprite positions and correlate them with viewport boundaries.

### Dailly's own SNES hardware comments

In the same Lemon64 discussion family, Dailly describes SNES sprite limits and notes that sprite positions can be changed on the fly despite hardware sprite multiplexing. These comments are general SNES-development context rather than Uniracers-specific implementation detail, but they reinforce the plausibility of the split-screen method.

Sources:
- https://www.lemon64.com/forum/viewtopic.php?p=325237
- https://www.lemon64.com/forum/viewtopic.php?p=325840

### Historical DMA archive sites

Steve Hammond described Mike Dailly's old dmadesign.org site as a detailed and unusually technical record of DMA development history.

Source:
- https://dmadesign.wordpress.com/

The old site and javalemmings mirrors should be treated as archival search surfaces even where modern indexing is poor. Historic paths referenced elsewhere include chapter-style pages such as javalemmings.com/DMA/DMA4_1.htm.
