"""Offline multi-checkpoint chain audit, NOT live P2P or durable trust storage.

An independently trusted initial anchor and inviter public key are mandatory.
Refuses ambiguous history rather than treating idempotent repeats as progress.
"""
from signed_checkpoint_anchor_lab import admit, ZERO

def verify_chain(receipts, *, pinned_key, session, initial_anchor=(0,ZERO)):
    if (type(initial_anchor) is not tuple or len(initial_anchor)!=2 or
            type(initial_anchor[0]) is not int or type(initial_anchor[1]) is not str):
        raise ValueError('invalid external high-water anchor')
    if type(receipts) is not list or not receipts or len(receipts)>1024:
        raise ValueError('missing/oversized receipt chain')
    anchor=initial_anchor
    for index, receipt in enumerate(receipts):
        if type(receipt) is not tuple or len(receipt)!=2:
            raise ValueError(f'malformed receipt {index}')
        raw, signature=receipt
        result=admit(raw,pinned_key,signature,session,*anchor)
        if result['admit'] is not True or result['reason']!='signed monotonic checkpoint':
            raise ValueError(f'untrusted/nonprogressing receipt {index}: {result["reason"]}')
        anchor=result['next_anchor']
    return anchor
