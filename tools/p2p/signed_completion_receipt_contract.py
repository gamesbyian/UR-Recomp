#!/usr/bin/env python3
"""Research-only signed responder-completion receipt validator.

A TCP status string is not evidence that a responder authenticated a session.
The initiator must receive a responder-signed receipt bound to the *entire*
three-message invite/response/initiator-finish transcript before reporting
success. This is a pure validator, not a network connector, trust store,
replay database, durable commit proof, or shipping multiplayer protocol.

The caller supplies an independently authenticated Ed25519 verifier. A
successful return proves only that verifier's assertion and transcript
binding; it does not establish that the responder persisted a replay token.
"""
from __future__ import annotations

import json
import re
from typing import Any, Callable

DOMAIN = b"UR-P2P-RESPONDER-COMPLETION/1\x00"
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
HEX32 = re.compile(r"[0-9a-f]{32}\Z")
HEX128 = re.compile(r"[0-9a-f]{128}\Z")
RECEIPT_KEYS = frozenset(("type", "payload", "signature"))
PAYLOAD_KEYS = frozenset(("version", "responder", "invite_sha256",
                          "response_sha256", "finish_sha256", "challenge_nonce"))


def _hex(value: Any, pattern: re.Pattern[str], field: str) -> str:
    if type(value) is not str or not pattern.fullmatch(value):
        raise ValueError("invalid " + field)
    return value


def completion_message(payload: dict[str, Any]) -> bytes:
    """Canonical domain-separated bytes to be signed by the responder."""
    if type(payload) is not dict or set(payload) != PAYLOAD_KEYS:
        raise ValueError("invalid completion fields")
    if type(payload["version"]) is not int or payload["version"] != 1:
        raise ValueError("invalid completion version")
    for key in ("responder", "invite_sha256", "response_sha256", "finish_sha256"):
        _hex(payload[key], HEX64, key)
    _hex(payload["challenge_nonce"], HEX32, "challenge_nonce")
    return DOMAIN + json.dumps(payload, sort_keys=True, separators=(",", ":"),
                               ensure_ascii=True, allow_nan=False).encode("ascii")


def verify_responder_completion(
    receipt: Any,
    *,
    expected_responder: str,
    invite_sha256: str,
    response_sha256: str,
    finish_sha256: str,
    challenge_nonce: str,
    verify_signature: Callable[[bytes, bytes, bytes], bool],
) -> None:
    """Raise unless an authenticated responder receipt matches this session.

    ``verify_signature(public_key, message, signature)`` MUST perform real
    owner-key signature verification and return literal ``True`` on success.
    It is an externally trusted boundary, not implemented in this model.
    Never treat this function alone as proof of durable replay-token commit.
    """
    if type(receipt) is not dict or set(receipt) != RECEIPT_KEYS:
        raise ValueError("missing signed completion receipt")
    if receipt["type"] != "responder_complete":
        raise ValueError("wrong completion packet type")
    sig = bytes.fromhex(_hex(receipt["signature"], HEX128, "signature"))
    message = completion_message(receipt["payload"])
    expected = {
        "version": 1,
        "responder": _hex(expected_responder, HEX64, "expected_responder"),
        "invite_sha256": _hex(invite_sha256, HEX64, "invite_sha256"),
        "response_sha256": _hex(response_sha256, HEX64, "response_sha256"),
        "finish_sha256": _hex(finish_sha256, HEX64, "finish_sha256"),
        "challenge_nonce": _hex(challenge_nonce, HEX32, "challenge_nonce"),
    }
    if receipt["payload"] != expected:
        raise ValueError("completion transcript mismatch")
    if not callable(verify_signature):
        raise ValueError("missing trusted signature verifier")
    try:
        verified = verify_signature(bytes.fromhex(expected_responder), message, sig)
    except Exception as exc:
        raise ValueError("responder signature invalid") from exc
    if verified is not True:
        raise ValueError("responder signature invalid")
