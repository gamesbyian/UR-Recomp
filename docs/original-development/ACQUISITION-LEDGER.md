# External Artifact Acquisition Ledger

Last updated: 2026-09-29

This tracks both acquired and still-missing external artifacts, with provenance and next actions.

## Acquisition triage rule

A missing artifact is not automatically a project dependency. Keep searching for all listed leads, but spend effort according to expected forward value:

- **P0 / high leverage** — likely to expose implementation behavior, original code/tool semantics, or hard-to-reconstruct mechanics. Active archival hunting is justified.
- **P1 / useful corroboration** — likely to make an existing reverse-engineering lane cheaper or independently confirm it. Pursue opportunistically and automate acquisition when cheap.
- **P2 / optional evidence** — useful if it falls into our hands, but existing ROM/runtime evidence can answer the same questions. Do not block project work on it.
- **P3 / archival tail** — preserve the lead and accept cheap wins, but do not build bespoke recovery machinery or delay milestones for it.

Current missing-artifact judgment:
- **P0:** Mike Dailly historical SNES framework; original Uniracers/DMA editor/converter/tool artifacts.
- **P1:** `usjo13.lua` or later USJO siblings now that internal v8 is recovered; Halamantariel boost/mechanics page; Sinister 100% translation patch; genuinely distinct old SMV/savestate corpora; Uniracers-specific Dailly development media.
- **P2:** VGMaps course images and official packaging maps; Uniracers-specific Steve Hammond material; US manual scan; Tamoketh recreation artifacts when technical/source material exists.
- **P3:** SNasm 1.7.2 after 1.7.1 + modern SNasm are already preserved; gamesTM #64 unless it contains material absent from the Nintendo Life republication; Uniracers Uncensored unless a surviving patch is trivially downloadable; generic DMA media with no Uniracers attribution.

P2/P3 does **not** mean “stop looking.” It means a future agent should not mistake archival completeness for a critical-path requirement.

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
- SHA-256 and header/mapping metadata are recorded by `analysis/generated/retail-vs-prototype-structure.md`.
- The first retail-vs-prototype structural diff is complete; future work should classify meaningful non-RNC differences.

## A-002 — DMA Design Miscellaneous Press Material

Priority: low for further acquisition  
Status: archive inspected by the user; Uniracers PDF uploaded; no additional useful files identified  
Hidden Palace: https://hiddenpalace.org/Assets/DMA_Design_Miscellaneous_Press_Material  
Internet Archive: https://archive.org/details/dma_press_material  
Archive size: about 638.6 MB.

Outcome: the archive was manually inspected and the Uniracers PDF was uploaded and organized at `reference/imported/press/dma-design/uniracers_01.pdf`. The user judged the remaining archive contents not useful for this project. Reopen only if a later clue points to a specific file or asset class.

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

Priority: completed evidence intake  
Status: acquired and analyzed transiently; binary intentionally not redistributed in this repository  
Primary source: https://www.snesmusic.org/v2/profile.php?profile=set&selected=3149  
Recovered mirror: https://www.zophar.net/music/nintendo-snes-spc/uniracers

The ten-track archive, including both tracks tagged unused, was recovered, fingerprinted and analyzed. Archive SHA-256 is recorded in `reference/catalog.yml`; durable analysis lives in `reference/notes/uniracers-spc-archaeology.md` and `analysis/generated/uniracers-spc-summary.json`. Later ROM-side work identified the two unused songs as retail records $3B and $3D and closed ordinary direct-call reachability. No further acquisition is needed unless a distinct historical dump or driver source appears.

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

Priority: P1 when specifically attributable to Uniracers; P3 for generic DMA imagery  
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

Priority: P2  
Status: holdings known generally; Uniracers-specific material unconfirmed  
Source: https://www.retrovideogamer.co.uk/rvg-interviews-steve-hammond/

Hammond says he retained old DMA graphics, photos, design/proposal documents, and complete source/assets for at least one unfinished project. Search published Hammond material and mirrors for Uniracers-era documents and scans. No outreach is assumed or required.

## A-008 — Modern SNasm reference build

Priority: medium  
Status: uploaded and organized at `reference/tools/snasm/modern/SNasm.zip`; inspection may still be useful  
Source: https://mdf200.itch.io/snasm  
File advertised: SNasm.zip, approximately 62 kB.

Purpose: compare syntax, macro behavior and assembler conventions with any reconstructed 65816 source. Treat only as a descendant/reference unless historical continuity is demonstrated.

The download is behind itch.io's "No thanks, just take me to the downloads" handoff, which the current non-interactive fetch path does not expose as a stable direct file URL.


## A-009 — Historical SNasm 1.7.x builds

Priority: P3 for 1.7.2; 1.7.1 already satisfies the historical-lineage need  
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

