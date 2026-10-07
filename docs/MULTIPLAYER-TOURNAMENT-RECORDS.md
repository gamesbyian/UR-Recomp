# Multiplayer / Tournament Records Authority

Status: Records destination exists. Ordinary-2P Race result, two-profile participant identity and canonical course identity are fail-closed authority seams; paired `.urrun` + `UR-MULTIPLAYER-MATCH/1` persistence is checksum/course bound. The Modern local-multiplayer join surface now supplies two explicit profile identities independently of device assignment. Pure ordinary-2P capture admission is now defined; live completion/pair-write integration and fresh-process acceptance are the remaining production blockers.

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
2. **[pure binding implemented]** `native/product/local_multiplayer_match_binding.*` accepts the authoritative title result plus two explicit `HostProfileCatalogEntry` values supplied by the Modern session layer. It rejects missing or storage-unsafe profile IDs, Windows-equivalent duplicate profile IDs, invalid racer identities, and any mismatch between the supplied identity rider index and the stock rider observed for that player. It does not infer identity from controller seats, active profile, timing, filenames or input payloads, and it does not persist anything.
3. **[live participant selection implemented]** `local_multiplayer_participants.*` keeps device assignment and participant identity separate. Each joined seat cycles and explicitly confirms one catalogued Modern profile; storage-unsafe IDs and Windows-equivalent duplicates fail closed. A disconnect clears the affected participant identity. Confirmed identities survive stock setup/race/result/track-choice and retire on settled frontend return. The stock rider picker remains authoritative; the host does not write rider IDs, and later binding still rejects any profile/rider mismatch.
4. **[pure course/event binding implemented]** The same binder can now accept `UrUniracersCourseIdentity` from the established decoded-course observer and produces the canonical completed-run course key only for valid ordinals 1..45. Because the result observer already admits only ordinary 2P Race results, this completes the pure `{result, participants, course/event}` authority tuple without inferring from filenames, timers or controller seats.
5. **[sidecar path implemented]** `native/product/multiplayer_match_record.*` stores the already-bound `{result, two profiles, course}` tuple as bounded deterministic `UR-MULTIPLAYER-MATCH/1` metadata. It has its own checksum, strict decoding/file limits, and carries the exact existing `.urrun` artifact checksum. Admission against a decoded run requires checksum equality, canonical course equality, and explicit `race-2p` run provenance; a checksum-bound `race-1p` artifact cannot acquire multiplayer-match authority. A dedicated constructor creates match metadata only from a validated `race-2p` run and an already-bound authoritative match context. The replay schema and replay authority are unchanged.
6. **[pair persistence implemented]** The sidecar API canonically places metadata at `<run>.urmatch` (for example `run-…urrun.urmatch`) and refuses save or fresh-process load unless the sidecar checksum/course binding matches the supplied immutable completed run. Focused coverage writes a `.urrun`, writes its bound `.urmatch`, reloads both from disk, and proves a changed run or mismatched course is rejected.
7. **[pure capture admission implemented]** `run_record_capture_policy.hpp` now distinguishes the existing Modern 1P timed-Race path from the bounded ordinary-2P Race path without changing the recorder or `.urrun` schema. 2P admission requires explicit participant readiness, uses distinct `race-2p` provenance, requires the checksum-bound match record, and deliberately disables 1P timing/PB/ghost authority. Practice, VS, unclassified events and non-Race course semantics remain closed. The live host still records only 1P until the 2P completion/pair-write lifecycle is wired and accepted.
8. **[paired store implemented]** `multiplayer_match_store.*` gives production capture one narrow persistence call for an already-authoritative `race-2p` run plus bound match context. It validates both artifacts before disk I/O, appends the immutable `.urrun`, writes the checksum-bound `.urmatch`, and removes the just-created run on synchronous sidecar failure so ordinary Records cannot discover a newly unpaired multiplayer artifact. A pre-existing sidecar path is preserved and treated as a collision rather than overwritten. Replay authority remains entirely in `.urrun`.
9. Broaden the live host capture only for that admitted ordinary-2P Race slice: retain the confirmed participant session, capture the existing P1/P2 resolved input stream, observe the authoritative result/course tuple, call the paired store, and prove fresh-process deterministic replay remains unchanged.
10. Only then let Multiplayer/Tournament Records aggregate completed matches and later tournament standings.

Tournament aggregation must consume persisted match evidence. It must never become the authority that decides what happened in the guest.

## Stop condition

Do not generalize merely because the input format can encode P2. Result/participant/course authority, explicit live two-profile identity, and paired persistence are now available for the bounded ordinary-2P Race slice. The remaining blocker is production paired capture and fresh-process acceptance; Circuit, Stunt, VS and tournament standings remain outside this authority.
