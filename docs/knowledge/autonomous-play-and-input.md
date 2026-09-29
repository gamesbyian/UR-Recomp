# Autonomous play and deterministic input

## Recovered full-game bot

The repository preserves Dessyreqt's 2014 public Lua source:

`references/imported/tas-bots/uniracers-tabletop-bot-2014.lua`

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
