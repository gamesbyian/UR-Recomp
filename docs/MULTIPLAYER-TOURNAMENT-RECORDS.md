# Multiplayer / Tournament Records Authority

Status: Records destination exists; durable match-history production is deliberately blocked on missing authoritative result semantics.

## Existing reusable substrate

The existing completed-run record format is already capable of retaining both players' resolved 12-bit controller words. Its provenance also carries game, ROM, build, course and mode identity. That makes `.urrun` suitable as a future deterministic two-player replay carrier without defining another run format.

Production capture is intentionally narrower. Ordinary persisted Records currently admit supported Modern 1P timed Race runs only. Session-local local-multiplayer setup owns device assignment, not player identity, standings or match results.

## What is still missing

A trustworthy Multiplayer / Tournament history row needs authoritative evidence for at least:

- the completed match/event identity and course;
- the participating Modern profile/racer identities, including the second participant when one exists;
- the authoritative terminal result needed by the product view, such as winner/loser or an explicit draw/result classification;
- the tournament/series identity and round context when the match belongs to a Local Tournament;
- the ordering/points semantics used by the Local Tournament policy.

None of those fields may be inferred from controller seat numbers, elapsed time alone, filenames, input masks or the current active profile.

The current v1 `.urrun` schema therefore must not be reinterpreted as a tournament database. Its P1/P2 input payload proves replay capability, not participant or standings authority.

## Records view policy

The unified Records root exposes **Multiplayer/Tournament** now so the information architecture is stable. Until a durable producer exists, the view explicitly reports that no stored match history is available.

This fail-closed state is intentional:

- no synthetic win/loss totals;
- no guessed opponent identity;
- no ranking by lowest elapsed time;
- no use of 1P PB/Previous selectors as multiplayer standings;
- no promotion of session-local device assignment into persistent identity;
- no second replay or course-identity model.

Tracks, Racers/Profiles and Runs/Replays continue to use the established completed-run catalog unchanged.

## Smallest future implementation slice

The next implementation should begin at the authoritative stock 2P results boundary, not in Records UI.

1. Promote a typed, read-only title result observation for the validated ordinary 2P results surface.
2. Bind the observed result to explicit participant identity supplied by the Modern multiplayer/session layer.
3. Decide whether those additional semantics can be represented as an additive sidecar bound to the existing `.urrun` checksum or require a deliberate schema evolution. Do not silently overload existing fields.
4. Prove fresh-process persistence and deterministic replay compatibility independently from result metadata.
5. Only then let Multiplayer/Tournament Records aggregate completed matches and later tournament standings.

Tournament aggregation must consume persisted match evidence. It must never become the authority that decides what happened in the guest.

## Stop condition

Do not broaden production 2P capture merely because the input format can encode P2. The lane is unblocked only when participant identity and the authoritative terminal result are both observable and can be durably bound to the same completed match without writing guest state.
