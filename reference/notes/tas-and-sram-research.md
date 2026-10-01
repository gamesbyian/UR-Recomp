# TAS, SRAM, bot and course-map research

Retrieved: 2026-09-28

## TASVideos Uniracers research thread

Primary:
https://tasvideos.org/Forum/Topics/979

Submission documenting USJO:
https://tasvideos.org/3072S

The long-running TASVideos Uniracers thread is a substantial technical source. Halamantariel and other TAS authors used hex editing, savestates, SRAM modification and emulator tooling to investigate the game.

### SRAM tour/progression structure reported by Halamantariel

Historical posts describe the following SRAM offsets for tour medal state:

- `0x069C–0x06AB`: Crawler
- `0x06AC–0x06BB`: Jumper
- `0x06BC–0x06CB`: Shuffler
- `0x06CC–0x06DB`: Bounder
- `0x06DC–0x06EB`: Walker
- `0x06EC–0x06FB`: Runner
- `0x06FC–0x070B`: Hopper
- `0x070C–0x071B`: Sprinter
- `0x071C–0x072B`: Hunter

Each block reportedly contains one byte per selectable unicycle (16 bytes), with medal values:
- `00`: none
- `01`: bronze
- `02`: silver
- `03`: gold

Hunter reportedly begins with silver-like values in clean SRAM.

Tour-unlock state is reported at:
- `0x10D3–0x10E2`, one byte per unicycle
- `00`: first 4 tours
- `01`: first 6
- `02`: first 8
- `03`: all tours

A historical recipe to prepare a broad silver/unlocked state was to set `0x069C–0x071B` and `0x10D3–0x10E2` to `02`. These offsets are now strongly corroborated by Dessyreqt's directly recovered controlled SRAM snapshots: `Clean → All Silvers - No Hunter` changes `0x069C..0x071B` uniformly `00→02` and `0x10D3..0x10E2` uniformly `00→02`; adding Hunter changes only the latter 16 bytes `02→03`. Exact per-record/value semantics still deserve a one-change-at-a-time runtime/save check. See `analysis/generated/dessyreqt-sram-diff.json`.

### Lost SRAM and movie files

Halamantariel historically hosted clean/hacked SRAM and SMV files at:
- `http://halamantariel.homeip.net/speedruns/`
- later references point to `obellemare.com/speedruns/`

The live files have not yet been recovered. Search targets include likely clean/hacked `.srm` files and old Snes9x `.smv` movies.

### Jumpover fall-through savestates

A 2009 TAS discussion references a dedicated page:
`http://dscarroll.com/uniracerstas/FallThrough.ashx`

It reportedly hosted two savestates demonstrating the Jumpover corner/fall-through behavior: one state during the jump and one before it. The exact historical savestates remain unrecovered, but the practical evidence gap is now closed: Dessyreqt directly supplied two Jumpover halfpipe SMVs plus dedicated left/right reproduction scripts, preserved under `reference/imported/reverse-engineering/dessyreqt/Glitches/` and `Scripts/`. The scripts retain the original starting-position sweep method and successful-X notes.

## USJO Lua stunt bot

On 2026-09-30 Olivier Bellemare (Halamantariel) directly recovered **Internal Version 8**, dated 2008-02-10. The exact historical source is preserved at `reference/imported/tas-bots/usjo8.lua` (62,406 bytes; SHA-256 `64b1a26966490a619a6557adee79d6ee0463e534fa2488cf3b5913d55a316ffc`). Olivier reported that he does not remember who the main developer was and specifically recalled that it was not him, so authorship remains unresolved.

Dessyreqt's TASVideos submission #3072 describes the later USJO lineage as originating with Halamantariel and later improved with Nitrodon. According to the submission, USJO automated highly frame-precise stunt/jump behavior and was improved until it could play through Uniracers autonomously.

Version 8 already directly encodes:
- RAM addresses for player state, position, speed and boost;
- exact stunt timing;
- track-state observations;
- emulator scripting assumptions;
- practical deterministic-control knowledge accumulated by TAS authors;
- savestate-driven search and best-result replay;
- a boost-plus-horizontal-speed objective and explicit stunt reward table;
- additional working addresses not present in the short published watch list, including vertical speed and Z-rotation/pre-rotation state.

