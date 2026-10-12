#!/usr/bin/env python3
"""Lossless, bounded, source-epoch-scoped frontier fingerprint/witness census.

Counts are exact for the stored 96-bit *normalized fingerprint identities*.
SHA-256 truncated fingerprints are not a proof of collision-free raw state
identity, original-SNES parity, complete events or release acceptance.
Legacy HLL-only campaigns are excluded rather than retroactively counted.
"""
from __future__ import annotations

import base64
import hashlib
import re
import struct
import zlib

import qa_frontier_coverage as coverage

SCHEMA = "ur-frontier-exact-witness-census/1"
ARMS = ("balanced", "p1-focus", "p2-focus", "alternating", "rotation")
RUN_WIDTH = 18  # 12 token + uint32 seed + uint8 arm + uint8 shard
LEDGER_WIDTH = 26  # run record plus uint64 GitHub run ID
MAX_RUN_TOKENS = 30000
MAX_CUMULATIVE_TOKENS = 1000000
HEX = re.compile(r"^[0-9a-f]{24}$")


def _unpack(encoded: str, width: int, maximum: int) -> bytes:
    if not isinstance(encoded, str) or len(encoded) > maximum * width * 2 + 1024:
        raise ValueError("invalid bounded exact census encoding")
    try:
        compressed = base64.b64decode(encoded, validate=True)
        dec = zlib.decompressobj()
        raw = dec.decompress(compressed, maximum * width + 1)
        if (len(raw) > maximum * width or not dec.eof or
                dec.unconsumed_tail or dec.unused_data or len(raw) % width):
            raise ValueError("invalid or oversized exact census payload")
    except (ValueError, zlib.error, base64.binascii.Error) as exc:
        raise ValueError("invalid exact census compression") from exc
    if base64.b64encode(compressed).decode("ascii") != encoded:
        raise ValueError("noncanonical exact census base64")
    return raw


def _pack(raw: bytes) -> str:
    return base64.b64encode(zlib.compress(raw, level=9)).decode("ascii")


def _parse(encoded: str, cumulative: bool) -> dict[str, tuple[int, str, int] | tuple[int, int, str, int]]:
    width = LEDGER_WIDTH if cumulative else RUN_WIDTH
    maximum = MAX_CUMULATIVE_TOKENS if cumulative else MAX_RUN_TOKENS
    raw = _unpack(encoded, width, maximum)
    records = {}
    last = b""
    for pos in range(0, len(raw), width):
        item = raw[pos:pos + width]
        token = item[:12]
        if last and token <= last:
            raise ValueError("duplicate or unsorted exact fingerprint")
        last = token
        if cumulative:
            run_id, seed, arm, shard = struct.unpack(">QIBB", item[12:])
            if run_id == 0:
                raise ValueError("invalid original witness run")
            records[token.hex()] = (run_id, seed, ARMS[arm] if arm < len(ARMS) else "", shard)
        else:
            seed, arm, shard = struct.unpack(">IBB", item[12:])
            records[token.hex()] = (seed, ARMS[arm] if arm < len(ARMS) else "", shard)
        if arm >= len(ARMS) or shard >= 40 or seed > 99999999:
            raise ValueError("invalid source witness seed/arm/shard")
    return records


def _serialize(records: dict, cumulative: bool) -> str:
    if len(records) > (MAX_CUMULATIVE_TOKENS if cumulative else MAX_RUN_TOKENS):
        raise ValueError("exact census capacity exceeded: shard/archive before new runs")
    out = bytearray()
    for token in sorted(records):
        if not isinstance(token, str) or not HEX.fullmatch(token):
            raise ValueError("invalid exact source fingerprint")
        witness = records[token]
        if cumulative:
            if (not isinstance(witness, (tuple, list)) or len(witness) != 4):
                raise ValueError("invalid cumulative exact witness")
            run_id, seed, arm, shard = witness
            if type(run_id) is not int or run_id <= 0 or run_id >= 2**64:
                raise ValueError("invalid witness run identifier")
            out.extend(bytes.fromhex(token) + struct.pack(">QIBB", run_id, seed, ARMS.index(arm), shard))
        else:
            if (not isinstance(witness, (tuple, list)) or len(witness) != 3):
                raise ValueError("invalid source-run exact witness")
            seed, arm, shard = witness
            out.extend(bytes.fromhex(token) + struct.pack(">IBB", seed, ARMS.index(arm), shard))
    return _pack(bytes(out))


def encode_run(records: dict[str, tuple[int, str, int]]) -> str:
    result = _serialize(records, False)
    if _parse(result, False) != records:
        raise ValueError("noncanonical or invalid source-run witnesses")
    return result


