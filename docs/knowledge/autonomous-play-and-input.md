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
