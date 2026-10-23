#!/usr/bin/env python3
"""R4 offline monotonic-revision *interface contract*, not persistence/crypto.

A trusted revision is intentionally supplied by an independent durable anchor.
The code does not provide one. Rewinding both checkpoint and anchor remains
undetectable, so this is a bounded design discriminator only.
"""
import json

def adjudicate(checkpoint_revision, trusted_revision, *, checkpoint_present=True,
               trusted_anchor_present=True):
    if not checkpoint_present or not trusted_anchor_present:
        return {'admit':False,'reason':'missing checkpoint or trusted anchor'}
    if type(checkpoint_revision) is not int or type(trusted_revision) is not int or (
        not 1 <= checkpoint_revision < 2**64 or
        not 1 <= trusted_revision < 2**64):
        return {'admit':False,'reason':'invalid revision type or range'}
    if checkpoint_revision < trusted_revision:
        return {'admit':False,'reason':'checkpoint rollback'}
    if checkpoint_revision > trusted_revision:
        return {'admit':False,'reason':'unanchored future checkpoint'}
    return {'admit':True,'reason':'revision matches supplied independent anchor'}

def report():
    return {'schema':'p2p-independent-monotonic-anchor-contract/1',
            'fresh':adjudicate(3,3),'stale':adjudicate(1,3),
            'missing':adjudicate(None,3,checkpoint_present=False),
            'unanchored':adjudicate(3,None,trusted_anchor_present=False),
            'co_rollback_unprovable':adjudicate(1,1),
            'anchor_implementation_exists':False,'authenticated_signature_proof':False,
            'production_network_tested':False,'release_gate_credit':0}
if __name__=='__main__':print(json.dumps(report(),indent=2,sort_keys=True))
