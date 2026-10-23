#!/usr/bin/env python3
"""R4 pure offline *contact-cache model*, NOT peer discovery or cryptography.

Research-only bound for bootstrap-extinction/reconstitution experiments.
Every accepted record must already have independent owner-signature proof,
supplied by a future authenticated protocol. No URP0 checksum is such proof.
No socket, DNS, multicast, key store, relay or gameplay code exists here.
"""
from __future__ import annotations

from dataclasses import dataclass
import ipaddress
import re

MAX_PEERS = 64
MAX_EXPORT = 8
MAX_ENDPOINTS = 4
MAX_LIFETIME = 86400
IDENTITY = re.compile(r"[0-9a-f]{64}\Z")


@dataclass(frozen=True)
class Contact:
    owner: str
    sequence: int
    issued: int
    expires: int
    endpoints: tuple[tuple[str, int], ...]
    scope: str  # lan or wan
    share_consent: bool
    revoked: bool = False

    def validate(self, now: int) -> None:
        if not isinstance(self.owner, str) or not IDENTITY.fullmatch(self.owner) or (
            int(self.owner, 16) == 0
        ):
            raise ValueError("invalid identity")
        if type(self.sequence) is not int or not 1 <= self.sequence <= 2**53-1:
            raise ValueError("invalid sequence")
        if any(type(x) is not int for x in (self.issued, self.expires, now)) or (
            self.issued < 0 or self.expires <= self.issued or
            self.expires-self.issued > MAX_LIFETIME or
            not self.issued <= now < self.expires
        ):
            raise ValueError("expired or future contact")
        if self.scope not in ("lan", "wan") or type(self.share_consent) is not bool or (
            type(self.revoked) is not bool
        ):
            raise ValueError("invalid scope/consent/revocation")
        if not isinstance(self.endpoints, tuple):
            raise ValueError("endpoints must be immutable")
        if self.revoked:
            if self.endpoints or self.share_consent:
                raise ValueError("revocations contain no endpoints or consent")
        elif not 1 <= len(self.endpoints) <= MAX_ENDPOINTS:
            raise ValueError("invalid endpoint count")
        seen: set[tuple[str, int]] = set()
        for endpoint in self.endpoints:
            if not isinstance(endpoint, tuple) or len(endpoint) != 2:
                raise ValueError("invalid endpoint tuple")
            address, port = endpoint
            if type(address) is not str or type(port) is not int or (
                not 1 <= port <= 65535 or "%" in address
            ):
                raise ValueError("invalid endpoint")
            try:
                ip = ipaddress.ip_address(address)
            except ValueError as exc:
                raise ValueError("numeric IP required; DNS forbidden") from exc
            if address != str(ip) or ip.is_multicast or ip.is_unspecified or (
                ip.is_loopback
            ) or (self.scope == "wan" and not ip.is_global):
                raise ValueError("noncanonical/unshareable endpoint")
            if endpoint in seen:
                raise ValueError("duplicate endpoint")
            seen.add(endpoint)


class PeerIslandDirectory:
    """Bounded verified-contact cache; no central root or network operation."""

    def __init__(self, *, capacity: int = MAX_PEERS):
        if type(capacity) is not int or not 1 <= capacity <= MAX_PEERS:
            raise ValueError("invalid cache capacity")
        self._capacity = capacity
        self._entries: dict[str, Contact] = {}
        # Keep process-local high-water even after expiration or bounded
        # active-cache eviction. Never silently forget signed revocations.
        # A durable independent anchor is still required across restarts.
        self._high_water: dict[str, int] = {}

    def prune(self, now: int) -> None:
        if type(now) is not int or now < 0:
            raise ValueError("invalid current time")
        for key, entry in list(self._entries.items()):
            if now >= entry.expires:
                del self._entries[key]

    def learn(self, entry: Contact, *, owner_signature_verified: bool,
              now: int) -> bool:
        """Reject hearsay without verified owner signature. This lab does NOT
        verify signatures: the caller must later supply actual RFC8032 proof.
        """
        if type(owner_signature_verified) is not bool:
            raise ValueError("invalid signature witness")
        if not owner_signature_verified:
            return False
        if not isinstance(entry, Contact):
            raise ValueError("invalid contact")
        entry.validate(now)
        self.prune(now)
        highest = self._high_water.get(entry.owner)
        if highest is not None and highest >= entry.sequence:
            return False
        if highest is None and len(self._high_water) >= MAX_PEERS:
            # Refuse new identities when retained replay barriers fill up.
            return False
        previous = self._entries.get(entry.owner)
        if previous is None and len(self._entries) >= self._capacity:
            # Deterministic bounded eviction, no privileged bootstraps.
            victim = min(self._entries.values(), key=lambda item:
                         (item.expires, item.issued, item.owner))
            del self._entries[victim.owner]
        self._entries[entry.owner] = entry
        self._high_water[entry.owner] = entry.sequence
        return True

    def known(self, *, now: int) -> tuple[str, ...]:
        self.prune(now)
        return tuple(sorted(k for k, e in self._entries.items()
                            if not e.revoked))

    def introduce(self, *, now: int, scope: str,
                  limit: int = MAX_EXPORT) -> tuple[Contact, ...]:
        """Only explicitly share-consented fresh records on correct network.

        An authorized caller can choose whether/how to deliver these bytes
        out of band. This function performs NO network activity.
        """
        if scope not in ("lan", "wan") or type(limit) is not int or (
            not 1 <= limit <= MAX_EXPORT
        ):
            raise ValueError("invalid introduction bounds")
        self.prune(now)
        eligible = [e for e in self._entries.values() if
                    not e.revoked and e.share_consent and e.scope == scope]
        eligible.sort(key=lambda e: (-e.issued, -e.sequence, e.owner))
        return tuple(eligible[:limit])
