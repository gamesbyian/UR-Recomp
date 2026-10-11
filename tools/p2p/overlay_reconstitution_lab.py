#!/usr/bin/env python3
"""Deterministic OFFLINE R4 P2P extinction preflight, NOT a network or netplay stack.

The World object is test instrumentation, never a product rendezvous server.
Opaque peer IDs are NOT cryptographic identities; model flags stand in for
later independently authenticated/consented discovery records. No sockets,
DNS, project address, OS clipboard, secrets, game state, or persistence I/O.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

MAX_CONTACTS = 32
MAX_PEX = 8
MAX_CONTACT_AGE = 3600


class Outcome(str, Enum):
    CONNECTED = "direct-connected"
    UNKNOWN = "no-current-contact"
    UNREACHABLE = "direct-route-unavailable"
    INCOMPATIBLE = "simulation-incompatible"
    OFFLINE = "peer-offline"
    REJECTED = "peer-refused"


@dataclass(frozen=True)
class Contact:
    # These names are synthetic fixture IDs; not DNS, account or DHT keys.
    peer: str
    endpoint: str
    sim: str
    issued_at: int
    expires_at: int
    redistributable: bool = False

    def valid(self, now: int) -> bool:
        return (0 <= self.issued_at <= now < self.expires_at and
                self.expires_at - self.issued_at <= MAX_CONTACT_AGE)


@dataclass
class Node:
    peer: str
    endpoint: str
    sim: str
    # Explicit local privacy/consent decisions. They are NOT network proofs.
    invite_accepted: bool = True
    share_contact: bool = False
    online: bool = True
    contacts: dict[str, Contact] = field(default_factory=dict)
    connected: set[str] = field(default_factory=set)

    def current_contact(self, now: int) -> Contact:
        return Contact(self.peer, self.endpoint, self.sim, now,
                       now + MAX_CONTACT_AGE, self.share_contact)

    def expire(self, now: int) -> None:
        self.contacts = {
            k: v for k, v in self.contacts.items() if v.valid(now)
        }

    def receive(self, contact: Contact, now: int) -> bool:
        # Caller MUST already have an authenticated/consented source in a
        # future product. This offline research model provides neither.
        self.expire(now)
        if (contact.peer == self.peer or not contact.valid(now) or
                contact.peer == "" or contact.endpoint == "" or
                contact.sim == "" or not contact.peer.isascii() or
                len(contact.peer) > 128 or len(contact.endpoint) > 128):
            return False
        old = self.contacts.get(contact.peer)
        if old is not None and contact.issued_at <= old.issued_at:
            # Neither replay nor a same-epoch address swap can poison cache.
            return False
        if old is None and len(self.contacts) >= MAX_CONTACTS:
            return False
        self.contacts[contact.peer] = contact
        return True


@dataclass
class World:
    """Non-shipping lab scheduler for explicitly specified direct routes."""
    nodes: dict[str, Node]
    routable: set[frozenset[str]]
    now: int = 10000

    def manual_exchange(self, recipient: str, sender: str) -> bool:
        """Models a voluntary OUT-OF-BAND contact message, not online lookup."""
        a, b = self.nodes[recipient], self.nodes[sender]
        if not b.online or not b.invite_accepted:
            return False
        return a.receive(b.current_contact(self.now), self.now)

    def connect(self, initiator: str, target: str) -> Outcome:
        self.nodes[initiator].expire(self.now)
        a, b = self.nodes[initiator], self.nodes[target]
        if not a.online or not b.online:
            return Outcome.OFFLINE
        descriptor = a.contacts.get(target)
        if descriptor is None:
            return Outcome.UNKNOWN
        if descriptor.sim != a.sim or b.sim != a.sim:
            return Outcome.INCOMPATIBLE
        if not b.invite_accepted:
            return Outcome.REJECTED
        if (frozenset((initiator, target)) not in self.routable or
                descriptor.endpoint != b.endpoint):
            return Outcome.UNREACHABLE
        a.connected.add(target)
        b.connected.add(initiator)
        # The response endpoint need not be redistributable. It is only
        # shared with this accepting direct peer for its own return route.
        b.receive(a.current_contact(self.now), self.now)
        return Outcome.CONNECTED

    def exchange_contacts(self, receiver: str, sender: str) -> int:
        """Opt-in bounded PEX after a confirmed direct link; no public DHT."""
        a, b = self.nodes[receiver], self.nodes[sender]
        if (not a.online or not b.online or sender not in a.connected or
                receiver not in b.connected):
            return 0
        a.expire(self.now)
        b.expire(self.now)
        # Never gossip another member's endpoint without that member's
        # explicit affirmative redistribution consent. No relay implied.
        sharable = sorted(
            (v for v in b.contacts.values()
             if v.redistributable and v.peer != receiver),
            key=lambda v: (v.peer, v.issued_at),
        )[:MAX_PEX]
        count = 0
        for contact in sharable:
            count += int(a.receive(contact, self.now))
        return count

    def extinction(self) -> None:
        """Destroy ALL cached bootstrap edges; no hidden fallback addresses."""
        for node in self.nodes.values():
            node.contacts.clear()
            node.connected.clear()

    def disconnect(self, peer: str) -> None:
        node = self.nodes[peer]
        node.online = False
        node.contacts.clear()
        for other in self.nodes.values():
            other.connected.discard(peer)


def no_service_scenario() -> dict[str, str | int]:
    """Run explicitly fixture-routable A/B then discover new C via B."""
    nodes = {
        name: Node(name, f"198.51.100.{i}", "sim-1", share_contact=True)
        for i, name in enumerate(("A", "B", "C"), start=1)
    }
    world = World(nodes, {
        frozenset(("A", "B")), frozenset(("A", "C")),
        frozenset(("B", "C")),
    })
    world.extinction()
    before = world.connect("A", "B")
    assert world.manual_exchange("A", "B")
    first = world.connect("A", "B")
    assert world.manual_exchange("B", "C")
    second = world.connect("B", "C")
    introduced = world.exchange_contacts("A", "B")
    third = world.connect("A", "C")
    return {"without_contact": before.value,
            "manual_ab": first.value, "manual_bc": second.value,
            "pex_records": introduced, "discovered_ac": third.value,
            "mandatory_service_contacts": 0,
            "network_sessions_proven": 0}


if __name__ == "__main__":
    import json
    print(json.dumps(no_service_scenario(), sort_keys=True))
