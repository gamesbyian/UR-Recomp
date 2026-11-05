# P1 collective CI candidate: offline manifest pilot

This is the first opt-in implementation step of the plan in [PR #3141](https://github.com/gamesbyian/UR-Recomp/pull/3141). It is **proposal validation only**, not acceptance, and changes no workflows, runner settings, scheduled prompts, broker authorization or release gates.

Run `python3 tools/ci_collective_candidate.py proposed-batch.json` on a **manually supplied** manifest. The script rejects duplicate work IDs/PRs/head SHAs, unexpected fields, invalid source SHA formats, path traversal, and changed-path overlap between two to five members. Example schema:

```json
{
  "schema": 1,
  "batch_id": "UR-CI-PILOT-001",
  "base_sha": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "candidate_sha": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
  "members": [
    {"work_id": "UR-WIDE-07", "pr": 100, "head_sha": "cccccccccccccccccccccccccccccccccccccccc", "changed_paths": ["native/presentation/one.cpp"]},
    {"work_id": "UR-UI-08", "pr": 101, "head_sha": "dddddddddddddddddddddddddddddddddddddddd", "changed_paths": ["native/product/two.cpp"]}
  ]
}
```

These source IDs and PRs are **illustrative**, not a real candidate.

A pass establishes *only* coherent claimed fields. The next P1 step is to fetch the **live** PR heads, work IDs, source ancestry and all changed paths, compare them to this manifest, inspect active writers and dependency conflicts, then independently construct and verify the exact composite source tree. Same-name paths are not the only possible collisions; shared generated outputs, cross-module interfaces and merge conflicts require separate inspection. Unknown dependency or test impact means full applicable tests. Changed source invalidates prior receipts.

P2 must separately prove exact build/PE/ZIP identities, all expected tests and real executed case identities, with negative controls and trustworthy per-consumer isolation. There is no license here to run unmerged code on the owner's HP.

Focused tests: `python3 -m unittest tests.unit.test_ci_collective_candidate`. Retain the existing complete tooling and product checks; no skipped tests acquire acceptance by inclusion in a batch.
