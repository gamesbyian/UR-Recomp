# Read-only release evidence briefing

Run `python3 tools/release_evidence_brief.py --source-sha <40-character-checked-out-commit> --json-out /tmp/release-brief.json --markdown-out /tmp/release-brief.md` after fetching a fresh repository checkout.

This is an agent navigation aid over the **existing** `docs/RELEASE-QUALITY-LEDGER.json`, not a new release authority or validator. It produces a bounded twelve-gate view with the required evidence layer, reference count, explicitly registered witness count, candidate mismatch blockers and an abbreviated ledger next action. Its JSON includes a SHA-256 of the ledger bytes, allowing handoff readers to detect stale packets. It deliberately does **not** fetch GitHub, visit references, open purported witness files, change the ledger, authenticate content, certify physical hardware, or award acceptance. Source mismatches are marked, not silently rebased. Run the existing structural validators separately, and submit candidate-bound independent evidence for human adjudication before changing release status.

Do not use reference counts or witness counts as progress percentages. A referred document can be old, duplicated, or non-authoritative. All twelve gates remain governed by the release quality ledger and its independent-acceptance contract.
