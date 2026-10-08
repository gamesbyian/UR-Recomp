# Local Tournament: launch-time fixture authority

Status: **pure model and strict C++ acceptance only**. Not wired to the Windows frontend or persisted by a runtime store. The earlier round-robin reducer and existing `.urrun` / `.urmatch` catalog remain the only match/result authority.

## The missing distinction

The catalog proves that two players raced a given course. Even an otherwise valid supplemental tournament fixture receipt cannot prove an old catalog match belonged to the current tournament unless the live host **bound the selected fixture before starting the race**. Matching profile IDs, elapsed times, courses or filenames is not a substitute for that binding.

`native/product/local_tournament_fixture_launch.hpp` adds a bounded, host-owned in-flight admission model. The host must independently mint a canonical 32-character lowercase-hex tournament instance ID **at tournament creation** and a distinct 32-character lowercase-hex attempt ID **for each explicit fixture launch**. Neither is derived from the guest, a run artifact, the filename or existing Records history. The model validates that the selected round-robin fixture is unfinished, snapshots its round, two case-normalized profile identities, course, index and a deterministic digest of the **entire immutable roster/course pool/fixture schedule**, and prevents a second launch from silently replacing it. Results are excluded from the digest because other fixtures can finish without rewriting the tournament schedule.

On authoritative completed ordinary-2P capture, the producer supplies **its own retained live attempt ID**, rather than a value found in a saved artifact. The model requires both IDs to agree, checks that the fixture/course/entrant schedule has not changed, and then delegates the outcome and reversed-seat semantics to the existing `record_local_tournament_result` reducer over an independently catalog-admitted run+sidecar pair. A mismatch never mutates standings or consumes a pending attempt. Successful assignment retires the exact attempt; cancellation and failed guest routes retire only the explicitly matching attempt and never manufacture a result.

`native/product/local_tournament_fixture_launch_codec.hpp` adds an exact-order, bounded (2 KiB) `UR-LOCAL-TOURNAMENT-LAUNCH/1` encoding for that pending snapshot, intended for transactional storage **before** stock route entry. It uses canonical field spelling, strict lowercase hex and decimal forms, a full-schedule fingerprint, and an FNV-1a corruption checksum. The checksum is **not an authenticity signature**: a recomputed valid payload can decode, but still cannot be restored unless the active tournament instance, immutable roster/schedule and unfinished fixture all match. Restoring cannot overwrite a pending launch.

## Shipping boundary still open

The live host does not yet create/persist tournament instances, generate cryptographically unpredictable attempt IDs, atomically publish launch checkpoints, launch stock 2P races for a particular fixture, or pass a trusted attempt ID from the ordinary-2P recorder into this reducer. A run/receipt publication transaction and fresh-process acceptance also remain necessary. The already-merged `local_tournament_fixture_receipt.hpp` codec is complementary: that codec **seals a completed fixture**; this model establishes **pre-race provenance**. It does not duplicate the receipt or alter `UR-MULTIPLAYER-MATCH/1`.

Runtime integration must preserve this order:

1. Explicit player selection of a fixture that belongs to the current tournament and current eligible profile roster.
2. Generate and atomically persist a fresh launch snapshot before entering stock 2P routing. Bind its attempt ID into the active capture owner. On failure, launch no guest route.
3. After stock result + participant + course validation and transactional run/match publication, pass that *same live attempt* to the launch reducer. Commit the fixture result and supplemental receipt transactionally, retiring pending state only when durable commit succeeds.
4. On fresh-process restart, restore only an exact snapshot for the current unfinished fixture; never guess completed events from the global multiplayer catalog. If the guest race cannot be safely restored, abort/retire the pending launch without awarding points.

Strict tests cover unique attempt identity, busy and cancelled attempts, different tournament IDs, changed fixtures/rosters, mismatched result mode/course/profiles, reversed seats, duplicate/late outcomes, canonical byte roundtrips, malformed/corrupt/oversize data and resealed-but-unapproved checkpoints. No native end-to-end or player-visible claim is made.
