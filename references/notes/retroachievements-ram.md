# RetroAchievements RAM evidence

Recovered snapshot:
`references/imported/retroachievements/1295.json`

Source mirror:
https://github.com/hoanghdtv/achievements/blob/b5e0e0f1e880dcb367abb08b9ea3b583ab846f10/1295.json

Upstream game:
https://retroachievements.org/game/1295

Retrieved: 2026-09-28

The JSON snapshot contains 24 Uniracers achievement definitions with raw RetroAchievements memory conditions. This is valuable because the addresses were independently exercised by achievement authors and users rather than inferred solely from one reverse-engineering session.

## Strong address clusters

### Persistent/progression SRAM-derived state

The achievement rules repeatedly read:

- `0x02069C` Crawler medal byte for the selected/first Uni
- `0x0206AC` Jumper
- `0x0206BC` Shuffler
- `0x0206CC` Bounder
- `0x0206DC` Walker
- `0x0206EC` Runner
- `0x0206FC` Hopper
- `0x02070C` Sprinter
- `0x02071C` Hunter

This independently matches the offsets reported years earlier by Halamantariel in TASVideos, modulo RetroAchievements' SNES memory-domain addressing convention.

### Stunt counters / flags

A contiguous cluster appears repeatedly:

- `0x02076B`
- `0x02076F`
- `0x020773`
- `0x020777`
- `0x02077B`
- `0x02077F`
- `0x020783`
- `0x020787`
- `0x02078B`
- `0x02078F`
- `0x020793`
- `0x020797`
- `0x02079B`
- `0x02079F`
- `0x0207A3`
- `0x0207A7`
- `0x0207AB`
- `0x0207AF`

Achievement descriptions strongly associate this block with the various single/double/triple/city/mega stunt counters. In particular, rules identify:

- `0x020777` with Roll City state/count
- `0x020787` with Flip City
- `0x020797` with Twist City
- `0x0207A7` with Z-Flip City
- `0x02076B` and `0x02078B` as counters used in a 30-twists/30-rolls Dragster challenge

The exact ordering of every stunt in the 18-entry block should be derived experimentally rather than guessed from the achievement ordering.

### Per-tour race/result cluster

Gold-medal achievements reference compact five-byte groups:

- Crawler: `0x021075–0x021079`
- Jumper: `0x02107A–0x02107E`
- Shuffler: `0x02107F–0x021083`
- Bounder: `0x021084–0x021088`
- Walker: `0x021089–0x02108D`
- Runner: `0x02108E–0x021092`
- Hopper: `0x021093–0x021097`
- Sprinter: `0x021098–0x02109C`
- Hunter: `0x02109D–0x0210A1`

The achievement logic watches transitions in these groups while also checking medal state, making them strong candidates for per-course/race completion status or event state.

### Other useful probes

Achievement logic also references:

- `0x0210AD` as a mode/state discriminator used to suppress stunt achievements in at least one game state.
- `0x020F39`, `0x001265`, `0x0004D5`, `0x0004D6`, and `0x000EF1` in the Dragster stunt-count challenge.
- low addresses `0x000000`, `0x000002`, `0x000005`, `0x000006` in the forbidden-name achievement.

## Why this is unusually useful

The RetroAchievements set independently corroborates Halamantariel's SRAM map and adds a much richer set of volatile RAM probes for stunt and race state. These addresses should become watchpoints in the recomp/emulator tracing workflow.

Do not treat achievement descriptions as definitive variable names. The rules prove that an address participates in the stated observable condition; they do not prove the internal semantic label or representation.
