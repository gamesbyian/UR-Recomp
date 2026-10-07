# Multiplayer / Tournament Records Authority

Status: Records destination exists. A typed read-only ordinary-2P Race result observer now consumes the already-promoted stock result surface, rider identities and last-result pair; durable match-history production remains blocked on participant binding and persistence.

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

1. **[implemented]** Promote a typed, read-only title result observation for the validated ordinary 2P Race result surface. `native/title/uniracers_two_player_result.*` admits only an explicitly classified ordinary-2P context plus stock menu `0xF9`, stock rider indices `7E:017D/017F`, and the stock `77:0618/061A` last-result pair. It classifies P1 win, P2 win or draw with `60000` as `NO TIME`, and fails closed on invalid riders/result values. It writes nothing.
2. **[model implemented]** Bind the observed result to explicit participant identity without treating controller seats as people. `multiplayer_match_binding.*` accepts optional authoritative Modern profile entries that must agree with the stock rider actually used. An unprofiled participant remains explicitly a local guest and retains the exact selected legacy racer identity; it does not acquire a fake profile.
3. **[sidecar path selected and implemented]** Keep replay authority in `.urrun` and store match semantics in strict `UR-MULTIPLAYER-MATCH/1` `.urmatch` metadata. The sidecar carries participants, course, race result/outcome and the exact existing run-artifact checksum, has its own deterministic checksum, bounded file I/O, and is admitted only when its checksum/course binding matches a validated decoded `.urrun`. The existing run schema is not overloaded.
4. Prove production ordinary-2P capture + fresh-process paired `.urrun`/`.urmatch` persistence while preserving deterministic replay compatibility independently from result metadata.
5. Only then let Multiplayer/Tournament Records aggregate completed matches and later tournament standings.

Tournament aggregation must consume persisted match evidence. It must never become the authority that decides what happened in the guest.

## Stop condition

Production 2P capture may now advance only through the bounded ordinary-2P Race slice: participant identity, authoritative terminal result, strict sidecar persistence and exact `.urrun` binding all have typed fail-closed models. Do not generalize to Circuit, Stunt, VS or tournament standings until their distinct result/session semantics are explicitly admitted.
