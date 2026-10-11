# P2P R2: actual two-process manual loopback UDP contact, no coordinator

**Status 2026-10-11: bounded local transport laboratory, NOT UR-Recomp netplay.** This is a deliberately separate C++17 exercise in `tools/p2p/direct_udp_loopback_lab.cpp`. It never talks to the original SNES guest, SDL controller state, Profiles, Records, a DHT, an online relay or an external host. It is not the current invitation wire format, cannot authenticate strangers and does not make an ordinary/CGNAT-protected Internet path magically routable.

## What genuinely happens

The script's unit driver starts **two independent native OS processes**. The first explicitly binds **only `127.0.0.1`**, asks the OS for a temporary UDP port, and prints `READY udp@127.0.0.1:<port>`. The second receives that numerical port **out of band through the local fixture**, explicitly sends one bounded challenge to that literal loopback socket and accepts only the matching return packet, source address and port. Both processes exit and discard socket state. There is no background service or global network identity.

The explicit `--allow-loopback-only` argument is mandatory. Supplying no flag, wrong number of arguments, a zero/invalid hexadecimal test nonce or an invalid port must not start an unsolicited receiver. Neither process can dial another machine, send broadcast or contact any website. The 32-hex-character nonce is **test correlation only**, not a private key or security credential; a local attacker could forge it. Timeout is 2.5 seconds using platform-specific `SO_RCVTIMEO` (`DWORD` milliseconds on Windows and `timeval` on POSIX).

**Run:** `python3 -m unittest tests.unit.test_p2p_direct_loopback_cpp -v`.

On Linux/macOS this compiles with `g++` or `clang++` and C++17. On Windows it needs the corresponding native C++ compiler and `Ws2_32` (`-lws2_32` on MinGW). Cross-platform source compatibility is intended, **not yet independently verified on actual Windows/macOS devices**. No third-party download or library, root/admin privileges, cloud address, router mapping or user account is necessary. The ordinary game still has no online feature.

## What it does *not* establish

- A second physical machine or Internet path, IPv6, IPv4/IPv6 interoperability, typical NAT/CGNAT, symmetric UDP hole punching, encrypted sessions, signed invites, security, relay participation, or an operating-system firewall rule.
- Identity/friend verification: matching a short literal test token and loopback source is insufficient to establish who sent the packet. Never reuse `UR-LOOPBACK-HELLO-V0` or its ACK as a product wire protocol.
- Real 60 Hz guest input delivery, frame lockstep, independent-process determinism, gameplay result publication, 2P controller ownership, macOS product integration, or external-network performance.
- Automatic discovery after complete network extinction. It demonstrates only that a *current contact* exchanged outside the game suffices for two **fixture-routable** endpoints to exchange UDP datagrams; R4's separate offline state model covers the missing-contact/PEX state-policy question.

Before any real online feature, pin the complete R1 two-process original-guest state oracle, specify and independently implement a signed/versioned wire format, verify identity and compatibility, and reproduce DNS-blocked LAN/WAN successes and negative NAT cases with explicit user consent. Optional volunteer relays must be permissioned and resource-bounded; no permanent required central service or developer-owned certificate is allowed.

Platform socket API references: [Microsoft `setsockopt`](https://learn.microsoft.com/en-us/windows/win32/api/winsock/nf-winsock-setsockopt) and [POSIX receive timeout](https://linux.die.net/man/3/setsockopt). Those references support the socket option types, **not** cross-platform UR acceptance.

See [decentralized P2P charter](SELF-SUSTAINING-P2P-MULTIPLAYER-RESEARCH.md), [R0 native seam audit](P2P-R0-NATIVE-SEAM-INVENTORY-20261011.md), and [offline R4 extinction model](P2P-R4-EXTINCTION-OVERLAY-PREFLIGHT-20261011.md).
