# Read-only release evidence briefing

Run `python3 tools/release_evidence_brief.py --source-sha <40-character-checked-out-commit> --json-out /tmp/release-brief.json --markdown-out /tmp/release-brief.md` after fetching a fresh repository checkout.

This is an agent navigation aid over the **existing** `docs/RELEASE-QUALITY-LEDGER.json`, not a new release authority or validator. It produces a bounded twelve-gate view with the required evidence layer, reference count, explicitly registered witness count, candidate mismatch blockers and an abbreviated ledger next action. Its JSON includes a SHA-256 of the ledger bytes, allowing handoff readers to detect stale packets. It deliberately does **not** fetch GitHub, visit references, open purported witness files, change the ledger, authenticate content, certify physical hardware, or award acceptance. Source mismatches are marked, not silently rebased. Run the existing structural validators separately, and submit candidate-bound independent evidence for human adjudication before changing release status.

Do not use reference counts or witness counts as progress percentages. A referred document can be old, duplicated, or non-authoritative. All twelve gates remain governed by the release quality ledger and its independent-acceptance contract.

## Source-to-source handoff comparison

Generate one immutable JSON briefing from each specific source checkout, with a
real 40-character commit SHA, then compare them using:

    python3 tools/release_evidence_delta.py --before /tmp/previous-brief.json --after /tmp/current-brief.json --json-out /tmp/brief-delta.json --markdown-out /tmp/brief-delta.md

The comparator refuses foreign schemas, invalid fingerprints, malformed gate
inventories and claimed authority other than diagnostic-only. It reports
changes in the nominated source, ZIP identity, checked source, gate statuses,
layers, reference/witness counts, blocker flags and bounded next actions. It
also flags unexplained ledger-byte changes that leave all tracked fields
unchanged. Equal reference or witness counts **do not** imply equal evidence
identity, contents, authenticity or acceptance.

The agent-context generator now includes a bounded read-only view for each
relevant lane. The local checkout HEAD is compared with the ledger nominee;
a missing Git HEAD is displayed as unknown, never as a match. Neither the
context packet nor the delta comparator reads external witnesses or changes
the acceptance ledger. Use existing validators and independent review before
any release decision.

## One bounded agent action handoff

From an unchanged tracked checkout:

    python3 tools/agent_action_handoff.py release-qa --gate QA-02 \
      --json-out /tmp/agent-handoff.json \
      --markdown-out /tmp/agent-handoff.md

The new command reads the existing release ledger and lane authorities
without creating new acceptance status. Explicit \`--gate\` is required to
suggest a concrete evidence-navigation decision; without it, the command
only lists relevant gates and asks the agent to reconcile ownership first.
The live hourly board and active PRs, not lane names or this tool, determine
who is allowed to modify files or run work.

To inspect source changes since a *verified ancestor commit*, add
\`--since FULL_40_CHARACTER_SHA\`. The handoff checks Git ancestry and
rejects a dirty tracked working tree; no baseline means the change state
is **unknown**, not "zero changes". It gives total changed-path count,
a bounded list of changed paths, and a few commit subjects. These Git
changes are not proof of tests or gameplay parity.

For source-bound release-ledger metadata differences, also provide
\`--previous-brief /private/earlier-brief.json\` (produced by
\`tools/release_evidence_brief.py\` from that exact \`--since\` checkout).
The CLI rejects a previous brief whose checked source does not equal
\`--since\`. The comparator reports metadata differences and warns when
ledger bytes changed without tracked field changes. Neither the prior
snapshot's asserted provenance nor its registered witness references
are independently authenticated by this command.

The handoff records SHA-256 fingerprints of the queue, hourly agent board,
ledger and lane registry, the full local checkout SHA, nominated release
candidate/ZIP and explicit source-mismatch state. It is an offline
navigation packet and does not query GitHub for open PRs, read private
Windows/ROM evidence, run a guest, dispatch Actions, nominate a release
candidate or accept any gate. Re-read live board/PR/CI before acting;
only independent reviewers may adjudicate release evidence.
