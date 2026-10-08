# Modern Local Tournament: bounded round-robin policy

Status: **pure model and strict tests**. Not yet player-facing. The stock League interface and Authentic execution remain untouched.

## Scope and authority

The decided Modern product format is round-robin points play, replacing *administrative* League obligations rather than changing authoritative two-player racing. `native/product/local_tournament_round_robin.hpp` implements only the tournament schedule, explicit fixture-result admission and standings projection. No new guest menu router, SRAM writer, racer simulation, score observer, file format, background catalog scan or local network dependency has been introduced.

The first playable scope is deliberately restricted to **2 through 8 already-authorized Modern profiles** and a nonempty pool of **ordinary Race courses**, with canonical `course:01`/`course:04` etc. through `course:36`/`course:39`. This excludes Circuit, Stunt, VS and secret/Hunter content, whose result authority is not yet paired with `race-2p` artifacts.

A stable circle-method scheduler builds one meeting per unordered participant pair; an odd roster gets one bye per round. Fixture indices, round numbers, seat assignments and course choice are deterministic. Course choices cycle over the explicit validated pool. Profile identity comparison follows the case-insensitive Windows storage-key rule used by the existing match binder; profile catalog validation remains the owner of whether a profile ID is eligible.

A fixture can be marked complete only by **explicit assignment** of a `StoredMultiplayerMatch` already admitted by the checksum/course-bound multiplayer catalog. The reducer checks that the source is a `race-2p` run with sidecar metadata, that its canonical course agrees with the selected fixture, and that its two stored profile IDs are exactly that fixture's participants (allowing reversed seats). Unknown outcomes, duplicate fixture completion, another fixture's participants, incorrect courses, 1P artifacts and reuse of an already-counted artifact checksum fail without mutating the state.

Results retain the stored stock 2P P1/P2 win/draw outcome and seat orientation. Standings derive only from successfully assigned fixture outcomes, using a **Modern** 3-points-win / 1-point-draw / 0-points-loss policy. They sort by points, wins and normalized profile identity. Equal points and wins share the same displayed rank, with deterministic identity order between ties. These points are *not* claims about the original cartridge League points system.

## Required next shipping gates

A strict canonical supplementary fixture receipt codec now exists in `native/product/local_tournament_fixture_receipt.hpp` (see `docs/MODERN-LOCAL-TOURNAMENT-RECEIPT.md`); it binds explicit instance/fixture identity to the checksum-bound existing pair on decode, but live minting, file publication and tournament-state persistence are not yet implemented.

**Critical:** `StoredMultiplayerMatch` is an already-validated *catalog input type*, not a proof of tournament membership. Calling this pure reducer directly with an arbitrary old validated match from general Records would not prove that it was played for the active tournament. Before wiring a UI or persisted standings, the runtime needs a distinct, durable **active tournament identity and fixture binding**, produced when a specific fixture is launched, and tied to the completed `.urrun` plus `.urmatch` artifacts. The bound result must survive fresh-process restore without guessed associations, even when the same profiles play the same course repeatedly. Keep the v1 match codec authoritative for its existing fields; extend through a separately versioned/bound sidecar or a proven equivalent, rather than inferring fixture membership from filenames, timestamps, profile sequence, or session-local device assignment.

The eventual host UI must also consume the already-decided explicit participant/profile and stock 2P route authorities; the source-identity admission rule is not satisfied by selecting two controller seats. Automatic persistence of active tournament state and retaining the original League standings *visual grammar* remain unimplemented. This slice alone does not deliver a playable tournament.

Focused tests in `tests/native/local_tournament_round_robin_test.cpp` cover even/odd rosters, byes, pair uniqueness, ordinary Race admission, invalid/duplicate identities, course mismatches, reversed source seats, duplicate run checksum, unsupported outcome, fail-closed refusal and correctly oriented points. They run in `local-multiplayer-product-contracts.yml` through strict C++17 compilation. No full desktop boot or visual acceptance is claimed for this pure model.
