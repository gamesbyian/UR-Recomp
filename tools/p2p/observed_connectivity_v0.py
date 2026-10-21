#!/usr/bin/env python3
"""R5 offline *diagnostic policy*, never a NAT detector or network connector.

This experimental policy consumes independently witnessed stage outcomes. It
does not verify signatures, open sockets, contact peers or claim that any
unprobed candidate is reachable. URP0 cannot produce a signed descriptor.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any

MAX_EVIDENCE_BYTES = 4096
SOURCES = frozenset(("none", "manual", "lan", "cache", "overlay"))
DESCRIPTORS = frozenset(("absent", "urp0_untrusted", "expired", "signed_verified"))
SIMULATIONS = frozenset(("unknown", "match", "mismatch"))
DIRECT = frozenset(("not_tried", "failed", "authenticated"))
RELAY = frozenset(("unavailable", "not_tried", "refused", "failed", "authenticated"))
FIELDS = frozenset(("source", "descriptor", "friend_confirmed", "simulation",
                    "direct", "manual_reply_received", "volunteer_relay_opt_in",
                    "relay"))


@dataclass(frozen=True)
class Evidence:
    source: str
    descriptor: str
    friend_confirmed: bool
    simulation: str
    direct: str
    manual_reply_received: bool
    volunteer_relay_opt_in: bool
    relay: str

    @classmethod
    def from_mapping(cls, obj: Any) -> "Evidence":
        if not isinstance(obj, dict) or set(obj) != FIELDS:
            raise ValueError("missing or unknown R5 evidence fields")
        for key, allowed in (
            ("source", SOURCES), ("descriptor", DESCRIPTORS),
            ("simulation", SIMULATIONS), ("direct", DIRECT),
            ("relay", RELAY),
        ):
            if type(obj[key]) is not str or obj[key] not in allowed:
                raise ValueError("invalid " + key)
        for key in ("friend_confirmed", "manual_reply_received",
                    "volunteer_relay_opt_in"):
            if type(obj[key]) is not bool:
                raise ValueError("invalid boolean " + key)
        if obj["source"] == "none" and obj["descriptor"] != "absent":
            raise ValueError("no-contact evidence cannot contain an invite")
        if obj["source"] != "none" and obj["descriptor"] == "absent":
            raise ValueError("contact source requires an assessed descriptor")
        if obj["source"] != "manual" and obj["manual_reply_received"]:
            raise ValueError("out-of-band reply requires manual contact")
        if obj["relay"] == "authenticated" and not obj["volunteer_relay_opt_in"]:
            raise ValueError("unconsented relay cannot be authenticated")
        if obj["direct"] == "authenticated" and obj["relay"] == "authenticated":
            raise ValueError("ambiguous simultaneous active transport")
        if (obj["direct"] == "authenticated" or
                obj["relay"] == "authenticated") and (
                obj["descriptor"] != "signed_verified" or
                not obj["friend_confirmed"] or
                obj["simulation"] != "match"):
            raise ValueError("authenticated route needs independent authority")
        return cls(**obj)


@dataclass(frozen=True)
class Decision:
    status: str
    meaning: str
    next_action: str
    # A classification can advise what to try, never predict that it succeeds.
    evidence_class: str = "OBSERVED_STAGES_ONLY"

    def to_mapping(self) -> dict[str, str]:
        return asdict(self)


def classify(e: Evidence) -> Decision:
    """Return one truthful next action, not a fabricated NAT success rate."""
    def result(code: str, meaning: str, action: str) -> Decision:
        return Decision(code, meaning, action)

    if e.source == "none":
        return result("NO_CONTACT", "No peer address or discovery root is known.",
                      "Exchange a complete invite outside the game, or discover a LAN peer.")
    if e.descriptor == "expired":
        return result("CONTACT_EXPIRED", "The advertised contact is no longer valid.",
                      "Ask the inviter for a newly issued, signed contact descriptor.")
    if e.descriptor == "urp0_untrusted":
        return result("CONTACT_UNAUTHENTICATED",
                      "URP0 is a checksummed research contact, not proof of identity.",
                      "Obtain a future signed invite and independently confirm its owner.")
    if e.descriptor == "absent":
        # from_mapping() disallows this with a nonempty source.
        raise ValueError("inconsistent contact state")
    if not e.friend_confirmed:
        return result("FRIEND_NOT_CONFIRMED",
                      "A signature authenticates a key, not its human owner.",
                      "Confirm the fingerprint with the intended friend before joining.")
    if e.simulation == "mismatch":
        return result("SIMULATION_INCOMPATIBLE",
                      "The signed simulation identity differs from the local game.",
                      "Agree on the same authenticated compatible guest and deterministic build.")
    if e.simulation == "unknown":
        return result("SIMULATION_NOT_CHECKED",
                      "Guest compatibility has not been confirmed.",
                      "Check the signed simulation digest before admitting game input.")
    if e.direct == "authenticated":
        return result("DIRECT_SESSION_CONFIRMED",
                      "An independently observed authenticated direct transport exists.",
                      "Proceed only through separately verified synchronized-gameplay admission.")
    if e.relay == "authenticated":
        return result("VOLUNTEER_RELAY_SESSION_CONFIRMED",
                      "An opted-in independent relay carries an authenticated session.",
                      "Proceed through synchronized-gameplay admission; respect relay limits.")
    if e.direct == "not_tried":
        return result("DIRECT_PROBE_REQUIRED",
                      "A contact is known, but direct reachability is unmeasured.",
                      "Attempt bounded authenticated direct connectivity; do not claim success yet.")
    if e.source == "manual" and not e.manual_reply_received:
        return result("REPLY_CODE_SUGGESTED",
                      "Direct connectivity failed with only one-way manual contact data.",
                      "Exchange a fresh reply code and retry bounded candidate checks; success is not guaranteed.")
    if e.volunteer_relay_opt_in and e.relay == "not_tried":
        return result("VOLUNTEER_RELAY_PROBE_REQUIRED",
                      "Direct checks failed; a voluntary relay has not been tried.",
                      "Ask a willing reachable independent node for a bounded relay reservation.")
    return result("NO_USABLE_ROUTE",
                  "Direct connectivity failed and no confirmed usable relay remains.",
                  "Try reachable IPv6/manual port mapping, another network, or a consenting peer relay.")


def _finite_json_float(token: str) -> float:
    import math
    number = float(token)
    if not math.isfinite(number):
        raise ValueError("nonfinite R5 observation: " + token)
    return number


def _unique_stage_fields(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate R5 observation key: " + key)
        result[key] = value
    return result


def assess_mapping(raw: Any) -> dict[str, str]:
    """Tool-independent JSON boundary for repeatable external R5 fixtures."""
    return classify(Evidence.from_mapping(raw)).to_mapping()


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("evidence_file", type=Path,
                   help="Small local JSON stage-evidence file; never a peer URL")
    args = p.parse_args()
    try:
        with args.evidence_file.open("rb") as stream:
            data = stream.read(MAX_EVIDENCE_BYTES + 1)
        if len(data) > MAX_EVIDENCE_BYTES:
            raise ValueError("evidence file exceeds bounded limit")
        observed = json.loads(data.decode("utf-8"), object_pairs_hook=_unique_stage_fields,
                             parse_float=_finite_json_float,
                             parse_constant=lambda token: (_ for _ in ()).throw(
                                 ValueError("nonfinite R5 observation: " + token)))
        print(json.dumps(assess_mapping(observed), sort_keys=True))
    except (ValueError, OSError, UnicodeDecodeError) as exc:
        p.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
