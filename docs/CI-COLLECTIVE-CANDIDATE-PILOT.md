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

The offline validator establishes *only* coherent claimed fields. It also rejects Windows case-insensitive filename collisions, file-vs-directory path ancestry collisions, reserved DOS path segments and noncanonical Windows filename forms; a boolean is not accepted as JSON schema version 1. A separate, opt-in **read-only live attestation** is now available:

```sh
python3 tools/ci_collective_live.py proposed-batch.json
python3 -m unittest discover -s tests/unit -p 'test_ci_collective_live.py'
```

The live checker uses GitHub's REST API (the `GH_TOKEN` or `GITHUB_TOKEN` environment variable is optional for public rate-limited reads). It fails closed unless current main equals the declared base, all two to five PRs remain open, ready, same-repo and definitely mergeable, every declared head SHA and complete paginated changed-path inventory match GitHub, the actual composite SHA is a commit descended from the base and every member commit, and all member blob SHAs or deleted/renamed file absences are preserved at that composite SHA. It rereads PR heads and main at the end to catch observed races. A first pilot deliberately limits PRs to at most 300 file entries each.

**Important:** these are conservative **merge-based** pilot requirements, so ordinary cherry-picked/squashed composite candidates without the source heads in ancestry are rejected even when semantically equivalent. Construct the composite with actual merge ancestry and preserve all touched file bytes; if a conflict requires changing a member's bytes, stop for manual source reconciliation and a new proposal. A genuine future exception mechanism requires separately reviewed provenance proof.

The live checker **does not** inspect active human/agent writers, prove no unseen changes occur after the second read, assess cross-module/generated-output collisions, qualify workflow check contexts, or verify that tests actually executed. A successful result is source evidence for a frozen candidate, never a green CI badge. The coordinator must inspect active writers and dependency conflicts, and independently review the composite source tree and expected test set. Same-name paths are not the only possible collisions; shared generated outputs, cross-module interfaces and merge conflicts require separate inspection. Unknown dependency or test impact means full applicable tests. Changed source invalidates prior receipts.

P2 must separately prove exact build/PE/ZIP identities, all expected tests and real executed case identities, with negative controls and trustworthy per-consumer isolation. There is no license here to run unmerged code on the owner's HP.

Focused tests: `python3 -m unittest discover -s tests/unit -p 'test_ci_collective_candidate.py'` and `python3 -m unittest discover -s tests/unit -p 'test_ci_collective_live.py'`. Retain the existing complete tooling and product checks; no skipped tests acquire acceptance by inclusion in a batch.
