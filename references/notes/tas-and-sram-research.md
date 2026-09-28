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

A historical recipe to prepare a broad silver/unlocked state was to set `0x069C–0x071B` and `0x10D3–0x10E2` to `02`. These offsets should be verified against the supported ROM/SRAM before being treated as canonical.

### Lost SRAM and movie files

Halamantariel historically hosted clean/hacked SRAM and SMV files at:
- `http://halamantariel.homeip.net/speedruns/`
- later references point to `obellemare.com/speedruns/`

The live files have not yet been recovered. Search targets include likely clean/hacked `.srm` files and old Snes9x `.smv` movies.

### Jumpover fall-through savestates

A 2009 TAS discussion references a dedicated page:
`http://dscarroll.com/uniracerstas/FallThrough.ashx`

It reportedly hosted two savestates demonstrating the Jumpover corner/fall-through behavior: one state during the jump and one before it. The files have not yet been recovered.

## USJO Lua stunt bot

Dessyreqt's TASVideos submission #3072 describes a Lua script called **USJO**, originally from Halamantariel and later improved with Nitrodon. According to the submission, USJO automated highly frame-precise stunt/jump behavior and was improved until it could play through Uniracers autonomously.

This makes USJO one of the highest-value missing artifacts for UR-Recomp because it may encode:
- RAM addresses for player state, position, speed and boost;
- exact stunt timing;
- track-state observations;
- emulator scripting assumptions;
- practical deterministic-control knowledge accumulated by TAS authors.

The same community later discussed real-time AI/bot play by Dessyreqt. No public GitHub copy of USJO was found in the current pass.

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

The live file is currently unavailable from this environment, but the exact filename and path are now known. The contemporary description says v13 starts from a pre-jump emulator state, searches stunt combinations, optimizes for speed, then replays the best input sequence. Halamantariel said it could optimize in seconds what took a person hours.

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

## Historical boost table

Halamantariel linked a dedicated boost/mechanics page:

`http://www.obellemare.com/speedruns/Uniracers%20%28U%29%20%5B%21%5D/Uniracers.html`

The page reportedly contained a boost table including head-bounce values and was used to reason about optimal stunt ordering. The live page has not yet been recovered.

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
