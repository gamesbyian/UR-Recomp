# Native Modern Multiplayer: explicitly selected participant handoff

**Scope:** staged above the native read-only Records integration in
PR #1323. This is product/frontend participant *selection*, not a
guest-authenticated 2P match producer or final Windows multiplayer acceptance.

## Existing authority and new UI connection

The Baldosa Modern root continues to use its existing five-destination
`ModernRootMenu`, the same stock-density root painter and the real SDL
host/input seam. A selected **named** Modern P1 with a canonical catalog
of at least two safe distinct profiles can open a two-pad confirmation
panel from Multiplayer.

- P1 A/Start explicitly confirms the already-booted named racer;
  P1 cannot browse a different SRAM owner in this guest process.
  P2's *independent* physical gamepad Up/Down/A/Start highlights and
  explicitly confirms a different named profile. P2 B clears only P2's
  confirmation; P1 B cancels the panel without a stock transition.
- P1's identity is constrained to the already-authorized active native
  profile and its initialized cartridge SRAM. A cursor change cannot
  silently load a different profile's SRAM midway through a game.
- A distinct, storage-safe P2 catalog profile is mandatory for a bound
  record. Selecting the same Windows-casefolded ID fails. Highlighting
  never counts as selecting, and confirming either seat never confirms
  the other. On both acknowledgements the already-established guest
  stock 2P transition is requested, using the same queued original-menu
  input and source-verified handoff as before.
- The result observer may query the two profile entries **only** while
  the root has acknowledged the original stock 2P menu handoff and still
  owns both explicit confirmations. Re-entry, cancelled guest routing,
  new stock setup, or changed player mode immediately revoke that
  borrowed identity. No code assigns profile identity from gamepad
  device number, guest rider index, inferred name, or result time.
- Anonymous installs and named installs without a usable second
  catalog profile remain able to play stock 2P, but have **no identity
  binding** and cannot mint `.urmatch` records. They log the honest
  unbound route rather than manufacturing an opponent. Authentic mode
  remains unchanged.

## Remaining gate

Source-authenticated result capture already exists in
`BaldosaGuestResultObserver`; the existing
`bind_local_multiplayer_match_context` verifies the stock riders against
explicit selected participant identities, and canonical pair append exists
in `multiplayer_match_record`. The next product task is to consume this
bounded native handoff under fresh selector/catalog/profile OS leases,
recheck course and source result, and publish one bound `.urrun` +
`.urmatch` pair atomically. After that, exact Windows two-pad human
acceptance must prove original rider choices match those confirmed profiles,
a real guest result publishes a pair, and a fresh process reads it. A
synthetic fixture or this isolated UI policy test cannot satisfy that
complete journey.

Test: `tests/unit/test_baldosa_native_two_seat_join_cpp.py` builds the
C++ policy using the existing product profile runtime and exercises both
physical-seat authorizations, P1 source profile restriction, duplicate
IDs, invalid catalog entries, cursor revocation, cancellation and readiness.
This does not replace the original guest Win32 test or independent QA.

The existing Windows named Records fixture is also reused in an additional
**fresh process** with one valid named profile and SDL root 2P navigation.
It must still reach the authentic stock 0x3D setup, emit an explicitly
unbound `join_unavailable` diagnostic, and leave all historical run+match
archive files identical. This is a consumer regression for graceful play
without inventing P2 identity, not a completed played 2P result.

