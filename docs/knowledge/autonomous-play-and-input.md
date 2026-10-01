# Autonomous play and deterministic input

## Recovered full-game bot

The repository preserves Dessyreqt's 2014 public Lua source:

`reference/imported/tas-bots/uniracers-tabletop-bot-2014.lua`

Associated TASVideos submission #4250 states that the bot can complete Uniracers without savestate search and can be adjusted for human-vs-bot play.

This is distinct from the still-missing 2008 `usjo13.lua` stunt-search optimizer.

## Why the 2014 bot matters

It is simultaneously:

- a working state-feedback controller;
- a frontend navigation model;
- a labeled RAM map;
- a collection of track-specific control heuristics;
- a source of internal track IDs;
- a regression-workload candidate.

That makes it more valuable to the port than a conventional prerecorded TAS alone.

## Preserved deterministic movies

The repository also contains:

- the 2014 TASVideos #4250 submitted SMV;
- Halamantariel's recovered 2008 Microstorage TAS WIP.

These should be treated as independent historical input corpora.

## Recommended architecture

Do not wire Snes9x Lua APIs directly into the native port.

Instead separate the old bot into:

```
state adapter
    reads semantic state

policy
    maps semantic state -> desired controller state

input adapter
    writes controller state to native port or snesref
```

Where possible, log the emitted controller masks and state checkpoints.

That yields:

- policy-driven autonomous tests;
- frozen replay tests;
- the ability to run one controller policy against both native and reference runtimes;
- easier diagnosis when the same input produces divergent state.

## First practical use

The frontend portion should be adapted before the race AI.

A successful first milestone is:

1. boot both native and `snesref`;
2. read enough frontend state to identify menus;
3. drive both to the same one-player event;
4. begin the race;
5. compare state checkpoints;
6. freeze the resulting controller stream as a reusable regression fixture.

After that, the race-driving policy can become an autonomous soak workload.

## USJO remains useful

The original 2008 `Uniracers Stunts & Jump Optimizer v13` remains worth recovering because it appears to use savestate search to optimize stunt combinations and speed.

Its value is now specialized: evaluator/search logic, stunt grammar, timing assumptions and additional RAM knowledge. It is no longer a prerequisite for obtaining an autonomous player.


## Native harness status

The pinned SNESRecomp desktop host already provides a frame-synchronous `--script` grammar with controller presses, WRAM `until` conditions and state dumps. That is the cheapest current bridge for frontend bring-up; no SDL keystroke injector is needed.

The first project-owned route is `tests/input/reach-first-race.script`. On the canonical USA ROM it has reproduced four historical labels from Dessyreqt's bot under native execution:

- `7E:009F = 0xD7` for `mainMenu`;
- `7E:009F = 0x3C` for `onePlayerSelect`;
- `7E:009F = 0x6D` for `onePlayerTours1`;
- `7E:009F = 0xF6` for `onePlayerTracks`.

The settled captures also reproduce `7E:009B = 0x00` on the clean path, matching the bot's default one-player / first-tour selections.

A useful native-specific timing fact is now established: the menu-state byte can change before the scene accepts its first confirm edge. A one-frame A pulse sent immediately on first observing `0xD7` was ignored, while the same pulse after 60 guest frames moved the game to `0x3C`. Dessyreqt's original policy naturally tolerated this because it reevaluated state and retried inputs every frame.

Therefore:
- short deterministic routes can use guest-state `until` conditions plus a conservative scene-settle before confirmation;
- do not interpret first visibility of a menu-state byte as proof that the menu is already input-ready;
- if repeated conditional retries or branching become cumbersome, use SNESRecomp's opt-in Lua/TCP bridge instead of growing a large timing script. It exposes WRAM reads and per-frame joypad writes and is the natural adapter for porting the original policy nearly directly.

Once a complete route to race entry is stable, run the exact same script through `snesref` before freezing it as a long-term regression fixture.

## Dual-controller deterministic input

Two-player automation now has a project-owned neutral controller stream rather than an emulator-specific convention.

The canonical row format is:

```text
start:duration:p1-mask[:p2-mask]
```

The existing three-field files remain valid and mean "P1 only; P2 idle." The optional fourth field is an independent 12-bit P2 mask using the same button layout. Per-player intervals may not overlap, while P1 and P2 intervals may overlap freely. This preserves every historical one-player corpus while allowing deterministic simultaneous input.

Project adapters are:

- `tools/controller_input.py`: parser and frame-state authority;
- `tools/replay_input_via_lua.py`: writes both controller 1 and controller 2 through the native SNESRecomp Lua bridge;
- `tools/replay_input_mesen.py`: writes libretro-style ports 0 and 1 through the Mesen bridge;
- `tools/patches/snesrecomp-dual-controller-input.patch`: minimal pinned `snesref` patch adding P2 to `SNESREF_INPUT_FILE` while preserving three-field compatibility;
- `.github/workflows/dual-player-input.yml`: ROM-free adapter tests plus a build check proving the pinned `snesref` patch still applies and compiles.

