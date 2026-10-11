#!/usr/bin/env python3
"""Deterministic R4 preflight policy checks; NO live network or cryptography."""
from pathlib import Path
import importlib.util
import unittest

SOURCE = Path(__file__).resolve().parents[2] / 'tools/p2p/overlay_reconstitution_lab.py'
spec = importlib.util.spec_from_file_location('urp_r4_preflight', SOURCE)
assert spec and spec.loader
lab = importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name] = lab
spec.loader.exec_module(lab)


class R4ExtinctionPreflight(unittest.TestCase):
    def setUp(self):
        self.nodes = {n: lab.Node(n, f'198.51.100.{i}', 'sim-a', share_contact=True)
                      for i, n in enumerate('ABCDE', 1)}
        self.world = lab.World(self.nodes,
            {frozenset(x) for x in [('A','B'), ('A','C'), ('B','C'),
                                   ('C','D'), ('D','E')]}, now=10000)

    def test_zero_bootstrap_reconstitutes_with_manual_contact_then_third(self):
        w = self.world
        w.extinction()
        self.assertEqual(w.connect('A','B'), lab.Outcome.UNKNOWN)
        self.assertTrue(w.manual_exchange('A','B'))
        self.assertEqual(w.connect('A','B'), lab.Outcome.CONNECTED)
        self.assertTrue(w.manual_exchange('B','C'))
        self.assertEqual(w.connect('B','C'), lab.Outcome.CONNECTED)
        self.assertEqual(w.exchange_contacts('A','B'), 1)
        self.assertEqual(w.connect('A','C'), lab.Outcome.CONNECTED)
        self.assertEqual(lab.no_service_scenario(), {
            'without_contact': lab.Outcome.UNKNOWN.value,
            'manual_ab': lab.Outcome.CONNECTED.value,
            'manual_bc': lab.Outcome.CONNECTED.value,
            'pex_records': 1,
            'discovered_ac': lab.Outcome.CONNECTED.value,
            'mandatory_service_contacts': 0,
            'network_sessions_proven': 0,
        })

    def test_consent_is_not_global_and_no_automatic_peer_exposure(self):
        w=self.world
        self.nodes['C'].share_contact=False
        self.assertTrue(w.manual_exchange('A','B'))
        self.assertTrue(w.manual_exchange('B','C'))
        self.assertEqual(w.connect('A','B'), lab.Outcome.CONNECTED)
        self.assertEqual(w.connect('B','C'), lab.Outcome.CONNECTED)
        self.assertEqual(w.exchange_contacts('A','B'), 0)
        self.assertEqual(w.connect('A','C'), lab.Outcome.UNKNOWN)
        self.assertNotIn('C', self.nodes['A'].contacts)

    def test_unreachable_manual_and_pex_are_not_magical_nat_traversal(self):
        w=self.world
        self.assertTrue(w.manual_exchange('A','E'))
        self.assertEqual(w.connect('A','E'), lab.Outcome.UNREACHABLE)
        self.assertFalse(self.nodes['A'].connected)
        self.nodes['B'].sim='sim-b'
        self.assertTrue(w.manual_exchange('A','B'))
        self.assertEqual(w.connect('A','B'), lab.Outcome.INCOMPATIBLE)

    def test_isolated_islands_require_out_of_band_bridge(self):
        w=self.world
        w.extinction()
        for a,b in [('A','B'),('D','E')]:
            self.assertTrue(w.manual_exchange(a,b))
            self.assertEqual(w.connect(a,b), lab.Outcome.CONNECTED)
        self.assertEqual(w.connect('D','C'), lab.Outcome.UNKNOWN)
        self.assertTrue(w.manual_exchange('D','C'))
        self.assertEqual(w.connect('D','C'), lab.Outcome.CONNECTED)
        self.assertEqual(w.exchange_contacts('E','D'), 1)
        self.assertEqual(w.connect('E','C'), lab.Outcome.UNREACHABLE)

    def test_ttl_replay_and_changed_endpoint_are_bounded(self):
        w=self.world
        self.assertTrue(w.manual_exchange('A','B'))
        old=self.nodes['A'].contacts['B']
        self.assertFalse(self.nodes['A'].receive(old, w.now))
        self.nodes['B'].endpoint='198.51.100.77'
        self.assertEqual(w.connect('A','B'), lab.Outcome.UNREACHABLE)
        w.now+=1
        self.assertTrue(w.manual_exchange('A','B'))
        self.assertEqual(w.connect('A','B'), lab.Outcome.CONNECTED)
        w.now+=lab.MAX_CONTACT_AGE
        self.assertEqual(w.connect('A','B'), lab.Outcome.UNKNOWN)
        self.assertFalse(self.nodes['A'].receive(old, w.now))

    def test_memory_quotas_and_pex_bounds_are_explicit(self):
        n=self.nodes['A']; now=self.world.now
        for i in range(lab.MAX_CONTACTS):
            self.assertTrue(n.receive(lab.Contact(f'peer{i}', f'10.0.0.{i}', 'sim-a',now,now+100,True),now))
        self.assertFalse(n.receive(lab.Contact('overflow','10.0.0.200','sim-a',now,now+100,True),now))
        self.assertEqual(len(n.contacts),lab.MAX_CONTACTS)
        self.assertFalse(n.receive(lab.Contact('A','10.0.0.1','sim-a',now,now+100,True),now))
        self.assertFalse(n.receive(lab.Contact('expired','10.0.0.1','sim-a',now-200,now-1,True),now))
        self.assertFalse(n.receive(lab.Contact('too-long','10.0.0.1','sim-a',now,now+lab.MAX_CONTACT_AGE+1,True),now))

    def test_pex_limits_even_when_sender_has_more_shareable_contacts(self):
        w=self.world
        a,b=self.nodes['A'],self.nodes['B']
        self.assertTrue(w.manual_exchange('A','B'))
        self.assertEqual(w.connect('A','B'), lab.Outcome.CONNECTED)
        for i in range(lab.MAX_PEX+4):
            self.assertTrue(b.receive(lab.Contact(
                f'extra{i:02}',f'203.0.113.{i+1}','sim-a',w.now,w.now+60,True),w.now))
        self.assertEqual(w.exchange_contacts('A','B'),lab.MAX_PEX)
        self.assertEqual(len(a.contacts),lab.MAX_PEX+1)

    def test_bad_contact_and_same_epoch_substitution_rejected(self):
        w=self.world
        a=self.nodes['A']
        contact=self.nodes['B'].current_contact(w.now)
        self.assertTrue(a.receive(contact,w.now))
        swapped=lab.Contact(contact.peer,'203.0.113.200',contact.sim,
                            contact.issued_at,contact.expires_at,True)
        self.assertFalse(a.receive(swapped,w.now))
        self.assertEqual(a.contacts['B'].endpoint,contact.endpoint)
        self.assertFalse(a.receive(lab.Contact('', '127.0.0.1','sim-a',w.now,w.now+1),w.now))
        self.assertFalse(a.receive(lab.Contact('X','', 'sim-a',w.now,w.now+1),w.now))

    def test_peer_quit_and_refused_invite_do_not_discover(self):
        w=self.world
        self.nodes['B'].invite_accepted=False
        self.assertFalse(w.manual_exchange('A','B'))
        self.nodes['B'].invite_accepted=True
        self.assertTrue(w.manual_exchange('A','B'))
        self.nodes['B'].invite_accepted=False
        self.assertEqual(w.connect('A','B'), lab.Outcome.REJECTED)
        w.disconnect('B')
        self.assertEqual(w.connect('A','B'), lab.Outcome.OFFLINE)
        self.assertNotIn('A',self.nodes['B'].contacts)

if __name__ == '__main__':
    unittest.main()
