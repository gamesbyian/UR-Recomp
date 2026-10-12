#!/usr/bin/env python3
"""Bounded probabilistic cross-run state coverage for the adaptive 2P frontier.

A register sketch estimates how many distinct *observed normalized native
state bins* accumulated across campaigns. It never claims original-SNES
correctness, exact uniqueness, newly accepted events or source PPU fidelity.

The source-field normalization schema/epoch must be incremented if the fields,
quantization, checkpoint definitions or digest representation change.
"""
from __future__ import annotations

import base64
import hashlib
import math
import re

SCHEMA = "ur-frontier-hll-coverage/1"
EPOCH = "native2p-semantic-checkpoints-1740-2580-3420-v1"
PRECISION = 12
REGISTERS = 1 << PRECISION
REMAINDER_BITS = 64 - PRECISION
MAX_RANK = REMAINDER_BITS + 1
HEX_TOKEN = re.compile(r"^[0-9a-f]{24}$")
MAX_TOKENS_PER_RUN = 30000


def empty() -> bytes:
    return bytes(REGISTERS)


def validate(value: bytes) -> None:
    if (not isinstance(value, bytes) or len(value) != REGISTERS
            or any(v > MAX_RANK for v in value)):
        raise ValueError("invalid bounded semantic coverage sketch")


def decode(encoded: str) -> bytes:
    if not isinstance(encoded, str) or len(encoded) > 6000:
        raise ValueError("invalid source-state sketch encoding length")
    try:
        data = base64.b64decode(encoded, validate=True)
    except (ValueError, base64.binascii.Error) as exc:
        raise ValueError("invalid source-state sketch encoding") from exc
    validate(data)
    if encode(data) != encoded:
        raise ValueError("noncanonical source-state sketch encoding")
    return data


def encode(value: bytes) -> str:
    validate(value)
    return base64.b64encode(value).decode("ascii")


def observe(tokens: set[str] | list[str] | tuple[str, ...]) -> bytes:
    if not isinstance(tokens, (set, list, tuple)) or len(tokens) > MAX_TOKENS_PER_RUN:
        raise ValueError("unbounded source-state population")
    out = bytearray(REGISTERS)
    for token in tokens:
        if not isinstance(token, str) or not HEX_TOKEN.fullmatch(token):
            raise ValueError("malformed normalized source-state fingerprint")
        h = int.from_bytes(
            hashlib.sha256(bytes.fromhex(token)).digest()[:8], "big")
        index = h >> REMAINDER_BITS
        remainder = h & ((1 << REMAINDER_BITS) - 1)
        rank = REMAINDER_BITS - remainder.bit_length() + 1
        if rank > out[index]:
            out[index] = rank
    return bytes(out)


def union(a: bytes, b: bytes) -> bytes:
    validate(a)
    validate(b)
    return bytes(max(x, y) for x, y in zip(a, b))


def estimate(sketch: bytes) -> float:
    """HLL cardinality, small-range linear-count correction, ~1.625% RSE.

    Returns an *estimate* only. Random sketch errors can make the estimated
    gain zero even when a real new state was observed.
    """
    validate(sketch)
    m = REGISTERS
    alpha = 0.7213 / (1.0 + 1.079 / m)
    raw = alpha * m*m / sum(math.ldexp(1.0, -r) for r in sketch)
    zeros = sketch.count(0)
    if zeros and raw <= 2.5*m:
        return m * math.log(m / zeros)
    return raw


def make_record(prior: dict | None, addition: bytes, cases: int) -> tuple[dict, dict]:
    """A source-matched, tamper-evident fixed-size cumulative coverage state."""
    if type(cases) is not int or not 1 <= cases <= 10000:
        raise ValueError("invalid actual frontier case population")
    validate(addition)
    old = empty()
    old_cases = 0
    old_updates = 0
    if prior is not None:
        validate_record(prior)
        old = decode(prior["registers_b64"])
        old_cases = prior["real_cases_observed"]
        old_updates = prior["updates"]
    merged = union(old, addition)
    before, after = estimate(old), estimate(merged)
    body = {
        "schema": SCHEMA,
        "semantic_epoch": EPOCH,
        "registers_b64": encode(merged),
        "estimated_unique_normalized_states": round(after),
        "real_cases_observed": old_cases + cases,
        "updates": old_updates + 1,
        "release_gate_credit": 0,
        "exact_state_count_claimed": False,
        "original_native_parity_claimed": False,
    }
    body["record_sha256"] = checksum(body)
    delta = {
        "estimated_prior_unique_bins": round(before),
        "estimated_post_unique_bins": round(after),
        "estimated_new_unique_bins": max(0, round(after)-round(before)),
        "hll_expected_relative_error": round(1.04 / math.sqrt(REGISTERS), 5),
        "approximate_not_an_exact_new_case_count": True,
    }
    return body, delta


def checksum(obj: dict) -> str:
    import json
    return hashlib.sha256(json.dumps(
        obj, sort_keys=True, separators=(",", ":")).encode("utf8")).hexdigest()


def validate_record(record: dict) -> None:
    if (type(record) is not dict
            or record.get("schema") != SCHEMA
            or record.get("semantic_epoch") != EPOCH
            or record.get("release_gate_credit") != 0
            or record.get("exact_state_count_claimed") is not False
            or record.get("original_native_parity_claimed") is not False
            or type(record.get("updates")) is not int or record["updates"] <= 0
            or type(record.get("real_cases_observed")) is not int
            or record["real_cases_observed"] < record["updates"]
            or type(record.get("estimated_unique_normalized_states")) is not int
            or record.get("record_sha256") != checksum({
                key: value for key, value in record.items()
                if key != "record_sha256"
            })):
        raise ValueError("tampered or mismatched cumulative source coverage record")
    registers = decode(record["registers_b64"])
    if (abs(record["estimated_unique_normalized_states"] - round(estimate(registers))) > 0
            or record["estimated_unique_normalized_states"] < 0):
        raise ValueError("cumulative source coverage estimate contradicts exact registers")


def observed_report(report: dict) -> bytes:
    if report.get("semantic_epoch") != EPOCH:
        raise ValueError("source observation schema not comparable to stored corpus")
    hll = decode(report.get("semantic_hll_b64"))
    observed = report.get("semantic_bins_observed")
    if type(observed) is not int or not 0 <= observed <= MAX_TOKENS_PER_RUN:
        raise ValueError("invalid source-observed semantic bin population")
    approximation = estimate(hll)
    # For small populations HLL linear-counting is generally close, but
    # allow 15% for deterministic hash collision variance, not exact equality.
    if abs(approximation - observed) > max(20, observed * 0.15):
        raise ValueError("semantic sketch grossly contradicts observed exact cohort")
    return hll
