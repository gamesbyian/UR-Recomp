#!/usr/bin/env python3
"""Offline direct-rendezvous offer pilot. No socket, STUN, relay or account.

A code may carry a signed public IP:port candidate set and session binding.
It cannot punch symmetric NAT or provide a reachable endpoint without
IPv6/public IP/manual forwarding. Inviter Ed25519 key must be pinned through
the same trusted out-of-band channel as the code; self-signature is not identity.
Recipients must remember used session IDs to reject replay.
"""
import hashlib
import ipaddress
import json
import re
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

DOMAIN=b'UR-DIRECT-RENDEZVOUS-OFFER-v1\x00'
HEX32=re.compile('[0-9a-f]{32}\\Z')
HEX64=re.compile('[0-9a-f]{64}\\Z')
MAX_BYTES=4096
MAX_ENDPOINTS=8
MAX_LIFETIME=600
CLOCK_SKEW=60


def _unique(pairs):
    result={}
    for key,value in pairs:
        if key in result:raise ValueError('duplicate offer JSON key')
        result[key]=value
    return result


def _no_float(value):raise ValueError('floating-point offer value')
def _no_constant(value):raise ValueError('nonfinite offer value')


def _parse(raw):
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_BYTES:
        raise ValueError('missing/oversized offer')
    try:
        obj=json.loads(raw.decode('utf-8'),object_pairs_hook=_unique,
                       parse_float=_no_float,parse_constant=_no_constant)
        canonical=json.dumps(obj,sort_keys=True,separators=(',',':'),
                             ensure_ascii=False,allow_nan=False).encode('utf-8')
    except (ValueError,UnicodeDecodeError,UnicodeEncodeError,RecursionError) as exc:
        raise ValueError('malformed offer') from exc
    if canonical!=raw:raise ValueError('noncanonical offer bytes')
    if type(obj) is not dict or set(obj)!={'version','session','inviter_key','nonce',
                                          'issued','expires','scope','endpoints'}:
        raise ValueError('invalid offer schema')
    if type(obj['version']) is not int or obj['version']!=1:
        raise ValueError('unsupported offer version')
    if any(type(obj[k]) is not str or HEX32.fullmatch(obj[k]) is None for k in ('session','nonce')):
        raise ValueError('invalid session/nonce')
    if type(obj['inviter_key']) is not str or HEX64.fullmatch(obj['inviter_key']) is None:
        raise ValueError('invalid inviter key')
    if (type(obj['issued']) is not int or type(obj['expires']) is not int or
            not 0 <= obj['issued'] < obj['expires'] <= obj['issued']+MAX_LIFETIME):
        raise ValueError('invalid bounded offer lifetime')
    if obj['scope'] not in ('public','lan') or type(obj['scope']) is not str:
        raise ValueError('invalid candidate scope')
    endpoints=obj['endpoints']
    if type(endpoints) is not list or not 1 <= len(endpoints) <= MAX_ENDPOINTS:
        raise ValueError('missing/excess endpoint candidates')
    order=[]
    for endpoint in endpoints:
        if type(endpoint) is not dict or set(endpoint)!={'ip','port'} or type(endpoint['ip']) is not str:
            raise ValueError('invalid endpoint schema')
        try:
            address=ipaddress.ip_address(endpoint['ip'])
        except ValueError as exc:
            raise ValueError('invalid IP candidate') from exc
        # H25 recovered negative: mapped IPv6 is an IPv4 endpoint alias.
        # Keep each signed candidate unambiguous across address families.
        if isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped is not None:
            raise ValueError('IPv4-mapped IPv6 candidate alias')
        if str(address)!=endpoint['ip']:
            raise ValueError('noncanonical IP spelling')
        # H25 supplemental unicast policy (recovered from the Evidence Library):
        # broadcast/reserved IPv4 and unscoped IPv6 link-local or reserved
        # addresses are not peer endpoints even in 'lan' scope.
        if address.version==4 and (
                address==ipaddress.IPv4Address('255.255.255.255') or
                address in ipaddress.IPv4Network('0.0.0.0/8') or
                address in ipaddress.IPv4Network('240.0.0.0/4')):
            raise ValueError('broadcast or reserved IPv4 candidate')
        if address.version==6 and (
                address.is_link_local or (address.is_reserved and not address.is_private)):
            raise ValueError('IPv6 link-local or reserved candidate')
        if (type(endpoint['port']) is not int or not 1 <= endpoint['port'] <= 65535 or
                address.is_unspecified or address.is_multicast or address.is_loopback or
                (obj['scope']=='public' and not address.is_global)):
            raise ValueError('unreachable or nonpublic candidate')
        order.append((address.version,address.packed,endpoint['port']))
    if order!=sorted(set(order)):
        raise ValueError('duplicate/noncanonical endpoint ordering')
    return obj


def verify_offer(raw, signature, pinned_inviter_key, now_unix_seconds, *, used_sessions=frozenset()):
    """Return authenticated endpoint tuple; no connection or reachability claim."""
    obj=_parse(raw)
    if (type(signature) is not bytes or len(signature)!=64 or
            type(pinned_inviter_key) is not bytes or len(pinned_inviter_key)!=32 or
            pinned_inviter_key.hex()!=obj['inviter_key']):
        raise ValueError('missing independent inviter-key pin or signature')
    try:
        Ed25519PublicKey.from_public_bytes(pinned_inviter_key).verify(signature,DOMAIN+raw)
    except (InvalidSignature,ValueError) as exc:
        raise ValueError('untrusted rendezvous signature') from exc
    if type(now_unix_seconds) is not int or not (obj['issued']-CLOCK_SKEW <= now_unix_seconds <= obj['expires']):
        raise ValueError('expired/not-yet-valid rendezvous offer')
    if obj['session'] in used_sessions:
        raise ValueError('replayed rendezvous session')
    return {'session':obj['session'],'scope':obj['scope'],
            'candidates':tuple((x['ip'],x['port']) for x in obj['endpoints']),
            'fingerprint':hashlib.sha256(pinned_inviter_key).hexdigest(),
            'reachable':None,'identity_assurance':'out-of-band-key-pin-only'}
