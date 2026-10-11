# R2/R8 offline manual contact exchange: URP0 laboratory

**Status 2026-10-11: tested offline framing proposal, NOT online multiplayer, NOT an authenticated invitation, NOT a final protocol.** This is a bounded optional research utility in `tools/p2p`, not a shipping in-game feature and not a substitute for R1's deterministic two-process guest proof. It is an explicitly disposable V0 compatibility/conformance test. No sockets, DNS, bootstrap provider, centralized authority, peer registry, relay, account, host gameplay, or external package is involved.

The owner requirement is that two or more friends can exchange **self-contained connection information out of band**, even when the project's existence, global peer discovery and DNS disappear. This is distinct from the happy path of autonomous participant discovery. A short lobby alias cannot retrieve unknown endpoint data without an accessible shared directory; URP0 codes are necessarily longer and carry the endpoint itself.

## Exact URP0 experimental envelope

`URP0.<unpadded-base64url-payload>.<unpadded-base64url-12-byte-checksum>`, optionally preceded by `ur-recomp://join/`. The payload is ASCII canonical JSON: key-sorted, no spaces (`separators=(",", ":")`), no NaNs, no duplicate keys, no unknown fields, and with unique canonical IP literals. The checksum is the first 12 bytes of SHA-256 of `b"UR-RECOMP-OFFLINE-UNTRUSTED-CONTACT-V0\\x00" + canonical_payload` (the `\\x00` represents **one actual zero byte**, not four printable characters). It only catches accidental mistyping. **It does not authenticate a peer**; any attacker can recompute it. `URP0` intentionally cannot be upgraded silently to a future signed invitation version.

Payload fields:

| Key | Laboratory meaning |
| --- | --- |
| `v` | Integer 0 only. Unknown versions fail closed. |
| `peer_key` | 32-byte nominal public-key material as 64 lowercase hex digits, nonzero; **unverified claim**, not a trusted identity. |
| `nonce` | Nonzero 16-byte invite nonce as 32 lowercase hex digits; no random generation in this tool. |
| `valid_from`, `valid_until` | Nonnegative UTC Unix seconds, strict interval, maximum lifetime 86,400 seconds; checking current time is an explicit decode argument. |
| `sim_sha256` | Nonzero 32-byte opaque *simulation compatibility digest*, not a claim of ROM legality or complete netplay determinism. |
| `endpoints` | 1..8 distinct `{"ip":"literal","port":1..65535,"transport":"udp"}` objects. IPv4/IPv6 only, with no DNS, zone IDs, multicast or unspecified addresses. |
| `recipient_key` | Optional 32-byte nominal recipient public key, **not a cryptographic restriction** in URP0. |
| `reply_to` | Optional 16-byte nonce identifying the initiating invite in an out-of-band reply. |

An entire UTF-8 payload must not exceed 1,400 bytes and code length must not exceed 2,050 characters. This bounds allocation/parsing and makes the code transportable in most chat apps, but intentionally not a few-letter friend code.

The code is read with `tools/p2p/manual_invite_v0.py`. The decoder returns *untrusted contact fields only*. It must never trigger network activity, give an identity authority, edit a profile, enqueue SNES guest input, save an award, or assert that a match started. No application should send packets based solely on this V0 result.

## Manual one-way invitation and two-way reply

To generate an **example** code for testing:

```bash
python3 tools/p2p/manual_invite_v0.py create \
  --peer-key "$(printf '01%.0s' {1..32})" \
  --nonce "$(printf '02%.0s' {1..16})" \
  --sim-sha256 "$(printf '03%.0s' {1..32})" \
  --valid-from 1700000000 --valid-until 1700000600 \
  --endpoint 'udp@192.0.2.10:7777' \
  --endpoint 'udp@[2001:db8::7]:7778' \
  --acknowledge-address-disclosure
```

Add `--link` to `create` to print a complete `ur-recomp://join/URP0....`
link instead of the bare code. Both forms import with `inspect`; a real
in-game URL handler is deliberately **not** registered by this prototype.
No domain or hosted resolver is consulted in either case.