The same community later discussed real-time AI/bot play by Dessyreqt. His directly recovered workspace now supplies internal v14, v14a, a v14a backup/test sibling, and a separate `movebot → teststuntbot → tabletopbot` autonomous-player lineage. Exact v13 is therefore only an intermediate historical gap; v14/v14a are the more important surviving later evidence.

## Determinism lead

TAS discussion repeatedly treats Uniracers behavior as deterministic enough for deep hex editing and scripted control, and the USJO/bot work is consistent with that. This is a lead rather than a formal proof. A deterministic replay harness would be extremely useful for recomp validation.

## VGMaps course atlas

Current index:
https://vgmaps.de/maps/snes/uniracers

The index exposes 44 course maps credited to Halamantariel, covering the eight main tours. These are unusually valuable external validation references because they represent complete stitched course geometry. Historical VGMaps statistics identify Uniracers maps among the site's extreme dimensions, including:

- Crawler Dragster: 28,128 × 152 pixels
- Crawler Stitcher: 65,469 pixels wide
- Hopper Downer: 36,864 × 16,111 pixels

The actual PNG files should be mirrored when their direct binary endpoints can be resolved. Until then, the index itself is preserved in the source catalogue.

The maps are especially interesting in combination with the 2008–09 ROMhacking.net level-viewer work: a future extractor should be able to render courses and compare them geometrically against Halamantariel's atlas.


## USJO v13 exact historical artifact path

The 2008 Snes9x Lua development thread preserves the original hyperlink for Halamantariel's script:

- Display name: **Uniracers Stunts & Jump Optimizer v13**
- Historical direct URL: `http://www.obellemare.com/speedruns/Uniracers%20%28U%29%20%5B%21%5D/usjo13.lua`
- First linked publicly: 2008-02-14

Version 13 itself remains unavailable, but the exact filename/path are known and internal v8 plus later v14/v14a are now recovered locally. The contemporary v13 description still documents an intermediate point in the lineage, but its exact bytes are no longer needed for technical reconstruction. Halamantariel said it could optimize in seconds what took a person hours.

The same Lua-development discussion is useful context because Halamantariel specifically requested signed memory-read support for Uniracers speed values. This strongly suggests USJO or adjacent tooling consumed signed game-state variables directly from WRAM.

## Native WRAM watch list used for TASing

On 2008-03-12 Halamantariel published the following memory-watch list, including width/signedness:

| WRAM address | Format | Reported meaning |
| --- | --- | --- |
| `7E:04B7` | 2-byte signed | Speed |
| `7E:11CD` | 2-byte unsigned | Booster Meter |
| `7E:0411` | 2-byte unsigned | X Position |
| `7E:0415` | 2-byte unsigned | Y Position |
| `7E:1509` | 1-byte unsigned | Screen X Position |
| `7E:11FD` | 1-byte unsigned | # of Flips |
| `7E:11F9` | 1-byte unsigned | # of Rolls |
| `7E:0F61` | 1-byte unsigned | # of Twists |
| `7E:042B` | 1-byte unsigned | # of Z-Flips |
| `7E:042F` | 1-byte unsigned | # of Tabletops |

These are higher-confidence semantic labels than most cheat-derived addresses because they were explicitly used as memory watches during manual TAS optimization. They should still be reproduced locally.


### 2026 direct recovery recollection

When returning the surviving v8 file on 2026-09-30, Olivier Bellemare also supplied the RAM-watch list he retained from the TAS workflow and recalled that the group was probably using **Snes9x 1.43**. His retained list corroborates all of the addresses above and additionally includes:

| WRAM address | Format | Reported meaning |
| --- | --- | --- |
| `7E:1361` | 1-byte unsigned | Air flag |
| `7E:0545` | 1-byte unsigned | Air flag |
| `7E:123F` | 1-byte unsigned | Unknown |

The v8 source directly consumes `7E:0545` as its air-state input, strongly linking that retained watch entry to the optimizer. It also reads `7E:04BB` as signed vertical speed plus `7E:0DFD`/`7E:0F57` as Z-rotation-related working state, which were not present in the short retained watch list.

