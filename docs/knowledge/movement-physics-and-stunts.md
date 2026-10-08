# Movement, physics and stunts

## Authoritative principle

The original executable simulation is the product authority. The modern port should not independently recreate acceleration, contact, stunt recognition or boost unless a specific subsystem is intentionally replaced and validated.

## High-value runtime anchors

Historical TAS work supplies strong candidate WRAM semantics:

- `7E:04B7`: signed 16-bit horizontal/X speed;
- `7E:04BB`: P1 Y speed in the recovered 2014 bot;
- `7E:0411`: P1 X position;
- `7E:0415`: P1 Y position;
- `7E:1509`: screen X position;
- `7E:11CD`: shared current-player boost working value; persistent player slots are `7E:11CF` / `7E:11D1`;
- `7E:11FD`: flips;
- `7E:11F9`: rolls;
- `7E:0F61`: twists;
- `7E:042B`: Z-flips;
- `7E:042F`: tabletop duration/progress;
- `7E:132B`: reverse-controls flag in the recovered bot.

Several of these come from independent historical sources and therefore make excellent symbol-validation anchors.

## Current conceptual model

**Supported.** Racing performance couples ordinary movement to successful stunt execution. Stunts are not only score events: landing useful tricks modifies the player's speed/boost state.

The reward application is now statically localized. `Stunt_FinalizeAndScoreAirTricks` queues trick messages through `HUD_QueueMessage`; the later bank-81 queue consumer applies per-message rewards. P1 consumption adds score into `77:07BB` and boost into persistent `7E:11CF`; P2 mirrors this through `77:0825` and `7E:11D1`. `7E:12AF`, previously treated as the stunt score itself, is a display cache refreshed from `77:07BB` when that backing score changes.

The game-facing effect is now measured (R-2026-10-08-PHYS-03, native-identical): on the ground, holding forward, X speed settles at `min(448 + boost/2, 640)` from the previous frame's meter, rising at most +24 per frame; the meter depletes faster as it grows (none at ≤ 32, then up to 4 per frame from 256), and storage itself is unclamped, so the `0x0180` clamp belongs to the reward path.

The 625-byte stunt-combination table at `02:9DAA` is also simpler at runtime than its varied byte contents suggest. The sole bank-82 consumer tests only for `FE`: `FE` suppresses the paired praise messages, while every non-`FE` byte, including `FF`, takes the same allowed path. The praise IDs are computed afterward from other state rather than from the table byte.

The recovered autonomous player does not solve physics from first principles. Instead it uses live player state plus hand-authored course regions such as:

- jump areas;
- brake areas;
- no-stunt areas.

That tells us something useful about the game architecture: high-level driving can be expressed as policy over native X/Y position and a relatively small set of movement/stunt state variables.

## Testing implications

The most useful deterministic scenarios are small and separable:

- accelerate on flat track with no stunt input;
- brake from a known speed;
- jump and land cleanly;
- perform one stunt class at a time;
- fail a landing;
- observe boost gain and depletion;
- cross a reversal/control-change region;
- collide while holding otherwise identical input.

The original developers reportedly used a flat straight race as an acid test for feel and fairness. That is unusually well aligned with our available speed/position/boost watchpoints and should become a permanent golden test.

## Unknowns worth resisting

Do not yet assume:

- speed units;
- exact fixed-point formats;
- whether boost is additive, multiplicative or a cap modifier;
- how trick chains are represented internally;
- exact contact-state representation;
- whether AI uses the same movement-control path as players.

Those should fall out of traces around the verified RAM anchors rather than from visual approximation.