The hex patterns, timestamps, and IANA documentation-prefix endpoints above are **fixed nonsecret test data**, not randomly generated authentication keys, live player addresses, or usable connectivity. A real candidate would need securely generated keys/nonces, actual consented reachable addresses, meaningful current timestamps, signature verification, and an authenticated transport. This CLI refuses to create a shareable code until the operator expressly acknowledges that IP and port information becomes visible to recipients.

A recipient can paste the full `URP0.` text or `ur-recomp://join/URP0.` link into:

```sh
python3 tools/p2p/manual_invite_v0.py inspect 'URP0....' --at 1700000001
```

It prints a `UNAUTHENTICATED_OFFLINE_RESEARCH_ONLY` marker. A recipient behind a restrictive NAT can send a *reply* code with its own fresh endpoint/nonce, a `reply_to` equal to the inviter's nonce, and an optional `recipient_key` echoing the inviter's nominal key. That proves the **offline data exchange grammar**, not true mutual authentication or a hole-punch. Neither user must query a project website, a directory or a mandatory relay. If neither address can accept packets and no willing intermediary exists, both still cannot race; provide an honest manual mapping/relay/network-change diagnostic later.

For two or more invitees, V0 deliberately encodes only **one proposed peer contact** per code. A group lobby, shared roster, admission limits, permissions, replay cache, and allocation of the original game's two active racers require a separately versioned, signed protocol. Do not put a multi-person key or hidden broadcast endpoint into the envelope.

## Evidence and negative controls

Run `python3 -m unittest tests.unit.test_p2p_manual_invite_v0 -v`. The suite checks: canonical base64url/JSON, independently framed checksum, manual code/link equivalence, time bounds, two-way offline reply, IPv4/IPv6 and malformed endpoint rejection, unknown/duplicate keys, oversized inputs, checksum mutations, deterministic fuzz mutations and CLI refusal to publish IP addresses without explicit consent.

**Nonclaims:** tests do not prove Ed25519 signatures, recipient restrictions, key rotation, end-to-end encryption, DHT/ICE/UDP connectivity, NAT traversal, replay cache, LAN discovery, cross-OS compatibility, any 60 Hz guest determinism, or completed multiplayer gameplay. The checksum can be forged by design. No automatic workflow was added; the existing Python unit discovery is sufficient.

## Promotion gate for a real invite format

1. Finish R1 deterministic original native two-process input and simulation checkpoint evidence. Determine the actual version/hash set for compatibility; V0's single opaque digest is not sufficient on its own.
2. Publish a new signed, authenticated version with canonical bytes/domain separation, independent crypto conformance vectors, freshness/replay storage and explicit local trust/fingerprint consent. Prefer a reviewed portable Ed25519 implementation over bespoke cryptography, auditing licences/provenance before adoption.
3. Connect only the authenticated result to the future dedicated host-side session, never to the existing SDL local-input edge code. Derive controller seat assignment and shared initial guest state by a handshake between **both** parties.
4. Demonstrate real DNS-free/manual LAN and routable WAN R2 sessions, no developer-operated bootstrap or account, and negative NAT cases; add two-way candidate exchange only after the transport can actually attempt ICE.
5. Only then offer code/link UX. The deep-link handler may launch the game but must require explicit user approval before any network request, even with a syntactically valid code.

See [research charter](SELF-SUSTAINING-P2P-MULTIPLAYER-RESEARCH.md), [R0 native seam inventory](P2P-R0-NATIVE-SEAM-INVENTORY-20261011.md), and [trusted upstream intake](TRUSTED-UPSTREAM-ADOPTION.md).

## Frozen cross-client vector

`tests/data/p2p-urp0-v0-golden.json` contains a complete static code,
canonical payload and checksum `1d5ad590813e31a861ad3306`. It is
non-live, expired test data using IANA documentation prefixes. The unit
suite independently computes and decodes the exact wire bytes so later
non-Python implementations can test interoperability. Manual CLI
`inspect` checks the current time by default; `--at` explicitly opts
into historical fixture evaluation.
