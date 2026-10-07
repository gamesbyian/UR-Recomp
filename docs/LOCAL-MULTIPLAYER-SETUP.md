# Modern local multiplayer setup contract

Status: implementation-ready Windows x64 product contract.

## Goal

Make ordinary local two-player play reachable without recreating the stock League administration layer. The guest remains authoritative for two-player race simulation, course rules, timing, collision, results and progression semantics. The host owns device assignment, explicit Modern participant-profile selection, and the route into an ordinary stock two-player session. Device identity and participant identity remain separate authorities.

## Product policy

Modern mode exposes a compact local multiplayer setup surface with two player slots.

- P1 and P2 each require both a usable input assignment and an explicitly confirmed Modern profile before the Modern join surface releases control to stock setup.
- P2 joins explicitly from an unassigned connected device. Keyboard remains P1-only unless the framework later provides genuinely independent keyboard partitions.
- Joining a device never chooses a profile. Profile cursors may be pre-positioned, but participant identity exists only after explicit confirmation.
- The same profile cannot occupy both player slots.
- A confirmed participant session survives stock setup, active race, result and track-choice surfaces and retires on return to the settled frontend.
- One physical controller cannot own both slots.
- Disconnecting an assigned controller marks that slot unavailable and blocks launch until the device returns or the slot is reassigned.
- Reconnection of the same framework device restores its prior slot when unambiguous.
- Reassignment changes host input routing only. It must not synthesize guest progression, race state or SRAM.
- Launch uses the existing stock two-player frontend/race path. Do not add a second multiplayer simulation or direct race-state writer.
- Rematch and track rotation use the stock post-race choice. An ordinary 2P result (`0xF9`) goes straight to the stock track choice `0x5A` (NEXT TRACK / SAME TRACK / SELECT TRACK / SELECT TOUR / QUIT), and SAME TRACK re-enters NOW PLAYING for the same course (`analysis/generated/vs-challenger-probe.json`, RESEARCH-LEDGER `two-player-result-decision`). Modern deliberately does not enable host Restart on `0xF9`: a restart there would discard the stock two-player session tally that the next `0x5A` choice carries forward.
- Authentic mode remains unchanged and exposes the stock administration path only.

## Input authority

SDL/framework device identity and binding state are authoritative. The title layer may retain a small session-local mapping from stable connected-device identity to P1/P2, but must not duplicate controller polling, deadzones, bindings or hot-plug state.

Keyboard support may expose a single P1 mapping initially if the framework cannot safely provide two independent keyboard partitions. Do not pretend one keyboard is two devices by aliasing the same physical bindings.

## Fail-closed rules

Launch is refused when:

- P1 or P2 lacks a usable assigned input source;
- P1 or P2 lacks an explicitly confirmed valid Modern profile;
- both slots resolve to the same exclusive physical device;
- both slots resolve to the same Modern profile;
- an assigned device disconnects between confirmation and stock route entry;
- the current frontend context is not the validated Modern multiplayer entry surface;
- another product-owned navigation router is in flight.

A refused launch leaves guest state and SRAM untouched.

## First implementation slice

1. **[implemented]** `LocalMultiplayerSetupState` owns framework device assignment only.
2. **[implemented]** `LocalMultiplayerParticipantSelection` owns explicit P1/P2 profile confirmation independently of device assignment; duplicate profiles, invalid profiles and selection for an unjoined slot fail closed.
3. **[implemented]** The settled Modern 2P join overlay lets each joined seat cycle and explicitly confirm a profile. Keyboard can join/confirm P1; each physical controller operates its own seat. Disconnect clears that seat's participant identity. Each joined seat shows its device beneath its row (`PAD <framework device name>`, `KEYBOARD`, or `… DISCONNECTED`), derived only from the presentation-safe seat projection (`local_multiplayer_seat_text.hpp`); opaque source IDs are never shown.
4. The stock rider picker remains authoritative. The Modern overlay does not write rider IDs; subsequent match-history binding accepts a result only when the guest-observed rider indices match the two confirmed profile identities.
5. Route the accepted session through the existing stock two-player menu/input machinery and retain participant identity through the session until frontend return.
6. **[decided]** Rematch/rotation is the stock `0x5A` choice. Do not add multiplayer-specific rollback, and do not extend host Restart to the 2P result surface.

## Acceptance

A Windows fresh-process acceptance must prove:

- two distinct framework devices can join P1/P2, each explicitly confirm a distinct Modern profile, and enter an ordinary stock two-player race;
- simultaneous P1/P2 input reaches the already-validated guest input boundary;
- swapping host assignments swaps only input ownership, not racer/course/progression state;
- disconnecting either assigned controller prevents launch or pauses setup without leaking input to the guest;
- reconnecting/reassigning restores a valid launch path;
- results SAME TRACK re-enters the same authoritative two-player course through the stock `0x5A` choice while the confirmed participant session persists;
- SRAM and guest simulation remain identical to the equivalent stock two-player route at the accepted semantic checkpoints;
- Authentic mode exposes none of the Modern setup UI or host assignment authority.

**Partial evidence (2P join surface):** `tests/native/run_modern_two_player_join_acceptance.sh` reaches the stock 2P select surface by the ordinary route, then two distinct SDL virtual gamepads seated by the framework join P1/P2 with their real buttons. Each seat's device line names its own pad. P2's attempt to take P1's profile is refused (`PROFILE_DUPLICATE`), P2 then confirms a distinct profile, and the session becomes ready exactly once with the overlay released to stock setup. Authentic with the same pads and route never opens the join surface. A second run unplugs P2's joined pad: readiness clears, the seat reports `CONTROLLER DISCONNECTED`, and the overlay remains host-owned. After replug, the stale seat must be left and explicitly rejoined/confirmed before readiness returns. Race entry, input swapping and the `0x5A` replay remain to be proven.

## Stop condition

Do not expand this lane into network play, controller-driver work, new guest multiplayer semantics, League redesign, or secondary-platform input. Once two distinct local devices can deterministically reach and replay an authoritative stock 2P race, return remaining UX polish to the ordinary frontend/accessibility queue.
