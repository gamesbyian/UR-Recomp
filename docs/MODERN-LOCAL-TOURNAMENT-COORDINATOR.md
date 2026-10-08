# Local Tournament: host session coordinator

Status: executable production-layer orchestration, with disk-backed C++ acceptance. No player-visible Modern Local Tournament launch route has been wired yet.

## How the existing authoritative components join

The single host-owned coordinator in native/product/local_tournament_session_coordinator.hpp/.cpp composes the already-merged canonical active session file, launch checkpoint and saved fixture receipt link stores. It does not alter guest 2P physics, SRAM, input mapping, controller routing or the frontend.

Creation requires an explicitly selected and authoritative catalog-validated roster of 2 through 8 Modern profiles, an ordinary Race course pool, an independently minted unique tournament instance ID and explicit overwrite policy for an existing active tournament. Active session identity is stored under the caller's existing per-user data root. Receipts and launch checkpoint live beneath a separate instance-ID-scoped directory, so starting another tournament with the same profiles or tracks never adopts results from an older event.

The caller explicitly selects an unfinished fixture, confirms both Modern participant identities and supplies a new independent live capture-attempt ID. A launch is not authorized until the exact canonical attempt checkpoint is durably written. The host must then route into the original stock 2P race/track selection rather than writing guest race state. At the ordinary 2P capture START, the host checks its live confirmed profiles and title-observed course against this persisted fixture and retains the exact attempt token inside that capture owner. Wrong profiles or course never produce an attempt token. The existing stock result and standard pair producer retain timing, rider/result and match authority.

AFTER append_multiplayer_match_pair succeeds, the host passes its retained live attempt and saved pair path to the coordinator's commit. It delegates to the exact .urrun + .urmatch re-admission and receipt-link publication introduced in PR #803, then marks only that fixture complete and retires the checkpoint. A cancelled route retires only its own token and creates no result. A new process reloads only its active session and explicit valid fixture links, never historical Records matches or an abandoned pre-restart race. A completed tournament is one for which every scheduled fixture is proven, and standings use the established Modern 3/1/0 policy and deterministic shared-rank ordering.

The focused native test uses real filesystem persistence and checksum/course-bound ordinary 2P run+match pairs. It exercises wrong participant/track/token rejection, uncredited cancelled fixtures, two-process continuation, explicit replacement isolation and complete standings. That proves product backend composition, **not** an actual Windows menu-routed two-controller tournament. No guest race or host UI was exercised in this test.

## Live Windows integration contract

1. Modern-owned tournament selection UI: explicit roster/ordinary Race pool and a selected fixture. Present fixtures and standings using original League visual grammar, including appropriate wide/HD reflow. Keep original administrative League available only in Authentic as dictated by product policy.
2. Host stock-2P route: confirm two distinct active Modern profiles and valid devices through the existing join overlay. Call coordinator arm BEFORE committing to the guest route. Require source course confirmation from the original guest observer rather than deducing it from the selected host row.
3. Existing ordinary-2P recorder: retain the coordinator attempt token only after real race start has matched the planned participant/course tuple; propagate the same token to normal pair publication and coordinator commit. Failed/timed-out routes cancel the exact pending attempt. Ordinary Records remain authoritative independently.
4. Host session lifecycle: choose the already-established per-user data root, mint IDs securely, load the active tournament and its receipt-linked standings at startup, and expose continuation and completed-tournament presentation. Do not restore a mid-race guest state from a pending checkpoint, or treat ordinary Records history as fixture evidence.
5. Native Windows acceptance: select an actual fixture via the player-visible frontend, join two separate controllers/profiles, race, observe official stock result, persist validated pair + supplemental receipt, exit, relaunch, continue and show consistent standings and a fully completed tournament. Until this passes the product is **not tournament-complete**.

This coordinator is intentionally in native/product rather than main menu code so Claude's concurrently active frontend/controls/pause work is untouched.
