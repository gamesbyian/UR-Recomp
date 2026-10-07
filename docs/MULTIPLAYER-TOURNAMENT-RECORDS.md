# Multiplayer / Tournament Records Authority

Status: Records destination exists. A typed read-only ordinary-2P Race result observer consumes the promoted stock result surface, and the pure product binder joins that result to two explicit Modern profile identities. A strict checksum-bound `UR-MULTIPLAYER-MATCH/1` sidecar now supplies the persistence contract without changing `.urrun`; live session integration remains blocked on explicit P2 profile selection and production paired capture.

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
2. **[pure binding implemented]** `native/product/local_multiplayer_match_binding.*` accepts the authoritative title result plus two explicit `HostProfileCatalogEntry` values supplied by the Modern session layer. It rejects missing or duplicate profile IDs, invalid racer identities, and any mismatch between the supplied identity rider index and the stock rider observed for that player. It does not infer identity from controller seats, active profile, timing, filenames or input payloads, and it does not persist anything.
3. **[persistence contract implemented]** `native/product/multiplayer_match_record.*` encodes a bounded, deterministic `UR-MULTIPLAYER-MATCH/1` `.urmatch` sidecar. It stores the two already-bound profile/racer identities, authoritative Race result/outcome, course identity, and the exact existing `.urrun` artifact checksum. The sidecar has its own checksum, strict decoding and bounded file I/O; admission against a run requires both checksum and course equality with a validated decoded `.urrun`. Replay authority remains entirely in `.urrun`.
4. Integrate the binder only after the live multiplayer/session layer can supply an explicit P2 profile identity. The current device-assignment model is not participant identity and must not be promoted into one.
5. Broaden production capture only for the admitted ordinary-2P Race slice, persist the paired `.urrun` + `.urmatch`, and prove fresh-process pairing plus unchanged deterministic replay.
6. Only then let Multiplayer/Tournament Records aggregate completed matches and later tournament standings.

Tournament aggregation must consume persisted match evidence. It must never become the authority that decides what happened in the guest.

## Stop condition

Do not broaden production 2P capture merely because the input format can encode P2. Result, participant binding and persistence format are now closed for the bounded ordinary-2P Race model, but live capture remains blocked until the session supplies explicit P2 profile identity. Device assignment alone is still insufficient.
