"""Offline P2P chain verifier bound to a separately trusted session/key anchor.

No durable storage, no network transport, and no automatic key rotation.
The external anchor must be stored independently of all checkpoint files.
"""
import hashlib
import re
from checkpoint_chain_audit import verify_chain


def verify_context_bound_chain(receipts, *, pinned_key, session, trusted_context):
    if (type(pinned_key) is not bytes or len(pinned_key)!=32 or
            type(session) is not str or re.fullmatch(r'[0-9a-f]{32}',session) is None):
        raise ValueError('missing pinned inviter identity or session')
    if type(trusted_context) is not dict or set(trusted_context)!={
            'session','inviter_key_sha256','revision','digest'}:
        raise ValueError('missing independent context anchor')
    if (trusted_context['session']!=session or
            trusted_context['inviter_key_sha256']!=hashlib.sha256(pinned_key).hexdigest()):
        raise ValueError('checkpoint context or inviter identity changed')
    revision=trusted_context['revision'];digest=trusted_context['digest']
    if (type(revision) is not int or not 0<=revision<2**64 or
            type(digest) is not str or re.fullmatch(r'[0-9a-f]{64}',digest) is None):
        raise ValueError('invalid independent high-water anchor')
    result=verify_chain(receipts,pinned_key=pinned_key,session=session,
                        initial_anchor=(revision,digest))
    return {'session':session,'inviter_key_sha256':trusted_context['inviter_key_sha256'],
            'revision':result[0],'digest':result[1]}