Treat the remembered Snes9x 1.43 version as provenance context rather than a proven execution requirement until the script is actually replayed under a period-compatible Lua build.

## Historical boost table

Halamantariel linked a dedicated boost/mechanics page:

`http://www.obellemare.com/speedruns/Uniracers%20%28U%29%20%5B%21%5D/Uniracers.html`

The page itself has not been recovered, but the surrounding 2008 TASVideos discussion preserves enough of its operational conclusions that the missing HTML is no longer a high-priority dependency:

- Halamantariel said the table included head-bounce boost values and made optimal stunt ordering directly inferable.
- He stated that a flip should come first, and that using one of each stunt before repeating a stunt is faster, giving `FRZ` versus `F2R` as an example.
- The same post publishes the WRAM watch list reproduced above.
- Follow-up discussion explicitly says exact per-button frame counts vary with the unicycle's angle, and Halamantariel considered the memory watches plus trial-and-error sufficient for perfect jump optimization.

The 2026-09-29 automated acquisition probe found no Wayback CDX snapshot for the **exact file URL**, despite an archived parent-directory listing that fingerprints `Uniracers.html` at 2.33 KB. Keep looking laterally for mirrors or archived directory payloads, but treat the page as P2: useful corroboration if recovered, not something to block local physics work on.

## Public 2008 TAS WIP

A later 2008 post exposed an exact Microstorage URL for the work-in-progress SMV:

`http://dehacked.2y.net/microstorage.php/info/1674584940/Uniracers%20%28U%29%20%5B%21%5D.smv`

The WIP reportedly included the 23.56 Dragster run and other optimized work. The historical host is currently inaccessible, but the exact microstorage ID, filename and URL are now preserved.


## Internet Archive directory snapshot fingerprint

A Wayback/Internet Archive snapshot of Halamantariel's historical Uniracers directory exposes the following directory inventory even though the payload files themselves are not archived:

| Filename | Listed size | Listed modified time |
|---|---:|---|
| `01 - Dragster in 23.46.avi` | 2.54 Mb | 2008-09-08 11:58:46 |
| `02 - Zoom Zoo 1st lap in 23.97.avi` | 1.70 Mb | 2008-09-08 11:59:14 |
| `Uniracers (U) [!] (Clean).srm` | 8.00 Kb | 2008-09-08 11:59:14 |
| `Uniracers (U) [!] (Hacked).srm` | 8.00 Kb | 2008-09-08 11:59:14 |
| `Uniracers.html` | 2.33 Kb | 2008-09-08 11:59:14 |
| `WRs.txt` | 1.28 Kb | 2008-09-08 11:59:16 |
| `ZZZ - Realtime Play.smv` | 611.75 Kb | 2008-09-08 11:59:26 |
| `usjo13.lua` | 80.12 Kb | 2008-09-08 11:59:16 |

These names and sizes are valuable archival fingerprints. Search exact filenames, URL-encoded filenames, filenames without punctuation, and likely mirrors/backup archives.

### Relationship between the SMV artifacts

TASVideos forum posts clarify that Halamantariel had at least two SMVs available in early 2008: one realtime-play movie and one actual TAS WIP containing the 23.56 Dragster work. The directory entry `ZZZ - Realtime Play.smv` strongly matches the former by name.

The TAS WIP was later posted publicly at Microstorage as:

`Uniracers (U) [!].smv`

with Microstorage ID:

`1674584940`

Historical URL:

`http://dehacked.2y.net/microstorage.php/info/1674584940/Uniracers%20%28U%29%20%5B%21%5D.smv`

This means the directory listing and the Microstorage WIP are complementary search targets, not duplicate names for the same file.

### USJO v13 fingerprint

The same directory snapshot independently pins the original public artifact as:

- filename: `usjo13.lua`
- listed size: 80.12 Kb
- directory modified timestamp: 2008-09-08 11:59:16
- historical direct path:
  `http://www.obellemare.com/speedruns/Uniracers%20%28U%29%20%5B%21%5D/usjo13.lua`