def observed_report(report: dict, base_seed: int, cases: int, shards: int) -> dict:
    if report.get("semantic_epoch") != coverage.EPOCH:
        raise ValueError("incompatible source-field epoch")
    seen = _parse(report.get("semantic_exact_witnesses_b64"), False)
    if (len(seen) != report.get("semantic_bins_observed") or
            len(seen) > 3 * cases or not seen):
        raise ValueError("exact source fingerprint count inconsistent")
    for seed, arm, shard in seen.values():
        if not base_seed <= seed < base_seed + cases or shard >= shards:
            raise ValueError("exact witness outside planned source population")
    # The old sketch is now cross-checked against the complete lossless set,
    # rather than accepted with a 15% statistical tolerance.
    if coverage.encode(coverage.observe(set(seen))) != report.get("semantic_hll_b64"):
        raise ValueError("source HLL does not match exact fingerprint population")
    return seen


def validate_record(record: dict) -> dict:
    if (type(record) is not dict or record.get("schema") != SCHEMA
            or record.get("semantic_epoch") != coverage.EPOCH
            or record.get("release_gate_credit") != 0
            or record.get("original_native_parity_claimed") is not False
            or record.get("legacy_sketch_campaigns_excluded") is not True
            or type(record.get("updates")) is not int or record["updates"] < 1
            or type(record.get("real_cases_observed")) is not int
            or record["real_cases_observed"] < record["updates"]
            or type(record.get("exact_unique_observed_fingerprints")) is not int):
        raise ValueError("invalid exact cumulative census contract")
    seen = _parse(record.get("witnesses_b64"), True)
    if len(seen) != record["exact_unique_observed_fingerprints"]:
        raise ValueError("exact census count disagrees with lossless witness set")
    unsigned = {k: v for k, v in record.items() if k != "record_sha256"}
    if record.get("record_sha256") != coverage.checksum(unsigned):
        raise ValueError("modified exact census ledger signature")
    return seen


def make_record(prior: dict | None, observed: dict, run_id: int, cases: int) -> tuple[dict, dict]:
    if (type(run_id) is not int or run_id <= 0 or
            type(cases) is not int or not 1 <= cases <= 10000):
        raise ValueError("invalid actual source research cohort identity")
    old = validate_record(prior) if prior is not None else {}
    prior_cases = prior["real_cases_observed"] if prior is not None else 0
    updates = prior["updates"] if prior is not None else 0
    merged = dict(old)
    for token, (seed, arm, shard) in observed.items():
        merged.setdefault(token, (run_id, seed, arm, shard))
    value = {
        "schema": SCHEMA,
        "semantic_epoch": coverage.EPOCH,
        "witnesses_b64": _serialize(merged, True),
        "exact_unique_observed_fingerprints": len(merged),
        "real_cases_observed": prior_cases + cases,
        "updates": updates + 1,
        "legacy_sketch_campaigns_excluded": True,
        "release_gate_credit": 0,
        "original_native_parity_claimed": False,
    }
    value["record_sha256"] = coverage.checksum(value)
    delta = {
        "exact_prior_unique_fingerprints": len(old),
        "exact_new_unique_fingerprints": len(merged) - len(old),
        "exact_post_unique_fingerprints": len(merged),
        "exact_counts_exclude_legacy_hll_only_runs": True,
        "fingerprint_identity_does_not_prove_raw_state_or_original_game_parity": True,
    }
    return value, delta


def lookup_witness(ledger: dict, token: str) -> dict:
    """Resolve an exact observed fingerprint to its first retained source run."""
    if not isinstance(token, str) or not HEX.fullmatch(token):
        raise ValueError("expected an exact 24-character lowercase source fingerprint")
    seen = validate_record(ledger.get("frontier_exact_coverage"))
    if token not in seen:
        raise ValueError("fingerprint was not observed in the post-upgrade exact corpus")
    run_id, seed, arm, shard = seen[token]
    matching = [r for r in ledger.get("records", [])
                if r.get("github_run_id") == run_id and
                r.get("campaign") == "frontier"]
    if len(matching) != 1:
        raise ValueError("first-witness source run is missing or ambiguous")
    row = matching[0]
    if (row.get("origin") != "coordinator" or
            row.get("disposition") != "completed_positive" or
            not re.fullmatch(r"[0-9a-f]{40}", str(row.get("source_sha", ""))) or
            row.get("record_sha256") != coverage.checksum({
                k: v for k, v in row.items() if k != "record_sha256"
            }) or not row.get("metrics", {}).get("exact_new_unique_fingerprints", 0) > 0):
        raise ValueError("witness points to an unqualified or tampered source run")
    return {
        "fingerprint": token,
        "source_sha": row["source_sha"],
        "github_run_id": run_id,
        "github_run_url": f"https://github.com/gamesbyian/UR-Recomp/actions/runs/{run_id}",
        "seed": seed,
        "arm": arm,
        "shard": shard,
        "evidence": "normalized native checkpoint only; original/native parity unverified",
        "release_gate_credit": 0,
    }


if __name__ == "__main__":
    import argparse
    import json
    from pathlib import Path

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", required=True, type=Path)
    parser.add_argument("--fingerprint", required=True)
    args = parser.parse_args()
    report = lookup_witness(json.loads(args.ledger.read_text(encoding="utf8")),
                            args.fingerprint)
    print(json.dumps(report, indent=2, sort_keys=True))
