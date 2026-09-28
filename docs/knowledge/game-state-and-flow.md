# Game state and flow

## Current model

**Supported.** Uniracers is organized around a compact set of frontend, progression, selected-track and in-race state variables that are read by both game logic and later tooling.

The recovered 2014 Dessyreqt autonomous bot is especially valuable because it navigates the game from live state rather than following a fixed frame script. Its behavior implies a frontend state machine with stable RAM-visible states and selections.

Important historical working addresses include:

- `7E:009F`: current menu/frontend state;
- `7E:000E`: selected menu row;
- `7E:0C63`: selected menu column;
- `7E:009B`: selected menu/tour option;
- `7E:00CE`: current track ID;
- `7E:0313`: in-race flag;
- progression/tour state around `7E:0A03` through `7E:0A23`.

These labels should be treated as supported historical semantics until locally verified against the canonical USA ROM.

## Runtime flow

A useful working model is:

```
boot
 -> title
 -> main menu
 -> player / name / mode selection
 -> tour / track selection
 -> "now playing" transition
 -> race / circuit / stunt event
 -> event results
 -> progression update
 -> next selection or ending
```

The bot recognizes concrete values for many of these states and already contains a state-driven policy for issuing controller input.

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
