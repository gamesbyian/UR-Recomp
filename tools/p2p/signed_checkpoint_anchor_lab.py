#!/usr/bin/env python3
"""Isolated P2P signed-checkpoint experiment, NOT a live networking feature.

Assumptions: 32-byte Ed25519 inviter key independently pinned via an out-of-band
channel; trusted local high-water mark is stored durably and not attacker-reset.
Without those assumptions, no rollback-resistance claim is possible.
"""
import hashlib
import json
import math
import re
import struct
import unicodedata
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature

DOMAIN = b'UR-P2P-CHECKPOINT-v1\x00'
ZERO = '0' * 64
MAX_BYTES = 1_048_576


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate key')
        result[key] = value
    return result


def finite_float(token):
    # No cross-language float canonicalization has been standardized for the
    # signed checkpoint wire format. Reject floats rather than sign ambiguity.
    raise ValueError('floating-point checkpoint member is not portable')


def reject_constant(token):
    raise ValueError('nonfinite constant')


def signature_message(session_hex, revision, checkpoint_digest):
    if not isinstance(session_hex, str) or re.fullmatch(r'[0-9a-f]{32}', session_hex) is None:
        raise ValueError('invalid session')
    if type(revision) is not int or not 1 <= revision <= (2**64 - 1):
        raise ValueError('invalid revision')
    if not isinstance(checkpoint_digest, str) or re.fullmatch(r'[0-9a-f]{64}', checkpoint_digest) is None:
        raise ValueError('invalid digest')
    return DOMAIN + bytes.fromhex(session_hex) + struct.pack('>Q', revision) + bytes.fromhex(checkpoint_digest)


def admit(raw, pinned_key, signature, session, prior_revision, prior_digest):
    """Return new trusted anchor or fail closed; never writes persistent state."""
    def fail(reason):
        return {'admit': False, 'reason': reason, 'next_anchor': None}
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_BYTES:
        return fail('missing/oversized checkpoint')
    if type(pinned_key) is not bytes or len(pinned_key) != 32:
        return fail('untrusted inviter key')
    if type(signature) is not bytes or len(signature) != 64:
        return fail('missing signature')
    if type(prior_revision) is not int or prior_revision < 0 or prior_revision >= 2**64:
        return fail('missing/invalid trusted high-water mark')
    if type(prior_digest) is not str or re.fullmatch(r'[0-9a-f]{64}', prior_digest) is None:
        return fail('missing/invalid trusted predecessor digest')
    if prior_revision == 0 and prior_digest != ZERO:
        return fail('genesis predecessor must be the protocol zero digest')
    try:
        parsed = json.loads(raw.decode('utf-8'), object_pairs_hook=unique_keys,
                            parse_float=finite_float, parse_constant=reject_constant)
    except (ValueError, UnicodeDecodeError, RecursionError):
        return fail('malformed checkpoint')
    # A signed digest binds raw bytes, but peers still need a unique wire
    # encoding for a semantic checkpoint. Otherwise whitespace, key order,
    # number spelling and escaped Unicode create distinct signed forks for
    # equivalent JSON objects across independent implementations.
    try:
        canonical = json.dumps(parsed, sort_keys=True, separators=(',', ':'),
                               ensure_ascii=False, allow_nan=False).encode('utf-8')
    except (ValueError, UnicodeEncodeError, RecursionError):
        return fail('noncanonical checkpoint encoding')
    if raw != canonical:
        return fail('noncanonical checkpoint encoding')
    if type(parsed) is not dict or set(parsed) != {'session', 'revision', 'previous_digest', 'contacts'}:
        return fail('invalid checkpoint schema')
    if type(parsed['contacts']) is not list or len(parsed['contacts']) > 1024:
        return fail('invalid contacts')
    # A signed list can still contain contradictory aliases. A consumer that
    # converts contacts to an id-keyed map may pick first/last inconsistently.
    # This remains a pilot: the full contact schema is not shipping policy.
    seen_entries, seen_ids, seen_folded_ids = set(), set(), set()
    for contact in parsed['contacts']:
        if type(contact) is not dict:
            return fail('nonobject contact')
        if 'id' not in contact:
            return fail('contact missing stable id')
        entry = json.dumps(contact, sort_keys=True, separators=(',', ':'),
                           ensure_ascii=False, allow_nan=False)
        if entry in seen_entries:
            return fail('duplicate contact')
        seen_entries.add(entry)
        if 'id' in contact:
            identifier = contact['id']
            if (type(identifier) is not str or not identifier or identifier in seen_ids or identifier.casefold() in seen_folded_ids or
                    identifier != identifier.strip() or
                    unicodedata.normalize('NFC', identifier) != identifier or
                    len(identifier.encode('utf-8')) > 128 or
                    any(unicodedata.category(ch) in ('Cc', 'Cf') for ch in identifier)):
                return fail('ambiguous contact id')
            seen_ids.add(identifier)
            seen_folded_ids.add(identifier.casefold())
    if parsed['session'] != session:
        return fail('session mismatch')
    revision = parsed['revision']
    digest = hashlib.sha256(raw).hexdigest()
    try:
        message = signature_message(session, revision, digest)
    except ValueError:
        return fail('invalid session/revision/digest')
    try:
        Ed25519PublicKey.from_public_bytes(pinned_key).verify(signature, message)
    except (ValueError, InvalidSignature):
        return fail('untrusted signature')
    if revision == prior_revision and digest == prior_digest:
        return {'admit': True, 'reason': 'idempotent anchored checkpoint',
                'next_anchor': (revision, digest)}
    if revision != prior_revision + 1:
        return fail('nonconsecutive or rolled-back revision')
    if parsed['previous_digest'] != prior_digest:
        return fail('untrusted predecessor')
    return {'admit': True, 'reason': 'signed monotonic checkpoint',
            'next_anchor': (revision, digest)}
