# Multiplayer / Tournament Records Authority

Status: Records destination exists. Ordinary-2P Race result, two-profile participant identity and canonical course identity are fail-closed authority seams; paired `.urrun` + `UR-MULTIPLAYER-MATCH/1` persistence is checksum/course bound and same-directory staged before catalog-visible publication. The Modern local-multiplayer join surface supplies two explicit profile identities independently of device assignment. Production ordinary-2P capture wiring is present and its dedicated native fresh-process acceptance is green on `main` (Shared Modern native acceptance run `37709847500`, `e17d167`, ordinary-2P shard). Aggregate tournament history over the persisted pairs is the next step; it must derive only from validated pairs, never from session-local assignment or 1P artifacts.

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

The unified Records root exposes **Multiplayer/Tournament** with a read-only validated match list/detail surface. The host scans the shared `multiplayer-runs` namespace through `multiplayer_match_catalog.*`; only fully bound `race-2p` run+sidecar pairs become rows. Missing, corrupt, wrong-mode, or unbound evidence contributes only an unavailable count and never gains match authority. Until the production producer lands, an ordinary installation will usually remain in the explicit no-history state.

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
6. **[pair persistence implemented]** The sidecar API canonically places metadata at `<run>.urmatch` (for example `run-…urrun.urmatch`) and refuses save or fresh-process load unless the sidecar checksum/course binding matches the supplied immutable completed run. Pair append now builds both artifacts in a private same-filesystem staging directory, publishes the bound sidecar first, and renames the `.urrun` last as the catalog-visibility commit. An interrupted stage can leave only inert staging or an orphan sidecar, never a catalog-visible run lacking its match authority. Focused coverage reloads the committed pair, proves a changed run or mismatched course is rejected, and requires successful publication to leave only the two public files.
7. **[production capture wiring implemented]** `run_record_capture_policy.hpp` distinguishes the existing Modern 1P timed-Race path from the bounded ordinary-2P Race path without changing the recorder or `.urrun` schema. 2P admission requires explicit participant readiness, uses distinct `race-2p` provenance, requires the checksum-bound match record, and deliberately disables 1P timing/PB/ghost authority. Practice, VS, unclassified events and non-Race course semantics remain closed. The live host now owns a separate ordinary-2P recorder over the authoritative resolved P1/P2 controller stream, retains the confirmed participant/course context, revalidates both participant entries throughout capture and revalidates course identity while the authoritative active-race course surface is still live, completes from the stock 2P result timing, writes the bound pair transactionally, and retires the capture on lost/invalid/stale authority. The dedicated native gate must still pass end to end before this is called production-validated.
8. **[fresh-process acceptance green on `main`: run `37709847500`]** Run the admitted ordinary-2P Race slice through the dedicated native workflow: capture the authoritative resolved P1/P2 stream, drive the already-proven P1 finish while retaining one validated P2 input pulse, let the stock ordinary-2P NO TIME timeout resolve P2 under script-level turbo (host pacing only), persist exactly one bound pair, emit the explicit acceptance-complete diagnostic and terminate through the product success path rather than the wall-clock guard, then reload and validate the pair in a separate process while requiring nonzero evidence from both resolved input lanes. Do not broaden modes or derive standings until this gate is green on current `main`.
9. **[aggregate match history implemented]** `multiplayer_match_summary.*` aggregates only the admitted pairs the browser lists: per-profile played/wins/losses/draws and per-pairing head-to-head, keyed by the binder's case-insensitive profile storage identity so a Windows-equivalent spelling cannot split one history. Same-identity pairs are counted as ignored, never aggregated. Records are kept in profile-identity order and carry no points, ranking or seeding; the newest admitted spelling/racer name is presented. The Records Multiplayer detail view shows the selected pairing's head-to-head oriented to that match's seats (`HEAD TO HEAD n MATCHES` / `P1 a  P2 b  DRAW c`), and the refresh diagnostic reports `MULTIPLAYER_SUMMARY` plus one `MULTIPLAYER_PROFILE` line per profile. Local Tournament standings (round-robin/points) remain a separate later policy that must consume these persisted pairs, not session state.

A read-only catalog substrate now exists independently of production capture: `multiplayer_match_catalog.*` scans the shared namespace in filename order but admits only a valid `race-2p` run whose sibling `.urmatch` reloads and binds to that exact run. Standalone/corrupt/wrong-mode runs and missing/bad sidecars contribute only unavailable-artifact health; they never become match rows. `multiplayer_match_presentation.*` formats only those already-admitted pairs into course, participant, outcome and exact stock-result text. This is query/presentation substrate, not standings aggregation, and it does not assume the live producer has passed native acceptance.

`multiplayer_match_browser.*` adds host-independent list/detail navigation over already-admitted match pairs. It owns only selection and view state, delegates all row/detail text to `multiplayer_match_presentation.*`, and has no standings, replay-routing or filesystem authority. Its bounded selected-centered visible-row projection preserves catalog order and returns authoritative row presentations plus selected state, so the host renderer does not invent clipping, paging, result text or selection semantics. The Windows Records host now wires that model to the Multiplayer/Tournament tab, refreshes the catalog when Records opens, renders validated rows/detail, and preserves unavailable-artifact health without reinterpreting result semantics.

Tournament aggregation must consume persisted match evidence. It must never become the authority that decides what happened in the guest.

## Stop condition

Do not generalize merely because the input format can encode P2. Result/participant/course authority, explicit live two-profile identity, transactionally published paired persistence and the bounded production capture wiring are now available for ordinary-2P Race. Native capture + fresh-process acceptance is green on `main` and aggregate head-to-head history is derived from the persisted pairs; Circuit, Stunt, VS and Local Tournament standings remain outside this authority.
