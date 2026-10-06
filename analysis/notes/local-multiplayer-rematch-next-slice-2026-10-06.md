# Modern Local Multiplayer Rematch / Rotation Contract

Status: bounded next Windows x64 product slice after the shipped independent local-join model.

## Existing authority to preserve

The Modern local-multiplayer setup work already owns independent player join/leave and must remain the only player-membership authority. Stock guest race simulation, racer state, course semantics, results, and timing remain authoritative. Existing Quick Practice / frontend launch routing remains the course-launch authority.

This slice must not add a second lobby model, write guest course state directly, or make multiplayer results authoritative host simulation.

## Product gap

The baseline product requirement calls for fast local multiplayer setup, rematch, and track rotation without returning through legacy League administration. Independent join is present; post-race continuation is the remaining narrow UX gap.

## Required behavior

For a completed Modern local multiplayer race:

1. **Rematch** launches the same authoritative course through the existing launch/router boundary while retaining the currently joined local players.
2. **Next Track** advances through an explicit host-owned course ordering derived from the existing authoritative course catalog, then launches through the same router boundary.
3. Back/Exit returns to the settled Modern frontend without mutating player membership or synthesizing progression.
4. Disconnect/reconnect remains owned by the local multiplayer device/join layer. A rematch must never silently substitute one physical device for another joined player.
5. Repeated rematches must not accumulate stale completion state, duplicate result handling, or duplicate launch requests.
6. Authentic mode remains inert and continues through stock frontend/results behavior.

## Ownership boundaries

The continuation controller may retain only:
- the settled course identity needed to request another authoritative launch;
- the chosen action (rematch, next track, exit);
- references/identities already owned by the local-player membership layer.

It must not retain or restore guest race-state bytes, timers, checkpoints, RNG, opponent state, or transient result flags.

Track rotation should consume the canonical course identity/catalog surface. Ordering is product policy, not inferred from guest memory. If the existing catalog cannot provide a stable product ordering, add that ordering at the catalog/policy seam rather than inside the results controller.

## Acceptance

A focused native acceptance should prove:

- two independently joined players complete a race, choose Rematch, and relaunch the identical canonical course;
- the same two player memberships survive the relaunch without a new join gesture;
- three consecutive rematches each produce exactly one launch and one completed-result lifecycle;
- Next Track selects the next catalog identity and launches it through the same authoritative router;
- wrapping behavior at the end of the chosen rotation is explicit and deterministic;
- disconnecting a joined controller before continuation fails closed according to the existing membership/device policy rather than reassigning another controller;
- Exit returns to the Modern frontend with no launch;
- Authentic mode exposes none of the host-owned continuation actions.

## Non-goals

Do not redesign the multiplayer setup panel, add tournament/bracket progression, add network play, change stock multiplayer simulation, or couple this slice to secondary-platform work. Tournament views remain a later Records/frontend concern.
