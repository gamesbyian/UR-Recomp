# Direct Google Drive Vault intake (manual GitHub Actions)

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

**Owner setup:** after reviewing the contents for material that should not
be publicly accessible, share only the necessary Drive folder as
"Anyone with the link" / Viewer. The default folder is **02 Incoming**,
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

## Local invocation

Install gdown 6.0.0. From the repo root:

    python -m pip install 'gdown==6.0.0'
    python tools/vault_gdown_intake.py --out /tmp/ur-vault-index
    python tools/vault_gdown_intake.py --out /tmp/ur-vault-one \
        --file-id EXACT_DRIVE_FILE_ID
    python tools/vault_gdown_intake.py --out /tmp/ur-vault-reviewed \
        --file-id REVIEWED_DRIVE_FILE_ID --stage-sources

Each output path must be new; downloaded archives remain local in
`downloads/` and are **not** part of the upload-artifact paths. The read-only
report is `report.json`; reviewed source copies, if requested, are staged
in `staged/<Drive ID>/`. The workflow is intentionally manual and has
`contents: read` permissions. It does not run on cron or spend resources
unless dispatched. Whole-folder download is an explicit optional audit,
bounded to 64 MiB per file and 128 MiB per run.

## Intended next integration enhancements

After a successful owner-driven intake smoke run, agents can add ID-level
checkpoint/resume, incoming-versus-existing-GitHub semantic classification,
and narrowly authorized draft-PR creation. Keep raw restricted materials out
of the public tree, preserve original Drive IDs, and continue disposition
tracking through [issue #2088](https://github.com/gamesbyian/UR-Recomp/issues/2088).
Do not introduce automatic public publishing or Drive deletion.
