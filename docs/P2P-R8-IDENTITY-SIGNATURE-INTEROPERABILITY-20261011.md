# R8 cryptographic identity and invitation interoperability: non-negotiable gates

**Research note 2026-10-11, not an adopted library or shipping crypto.** Companion to [self-sustaining P2P charter](SELF-SUSTAINING-P2P-MULTIPLAYER-RESEARCH.md), [R0 native seam inventory](P2P-R0-NATIVE-SEAM-INVENTORY-20261011.md), and [offline URP0 contact laboratory](P2P-R2-R8-MANUAL-INVITE-OFFLINE-LAB-20261011.md). This note addresses a concrete *independently implemented client interoperability* hazard. It does not modify the guest, start a network or select any production transport. Reuse `TRUSTED-UPSTREAM-ADOPTION.md` and `THIRD-PARTY-CODE-AUDIT.md` before obtaining code.

## Key requirement: independently generated and verifiable identity

An open network surviving the project's disappearance cannot authenticate users against a developer-issued certificate, root signing key, account service or mandatory rendezvous. Each installation eventually creates its own local identity key using an audited OS CSPRNG, holds the private material only locally, and may explicitly share a public-key fingerprint to authenticate a friend. An arbitrary signed discovery record is attributable to **some** public key but *not* proof that the key belongs to a particular friend. TOFU/pinned-contact verification, key rotation and blocked peers are distinct product policies. Private keys and operating-system account tokens must never appear in exported invite codes.

The URP0 code is intentionally **untrusted**: a SHA-256 checksum can be recomputed by anyone. Neither nominal `peer_key` nor optional `recipient_key` binds anyone until a separate signed version has both canonical verification and a live challenge/handshake. Do **not** quietly add a signature property to URP0 or auto-connect after parsing it. Give the authenticated wire version its own prefix, test vectors, domain separation and independently verified schema.

## Verified primitive compatibility trap

| Candidate | What the primary implementation actually exposes | Protocol permanence consequence |
| --- | --- | --- |
| [libsodium](https://doc.libsodium.org/public-key_cryptography/public-key_signatures) | `crypto_sign_detached` / `crypto_sign_verify_detached` provide **standard Ed25519** detached signatures. Library uses the [ISC licence](https://doc.libsodium.org/doc). | Strong cross-language interoperability reference, broader package surface. Vendor a **specific immutable version/revision**, not a changing “stable” build without exact provenance. |
| [Monocypher standard Ed25519 extension](https://monocypher.org/manual/ed25519) | `crypto_ed25519_sign` / `crypto_ed25519_check`, via `monocypher-ed25519.h`, implement Ed25519 according to RFC 8032. | A small portable C alternative; requires the correct additional source/header, exact length validation at call sites and independent test vectors. Verify build and licence inventory before adoption. |
| [Monocypher default EdDSA](https://monocypher.org/manual/eddsa) | `crypto_eddsa_sign` / `crypto_eddsa_check` use **BLAKE2b**, not standard Ed25519's SHA-512. [Monocypher's own compatibility note](https://monocypher.org/why/compatibility) states these signatures are **not interoperable with libsodium**. | **Do not choose these default API names** for a protocol promising Ed25519. A matching 32-byte public-key field or 64-byte signature does not imply identical wire semantics. |

Monocypher's project currently describes public-domain/CC0 with BSD-2-Clause alternative in its [licence rationale](https://monocypher.org/why/); this is a candidate observation, not approval to import unscreened source. Standard signing semantics must be independently frozen by [RFC 8032](https://www.rfc-editor.org/info/rfc8032/) and its official test vectors, not inferred from similarly named elliptic-curve APIs. Do not copy public library code or compiler settings from unreviewed external samples into the project.

## Proposed V1 acceptance contract, not yet a wire format

1. **Identity signature:** canonical versioned invitation payload including all endpoint candidates, session epoch, expiry, inviter public key, compatibility identity, optional recipient key and anti-replay nonce. Sign with **standard Ed25519** over the exact byte sequence `domain || canonical_payload`, e.g. a future `UR-RECOMP-P2P-INVITE-V1\0` domain. Verify before taking *any* network action; a valid signature still requires explicit friend/identity consent. No V0 checksum or URL handler is trusted.
2. **Freshness and authorization:** bound clocks, nonce replay cache (including cancellation/supersession semantics), explicit join approval, optional recipient-key restriction and host fingerprint confirmation. Expiry alone does not stop same-window replay. A code for an unreachable/offline endpoint is not proof of a live lobby.
3. **Session exchange:** separate ephemeral X25519 from long-term Ed25519 identity keys, with mutually verified transcript binding roles, version, candidates, session epoch, simulation digest and **both controller seat assignments**. [Monocypher X25519 guidance](https://monocypher.org/manual/x25519) emphasizes public-key binding in the KDF, all-zero shared-secret checks and forward secrecy. Do not treat raw X25519 output as a finished AEAD key; review protocol transcript and key derivation before writing socket code.
4. **Product gate:** the authenticated session must not mint guest-authoritative winner packets, trust remote save files, overwrite named SRAM or substitute network delivery for the native pre-step two-seat input authority. R1 independent-process guest determinism and complete state checks must pass first. Optional presentation settings remain outside the negotiated simulation identity only after proven safe.
5. **No privileged namespace:** any compatible independent client may produce and verify identities and signed invites with independently maintained code. The project's domain, default relay, signing certificate, GitHub repository and publisher are all removable without invalidating peer-owned keys and versioned wire signatures.

## Falsifiable experimental matrix for dependency adoption

A selected implementation must be tested with **at least two independent crypto libraries** (e.g. pinned libsodium and pinned Monocypher *standard* Ed25519), with official RFC 8032 vectors and at least one cross-implementation key/sign/verify matrix. Reject forged messages, substituted endpoint byte(s), wrong recipient, wrong version/domain, modified nonce, expired invitations, duplicated/replayed codes and changed session transcript. Include all-zero, malformed/noncanonical public keys and signatures, untrusted oversized payload, mixed case and illegal UTF-8. Sign/verify tests must have deterministic public expected bytes, not merely “same library signs and verifies itself”. Run under offline process isolation without a hosted service. Record exact library source hashes and licences, Windows x64 and available macOS toolchains, packaging size, memory footprint and cold-start costs before shipping.

The preferred design is **standard Ed25519 for long-term signatures and a separately reviewed authenticated ephemeral handshake**, but **no specific crypto library is selected by this memo**. Raw URP0 invitations remain parsing/fingerprint-study fixtures only. Native Windows P0 journeys and the R1 oracle continue to outrank an early online UI.

## Primary references

- [RFC 8032 standard and vectors](https://www.rfc-editor.org/info/rfc8032/)
- [libsodium detached Ed25519 APIs](https://doc.libsodium.org/public-key_cryptography/public-key_signatures), [ISC licence](https://doc.libsodium.org/doc)
- [Monocypher standard Ed25519](https://monocypher.org/manual/ed25519), [default nonstandard-for-Ed25519 EdDSA](https://monocypher.org/manual/eddsa), [explicit libsodium compatibility warning](https://monocypher.org/why/compatibility)
- [Monocypher X25519 key-exchange caveats](https://monocypher.org/manual/x25519)
