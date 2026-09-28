# External Artifact Acquisition Ledger

Last updated: 2026-09-28

This tracks valuable artifacts not yet part of the repository. "Not acquired" means no verified local copy has been committed.

## A-001 — Uniracers / Unirally PAL prototype, 1994-11-29

Priority: critical  
Status: acquired and committed  
Preservation record: https://hiddenpalace.org/Uniracers_%28Nov_29%2C_1994_prototype%29  
External mirror: linked there to Forest of Illusion.

Known provenance: four EPROMs, SHVC-4PV5B-01 board, label "UNIRALLY PAL", dumped by Zoda-Y13, released by Forest of Illusion on 2022-07-28.

Why we want it: a second executable snapshot can reveal late code/data changes and make function/table boundaries much easier to infer.

Repository path:
reference/roms/prototypes/Unirally_1994-11-29_PAL_prototype.sfc

Original uploaded filename: Unirally.6216.sfc
Exact size: 2,097,152 bytes
Git blob SHA: 53c4446921ca716d195533de3e0843e464704394
Acquired: 2026-09-28

Intake status:
- ROM preserved under a descriptive prototype path.
- Canonical USA retail ROM remains separate under reference/roms/retail/.
- The accidentally uploaded RAR container was removed after the SFC was supplied directly.
- Exact cryptographic ROM fingerprints beyond the Git blob SHA remain to be recorded by the prototype-diff/fingerprint step.
- Next action: generate header/mapping/vector metadata and retail-vs-prototype diffs.

## A-002 — DMA Design Miscellaneous Press Material

Priority: high  
Status: manual acquisition recommended  
Hidden Palace: https://hiddenpalace.org/Assets/DMA_Design_Miscellaneous_Press_Material  
Internet Archive: https://archive.org/details/dma_press_material  
Archive size: about 638.6 MB.

Why we want it: electronic press-kit material and scans explicitly include Uniracers/Unirally. Potentially useful files include high-resolution renders, development screenshots, filenames/metadata, early UI, alternate artwork, and internal terminology.

Do not commit the entire 638 MB archive to GitHub by default. Download it locally, inventory it, then commit only relevant files after checking individual sizes and provenance.

Requested local intake:
1. Download dma_press_material.zip from Internet Archive.
2. Hash the original archive.
3. List archive paths, sizes, timestamps and file types.
4. Extract only Uniracers/Unirally-related material to staging.
5. Preserve original filenames.
6. Hash retained files.
7. Record each retained file here before committing.

Why manual: direct archive download failed from the current execution environment.

## A-003 — Mike Dailly historical SNES framework source

Priority: critical  
Status: not located  
Evidence: https://dailly.blogspot.com/2008/10/past-tools.html

Dailly said in 2008 that he had found his old 65816 SNES framework source and might clean/release it. He separately credits himself with the SNES framework/tools on Uniracers.

Acquisition strategy: search Dailly blog attachments, old site directories, Wayback captures, historic downloadable archives, Flickr/YouTube descriptions, later lemmings.info mirrors, and code-hosting accounts. Do not assume modern SNasm is identical to the 1993 version.

## A-004 — Original Uniracers development-tool artifacts

Priority: high  
Status: not located as downloadable binaries/source

Known tools: SNasm, SNES graphics converter, SNES MIDI converter, Unicycle Compression, Uniracers Editor, A0 plotter, Amiga/SNES link.

Source: https://lemmings.info/things-ive-done/

Look for source, binaries, screenshots, manuals, sample data, command-line documentation, disk images, or file listings. Even screenshots can disclose filenames and vocabulary useful in ROM archaeology.

## A-005 — Preserved SPC soundtrack

Priority: medium  
Status: available externally, not imported  
Source: https://www.snesmusic.org/v2/profile.php?profile=set&selected=3149

Contains ten preserved tracks, including two marked unused. Use for driver identification, song-table mapping, and used/unused-content analysis.

## Intake standard

For every binary artifact record:
- source URL;
- retrieval date;
- original filename;
- exact byte size;
- SHA-256;
- archive/container relationship;
- license or preservation/redistribution note if known;
- whether committed, ignored, or retained only locally;
- technical reason for keeping it.
