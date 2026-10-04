# Game state and flow

## Current model

**Supported.** Uniracers is organized around a compact set of frontend, progression, selected-track and in-race state variables that are read by both game logic and later tooling.

The recovered 2014 Dessyreqt autonomous bot is especially valuable because it navigates the game from live state rather than following a fixed frame script. Its behavior implies a frontend state machine with stable RAM-visible states and selections.

Core frontend addresses (see `docs/SYMBOLS.md` for confidence):

- `7E:009F`: current menu/frontend value. **Confirmed** IDs include `0xD7` MAIN_MENU, `0x3C` rider select, `0x6D` / `0x10` tour pages, `0xF6` / `0x91` track select, `0x16` NOW PLAYING, and the result IDs. Two caveats: it doubles as DP scratch during text/course construction, and it goes stale on some Records sub-screens. Treat a value as a state only when it is stable and the screen agrees.
- `7E:009B`: selected option. On TOUR_SELECT it is the tour row; `7E:00D0` holds the confirmed tour row.
- `7E:000E` / `7E:0C63`: selected row / column (rider select: 8 rows × columns `0x06/0x07`).
- `7E:017D` / `7E:017F`: P1 / P2 rider index (the CPU opponent uses P2).
- `7E:0313`: in race (`0x01`). It also reads `0x3C/0x3D` on some result screens, so it is not a pure boolean.

## Runtime flow

**Confirmed** working model:

```
boot -> title (0x84; Up, Left, Up, R, A here = all tours for this power-on) -> MAIN_MENU
  idle 503 frames -> title -> split-screen two-player demo race (~2190 frames) -> title -> MAIN_MENU
1P: rider -> tour -> track -> NOW PLAYING -> race -> result (0x99 / 0xBC / 0x2F->0x18) -> TRACK_SELECT
      5th tour flag: medal +1 -> medal scene (bronze/silver) or per-tour gold scene; Hunter gold -> newspaper pages -> WHODUNNIT (0x5B) -> title
VS: P1 rider -> P2 rider -> tour -> track (0x91) -> NOW PLAYING -> race -> 0xF9
      decided: VS CHAMPIONS (0xD3) -> PICK CHALLENGER (0x3F, loser's pad) -> track choice (0x5A) -> NOW PLAYING
      drawn:   REMATCH (0xB7) -> NOW PLAYING
2P: P1 rider -> P2 rider -> tour -> track (0x91) -> NOW PLAYING -> race (continues until both finish or timeout) -> 0xF9
      -> track choice (0x5A: NEXT/SAME/SELECT TRACK, SELECT TOUR, QUIT) -> NOW PLAYING with win tally
```

The menus share one BG2 strip: MAIN_MENU, rider, tour and track select sit at scroll 0/256/512/768, and each step slides 256 px in 39 frames. Records/results screens reuse the same yellow-title / grey-data grammar (`analysis/generated/menu-visual-language.json`). `0x84` is also used during the post-race fade, so it is a title/fade value rather than a unique screen.

## Why this matters

The project does not need to rediscover frontend timing blindly. Once the state labels are verified, deterministic automation can respond to semantic game state instead of assuming fixed delays.

That gives the native port and `snesref` a common abstraction:

```
observe state -> choose controller mask -> advance frame -> repeat
```

This is more robust than long hard-coded input timelines and is suitable for menu traversal, race launch, repeated regression runs and eventual autonomous soak testing.

## Development consequence

The first deterministic native route should reuse the recovered bot's state machine where practical, but record controller output so the same route can also be replayed as a frozen input corpus.

That gives two useful modes:

1. **policy mode** for resilient autonomous traversal;
2. **replay mode** for exact cross-runtime comparisons.

See `autonomous-play-and-input.md` and `docs/VALIDATION.md`.