TASVideos independently records the public link on 2008-02-14 under the title **Uniracers Stunts & Jump Optimizer v13**, describing it as a savestate-driven Lua bot that searches stunt combinations, optimizes for speed and replays the best input sequence.

Later TASVideos submission text says USJO was subsequently improved with Nitrodon's help until it could play/beat Uniracers autonomously. Therefore two acquisition targets should be distinguished:

1. the original public `usjo13.lua` v13 artifact;
2. any later private or renamed descendant used by Halamantariel/Nitrodon/Dessyreqt that added full autonomous play.

Do not assume the 80.12 Kb v13 file is itself the later fully autonomous revision until code or provenance proves that.


## 2014 full-game realtime bot source recovered publicly

A much stronger artifact than the older USJO v13 stunt optimizer has been located.

TASVideos submission #4250, **Dessyreqt's SNES Uniracers "100%, Tabletops"**, submitted 2014-04-01, states that the run was crafted entirely by a bot. The submission specifically says the bot:

- does not abuse savestates to complete the game;
- plays through the game to completion on all difficulty modes;
- can, with minor script adjustments, be raced against by a human;
- had public source at Pastebin ID `A0XpKw9v`.

The Pastebin is still live in 2026 under the title **Uniracers Tabletop bot**, by Dessyreqt, dated 2014-04-01. It is a 29.34 KB Lua script.

Public source:
`https://pastebin.com/raw/A0XpKw9v`

TASVideos submission:
`https://tasvideos.org/4250S`

This is likely closely related to the separately documented February 2014 Twitch stream **AI plays Uniracers**, which Dessyreqt described as playing the game start-to-finish in real time and restarting with the next character. Do not assume byte-for-byte identity between the Twitch bot and the April submission script until provenance proves it.

### High-value state map exposed by the bot

The script labels and actively uses:

- `7E:04B7` P1 X speed, signed word;
- `7E:04BB` P1 Y speed;
- `7E:0411` P1 X position;
- `7E:0415` P1 Y position;
- `7E:11BA` countdown timer;
- `7E:0BA1` P1 facing direction;
- `7E:0545/0547` air-state values (the source contains duplicate/variant labels that require local verification);
- `7E:0FCC/0FCE` directional-arrow visibility;
- `7E:0FCB/0FCD` directional-arrow direction;
- `7E:00CE` current track;
- `7E:0313` in-race flag;
- `7E:132B` reverse-controls flag;
- `7E:0F49/04C9` pitch-related values (player/source variant requires verification);
- `7E:042F/0431` tabletop counters;
- `7E:009F` current menu state;
- `7E:000E` selected menu row;
- `7E:0C63` selected menu column;
- `7E:009B` selected menu/tour option;
- tour/progression bytes `7E:0A03` through `7E:0A23`.

The script also gives P2 counterparts for position/speed/facing.

Treat these semantic labels as strong historical working evidence, not yet locally verified symbols.

### Internal track-ID structure

The bot's `jumpAreas` / course logic names current-track IDs across the full 0-44 domain. Race/circuit entries occupy the expected four non-stunt positions in each five-track group. The omitted IDs are exactly:

`2, 7, 12, 17, 22, 27, 32, 37, 42`

Those are every fifth group's third slot, independently matching the nine stunt slots already inferred from the 45 decoded RNC payloads.

This is an important independent bridge between:

- runtime byte `7E:00CE` current track;
- the game's 0-44 internal track indexing;
- the nine stunt positions;
- the RNC stream cadence where ordinals 3, 8, 13, 18, 23, 28, 33, 38 and 43 alone carry decoded byte 2 = decimal 45.

A runtime course-load trace can now test whether RNC stream ordinal is simply `currentTrack + 1`.

### Course-control geometry embedded in the bot

The source contains hundreds of hand-authored rectangular regions keyed by internal track ID:

- `jumpAreas`;
- `brakeAreas`;
- `noStuntAreas`.

These are not authoritative course geometry, but they are valuable semantic landmarks in the game's native X/Y coordinate system and can be cross-checked against decoded course data and VGMaps.

### Frontend automation

