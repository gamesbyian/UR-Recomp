# Original-Development Source Index

Last updated: 2026-09-28

This is the citation spine for original-development archaeology. Prefer primary developer sources and period artifacts. Secondary sources are explicitly marked.

| ID | Source | Type | Main technical value | Local status |
|---|---|---|---|---|
| OD-001 | https://dailly.blogspot.com/2008/10/uniracerscredits.html | Mike Dailly, first-hand | Team roles; Dailly credits himself with level editor, unicycle compression, SNES framework/tools | Linked |
| OD-002 | https://dailly.blogspot.com/2008/10/past-tools.html | Mike Dailly, first-hand | Says old 65816 SNES framework source still existed in 2008 | Linked; source code not yet found |
| OD-003 | https://lemmings.info/things-ive-done/ | Mike Dailly, first-hand inventory | SNasm, SNES graphics/MIDI converters, Uniracers compression/editor, A0 plotter, Amiga/SNES link | Linked |
| OD-004 | https://lemmings.info/museum-donations/ | Mike Dailly, first-hand | SN Systems 65816 devkit used for Unirally; Magicom; EPROM workflow; Amiga-Magicom parallel link | Linked |
| OD-005 | https://www.nintendolife.com/news/2010/03/feature_the_making_of_unirally | Developer retrospective | Innes/Graham/Anderson recollections: copy protection, graphics/animation, design/physics tuning, capacity | Linked |
| OD-006 | https://ximwix.net/mirrors/rhdn-old/index.php%40topic%3D6940.15.html | Reported developer correspondence + RE | RNC claim; 256-tile-width claim; later 64x64/8x8 structural observations | Linked; normalized in `references/notes/course-layout-history.md`; local 1024-area header invariant now gives a direct test |
| OD-007 | https://hiddenpalace.org/Uniracers_%28Nov_29%2C_1994_prototype%29 | Preservation record | 1994-11-29 PAL prototype provenance and development-board details | Acquired; ROM preserved under `reference/roms/prototypes/` and structurally analyzed |
| OD-008 | https://hiddenpalace.org/Assets/DMA_Design_Miscellaneous_Press_Material | Preservation record | DMA press archive explicitly includes Uniracers/Unirally | Archive inspected; useful Uniracers PDF preserved under `references/imported/press/dma-design/` |
| OD-009 | https://archive.org/details/dma_press_material | Preservation artifact | 638.6 MB source archive behind OD-008 | Archive inspected; no further useful project material identified in current pass |
| OD-010 | https://www.snesmusic.org/v2/profile.php?profile=set&selected=3149 | Preservation | SPC set; ten tracks including two marked unused | Linked |
| OD-011 | https://www.mobygames.com/game/8085/uniracers/credits/snes/ | Credit transcription | Cross-check of retail credits | Linked |
| OD-012 | https://www.vgmpf.com/Wiki/index.php?title=Colin_Anderson | Secondary preservation research | Leads on music-entry method / driver family | Linked; binary verification required |
| OD-013 | https://forums.nesdev.org/viewtopic.php?t=24932 | Independent technical discussion | Leads for unusual OAM behavior | Linked; trace locally |

## Citation policy

When a claim is promoted into RESEARCH-LEDGER.md, cite the source ID and exact URL. Where practical, attach a local ROM address, hash, trace, script output, or reproducible command. Historical recollection is evidence about development practice; it is not a substitute for verifying the shipping binary.

## Preservation policy

Do not silently copy entire third-party sites or interviews into the repository. Preserve the URL/title, author or speaker, date when known, concise paraphrase, short quotation only when wording matters, retrieval date, hashes for downloaded artifacts, and license/redistribution notes when known.

If a source disappears, use an archived copy and record both original and archive URLs.

| OD-014 | https://dailly.blogspot.com/2007/09/?m=0 | Mike Dailly, first-hand | Says he was uploading old DMA images/videos and still had a stack of level-building graphics; specifically mentions hunting Uniracers pictures | Archival lead |
| OD-015 | https://www.flickr.com/photos/mikedailly/ | Mike Dailly historical media archive | Old DMA photos, scans and design material; set/image IDs may survive in citations even where UI indexing is weak | Needs systematic archive pass |
| OD-016 | https://www.retrovideogamer.co.uk/rvg-interviews-steve-hammond/ | Steve Hammond, first-hand | Confirms survival of personal DMA graphics/photos/design/proposal-document archive | Archival lead; Uniracers holdings unknown |
| OD-017 | https://mdf200.itch.io/snasm | Mike Dailly, modern tool | Modern SNasm supports 65816; useful descendant/context, not assumed identical to 1993 assembler | Downloadable; optional reference |
| OD-018 | https://github.com/mikedailly/SNES-Disassembler | Mike Dailly public GitHub fork | Later 65816/SNES disassembler used/retained by Dailly; analysis context, not original DMA tool | Public source |

| OD-019 | https://www.lemon64.com/forum/viewtopic.php?sid=36bb321ef89b54d4d24309d3388276a0&start=30&t=27153 | Mike Dailly, first-hand forum post | Explicitly says Uniracers changed SNES state on a scanline basis and required Nintendo R&D verification | Strong technical evidence |
| OD-020 | https://dailly.blogspot.com/2008/09/ | Mike Dailly, first-hand | Names Uniracers split technique as C64-style sprite ripping used for perfect splits | Strong technical evidence |
| OD-021 | https://lemmings.info/creating-a-commodore-64-emulator-in-gamemaker-part-6/ | Mike Dailly, first-hand technical retrospective | Explains sprite ripping mechanism, says Uniracers used it on SNES, black separator lines were aesthetic | Strong technical evidence |
| OD-022 | https://www.lemon64.com/forum/viewtopic.php?p=325237 | Mike Dailly, first-hand | General SNES sprite/VRAM timing comments from an experienced DMA SNES coder | Context |
| OD-023 | https://dmadesign.wordpress.com/ | Steve Hammond, first-hand archive/blog | Points to Dailly's historical DMA site as a detailed technical record; useful dead-site/Wayback lead | Archival lead |

| OD-024 | https://csdb.dk/release/?id=57677 | Preservation record | SNasm 1.7.1, 2007-11-30; preserves original javalemmings download URL and CSDb mirror | Historical binary acquisition attempted |
| OD-025 | https://dailly.blogspot.com/2007/07/snasm-65816-support.html | Mike Dailly, first-hand | Documents 65816 syntax/state directives including LongA/LongI and opt A65816 | Strong assembler-lineage evidence |
| OD-026 | https://dailly.blogspot.com/2007/ | Mike Dailly, first-hand | Says SNasm release has substantial 65816 support and debugger symbol output | Strong assembler-lineage evidence |
| OD-027 | https://dailly.blogspot.com/2008/05/ | Mike Dailly, first-hand | Announces 2008 SNasm release fixing misspelled 65816 opcodes | Strong release evidence |
| OD-028 | https://plus4world.powweb.com/tools/all/Windows/3 | Preservation index | Records SNasm 1.7.2 dated 2008-05-10 | Historical binary lead |

| OD-029 | https://library.gamehistory.org/subjects/14?filter_fields%5B%5D=primary_type&filter_values%5B%5D=archival_object&page=96 | VGHF catalog | Confirms physical holding of gamesTM issue 64 (December 2007), containing the original Unirally maker interview later republished online | Physical-source lead |
| OD-030 | https://www.neogaf.com/threads/gamestm-issue-64-review-scores-ac-ouch.210737/ | Contemporary forum reference | November 2007 thread explicitly notes the issue's retro section contains an interview with the Unirally SNES makers | Corroborates issue identification |