Do not fork a second fixture grammar for multiplayer. Scene-keyed `.script` files remain useful for state waits, dumps and P1 menu-driving; the neutral frame-mask stream is the controller transport when independent P2 input is required. A later upstream SNESRecomp grammar extension may collapse these layers, but the project format should remain stable.

The recovered 2014 bot is already a strong seed for the next stage: it contains distinct RAM tables for both racers and explicit two-player/VS frontend states. The intended progression is therefore:

1. verify a controller-2-only causal probe while P1 is idle;
2. capture a deterministic 2P frontend route and race entry;
3. compare both racer-state slots across native, `snesref` and Mesen;
4. freeze asymmetric and simultaneous interaction fixtures;
5. adapt the recovered policy so either player can be autonomous;
6. run bot-vs-bot and human-vs-bot soak workloads without changing simulation code.

Priority 2P regression cases are asymmetric acceleration, mirrored rotation, simultaneous jump/landing, collision/contact, split-screen camera/OAM behavior, menu ownership/handoff, finish ordering and pause/results flow.


## Verified shared race-entry fixture

`tests/input/reach-first-race.script` is now a shared native/reference regression fixture rather than a bring-up sketch.

The same file runs successfully in:
- the generated native SNESRecomp executable (run 36506120930);
- `snesref` with pinned Snes9x libretro revision `1bcc369e89f08243e0a462882fb1f3e42e51de3a` (run 36506281320).

Both reproduce the clean sequence:
`mainMenu 0xD7 → onePlayerSelect 0x3C → onePlayerTours1 0x6D → onePlayerTracks 0xF6 → onePlayerNowPlaying 0x16 → inRace 0x01`.

The native run reaches `inRace = 1` at frame 984; the reference run reaches it at frame 975. That timing difference is now a measurement target, not a reason to maintain separate input fixtures.

The next adapter step is full checkpoint comparison: compare complete WRAM dumps, not only selected known fields. Once the first-race state agrees closely enough to trust, extend the fixture with movement inputs and begin validating the recovered race-driving RAM labels/policy.


## Duplicate-key caution in recovered bot RAM table

Dessyreqt's preserved Lua source declares several player-1 byte-table keys twice. Standard Lua table-constructor semantics keep the **later** value for duplicate keys. Therefore the values actually read by the bot are:

- `airValue = 7E:0545`, not the earlier `7E:0547`;
- `pitch = 7E:0F49`, not the earlier `7E:04C9`;
- `showingArrows = 7E:0FCC`, not the earlier `7E:0FCE`;
- `arrowDirection = 7E:0FCB`, not the earlier `7E:0FCD`;
- `tabletops = 7E:042F`, not the earlier `7E:0431`.

The earlier addresses are still useful archaeological leads and line up suggestively with the player-2 table, but they must not be described as the player-1 values used by the running bot without independent validation.


## First-course jump probe alignment

The first clean one-player race selects bot track 0, labelled `Dragster` in the recovered source. Dessyreqt's `jumpAreas[0]` contains one large rectangle:

- X: 1090–25278
- Y: 790–870

The validated `accel-180` checkpoint from run 36512546762 is `xPos=1655`, `yPos=858`, which lies inside that rectangle. Therefore the branch's next `right+b` probe is not an arbitrary human-style jump test: it exercises a location where the recovered autonomous policy itself would return `ShouldJump() = true`.

This is useful for interpreting `ySpeed`, effective `airValue` and `pitch` changes and for later adapting the original race-driving policy into a deterministic regression workload.


## Short B pulse was a negative jump experiment

Run 36513805265 compared the original two-frame `Right+B` intervention with a timing-identical `Right`-only control. The pulse produced no causal change in the recovered player-1 semantic block. The second racer reproduced its airborne arc without B.

This matters operationally: do not use the visually changing `7E:0547` byte as evidence that player 1 jumped. It belongs structurally with the second-racer block and changed independently of the controlled B pulse.

The preserved bot's policy would keep B asserted every frame while table-[1] remains in Dragster's jump area. Subsequent controlled-jump fixtures should therefore use sustained B input and demand a causal change in table-[1] state before promoting air/Y semantics.


## Pitch-address correction from runtime + shipped-code evidence

The preserved bot's effective player-1 table reads `7E:0F49` as `pitch`. New evidence shows why that can work while still being the wrong address to call persistent player-1 pitch storage.

The shipped ROM contains sibling copy sequences:

- player-1-side routine near `02:8D84`: `LDY $0F49; STY $04C7`;
- player-2-side routine near `02:9272`: `LDY $0F49; STY $04C9`.

The surrounding destinations also shift in player-paired fashion (`0BA1→0BA3`, `0BAD→0BAF`, `0BB1→0BB3`). Dynamic L input changes `04C7` causally while `0F49` can be identical to control at sampled checkpoints.

Operational rule for future bot adaptation:

- use `04C7` as persistent player-1 pitch/rotation state;
- use `04C9` as the paired player-2 slot;
- treat `0F49` as current-player working/scratch pitch unless a specific routine/frame context says otherwise.

