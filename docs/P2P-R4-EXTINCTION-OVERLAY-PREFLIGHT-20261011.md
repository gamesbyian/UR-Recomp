# R4 preflight: reconstruct an overlay without a canonical bootstrap service

**Status, 2026-10-11: offline deterministic policy simulation only. Not a real network, authenticated DHT, ICE/UDP session, relay, platform port or multiplayer proof.** This document supplements [the self-sustaining P2P research charter](SELF-SUSTAINING-P2P-MULTIPLAYER-RESEARCH.md) and the [URP0 manual invite lab](P2P-R2-R8-MANUAL-INVITE-OFFLINE-LAB-20261011.md). It does not replace R1 determinism, R4 real-process verification or release QA, and adds no periodic CI workflow or shipping dependency.

The project's requirement is stronger than merely being able to reconnect to a known default bootstrap server: two independent surviving instances must be able to **re-create a network after every old discovery node disappears**, by exchanging enough current contact material outside the game. Every node may host a shareable contact but no node is privileged. Contact exchange with one reachable player is sufficient to introduce other *consenting* reachable players; a relay or public IP cannot be inferred from membership alone.

## Bounded model and repeatable command

Run `python3 -m unittest tests.unit.test_p2p_overlay_reconstitution -v` or `python3 tools/p2p/overlay_reconstitution_lab.py` from the repository root. The lab uses only Python's standard library and **does not open a socket, query DNS, generate identities, read a secret, or touch guest state**. The `World` object is centralized **test instrumentation** for reachability and injected out-of-band contact events, not a proposed real-world directory, account authority, rendezvous service or reference network protocol. `A`/`B`/`C` are synthetic peer IDs, and `sim-a` is a placeholder version digest.

Deterministic illustrative sequence:

1. **Extinction:** clear all cached contacts and overlay links. A knows nobody; attempts return `no-current-contact`. There is no hardcoded domain, canonical seed, contact or automatic phone-home.
2. **Manual cold start:** an external channel introduces B's current endpoint to A; only an explicitly permitted, model-routable pair connects. The reverse return contact is shared directly between those two accepted peers, not automatically with outsiders.
3. **Third participant:** B separately obtains C's current endpoint via manual exchange and connects. A learns C only if C authorized redistribution of its contact. This remains a **potential** direct route, not an added third active Uniracers racer or a claim of NAT traversal.
4. **Islands:** A/B and D/E establish separate contact islands; a deliberately exchanged C contact can bridge them only where the fixture permits direct routing. No source-controlled server joins them invisibly.
5. **Bounded adversaries:** short-lived contacts expire; same-epoch records cannot rewrite a prior endpoint; caches contain at most 32 contacts; a PEX exchange handles at most eight entries. A source changing its advertised endpoint needs a fresher contact, not an old alias. Refused invites, incompatible simulation identities and unreachable endpoints yield distinct failure reasons.

In a future authenticated protocol, peer-public-key signatures, explicit per-contact redistribution consent, replay protection, signed revocation/supersession and independent client conformance **must** replace every toy ID and model flag. Anyone can forge such a fixture contact; no tool here accepts it as trusted data. Sharing an endpoint may reveal an IP address and should require user consent. An existing recipient cannot reliably erase already shared endpoints when someone later revokes consent, so real-world TTLs and renegotiation, not promises of instant removal, define that limit.

## Invariants and next real experiments

The test explicitly distinguishes `no-current-contact`, `peer-offline`, `simulation-incompatible`, `peer-refused`, and `direct-route-unavailable`. **No current contact** can be repaired by exchanging an invitation. **No direct route** may require port mapping, a separately opted-in reachable peer relay, a different network or might remain impossible. Peer exchange is *not* a packet tunnel or NAT traversal mechanism, and none of the model's positive outcomes are measured connections.

R4 is *not satisfied* until two clean real Windows (and later macOS) processes have no old bootstrap/cache entries, exchange a **signed** self-contained descriptor out of band, authenticate, connect using actual chosen endpoints without project DNS, seed a third compatible peer, and prove a disconnected or unrouteable negative control. R1 separately requires identical authoritative guest-state checkpoints before netplay can publish results. Extend with permissionless discovery and volunteer relay only after actual transport/authentication and consent boundaries are sound.
