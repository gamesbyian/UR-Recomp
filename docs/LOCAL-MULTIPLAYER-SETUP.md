# Modern local multiplayer setup contract

Status: implementation-ready Windows x64 product contract.

## Goal

Make ordinary local two-player play reachable without recreating the stock League administration layer. The guest remains authoritative for two-player race simulation, course rules, timing, collision, results and progression semantics. The host owns only device assignment and the route into an ordinary stock two-player session.

## Product policy

Modern mode exposes a compact local multiplayer setup surface with two player slots.

- P1 must be assigned before launch.
- P2 joins explicitly from an unassigned connected device or keyboard partition.
- One physical controller cannot own both slots.
- Disconnecting an assigned controller marks that slot unavailable and blocks launch until the device returns or the slot is reassigned.
- Reconnection of the same framework device restores its prior slot when unambiguous.
- Reassignment changes host input routing only. It must not synthesize guest progression, race state or SRAM.
- Launch uses the existing stock two-player frontend/race path. Do not add a second multiplayer simulation or direct race-state writer.
- Rematch and track rotation should reuse the existing Modern Restart/fast-navigation authority once a two-player session exists.
- Authentic mode remains unchanged and exposes the stock administration path only.

## Input authority

SDL/framework device identity and binding state are authoritative. The title layer may retain a small session-local mapping from stable connected-device identity to P1/P2, but must not duplicate controller polling, deadzones, bindings or hot-plug state.

Keyboard support may expose a single P1 mapping initially if the framework cannot safely provide two independent keyboard partitions. Do not pretend one keyboard is two devices by aliasing the same physical bindings.

## Fail-closed rules

Launch is refused when:

- P1 or P2 lacks a usable assigned input source;
- both slots resolve to the same exclusive physical device;
- an assigned device disconnects between confirmation and stock route entry;
- the current frontend context is not the validated Modern multiplayer entry surface;
- another product-owned navigation router is in flight.

A refused launch leaves guest state and SRAM untouched.

## First implementation slice

1. Add a pure `LocalMultiplayerSetupState` model that consumes framework device-presence/identity events and exposes P1/P2 assignment, join, leave, disconnect and reconnect outcomes.
2. Add focused C++ tests for duplicate-device rejection, deterministic join order, disconnect/reconnect, reassignment and launch eligibility.
3. Integrate only the settled Modern frontend setup surface after the model is accepted. Keep device enumeration in the host adapter.
4. Route an accepted launch through the existing stock two-player menu/input machinery.
5. Reuse the existing fast-navigation Restart/rematch path rather than creating multiplayer-specific rollback.

## Acceptance

A Windows fresh-process acceptance must prove:

- two distinct framework devices can join P1/P2 and enter an ordinary stock two-player race;
- simultaneous P1/P2 input reaches the already-validated guest input boundary;
- swapping host assignments swaps only input ownership, not racer/course/progression state;
- disconnecting either assigned controller prevents launch or pauses setup without leaking input to the guest;
- reconnecting/reassigning restores a valid launch path;
- results Rematch re-enters the same authoritative two-player course through the existing Restart lifecycle;
- SRAM and guest simulation remain identical to the equivalent stock two-player route at the accepted semantic checkpoints;
- Authentic mode exposes none of the Modern setup UI or host assignment authority.

## Stop condition

Do not expand this lane into network play, controller-driver work, new guest multiplayer semantics, League redesign, or secondary-platform input. Once two distinct local devices can deterministically reach and replay an authoritative stock 2P race, return remaining UX polish to the ordinary frontend/accessibility queue.
