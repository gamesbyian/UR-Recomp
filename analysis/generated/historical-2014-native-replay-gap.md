# Historical 2014 native replay timing gap

Sources: historical replay runs `36780628583`, `36793691236`, `36794900073`, and bounded native writer trace `36795810324`.

The preserved 2014 Dessyreqt SMV remains useful historical input evidence, but absolute pre-race guest-frame equality is **not** a valid semantic fidelity oracle for the current native host.

## What the tighter replay pass established

Dense sampling from reset through frame 460 moved the first sampled tuple mismatch from the old observation boundary at frame 440 to frame **437**. A +5-frame native phase experiment then moved the first sampled mismatch to frame **455**, but did not restore the later route: native still was not in active-race state at the reference frame 794 or results state at frame 2874.

The apparent phase offset is not constant. Matching low-WRAM states drift by roughly +2 frames around frame 280, +3 around frame 400, and +5 by frame 436. This is startup/frontend timing drift, not evidence for one fixed five-frame correction.

## Why frame 437 is not a meaningful gameplay divergence

The original comparison treated several addresses as if their race semantics were valid during the frontend:

- `7E:0313` is only established as `Race_ActiveState` when its value is `0x01` in a race;
- `7E:0411/0415` are established player coordinates during race execution;
- `7E:009F` is useful as a stable frontend checkpoint but is also reused by text/layout code.

The bounded trace explains the pre-race values directly. Nitrodon's exact bank listings show:

- `83:8B79-8B8B` fills WRAM `$0200-$09FF` with word `$004C`, which necessarily overwrites `$0313`, `$0411`, and `$0415` during frontend setup;
- `80:C3AB` parses a compact frontend/text command stream;
- `80:C3C8` performs `JMP ($005D)` through the command-handler table at `80:C3CB-C3EA`;
- that same interpreter uses DP `$9F` as text/tile layout state.

Run `36795810324` dynamically reaches the existing analyzer gap at `80:C3C8` while the compensated frontend transition is being built. The trace scope is `interp@$80C3C8`; the transition also executes the `83:8B85` bulk-fill loop. The trace proves that the low-WRAM mismatch window is dominated by frontend rendering/setup reuse, not yet by authoritative player/race simulation.

## Current interpretation

The exact 2014 movie is still valuable for:

- controller-order and route evidence;
- event-relative frontend transitions;
- identifying code executed by a historically real route;
- later race/stunt behavior after a trustworthy semantic alignment point.

It should **not** drive more frame-by-frame pre-race tracing merely to force absolute clock equality. The deterministic project-owned fixtures already provide a better fidelity oracle for race physics because their semantic checkpoints are event-relative and native/reference movement, jump, rotation, landing, and collision cases match.

The durable discovery from this investigation is instead semantic: `80:C3C8`, one of the three analyzer's unresolved indirect dispatch sites, is a live frontend/text command dispatcher on a high-value historical route. That site should now be handled as executable semantic-decompilation work rather than as an unexplained frame-440 gameplay fault.

## Stopping rule

Do not collect more pre-race historical frames unless a concrete product or semantic decision depends on their absolute timing. Resume first-divergence tracing only at an address/state whose meaning is valid in both compared contexts and whose disagreement can change implementation.
