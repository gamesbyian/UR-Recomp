# R5 observed connection diagnostics: offline deterministic policy laboratory

**Status (2026-10-11): research-only; not a native online transport, NAT probe, cryptographic verifier, lobby or gameplay acceptance.** This is deliberately independent of the URP0 manual-invite parser, existing native Modern local multiplayer and #1346 invite-link work. It addresses the exact R5 research-charter rule: failures must distinguish **no discovery**, **untrusted/expired contact**, **incompatible game**, **untested connectivity**, **insufficient candidate exchange**, **no volunteer relay consent**, and **observed no usable route**. No permanent server, discovery authority, DNS lookup, traffic, accounts, background task, or new GitHub workflow.

## How to reproduce

`python3 -m unittest tests.unit.test_p2p_observed_connectivity_v0 -v`

`python3 tools/p2p/observed_connectivity_v0.py /path/to/local-observations.json`

The CLI reads at most 4,096 bytes of local JSON and emits one machine-readable decision. The input shape is exact:

| Field | Allowed observed values |
| --- | --- |
| `source` | `none`, `manual`, `lan`, `cache`, `overlay` |
| `descriptor` | `absent`, `urp0_untrusted`, `expired`, `signed_verified` |
| `friend_confirmed` | Boolean external fingerprint/identity confirmation |
| `simulation` | `unknown`, `match`, `mismatch` |
| `direct` | `not_tried`, `failed`, `authenticated` |
| `manual_reply_received` | Boolean explicit second out-of-band candidate exchange |
| `volunteer_relay_opt_in` | Boolean willingness/permission to use independent relay |
| `relay` | `unavailable`, `not_tried`, `refused`, `failed`, `authenticated` |

For example, a signed and independently confirmed friend invite with matching game identity, a failed direct probe, a returned reply code and **no usable relay** yields `NO_USABLE_ROUTE`, not "Connecting..." forever. A one-way manual invite with failed direct connectivity yields `REPLY_CODE_SUGGESTED`, but this is an *option*, **not** evidence that bidirectional hole punching will work. A relay can only count as confirmed when an independently observed authenticated transport exists **and** the user allowed volunteer relay use.

`signed_verified` and `authenticated` are **supplied stage evidence**, not conditions computed by this utility. No code in this module generates or verifies signatures, observes packets, proves NAT mappings, checks source guest determinism or takes network action. URP0 codes can only be `urp0_untrusted`; their SHA-256 checksum never qualifies as a signed invitation. Do not connect to an endpoint, award Records, or claim security merely because JSON labels declare it authenticated. Future real native code must replace these test inputs with audited cryptographic verification and actual bounded network probes, then test real Windows/macOS networks independently. A confirmed *transport* is not a completed authentic SNES event.

## Truthful end-state boundaries

- Zero project-controlled infrastructure is a design invariant. A reachable direct route or independent consenting intermediary is still physically necessary for WAN contact. No algorithm guarantees discovery from a completely isolated fresh node with no shared address.
- Offline LAN, user-shared address, and copyable invite or reply can recreate islands without a project website; they do not promise NAT traversal. Optional community relays may have cost/consent/availability limits and must be non-exclusive.
- The decision table is future UI vocabulary/evidence audit material, not automatic online multiplayer or a production protocol wire format. R1 source-deterministic cross-process guest simulation remains an independent prerequisite before a netplay session can start.
- The probe inputs deliberately distinguish untried connectivity from measured failure; aggregate "success rate" must count only actual attempted stages, not these hypothetical policy fixtures.

Related authorities: [self-sustaining P2P charter](SELF-SUSTAINING-P2P-MULTIPLAYER-RESEARCH.md), [manual invite lab](P2P-R2-R8-MANUAL-INVITE-OFFLINE-LAB-20261011.md), [identity/signed-invite requirements](P2P-R8-IDENTITY-SIGNATURE-INTEROPERABILITY-20261011.md).