Priority: P3 unless inspection reveals material omitted from the Nintendo Life republication  
Status: physical copy catalogued by Video Game History Foundation; no digital scan located

Catalog:
- https://library.gamehistory.org/subjects/14?filter_fields%5B%5D=primary_type&filter_values%5B%5D=archival_object&page=96
- identifier: MAG-GAMESTM.064

A contemporary November 2007 NeoGAF thread describes the issue's retro section as containing an interview with the Unirally SNES makers:
- https://www.neogaf.com/threads/gamestm-issue-64-review-scores-ac-ouch.210737/

Nintendo Life explicitly states that the feature originally appeared **in its entirety** in gamesTM and is reproduced there with permission. Treat the physical magazine as P3 layout/image archaeology only: it could still preserve print-only layout, captions or image treatment, but there is no reason to chase it for missing interview wording.


## A-011 — Unirally Europe retail ROM

Priority: high  
Status: acquired, verified, organized  
Repository path: `reference/roms/retail/Unirally_Europe.sfc`  
Original uploaded filename: `Unirally (Europe).sfc`  
Exact size: 2,097,152 bytes  
CRC32: `d8583ed7`  
SHA-1: `d39ec113ef153ec9b7bacf12ed4a47f1a6d63a06`  
SHA-256: `a1105819d48c04d680c8292bbfa9abbce05224f1bc231afd66af43b7e0a1fd4e`  
Acquired: 2026-09-28

Intake result: the supplied bytes match the catalogued European retail identity. Internal title is `UNIRALLY`, region byte is PAL (`0x02`), version is 0, and reset vector is `$8858`. It contains 45 plausible RNC Method 1 streams. Use as the final-PAL side of prototype-vs-retail and NTSC-vs-PAL differential analysis.

## A-012 — Historical GoodSNES “Uniracers (Beta)” image

Priority: critical for differential archaeology  
Status: acquired, verified against historical catalog identity; build provenance unresolved  
Repository path: `reference/roms/prototypes/Uniracers_Beta_legacy.sfc`  
Original uploaded filename: `Uniracers (Beta).smc`  
Exact size: 2,097,152 bytes  
CRC32: `7ca23359`  
MD5: `577f330153f90906efa13e7810412642`  
SHA-1: `c19a9239f56b0ccaaf0673d1fa9999c7727829d6`  
SHA-256: `450719206b1928287ac3bddbcacbba1907e38c0a1541825899d61df1a328c22d`  
Acquired: 2026-09-28

Observation: the bytes exactly match the historical GoodSNES-listed beta fingerprint. The image is 2 MiB, has internal title `UNIRACERS`, USA/NTSC region byte `0x01`, version 0, reset vector `$8858`, header checksum/complement `0x039B/0xFC64`, and 45 plausible RNC Method 1 streams. The matching header fields with USA retail are observations only and do not establish whether this is a genuine prerelease, a modified retail image, or another historical dump category.

Next action: perform byte/run/RNC comparison against USA retail and seek distinguishing build/provenance evidence only if the binary differences make that materially useful.


## A-013 — Dessyreqt autonomous-player and research corpus

Priority: critical for deterministic bring-up, behavior archaeology and validation  
Status: expanded direct recovery acquired and committed  
Initial public recovery: 2026-09-28  
Direct historical workspace recovery: 2026-09-30

The earlier public recovery remains preserved:
- `reference/imported/tas-bots/uniracers-tabletop-bot-2014.lua`
- `reference/imported/tas-bots/dessyreqt-4250-submission.smv`

Dessyreqt subsequently supplied his historical Uniracers working directory directly. The ZIP was used only as transport and removed after extraction. The 80 preserved files now live under:

`reference/imported/reverse-engineering/dessyreqt/`

Recovered contents:
- 17 Lua scripts, including `usjo14.lua`, `usjo14a.lua`, its backup/test variants, `movebot.lua`, `teststuntbot.lua`, `tabletopbot.lua`, mapping/grading/glitch helpers and related experiments;
- 9 historical glitch/test SMVs, including both Jumpover halfpipe directions and several other track-traversal/glitch cases;
- 45 course-map PNGs covering all nine tours;
- 3 SRAM images (clean and two progression states);
- 2 memory-watch files;
- 4 research documents/spreadsheets.

Immediate acquisition consequences:
- the USJO lineage is now recovered beyond the formerly missing v13 target, through v14/v14a development material;
- a distinct autonomous movement/control lineage is preserved in addition to the already-known tabletop/full-game bot;
- the previously missing Jumpover/FallThrough-style historical movie evidence is now locally available;
- further Dessyreqt acquisition should target only material outside this supplied directory.

Every extracted file is classified in `reference/imported/MANIFEST.json`. Treat labels, scripts and maps as historical working evidence until independently reconciled with the supported ROM/runtime.

