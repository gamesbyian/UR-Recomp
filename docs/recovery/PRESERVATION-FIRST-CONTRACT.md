# Preservation-first publication and independent recovery

Owner decision (2026-10-21): **A failed GitHub write must not cause the loss of tested, unpublished agent work.** This is a durability contract, never a means of evading a policy decision. Assignments remain exclusively in [HOURLY-AGENT-LINES.md](../HOURLY-AGENT-LINES.md).

**Preservation supports publication:** [first-party publication policy](FIRST-PARTY-PUBLICATION-CONTRACT.md). A complete, intact agent-authored archive should reach a reviewable GitHub branch or draft PR after bounded provenance/rights/main checks, not wait for recreated historical experiments. Publish first, apply ordinary merge checks second. Restricted-Drive remote readback is a durability contingency for prior failed writes, not an additional approval gate or reason to mirror successful GitHub work.\n\n## Required checkpoint contract

1. **Prepare before publishing:** preserve exact source/main SHA, changed source and tests, relevant logs, outer SHA-256 and a complete member manifest. Prefer the deterministic offline staging utility in tools/recovery_preservation.py; if unavailable, produce an equivalent byte-preserving package with provenance. Inspect for secrets, personal data and copyrighted ROM/game assets first. Do not call the work durable merely because a patch was described in chat.
2. **For known trouble spots, preserve remotely first:** where the same source family or API operation has suffered previous explicit refusals, or this session has already had failed publication calls, store the lossless package in restricted Vault Incoming before more risky editing. Independently verify its exact Drive ID/parent and re-download ZIP bytes to check outer hash and every manifest member. A pointer or folder listing is not readback verification.
3. **Normal GitHub-first path remains:** for new unblocked work, stage locally, create branch/commit/PR and check exact head. If GitHub succeeds, the PR is the durable record. Do not create routine Drive mirrors or status reports.
4. **Classify actual failures:** timeout, rate limit, 5xx or expired session get at most three total bounded attempts with genuine source revalidation; preimage/409 conflicts require comparison and rebase; unknown errors remain UNKNOWN until the response is recovered. An **explicit safety/policy refusal cannot be retried, disguised or repackaged to evade the restriction**. Preserve the exact attempted operation and error, and request independently authorized code review or escalate a suspected false positive. The refusal is invocation-specific, not a permanent finding about the whole feature.
5. **On nonpublication:** if no verified Drive rescue already exists, upload one complete immutable archive per distinct deliverable to Incoming, independently read back, update its incident/continuation, and place a short actionable pointer in Inbox only if new intake is necessary. If Drive also fails, classify **AT RISK / NOT DURABLY PRESERVED**, keep the best existing session artifact, and explicitly say what cannot be recovered. Never assert a merge, ZIP integrity or success without direct evidence.
6. **Resolve rather than repeat:** an independent reviewer checks current main, exact existing PRs, recovered source/tests and the real engineering need. The reviewer can ship genuinely distinct, independently justified code using normal contribution flow, identify semantic supersession, or keep a documented hold and raise a support ticket. No relabelled payload submission, alternate endpoint trick, or cosmetic rewrite of the rejected operation.

## Machine-checkable incident integrity

The curated `publication-incidents.json` is validated by
`python3 tools/validate_publication_incidents.py` and the
[agent control contract workflow](../../.github/workflows/agent-control-contract.yml)
whenever an incident is changed. The validator ensures distinct incident IDs,
active board work IDs, exact original operation/error, consistent source and
Drive identifiers, no release credit, and no conversion of an explicit policy
denial into an automatic retry. A `verified` byte-readback claim must have
a valid outer SHA-256. This is **offline structural validation only**: it
neither accesses Google Drive nor authenticates a digest, owner, refusal,
independent approval or physical/release evidence. A real receipt still needs
the separately observed Drive download and source comparison in the contract
below. The vault-clearing integration owner retains sole candidate
disposition, Inbox and folder-move ownership; this check is read-only.

## Offline staging and readback

From a local repo checkout:

    python3 tools/recovery_preservation.py stage --root . --out /safe/recovery/candidate.zip --candidate-id stable-candidate-id --work-id UR-CPU-01 --source-main-sha EXACT40HEX --file tools/example.py --file tests/unit/test_example.py

Stage output intentionally says remote_preserved=false. The tool verifies safe bounded members using tools/strict_vault_manifest.py, but **cannot comprehensively screen rights, secrets or other prohibited content**: inspect every included file. After uploading to Incoming via the authorized Drive connector, independently fetch its raw bytes as a local downloaded ZIP and run:

    python3 tools/recovery_preservation.py readback --original /safe/recovery/candidate.zip --downloaded /safe/recovery/downloaded.zip --expected-sha256 EXACT64HEX

This proves supplied downloaded bytes equal original ZIP and revalidates members. It deliberately reports provider_drive_id_independently_verified=false, because its own offline code cannot authenticate the provider. Separately record the real Drive metadata/readback ID and folder from the connector. **Never certify remote preservation until both provider identity and byte checks are complete.**

## Publication incident register and review handoff

The curated [publication incidents](publication-incidents.json) stores distinct known failed operations, original raw error and current preservation status. The [candidate index](agent-candidates.json), current PRs and [#2088](https://github.com/gamesbyian/UR-Recomp/issues/2088) remain the source-disposition authorities, not a duplicate queue. Append new incidents only for genuinely distinct failures; preserve the original refusal when later resolution is achieved. Never count a ZIP, conversation report or green ROM-free test as merged code or release acceptance.

For each unresolved incident record candidate/work ID, exact API operation/target, original response, last known source SHA, archived Drive ID and SHA if available, independent byte readback state, authorized review owner, and next action. Mark unverifiable facts unknown; do not manufacture a successful retry or an actual independent source review.

Monthly, sample unresolved incidents and newly deposited Incoming packages, verify ID and byte integrity where possible, prioritize any AT RISK candidate, and reconcile unique source deliverables rather than file counts. Never seek or restore the 387 intentionally deleted historical Drive files.

**ROM boundary:** [ROM-SAFETY.md](../ROM-SAFETY.md) requires the repository to remain private while original ROM objects are present in its Git history. No ROM or rights-restricted material belongs in rescue archives or PRs. Packaging does not grant source, human, device, art or release acceptance.
