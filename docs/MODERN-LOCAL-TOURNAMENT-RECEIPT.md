# Modern Local Tournament fixture receipt boundary

Status: **strict supplementary codec + read-only binding tests**, not yet a live or persisted tournament feature.

The accepted ordinary 2P `.urrun` + `UR-MULTIPLAYER-MATCH/1` pair proves course, participant identity and terminal result. It does **not** prove tournament membership. `native/product/local_tournament_fixture_receipt.hpp` now provides a separate, canonical `UR-LOCAL-TOURNAMENT-FIXTURE/1` envelope that could be saved alongside an explicitly launched tournament fixture.

A receipt identifies an **externally minted unique active tournament instance** (32 lowercase hex digits), a zero-based deterministic fixture index, canonical ordinary Race course, the checksum of an independently validated run+match pair, both original P1/P2 storage identities, stock 2P outcome and whether source seats were swapped relative to the fixture. These fields are stable on encoding, unambiguous and checked against the entire immutable fixture plan and the same catalog-admitted pair on reload. The envelope ends in a deterministic FNV-1a-64 checksum over its canonical bytes. This detects accidental byte damage, not an attacker with write access to local saves.

A receipt is admitted for construction **only after the active fixture has already accepted that exact run+match pair** through the round-robin reducer. Verification supports reconstructing a fresh instance before standings have been applied, but still requires the explicit tournament ID, fixture, course, source identities, outcome and original artifact checksum. It refuses a valid but differently sealed tournament/fixture, a different race result, wrong source profile/course/mode, and corruption or noncanonical record shapes. General Records history is never searched to guess a fixture assignment.

The decoder bounds the entire envelope to 2 KiB, requires an exact field set and order, canonical decimal index, lowercase hex IDs/digests, canonical source-profile byte encoding, valid typed outcomes, and a checksum validated through exact canonical re-encoding. No new `.urrun` or `.urmatch` fields are introduced.

## Deliberately not yet claimed

1. **No tournament receipt is minted by the live host.** The host must establish the unique tournament instance and active fixture before launching the stock 2P Race, retain that identity throughout the authoritative run, and call the receipt producer only after an exact paired capture succeeded. The test's fixture assignment is deliberate input, not provenance automatically discovered from history.
2. **No on-disk receipt writer or atomic publication protocol is shipped here.** The codec is persistence-ready, but a fresh-process integration gate must eventually prove that the receipt and paired run are published consistently without promoting an orphan receipt or losing valid history to interrupted writes.
3. **No tournament state codec or resume-on-restart is shipped.** Active tournament state needs its own strict format and transactional recovery, and must reject inconsistent fixture receipts before standings are restored.
4. **No player-facing tournament UI is shipped.** Ordinary 2P stock routing, source/participant confirmation and the original League-inspired visual grammar remain separate integration tasks.

Focused native-model tests assert byte-for-byte roundtrip, source/fixture verification including restoration with initially empty results, alternate tournament/fixture refusal, bad mode/course/profiles/outcome/primary checksum, noncanonical field shapes, extra/truncated bytes and invalid identifiers. The focused Local multiplayer product contracts workflow runs them with strict C++17 warnings.
