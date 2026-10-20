#!/usr/bin/env python3
"""Offline UR P2P contact-exchange laboratory. URP0 is NOT authenticated.

Only a versioned, strictly bounded, portable IP/port contact descriptor.
No DNS, sockets, keys, relay selection, guest input, or implicit discovery.
A checksum catches accidental corruption; it does NOT prove authorship.
NEVER admit a peer or run executable/network operations from parsed fields.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import ipaddress
import json
import re
import time
from typing import Any

PREFIX = "URP0."
LINK_PREFIX = "ur-recomp://join/"
DOMAIN = b"UR-RECOMP-OFFLINE-UNTRUSTED-CONTACT-V0\x00"
MAX_RAW = 1400
MAX_CODE = 2050
MAX_ENDPOINTS = 8
MAX_LIFETIME = 24 * 60 * 60
HEX32 = re.compile(r"[0-9a-f]{64}\Z")
HEX16 = re.compile(r"[0-9a-f]{32}\Z")
B64URL = re.compile(r"[A-Za-z0-9_-]+\Z")
REQUIRED = {"v", "peer_key", "nonce", "valid_from", "valid_until",
            "sim_sha256", "endpoints"}
OPTIONAL = {"recipient_key", "reply_to"}


class InviteError(ValueError):
    """Malformed, incompatible or expired *untrusted* contact proposal."""


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _unb64(value: str) -> bytes:
    if not value or not B64URL.fullmatch(value):
        raise InviteError("invalid base64url alphabet")
    try:
        binary = base64.urlsafe_b64decode(
            value + "=" * (-len(value) % 4))
    except (ValueError, base64.binascii.Error) as exc:
        raise InviteError("invalid base64url payload") from exc
    if _b64(binary) != value:
        raise InviteError("noncanonical base64url")
    return binary


def _unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise InviteError("duplicate JSON key")
        result[key] = value
    return result


def _canonical(value: dict[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("ascii")


def _hex(value: Any, length: int, label: str) -> None:
    if not isinstance(value, str) or not (
        HEX32.fullmatch(value) if length == 64 else HEX16.fullmatch(value)
    ) or int(value, 16) == 0:
        raise InviteError("invalid " + label)


def _endpoint(entry: Any) -> dict[str, Any]:
    if not isinstance(entry, dict) or set(entry) != {"ip", "port", "transport"}:
        raise InviteError("invalid endpoint keys")
    if entry["transport"] != "udp":
        raise InviteError("unsupported endpoint transport")
    port = entry["port"]
    if type(port) is not int or not 1 <= port <= 65535:
        raise InviteError("invalid endpoint port")
    name = entry["ip"]
    if not isinstance(name, str) or len(name) > 45 or "%" in name:
        raise InviteError("endpoint must be a literal IPv4/IPv6 address")
    try:
        ip = ipaddress.ip_address(name)
    except ValueError as exc:
        raise InviteError("endpoint must not require DNS") from exc
    if ip.is_multicast or ip.is_unspecified:
        raise InviteError("multicast/unspecified endpoint forbidden")
    if str(ip) != name:
        raise InviteError("noncanonical IP literal")
    return {"ip": name, "port": port, "transport": "udp"}


def validate_fields(value: Any, *, now: int | None = None) -> dict[str, Any]:
    """Exact shape. Does not establish authentication, trust or reachability."""
    if not isinstance(value, dict) or not REQUIRED <= set(value) or (
        set(value) - REQUIRED - OPTIONAL
    ):
        raise InviteError("missing or unknown descriptor fields")
    if type(value["v"]) is not int or value["v"] != 0:
        raise InviteError("unsupported laboratory format version")
    _hex(value["peer_key"], 64, "public key")
    _hex(value["nonce"], 32, "invite nonce")
    _hex(value["sim_sha256"], 64, "simulation compatibility digest")
    for key, length in (("recipient_key", 64), ("reply_to", 32)):
        if key in value:
            _hex(value[key], length, key)
    start, end = value["valid_from"], value["valid_until"]
    if type(start) is not int or type(end) is not int or start < 0 or (
        end <= start or end - start > MAX_LIFETIME or end > 2**53 - 1
    ):
        raise InviteError("invalid invitation validity window")
    if now is not None:
        if type(now) is not int or not start <= now < end:
            raise InviteError("invitation not presently valid")
    endpoints = value["endpoints"]
    if not isinstance(endpoints, list) or not 1 <= len(endpoints) <= MAX_ENDPOINTS:
        raise InviteError("invalid endpoint count")
    normalized = [_endpoint(item) for item in endpoints]
    unique = {(v["ip"], v["port"], v["transport"]) for v in normalized}
    if len(unique) != len(normalized):
        raise InviteError("duplicate endpoint")
    return value


def make_code(fields: dict[str, Any], *, now: int | None = None) -> str:
    """Encode *untrusted* advertised endpoints for explicit out-of-band sharing."""
    validate_fields(fields, now=now)
    raw = _canonical(fields)
    if len(raw) > MAX_RAW:
        raise InviteError("descriptor too large")
    checksum = hashlib.sha256(DOMAIN + raw).digest()[:12]
    result = PREFIX + _b64(raw) + "." + _b64(checksum)
    if len(result) > MAX_CODE:
        raise InviteError("invitation code too large")
    return result


def make_link(code: str) -> str:
    # Validate before constructing an OS-handler URL.
    read_code(code)
    return LINK_PREFIX + code


def read_code(text: str, *, now: int | None = None) -> dict[str, Any]:
    """Decode strict portable contact data. Result is NEVER an authenticated peer."""
    if not isinstance(text, str):
        raise InviteError("invite must be text")
    # Refuse huge pasted text before making a trimmed copy or decoding it.
    if len(text) > MAX_CODE + 8:
        raise InviteError("oversized invitation")
    text = text.strip(" \r\n\t")
    if text.startswith(LINK_PREFIX):
        text = text[len(LINK_PREFIX):]
    if len(text) > MAX_CODE or not text.startswith(PREFIX):
        raise InviteError("unsupported or oversized invite")
    split = text.split(".")
    if len(split) != 3 or split[0] != "URP0":
        raise InviteError("invalid invitation framing")
    raw = _unb64(split[1])
    tag = _unb64(split[2])
    if len(raw) > MAX_RAW or len(tag) != 12 or not hmac.compare_digest(
        tag, hashlib.sha256(DOMAIN + raw).digest()[:12]
    ):
        raise InviteError("invalid invitation checksum")
    try:
        decoded = json.loads(raw.decode("utf-8"),
                             object_pairs_hook=_unique_pairs,
                             parse_constant=lambda value: (_ for _ in ()).throw(
                                 InviteError("nonfinite JSON value")))
    except (ValueError, UnicodeDecodeError) as exc:
        raise InviteError("malformed invitation JSON") from exc
    # json.loads accepts huge JSON exponents as Python infinity. Rechecking
    # canonical bytes with allow_nan=False then raises ValueError, which must
    # remain a normal malformed-invite verdict rather than crash the CLI.
    try:
        canonical = _canonical(decoded) if isinstance(decoded, dict) else None
    except (TypeError, ValueError, OverflowError) as exc:
        raise InviteError("noncanonical invitation JSON") from exc
    if canonical != raw:
        raise InviteError("noncanonical invitation JSON")
    return validate_fields(decoded, now=now)


def parse_endpoint(text: str) -> dict[str, Any]:
    """CLI endpoint: udp@198.51.100.4:7777 or udp@[2001:db8::1]:7777."""
    if not text.startswith("udp@"):
        raise InviteError("endpoint must begin udp@")
    value = text[4:]
    if value.startswith("["):
        end = value.find("]")
        if end < 0 or value[end + 1:end + 2] != ":":
            raise InviteError("invalid IPv6 endpoint syntax")
        ip, port_str = value[1:end], value[end + 2:]
    else:
        if value.count(":") != 1:
            raise InviteError("IPv6 endpoints require brackets")
        ip, port_str = value.rsplit(":", 1)
    # Bounded ASCII digits only, prior to int() allocation/parsing.
    if not re.fullmatch(r"[0-9]{1,5}", port_str):
        raise InviteError("invalid endpoint port")
    return _endpoint({"ip": ip, "port": int(port_str), "transport": "udp"})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    create = sub.add_parser("create", help="Offline shareable contact proposal")
    create.add_argument("--peer-key", required=True)
    create.add_argument("--nonce", required=True)
    create.add_argument("--sim-sha256", required=True)
    create.add_argument("--valid-from", required=True, type=int)
    create.add_argument("--valid-until", required=True, type=int)
    create.add_argument("--endpoint", action="append", required=True)
    create.add_argument("--recipient-key")
    create.add_argument("--reply-to")
    create.add_argument("--link", action="store_true",
                        help="Print ur-recomp://join/ code for sharing instead of bare code")
    create.add_argument("--acknowledge-address-disclosure", action="store_true",
                        help="Explicitly allow IP/port disclosure via copyable code")
    decode = sub.add_parser("inspect", help="Decode as UNTRUSTED contact only")
    decode.add_argument("code")
    decode.add_argument("--at", type=int,
                        help="Optional UNIX-second validity check")
    args = parser.parse_args()
    try:
        if args.action == "create":
            if not args.acknowledge_address_disclosure:
                raise InviteError("refusing to expose IP addresses without consent")
            fields = {"v": 0, "peer_key": args.peer_key, "nonce": args.nonce,
                      "valid_from": args.valid_from, "valid_until": args.valid_until,
                      "sim_sha256": args.sim_sha256,
                      "endpoints": [parse_endpoint(x) for x in args.endpoint]}
            if args.recipient_key:
                fields["recipient_key"] = args.recipient_key
            if args.reply_to:
                fields["reply_to"] = args.reply_to
            code = make_code(fields)
            print(make_link(code) if args.link else code)
        else:
            # Default to current time: old contact information is not a
            # presently usable invitation. --at supports historical vectors.
            fields = read_code(args.code, now=(
                args.at if args.at is not None else int(time.time())))
            print(json.dumps({"trust": "UNAUTHENTICATED_OFFLINE_RESEARCH_ONLY",
                              "contact": fields}, sort_keys=True, indent=2))
    except InviteError as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
