# Direct Google Drive Vault intake (GitHub Actions and local Python)

This is a **transport and triage helper**, not another recovery status authority,
source publication permission, release gate, or alternative to the normal PR
process. It implements a narrowly controlled public-folder intake route without
requiring agents to relay ZIP bytes through chat or connector base64.

## Start here

The manual workflow is [Vault Direct Intake](../../.github/workflows/vault-direct-intake.yml).
The Python implementation is [tools/vault_gdown_intake.py](../../tools/vault_gdown_intake.py).
It uses pinned upstream gdown v6 and the repository's existing ZIP safety and
current Git blob crosswalk. It does not write to GitHub, move Drive files,
delete archives, open PRs, or update the release ledger.

**Live status (2026-10-23):** The owner has enabled public link access for 02 Incoming. GitHub Actions inventory run [40020834318](https://github.com/gamesbyian/UR-Recomp/actions/runs/40020834318) successfully listed **45 direct files, zero errors** and uploaded artifact `vault-direct-intake-report` (ID `12529619027`). This validates listing only, **not** archive download or source staging. [PR #2435](https://github.com/gamesbyian/UR-Recomp/pull/2435) merged the workflow-change PR trigger and `gdown==6.4.2` correction. No permissions changes are requested.

**Owner setup (already completed for 02 Incoming):** share the intended folder as an anonymous-link-accessible folder. The default folder is **02 Incoming**,
ID `1cdovDqle9IRYKX2lCt513mtWge75HywX`. You need not
make the other five Vault folders public. The service must actually permit
anonymous access to files within the shared folder; verify with an
incognito-browser download of a representative, non-sensitive ZIP.

**First run:** GitHub -> Actions -> Vault Direct Intake -> Run workflow.
Leave `drive_file_id` empty, `download_all=false`, `stage_sources=false`.
This creates a **metadata-only** 14-day artifact containing a discovered
ID/path/URL inventory, and makes no downloaded archive public on GitHub.
Compare the inventory against an independent Drive listing before asserting
completeness: gdown's public HTML enumeration is not an authenticated Drive
API inventory.

**Inspect packages:** supply one exact ID as `drive_file_id` and leave
staging disabled. The workflow downloads the ZIP onto its ephemeral runner,
checks bounded archive/member integrity and cross-references source/test
Git blob hashes against checked-out HEAD. The report includes package and
member SHA-256, whether a member is byte-exact on HEAD, and unresolved
candidates. Archive integrity and byte equality are *not* review, semantic
supersession, release acceptance, or permission to delete Drive originals.

**Optional direct handoff:** only after separate rights, credentials, ROM,
historical publication-denial, and source-ownership review of a particular
file ID, select `stage_sources=true` and `confirm_source_review=true`.
The workflow uploads a 3-day **source-only review artifact**, under
the exact Drive ID, with bounded text-like source/test/patch file extensions,
excluding recognized sensitive paths, symlinks, unsafe ZIP member names and
exact Git-blob duplicates. This artifact is visible to people with access to
GitHub Actions artifacts for this repository; in public repositories, assume
it can be retrieved by others. The automated filter is not a substitute for
human authorization and can never prove the contents have no sensitive
information. **Do not stage a package subject to an unresolved explicit
publication refusal without the appropriate authorized review.**

The agent can then fetch this artifact directly from the GitHub workflow run,
reconcile it against **fresh** main and current PRs, run relevant tests, and
open a reviewable narrow branch/PR. Source publication and integration are
separate actions. Never blindly apply an entire ZIP onto main.

**Log relay for connector-only agents:** the workflow also prints a triage summary (`UR-TRIAGE*` lines: per-file ID, size, SHA-256, and per-member size, SHA-256 prefix, source-like and exact-on-main flags) to the job log. When `stage_sources` and `confirm_source_review` are both true it additionally prints the staged UTF-8 source between `UR-STAGED-BEGIN`/`UR-STAGED-END` markers, each content line prefixed with `| ` (strip the prefix to reconstruct; the SHA-256 in the header verifies it), within a 1.5 MB budget. Read the job log through the GitHub connector. This has the same visibility as the review-gated artifact and the same rights/publication-hold review requirement.

## Local invocation

Install gdown 6.4.2. From the repo root:

    python -m pip install 'gdown==6.4.2'
    python tools/vault_gdown_intake.py --out /tmp/ur-vault-index
    python tools/vault_gdown_intake.py --out /tmp/ur-vault-one \
        --file-id EXACT_DRIVE_FILE_ID
    python tools/vault_gdown_intake.py --out /tmp/ur-vault-reviewed \
        --file-id REVIEWED_DRIVE_FILE_ID --stage-sources

Each output path must be new; downloaded archives remain local in
`downloads/` and are **not** part of the upload-artifact paths. The read-only
report is `report.json`; reviewed source copies, if requested, are staged
in `staged/<Drive ID>/`. The workflow supports manual dispatch and a narrowly scoped pull-request inventory smoke trigger (only PRs modifying the workflow YAML). It has
`contents: read` permissions. It does not run on cron. A PR changing the workflow YAML also invokes the inventory-only check; PRs cannot use the reviewed source-staging action. Whole-folder download is an explicit optional audit,
bounded to 64 MiB per file and 128 MiB per run.

## Intended next integration enhancements

After a successful owner-driven intake smoke run, agents can add ID-level
checkpoint/resume, incoming-versus-existing-GitHub semantic classification,
and narrowly authorized draft-PR creation. Keep raw restricted materials out
of the public tree, preserve original Drive IDs, and continue disposition
tracking through [issue #2088](https://github.com/gamesbyian/UR-Recomp/issues/2088).
Do not introduce automatic public publishing or Drive deletion.

## Fresh recovery agent launch checklist

1. Read [Recovery Agent Handoff](RECOVERY-AGENT-DIRECT-INTAKE-HANDOFF.md), [issue #2088](https://github.com/gamesbyian/UR-Recomp/issues/2088), current main and active PRs. Treat dated count snapshots as history.
2. Prefer **direct Python download** in an execution environment with shell access, using the commands above, when a particular Drive ID is known. No agent-mediated base64 transfer is needed. Use a new output path per invocation. Alternatively use the GitHub Actions manual workflow for inventory and single-ID download/report; artifacts only include a report unless explicit review-gated staging is requested.
3. Verify the archive bytes, member identities and repo preimages. Inspect nested ZIPs, encrypted/unsupported files and absent manifests as potential review items rather than claiming success from a top-level listing.
4. Compare against fresh main and open PRs, then create the smallest functional source/test PR. **Do not auto-apply all unmatched source bytes.** An unmatched blob is only a review lead. Move on to the next independent candidate while CI runs.
5. Record per-ID/member dispositions with commit and test evidence in #2088. Preserve Drive source copies; never delete/move items solely because a report was generated.

**Caveat:** the first proven successful run enumerated 45 files but downloaded none. Before treating transfer as production-validated, perform an actual single-ID audit from a runner or local Python using a deliberately selected reviewed package, and verify its outer SHA and ZIP members. Direct folder listing can be incomplete for nested folders; cross-check authenticated Drive inventory.