The bot already automates menus by reading `7E:009F` and related selection/progression bytes and issuing controller input. It recognizes many concrete menu-state values, including main menu, player selection, tour screens, track screen, now-playing screen, race/circuit/stunt results and ending states.

This may substantially shorten the path to deterministic native menu/race automation: port the bot's state-driven policy to the project's input harness rather than discovering the entire frontend blindly.

### Current recovery action

A temporary GitHub Actions recovery job is fetching the live Pastebin source and TASVideos #4250 submitted SMV into a provenance-marked recovery area, while separately probing Wayback/CDX for the older USJO/obellemare artifacts.

## Direct Nitrodon reverse-engineering archive recovery

On 2026-09-30 Nitrodon directly supplied a historical Uniracers reverse-engineering bundle after Dessyreqt referred the project to him. The nine extracted files are preserved under `reference/imported/reverse-engineering/nitrodon/`; the ZIP transport container is deliberately not retained.

The archive is a substantial independent evidence source rather than a casual note set. It includes a detailed WRAM map, ROM/course offsets, annotated disassemblies for banks 80-83, a focused stunt routine disassembly, internal message IDs and a bounce/collision trace log.

Several labels immediately reconcile ambiguities in the recovered USJO v8 material:

- `7E:11CD` is documented as a 2-byte boost meter for the currently handled player, with `7E:11CF` and `7E:11D1` as player-specific boost meters.
- `7E:0FEF` is documented as the currently handled player selector, using 0 for player 1 and 2 for player 2.
- `7E:0F9F` is documented as current-player X velocity.
- `7E:042F` is documented as tabletop duration rather than a generic tabletop count.
- `7E:0F61` is documented as number of half-twists.
- `7E:11F9` and `7E:11FD` are documented as 2-byte roll and flip counters.
- `stunts.txt` directly annotates the stunt-processing path around bank 82, including roll/flip accumulation, twist/Z-flip/tabletop handling, wipeout/headbounce handling and related score/boost logic.

These labels are high-quality historical reverse-engineering evidence because they are accompanied by disassembly and trace context, but they remain subject to local deterministic validation before being treated as canonical symbols.

### Nitrodon reconciliation of the TAS watch vocabulary

The directly recovered Nitrodon workspace materially sharpens several older TAS labels that were previously preserved only as short watch names:

- `7E:042F` is annotated and used as tabletop **duration/progress**, not a cumulative tabletop count; this agrees with the project's dynamic `0→1→2→3→4→0` transient.
- `7E:0F61` is the current-player count of **half-twists**; the stunt finalizer shifts it right to count complete twists.
- `7E:11F9` and `7E:11FD` are 16-bit roll/flip count slots, though historical Lua reads their low bytes.
- `7E:11CD` is shared current-player boost working state, with stable per-player meters at `7E:11CF/11D1`.
- `7E:0F9F/0FA1` are shared current-player X/Y velocity working slots.

The same stunt routine proves an exact base-5 stunt-combination index: `125*flips + 25*rolls + 5*twists + zflips`, selecting one of 625 response bytes beginning at `02:9DAA`. See `reference/notes/nitrodon-reverse-engineering-mining.md` for the full reconciliation.

### Direct Dessyreqt workspace update

The 2026-09-30 direct recovery changes several older acquisition statements in this note.

- USJO is locally represented by v8, v14 and v14a development variants, so v13 is historical gap-filling only.
- The autonomous-player source lineage is visible as `movebot → teststuntbot → tabletopbot`, alongside the published 2014 bot/movie.
- Nine glitch/test SMVs are local, including Jumpover halfpipe traversal in both directions.
- All 45 course maps are local.
- Three 8 KiB SRAM snapshots provide a controlled progression differential.
- V14a reads boost as a 16-bit word and accounts for delayed boost via the HUD/message queue; its message IDs reconcile directly with Nitrodon's named message table.

The current synthesis is `reference/notes/dessyreqt-workspace-mining.md`. Machine-readable outputs are `analysis/generated/dessyreqt-workspace-index.json`, `analysis/generated/dessyreqt-sram-diff.json`, `analysis/generated/dessyreqt-course-landmarks.json`, and `analysis/generated/dessyreqt-named-boost-messages.json`.
