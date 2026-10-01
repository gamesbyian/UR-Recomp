# UI screenshot / screen-flow reference corpus

Last updated: 2026-09-29.

Purpose: bootstrap the player-visible UI state map from public visual evidence without treating third-party screenshots as project-owned assets.

Canonical state model:
- `analysis/ui-state-map.yml`
- `docs/UI-STATE-MAP.md`

## Public galleries located

### MobyGames SNES screenshot gallery

URL: https://www.mobygames.com/game/8085/uniracers/screenshots/

Observed/indexed labels include:
- Intro Screen
- Main Menu
- Select your Unicycle
- Select Your Tour
- gameplay frames

Usefulness:
- strong visual anchors for `MAIN_MENU`, `PLAYER_SELECT_P1`, and `TOUR_SELECT`;
- useful for verifying that locally captured frames are the expected scene;
- not sufficient on its own to establish input behavior.

Rights posture:
- screenshot reuse license not established;
- do not vendor as project art by default;
- preserve URL/provenance and prefer local canonical-ROM captures for durable fixtures.

### GameStar Uniracers SNES gallery

URL: https://www.gamestar.de/galerien/uniracers_snes,48628.html

Observed/indexed labels mirror the useful early-game states:
- Intro Screen
- Main Menu
- Select your Unicycle
- Select Your Tour
- gameplay

Usefulness:
- independent visual corroboration of the same early frontend states.

Rights posture:
- screenshot reuse license not established;
- keep as an external visual reference.

### Demented Ferrets review

URL: https://dementedferrets.com/2021/02/24/uniracers-review-bombastic-fun/

Observed screenshot:
- Hunter tour `PICK TRACK` screen with five track entries, track-type icons, selection arrow, and GOLD status.

Usefulness:
- anchors the generic `TRACK_SELECT` presentation and proves that Hunter uses the same broad selection-screen family.

Rights posture:
- screenshot reuse license not established;
- external reference only.

### Freebie Games gallery

URL: https://freebie.games/games/uniracers/

Observed screenshot:
- Main Menu with 1P, 2P, VS, LEAGUE, OPTIONS and arrow on 1P.

Usefulness:
- redundant visual corroboration; lower evidentiary value than the manual + MobyGames/GameStar pair.

Rights posture:
- external reference only.

## Primary manual

The repo already catalogues:
- USA manual scan: https://www.videogamemanual.com/snes/Uniracers%20(USA).pdf
- transcription: https://www.world-of-nintendo.com/manuals/super_nes/uniracers.shtml

The manual is especially valuable because it explicitly defines:
- menu vs informational-screen terminology;
- D-pad cursor movement;
- A/B forward/choose;
- Y/X previous menu;
- Main Menu choices;
- 1P/2P/VS -> unicycle select -> tour select -> track select -> race flow;
- repeated player selection in 2P/VS;
- League and Options branches;
- Records/Player/League editing screen families;
- three result screen types;
- destructive Main Menu and Define League button chords.

## Local evidence is already better than expected

`tests/input/reach-first-race.script` already traverses the 1P frontend using controller input only and emits `dump` checkpoints at:

- `main-menu-ready`
- `rider-select-ready`
- `tours-ready`
- `tracks-ready`
- `after-track-confirm`
- `now-playing-ready`
- `race-entered`

Pinned SNESRecomp's `dump <tag>` command writes not just WRAM but a framebuffer BMP (`<tag>.fb.bmp`) plus VRAM, CGRAM, OAM, SRAM, register, write-log and metadata artifacts. Therefore the existing native smoke workflow is already capable of producing a canonical-ROM screenshot atlas for the basic 1P spine without new rendering instrumentation.

Current locally reproduced state signatures from that route:

| State | WRAM signature |
|---|---|
| MAIN_MENU | `7E:009F = D7` |
| PLAYER_SELECT_P1 | `7E:009F = 3C` |
| TOUR_SELECT (first 1P page/state) | `7E:009F = 6D` |
| TRACK_SELECT (1P) | `7E:009F = F6` |
| PRE_RACE_CARD / Now Playing | `7E:009F = 16` |
| GAMEPLAY active | `7E:0313 = 01` |

These are stronger anchors than online screenshots because they connect player-visible states to the canonical native runtime.

## Recovered historical-bot labels

Dessyreqt's recovered 2014 Lua bot labels `7E:009F` menu values for additional states:

- demo `00`
- splash `84`
- main menu `D7`
- one-player select `3C`
- two-player select `3D`
- VS select `3E`
- VS challenger `3F`
- VS challenge track `5A`
- one-player tours 1 `6D`
- one-player tours 2 / two-player tours `10`
- one-player tracks `F6`
- two-player track states `91` / `96`
- one-player Now Playing `16`
- race results `99`
- circuit results `BC`
- stunt results `18`
- several intermediate stunt-result summing states
- ending `5B`

Treat values not yet reproduced by local fixtures as historical-source leads. They are excellent navigation targets, not automatic canonical truth.

## Acquisition strategy

Do not spend time scraping dozens of screenshots merely to possess images.

Preferred order:
1. use public screenshots to name/recognize states;
2. use the manual to infer candidate controls and branching;
3. use existing controller-only fixtures to reach states;
4. use SNESRecomp `dump` output to capture canonical local BMPs and machine state;
5. add narrow new fixtures only for uncovered branches.

This keeps the visual atlas legally cleaner, more reproducible, and far more useful to reverse engineering than a folder of anonymous web images.

### Vizzed screenshot / cheat pages

Screenshot page: https://www.vizzed.com/games/uniracers-snes-super-nintendo-8767-user-screenshots

Cheat/reference page: https://www.vizzed.com/games/uniracers-snes-super-nintendo-8767-cheats-codes

Indexed screenshot labels include:
- Menus
- Cut-Scene: Victory!
- character/menu examples

The wider public screenshot set also reproduces the well-known "No Sonic Allowed" forbidden-name screen, which makes the name-rejection path worth representing explicitly in the UI graph even before its local menu ID is known.

The cheat page describes a title-screen ending shortcut using Down+L+R+B. This is a useful low-cost route to the ending state, but it is secondary-source evidence and should be tested against the canonical ROM before promotion.

Rights posture:
- screenshot reuse license not established;
- index only; prefer local canonical-ROM framebuffer captures.

