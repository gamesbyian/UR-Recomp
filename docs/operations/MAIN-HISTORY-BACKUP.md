# Main-history recovery and independent Drive custody

This lane protects the **complete committed history of `main`**, separately
from the existing recovery vault's unpublished candidate ZIPs. It does not
silently expand the five hourly agents or add a subscription. The first
one-shot request is
[20261021-initial.json](backup-requests/20261021-initial.json).

## Creation and validation

[Verified main history backup](https://github.com/gamesbyian/UR-Recomp/actions/workflows/verified-main-history-backup.yml)
runs only when a versioned request under `docs/operations/backup-requests/`
is merged to **main**, or via explicit `workflow_dispatch`. It never runs on
an ordinary source push. The workflow fetches **all ancestors of the main
commit** while avoiding unnecessary remote secondary branches. It creates
one bounded Git bundle and **independently clones** it into a fresh
directory, compares exact source HEAD and ancestry count, and runs
`git fsck --connectivity-only`. The manifest pins a full 40-hex source
commit, number of ancestors, bundle bytes/SHA-256 and the exact restored
commit. This is a real restore drill, not a ZIP file-open check.

The bundle is rejected if it exceeds **650 MiB**. A successful workflow
uploads a temporary GitHub artifact held for **two days**, with no write
permissions. GitHub custody alone does **not** satisfy the independent backup
objective. An existing connected integration agent or the manual integrator
must download that run's exact artifact ZIP through GitHub and upload the
returned file reference into the owner's private Drive
[03 Evidence Library](https://drive.google.com/drive/folders/1t0J4GT0N9PQEJkf2TqDt1P6lbYlLArx2),
then read back the Drive ID, exact file size and available digest evidence.

**Only claim an independently stored backup when the Drive upload succeeds**;
only claim a fully verified Drive restore after downloading **the Drive copy**
and checking the bundle SHA-256 and actual clone. Source-generation
self-verification alone does not prove the Drive copy's integrity. If
Connector artifact download/Drive upload fails, retain the exact failing
operation and report **Drive copy UNKNOWN**; do not delete the original
GitHub artifact or assert durable independent custody.

## Restore procedure

1. Obtain the ZIP **from Drive**, extract
   `UR-Recomp-main-history.bundle` and `manifest.json`.
2. Compare the bundle's `sha256sum` with the manifest's
   `bundle_sha256`; check `bundle_bytes`.
3. `git clone --branch ur-restorable-main UR-Recomp-main-history.bundle recovered`
4. In `recovered`, run `git fsck --no-reflogs --connectivity-only`
   and compare `git rev-parse HEAD` against `source_main_sha`.

If all checks pass, the committed `main` source and its ancestor history
are independently restorable at the pinned commit. Recoveries **do not**
include other unmerged branches, tags, GitHub issue/PR discussions,
review/merge metadata, Actions runs/artifacts, releases, remote Git LFS
content, submodule repositories, Drive files or ChatGPT scheduled tasks.
Those need independent, clearly bounded exports if disaster recovery
requirements expand. **Never call this a complete GitHub account backup.**

The underlying repository has historically been large, so this workflow
is intentionally opt-in and size-capped rather than hourly, daily or
triggered by every merge. A later backup should first verify the last
Drive copy and expiry/restore state, then use a new versioned request; do
not increase artifact retention or runners simply to accumulate archives.
