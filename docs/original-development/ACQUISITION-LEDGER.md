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


## A-006 — Mike Dailly Flickr / historical DMA media corpus

Priority: high  
Status: systematic archival capture not yet done  
Sources:
- https://www.flickr.com/photos/mikedailly/
- https://dailly.blogspot.com/2007/09/?m=0

Dailly specifically wrote while searching for Uniracers pictures that he had a very large store of old DMA imagery and later said he still had a stack of level-building graphics.

Acquisition strategy:
1. enumerate surviving Flickr sets/items and descriptions;
2. search Wayback for historical set pages and original-size asset URLs;
3. preserve Uniracers/1x1-attributable images with original IDs, captions and dates;
4. record ambiguous DMA assets separately rather than assigning them to Uniracers;
5. inspect YouTube descriptions/thumbnails for matching archived development material.

## A-007 — Steve Hammond personal DMA archive traces

Priority: medium-high  
Status: holdings known generally; Uniracers-specific material unconfirmed  
Source: https://www.retrovideogamer.co.uk/rvg-interviews-steve-hammond/

Hammond says he retained old DMA graphics, photos, design/proposal documents, and complete source/assets for at least one unfinished project. Search published Hammond material and mirrors for Uniracers-era documents and scans. No outreach is assumed or required.

## A-008 — Modern SNasm reference build

Priority: medium  
Status: downloadable but not yet imported  
Source: https://mdf200.itch.io/snasm  
File advertised: SNasm.zip, approximately 62 kB.

Purpose: compare syntax, macro behavior and assembler conventions with any reconstructed 65816 source. Treat only as a descendant/reference unless historical continuity is demonstrated.

The download is behind itch.io's "No thanks, just take me to the downloads" handoff, which the current non-interactive fetch path does not expose as a stable direct file URL.


## A-009 — Historical SNasm 1.7.x builds

Priority: high  
Status: SNasm 1.7.1 acquired and committed; 1.7.2 remains an external preservation lead

SNasm 1.7.1:
- preservation page: https://csdb.dk/release/?id=57677
- release date: 2007-11-30
- original URL preserved by CSDb: http://www.javalemmings.com/minus4/files/snasm1.7.1.zip
- CSDb mirror: http://csdb.dk/getinternalfile.php/49921/snasm1.7.1.zip

SNasm 1.7.2:
- preservation index: https://plus4world.powweb.com/tools/all/Windows/3
- recorded date: 2008-05-10

SNasm 1.7.1 is now preserved at:
- reference/tools/snasm/historical/snasm-1.7.1-2007-11-30.zip
- reference/tools/snasm/historical/snasm-1.7.1-2007-11-30.sha256

SHA-256:
0c5f1ccfbe82d893fe5cc1b638c01343f414898a8f571786f098238151d7ed1b

Acquisition date: 2026-09-28. The one-shot acquisition workflow was removed after successful capture.

Why important: these builds are only ~13-14 years newer than the Uniracers assembler and come from the same author/tool lineage, while explicitly retaining 65816 support. Compare them with the modern SNasm package and with any future reconstructed source, but do not assume syntax identity with the 1993 Amiga version.


## A-010 — gamesTM issue 64 (December 2007)

Priority: medium-high  
Status: physical copy catalogued by Video Game History Foundation; no digital scan located

Catalog:
- https://library.gamehistory.org/subjects/14?filter_fields%5B%5D=primary_type&filter_values%5B%5D=archival_object&page=96
- identifier: MAG-GAMESTM.064

A contemporary November 2007 NeoGAF thread describes the issue's retro section as containing an interview with the Unirally SNES makers:
- https://www.neogaf.com/threads/gamestm-issue-64-review-scores-ac-ouch.210737/

The Nintendo Life 2010 feature appears to be a republication of this interview, but the physical issue may contain omitted captions, sidebars, images, layout annotations, or wording. Acquire/inspect only if it becomes useful; current web text already preserves the main interview content.
