import io
import json
import unittest
from unittest.mock import patch
from tools.find_exact_experiment_run import discover, WORKFLOW

SHA = "a31ec269a0034a8e4412ab8c438583a012a2f6a2"

class Response(io.BytesIO):
    def __enter__(self): return self
    def __exit__(self, *args): self.close()

class ExactDiscoveryTests(unittest.TestCase):
    def test_paginate_and_filter_all_three_fields(self):
        urls = []
        def open_mock(req, timeout):
            urls.append(req.full_url)
            page = len(urls)
            if page == 1:
                runs = [{"id": i, "head_sha": SHA, "event": "pull_request", "name": WORKFLOW}
                        for i in range(100)]
            else:
                runs = [{"id": 999, "head_sha": SHA, "event": "push", "name": "Wrong workflow"},
                        {"id": 44121842871, "head_sha": SHA, "event": "push", "name": WORKFLOW}]
            return Response(json.dumps({"workflow_runs": runs}).encode())
        result = discover(SHA, opener=open_mock)
        self.assertEqual(result["run_id"], 44121842871)
        self.assertEqual(result["page"], 2)
        self.assertEqual(len(urls), 2)
        self.assertIn("page=2", urls[1])

    def test_empty_page_is_exhaustive(self):
        result = discover(SHA, opener=lambda req, timeout: Response(b'{"workflow_runs":[]}'))
        self.assertFalse(result["found"])
        self.assertTrue(result["exhausted"])

    def test_limit_is_not_proof_of_absence(self):
        def full(req, timeout):
            return Response(json.dumps({"workflow_runs": [{"head_sha": "other"}] * 100}).encode())
        result = discover(SHA, opener=full, max_pages=1)
        self.assertFalse(result["exhausted"])

    def test_reject_partial_sha(self):
        with self.assertRaises(ValueError):
            discover("a31ec269")

    def test_reject_malformed_payload(self):
        with self.assertRaises(ValueError):
            discover(SHA, opener=lambda req, timeout: Response(b'{"message":"rate limited"}'))

if __name__ == "__main__":
    unittest.main()