Do not rewrite the historical source; preserve it as evidence of what the 2014 bot actually sampled.


## Confirmed pitch-angle encoding

Mirrored airborne rotation establishes the persistent player-1 slot at `7E:04C7` as a circular 6-bit-style pitch/orientation angle. From a control value of 7, eight L frames produce 55 (`7−16 mod 64`) and eight R frames produce 23 (`7+16`). Native and Snes9x agree exactly.

This makes the 2014 bot's threshold policy around 14, 24, 32, 40 and 50 structurally sensible: those are sectors of a 0–63 orientation circle. For autonomous-player work, read persistent player 1 from `04C7`; use `0F49` only as the historical/current-player scratch value when reproducing the old bot literally.


## Historical SMV extraction path

The preserved 2014 submission movie is now directly consumable as controller evidence rather than only as an opaque emulator artifact.

- `tools/extract_smv_input.py` parses standard-controller SMV versions 1/4/5, records reset/movie metadata, translates Snes9x button bits into the neutral 12-bit `snesref` mask layout, and run-length encodes exact nonzero controller intervals as `start-frame:duration:hex-mask`.
- `.github/workflows/historical-smv-first-race.yml` replays that extracted stream through pinned Snes9x/snesref from the canonical ROM at bounded frame cutoffs and records menu/race/player state from WRAM.

This gives the project two complementary autonomous inputs: the recovered Lua policy explains why inputs are chosen, while the SMV records what the historical run actually pressed. Prefer the SMV when an exact known-working controller sequence can answer the question; prefer the policy when state feedback or adaptation is required.


## 2008 WIP Dragster input structure

The recovered Halamantariel Microstorage WIP is a raw SMV v1 movie, reset-anchored, with one recorded controller and 4,974 header frames (4,975 controller samples including frame 0). Its controller data begins at file offset 592. The translated stream is frozen at `tests/input/historical-2008-wip.input`; CI re-extracts the SMV and requires semantic interval identity before replay. Direct inspection of all 4,975 controller samples finds no explicit `0xFFFF` reset samples, so no mid-movie reset event needs to be reproduced for this corpus. Because SMV v1 reset movies also embed their starting SRAM, the extractor now recovers that snapshot and emits the canonical cartridge-sized 8 KiB prefix. The historical replay preloads the same SRAM bytes into both pinned Snes9x and the native host before frame 0.

Direct parsing exposes a conspicuous first long race-like control block beginning around movie frame 1184. After a 31-frame `Y+Right` interval, the input settles into a repeating approximately 40-frame stunt/drive cycle dominated by:

- `B+Right+R` airborne drive;
- one-frame `X` additions at regular positions;
- `Right+R` release intervals;
- short `B+Left+R` corrections.

Near frame 2296 the pattern collapses into 359 frames of plain Right input, ending around frame 2655, followed by a long quiet/menu-like interval. A second complex race-like block begins around frame 3472.

These are **controller-stream observations only** until `.github/workflows/historical-wip-dragster.yml` confirms the corresponding WRAM race/results states under pinned Snes9x. Do not yet name 1184 or 2655 as exact game-state boundaries.


### SMV frame-zero and legacy timing semantics

The historical 2008 WIP's controller indexing is now source-checked rather than inferred from the file format alone. Snes9x movie playback reads controller sample 0 as **baseline controller data before playback starts**, then initializes `CurrentFrame=0` / `CurrentSample=0`; subsequent movie updates consume later samples. This matches the project's neutral replay model in which sample 0 supplies the controller state for the first emulated frame. The extra `frames + 1` sample is therefore intentional and not evidence of a one-frame shift.

This specific SMV has authoritative legacy sync flags (`sync_data_exists=1`) and sets only the old `WIP1TIMING` compatibility bit in addition to `HASROMINFO`; initial FastROM, Left+Right, volume-envelope, fake-mute and sync-sound flags are clear. Snes9x's SMV documentation states that WIP1 timing ceased to have meaning with SMV version 4 / Snes9x 1.51. Therefore a modern-core raw-input replay should keep controller timing unchanged, but a desync must be checked against the old 1.43 WIP1 timing behavior before blaming the movie or game logic.


### 2014 movie as independent timing oracle

Dessyreqt's submission #4250 is a useful independent replay corpus because TASVideos records it as Snes9x 1.51 v17, substantially later than the 2008 WIP's SMV-v1/WIP1-timing environment. The submission states it starts from blank SRAM and was sync-verified with its embedded movie settings. The repository's 2014 workflow now extracts the wrapped SMV, requires a reset/SRAM anchor, replays the first 5,000 frames through pinned Snes9x in one trace pass, detects exact race/results transitions, and persists `analysis/generated/historical-2014-first-race-reference.json`.

Use this corpus as a timing-independent cross-check on the 2008 WIP. If both historical streams reach the expected first Dragster race under the pinned modern core, confidence in the extracted-input route rises sharply. If only the 2014 movie works, investigate the 2008 WIP's legacy `WIP1TIMING` mode before modifying controller alignment or game logic.
