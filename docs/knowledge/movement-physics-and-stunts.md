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
- `7E:11CD`: boost meter;
- `7E:11FD`: flips;
- `7E:11F9`: rolls;
- `7E:0F61`: twists;
- `7E:042B`: Z-flips;
- `7E:042F`: tabletops;
- `7E:132B`: reverse-controls flag in the recovered bot.

Several of these come from independent historical sources and therefore make excellent symbol-validation anchors.

## Current conceptual model

**Supported.** Racing performance couples ordinary movement to successful stunt execution. Stunts are not only score events: landing useful tricks modifies the player's speed/boost state.

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
- stunt counter update timing;
- how trick chains are represented internally;
- exact contact-state representation;
- whether AI uses the same movement-control path as players.

Those should fall out of traces around the verified RAM anchors rather than from visual approximation.