## A-014 — Halamantariel 2008 Uniracers TAS WIP SMV

Priority: high  
Status: acquired and committed  
Retrieved: 2026-09-28

Historical info URL:
`http://dehacked.2y.net/microstorage.php/info/1674584940/Uniracers%20%28U%29%20%5B%21%5D.smv`

Recovered from the still-live Microstorage direct-download form:
`http://dehacked.2y.net/microstorage.php/get/1674584940/Uniracers%20%28U%29%20%5B%21%5D.smv`

Repository path:
`reference/imported/tas-bots/uniracers-2008-wip-microstorage.smv`

Exact size: 10,542 bytes  
SHA-256: `61cafb40a32d13bc691e93034449f31c6537736aa6caa0e7d933450e2df269a0`

Historical discussion identifies this as an optimized WIP containing the 23.56 Dragster work and additional progress. It is valuable as an independent deterministic input corpus and a bridge to the earlier USJO/TAS workflow.

Rights: explicit redistribution license not identified; retained as third-party evidence in this private research repository.

## A-015 — USJO source lineage (v8 plus v14/v14a recovered)

Priority: P2 for historical gap-filling only; multiple surviving versions are now active local evidence  
Status: **internal v8 plus Dessyreqt's v14/v14a development family recovered and committed; exact v13 bytes remain missing but are no longer technically important**  
Recovered source: `reference/imported/tas-bots/usjo8.lua`  
Internal date: 2008-02-10  
Recovered: 2026-09-30 directly from Olivier Bellemare (Halamantariel), who retained the historical file  
Exact size: 62,406 bytes  
SHA-256: `64b1a26966490a619a6557adee79d6ee0463e534fa2488cf3b5913d55a316ffc`  
Git blob SHA-1: `d78962aae7ca6a63bf94113f68680e730dade3fb`  
Historical v13 URL: `http://www.obellemare.com/speedruns/Uniracers%20%28U%29%20%5B%21%5D/usjo13.lua`

Need judgment: **the high-value knowledge is now directly usable; v13 is no longer a blocker.** Version 8 already contains savestate-driven search over jump/stunt timing, direct RAM reads for speed/vertical speed/air state/stunt counters/rotation/boost, heuristic stunt-combination search, a boost-plus-speed objective, and replay of the best result. This turns USJO from a speculative acquisition lead into an active reverse-engineering input.

Version 13 is now mainly a historical lineage gap. Dessyreqt's directly recovered workspace supplies v14/v14a plus backup/test variants and therefore supersedes v13 as the highest surviving later-version evidence. Keep passive recovery cheap, but spend no bespoke effort on v13 unless a copy surfaces naturally.

Authorship note: Olivier explicitly reported that he does not remember who the main developer was and that it was not him. Preserve that uncertainty rather than assigning authorship from the surviving hosting/history.

Acquisition boundary for further versions: **passive recovery only.** Public archives, mirrors, preserved attachments, old directory backups, code indexes, repository history and already-public collections are fine; no new project outreach is required.

Working dossier: `reference/notes/usjo13-passive-recovery.md`.

## A-016 — Halamantariel boost/mechanics table

Priority: P2  
Status: exact historical URL known; page bytes not recovered  
Historical URL: `http://www.obellemare.com/speedruns/Uniracers%20%28U%29%20%5B%21%5D/Uniracers.html`

Need judgment: **useful, but no longer important enough to chase expensively.** Surviving TASVideos posts already preserve several core claims from the page plus RAM addresses, including peak speed, airborne-speed behavior, boost timing and stunt-order observations. Local deterministic physics work can verify the remainder. Keep automated/archive probes alive, but do not block or build bespoke recovery tooling around this page.

## A-017 — Sinister Translations Spanish v1.00 / 100% patch

Priority: P1  
Status: metadata confirmed; original patch archive not located

Need judgment: **genuinely useful corroboration, not a dependency.** The recovered Sayans patch already exposed text/control regions and reader semantics. An independently authored Sinister patch could quickly confirm those structures and highlight alternative pointer/font/layout discoveries. Search cheaply and periodically; do not pause localization archaeology waiting for it.

## A-018 — Jumpover FallThrough glitch savestates / related historical files

Priority: P1 for actual savestates or SMV; P3 for page text alone  
Status: historical page and contemporary description known; binaries not recovered  
Historical URL: `http://dscarroll.com/uniracerstas/FallThrough.ashx`

Need judgment: **actual state/movie files would be useful.** They would give a deterministic seed for an unusual collision/track-boundary case and could save substantial reproduction time. The prose page itself adds little beyond surviving TASVideos discussion.

## A-019 — USA instruction manual scan

