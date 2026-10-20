# R8 signed-contact offline pilot and cold-restart replay boundary (2026-10-20)

**Research HOLD.** This is an independent offline protocol experiment, not a shipping P2P implementation, authenticated friend invitation, live socket, or Windows release gate. Read `docs/P2P-R8-IDENTITY-SIGNATURE-INTEROPERABILITY-20261011.md` and `docs/P2P-R4-OFFLINE-PEER-ISLAND-RESURRECTION-20261011.md` before treating it as a design input.

## Experiment and result

On 2026-10-20, Agent 1 exercised a self-contained Python `cryptography` Ed25519 pilot using the canonical domain `UR-RECOMP-P2P-CONTACT-V1\\0`. The signed payload includes owner public-key SHA256 identity, sequence, issued/expiry, numeric endpoints, scope, consent and revocation state. It uses deterministic canonical JSON bytes, rejects duplicate fields, nonfinite values, substituted keys, modified endpoints, wrong signature domain, expired/future records and wrong pinned identities. A known RFC 8032 empty-message vector independently checks standard Ed25519 behavior. **12/12 isolated tests passed**, after correcting a one-character transcription error in the test-vector fixture; no cross-library interoperability matrix or shipping dependency qualification has been performed.

The decisive negative: an authentic signed sequence-1 contact is correctly refused after a signed sequence-2 revocation **within the same process**. After reconstructing the directory without independently durable monotonic state, the still-valid sequence-1 contact is accepted again. Standard signatures prove authorship, not freshness across lost local history. The experimental `VolatileSequenceAnchor` deliberately models that failure. A purported checkpoint SHA stored beside its checkpoint does not fix co-rollback.

A correct production design must explicitly choose and document its offline rollback trust model, e.g. an independently durable local monotonic anchor with crash-safe publication, a user-pinned out-of-band latest sequence, or a conservative fail-closed recovery policy. No general offline cryptographic mechanism can distinguish a restored valid old checkpoint from a genuine old installation when all trusted local state is rolled back. An independently implemented client must be able to reproduce the canonical wire format without the project's server, root key, DNS or account service.

## Evidence boundary and next experiment

The source/test pair is preserved in the recovery bundle and is **not** incorporated into the game. Pilot SHA256: source `9a8cfd8b5d15e19614763661e0bb39187f958c7e7be88994f6e6543b4dbc42ff`; tests `44acbdd1fc60fcbeb0e6e95889656b8fb60d41d40ff7ad74b1bf90cfb1903825`. The tested `cryptography` Python package version was 46.0.4; it is a research tool, not a selected Windows/Mac/Linux runtime dependency. No sockets, NAT/CGNAT, recipient handshake, X25519 transcript, key rotation, durable key store, friend TOFU, two-seat guest input or real multiplayer were exercised.

Next: freeze a binary wire format and independently verify canonical test vectors in two distinct RFC 8032 implementations; design a separately persisted and authenticated monotonic anchor with power-failure and rollback tests; bind identity and seat assignment to a mutually authenticated ephemeral handshake. Keep R1 deterministic guest parity and Windows P0 above P2P shipping work. No release gate credit.

This note must not be treated as evidence of approved multiplayer or as permission to change native guest timing.
