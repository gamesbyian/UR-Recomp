# Recurring Vault Intake: resumable artifact queue

The [Vault Recurring Intake workflow](../../.github/workflows/vault-recurring-intake.yml)
runs at **23 minutes past every sixth UTC hour** and is also manually dispatchable.
It uses \`tools/vault_scheduled_intake.py\`, \`gdown==6.4.2\`,
the existing public-Drive download helper and current-revision Git blob crosswalk.

## What the automation does

1. Index publicly linked **02 Incoming** (currently 45 direct files).
2. Restore the newest checkpoint from the \`vault-recurring-state\` artifact of a
   completed \`main\` workflow run, or start fresh if absent/expired.
3. Prioritize unexamined ZIPs, then other files, then old rechecks.
   Download at most **3 files per scheduled run** (12 hard maximum) and enforce
   a **64 MiB accepted-byte budget** (128 MiB hard upper bound). Original
   downloads are confined to the ephemeral runner. A file whose downloaded
   size breaches the remaining batch budget is deferred, not credited.
4. Audit downloaded ZIP/member paths, size/CRC, nested archives to the bounded
   crosswalk depth, member SHA-256 and exact Git-blob matches against the
   checkout revision. Error cases remain unaudited and eligible for retry.
5. Upload the metadata-only artifact \`vault-recurring-state\` containing:
   - \`report.json\`: that run's successes, failures, deferred work, SHA-256,
     sizes and ZIP-member hash inventory.
   - \`checkpoint.json\`: last verified date, byte count, SHA-256 and exact
     blob observation per Drive ID.
   - \`queue.json\`: unaudited file IDs, failed downloads, and existing
     unmatched/source-like **review leads** for recovery agents.

The checkpoint is not a semantic integration ledger. ZIP member names and
blob hashes may provide leads, **not rights or publication permission**.
Archives can be changed under the same Drive ID: every verified file becomes
eligible for re-download after 14 days, or at any time with a manual
\`file_id\` probe. A renamed file ID/path is also rechecked. Checkpoint
artifacts expire after 90 days, so a long idle interval may cause
re-auditing. GitHub can delay or skip scheduled runs; do not promise exact
clock delivery.

## Explicit boundaries

- Only the public Incoming folder is indexed. Other Vault folders (including
  the Evidence Library holding the 28 MB H26 QA04 pilot) require their own
  authorized access method; this workflow does not bypass folder permissions.
- No original ZIPs, unpacked source, ROMs, proprietary assets or secret-bearing
  files are included in automatic artifacts or Git commits.
- The workflow has \`contents: read\` and \`actions: read\` only. It cannot
  publish branches, issue comments, open PRs, move Drive files, delete records
  or modify the release ledger.
- ZIP/member equality is byte evidence only. It is not a semantic
  supersession or approval for public redistribution.
- Compressed input is bounded to 64 MiB per archive and the existing member
  inspector bounds expanded totals. The total-run budget is an *accepted-byte*
  budget, not a hard limit on download network transfer, because public folder
  enumeration does not expose trusted content lengths in advance.
- A failed file does not poison the checkpoint. The run reports the error
  and exits nonzero after preserving its successful items.
- Concurrent intake executions are serialized through a single workflow
  concurrency group; other project CI remains unaffected.

## How recovery agents consume results

Open [Actions: Vault Recurring Intake](https://github.com/gamesbyian/UR-Recomp/actions/workflows/vault-recurring-intake.yml).
Select the newest completed \`main\` run, download \`vault-recurring-state\`,
and begin with \`queue.json\` and \`report.json\`. The candidate queue is
advisory; inspect original source via direct Python download in a shell
environment, or the *separate, explicitly reviewed* staging option in the
[manual Direct Intake workflow](DIRECT-VAULT-INTAKE.md).

Compare each reviewed member against **fresh main, active PRs and rights /
publication holds**, then create focused implementation/test PRs as permitted.
Record per-ID dispositions in [#2088](https://github.com/gamesbyian/UR-Recomp/issues/2088).
Do not use a checkpoint record as evidence that a PR was merged or a Vault
item can be deleted.

## Verification and live smoke

The recurring workflow's \`pull_request\` trigger applies only to changes in
its workflow, Python code or tests. It runs local tests and attempts the known
**4.65 MB** H26 five-line recovery ZIP ID
\`1kULfQIJSV-YJ1lwWBPJAnH6iLtzt5W9d\` in inventory/verification-only
mode. This intentionally bypasses the historical checkpoint and never stages
source. If the package is malformed or inaccessible, the run reports an error
rather than claiming it is integrated.

The initial [direct-transfer proof run](https://github.com/gamesbyian/UR-Recomp/actions/runs/40022473433)
downloaded a separate 2,688-byte ZIP with zero reported errors. Neither proof
constitutes large-Evidence-folder coverage.

## Manual operation

GitHub Actions → Vault Recurring Intake → Run workflow. Choose a bounded
\`max_files\` (1, 2, 3, or 6) and optionally a known \`file_id\`.
The checkpoint is automatically restored on \`main\`; a supplied \`file_id\`
forces reinspection even if recently verified. The manual workflow still
cannot publish source.

Local (with a checkout and gdown installed):

\`\`\`bash
python -m pip install 'gdown==6.4.2'
python -m unittest tests.unit.test_vault_scheduled_intake -v
python tools/vault_scheduled_intake.py --out /tmp/ur-vault-recurring
python tools/vault_scheduled_intake.py \
  --previous /tmp/ur-vault-recurring/checkpoint.json \
  --out /tmp/ur-vault-resumed
\`\`\`

Never reuse an existing \`--out\` directory.