Priority: P2, acquisition complete  
Status: acquired and committed 2026-09-29  
Repository path: `reference/imported/manuals/Uniracers-USA-manual.pdf`  
Exact size: 6,006,270 bytes  
SHA-256: `50d5d02a3f8f04b9a38a1dac7ff05fd96f5583fbdf1d0afc201bbaea454e2235`

Need judgment: **nice to preserve, but not needed.** It is canonical player-facing terminology and mechanics documentation, but current runtime evidence covers the implementation-critical questions. Acquisition is now closed.

## A-020 — Halamantariel VGMaps course-map corpus

Priority: P2  
Status: 44-map public corpus indexed; binary mirroring intentionally deferred unless cheap and size-appropriate

Need judgment: **potentially useful geometric ground truth, but not necessary.** ROM extraction and deterministic rendering are stronger authorities. The maps can accelerate visual checks, especially while course decoding is incomplete, but importing a very large raster corpus merely for completeness is not justified. Preserve a durable inventory/URLs first; fetch individual maps when a concrete comparison needs them.

## A-021 — Uniracers Uncensored IPS patch

Priority: P3  
Status: current Romhack Plaza record survives but reports no downloadable files

Need judgment: **superfluous to the critical path.** It would cheaply reveal the forbidden-name table, but that behavior is archaeological tail and can be recovered locally if it ever matters. Keep the lead; no bespoke archive hunt unless a surviving patch URL appears incidentally.

## A-022 — Tamoketh UE4 recreation artifacts

Priority: P2 for source/measurements; P3 for ordinary screenshots/video  
Status: author/project breadcrumbs known; source availability unconfirmed

Need judgment: **only technical artifacts are likely to help.** Source, Blueprints, measurements or explicit movement/track data could provide independent hypotheses. A visual fan recreation is not an oracle and should not compete with the canonical ROM for attention.

## A-023 — Further historical SMV/WIP files

Priority: P1 only when materially distinct from recovered corpora  
Status: some important movies recovered; additional historical links may exist

Need judgment: **selectively useful.** A movie is valuable when it reaches a scene, glitch, stunt sequence or progression state absent from current deterministic fixtures. Duplicative race footage is archival tail. Acquire cheaply, classify by unique behavioral coverage, and avoid hoarding redundant movies.




## A-024 — Nitrodon reverse-engineering workspace

Priority: P0 evidence intake and first mining pass complete  
Status: acquired, extracted, committed and reconciled 2026-09-30  
Source: supplied directly by Nitrodon to Ian Wallace via Discord after referral from Dessyreqt  
Repository directory: `reference/imported/reverse-engineering/nitrodon/`

Nine original files are preserved individually; the ZIP transport container is intentionally not retained:

- `RAM addresses.txt` — detailed WRAM map, including per-player/current-player state, stunt counters, boost, camera, timing, checkpoints, messages and track data.
- `ROM addresses.txt` — course/map ROM offsets.
- `bank 80.txt` through `bank 83.txt` — large annotated 65816 bank disassemblies.
- `bounce tracelog.txt` — historical execution trace around bounce/collision behavior.
- `messages.txt` — internal message-ID mapping.
- `stunts.txt` — focused annotated stunt-processing disassembly.

Immediate value: this archive materially strengthens and clarifies the recovered USJO evidence. It identifies `7E:11CD` as a two-byte current-player boost meter with player-specific slots at `7E:11CF/11D1`; identifies `7E:0FEF` as the current-player selector; describes `7E:0F9F` as current-player X velocity; refines `7E:042F` to tabletop duration and `7E:0F61` to half-twist count; and records 16-bit roll/flip counters at `7E:11F9/11FD`. Treat these as unusually strong historical working labels, but retain local runtime reproduction as the promotion gate.

Acquisition is complete for this supplied bundle. The first mining/reconciliation pass is preserved at `reference/notes/nitrodon-reverse-engineering-mining.md` with machine-readable conclusions in `analysis/generated/nitrodon-reconciliation.json`; resulting symbol corrections and routine landmarks are integrated into the canonical symbol exports. Further outreach should ask Nitrodon only about distinct material not present here, especially Lua/USJO versions, savestates, SRAMs, SMVs or additional notes.

### 2026-09-29 automated archive probe

The one-shot harvest probed the exact known URLs before retirement:

- `usjo13.lua`: no Wayback CDX snapshot for the exact historical URL.
- Halamantariel boost/mechanics page: no Wayback CDX snapshot for the exact historical URL.
- FallThrough page: Wayback route timed out during this pass; remain open and try alternate archive/index routes opportunistically.
- VGMaps course corpus: direct automated inventory request returned HTTP 403; do not build bypass machinery for a P2 corpus.
- USA manual: recovered successfully and promoted to A-019.

These are route-specific negative results, not claims that the artifacts no longer exist elsewhere. Continue lateral searches, mirrors, filename searches and author/archive pivots according to the P0-P3 effort tiers above.
