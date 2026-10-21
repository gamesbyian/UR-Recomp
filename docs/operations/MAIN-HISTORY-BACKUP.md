# Main-history recovery and independent Drive custody

This lane protects the **complete committed history of `main`**, separately
from the existing recovery vault's unpublished candidate ZIPs. It does not
silently expand the five hourly agents or add a subscription. The first request [20261021-initial.json](backup-requests/20261021-initial.json)
proved Git-side restoration but hit the Drive transfer limit. The bounded
chunk-transfer follow-up is
[20261021-chunked.json](backup-requests/20261021-chunked.json).

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

The bundle is rejected if it exceeds **650 MiB**. The current transport also
splits the verified bundle into parts of **at most 80 MiB**. The
`transfer_parts` array in `manifest.json` records exact order, names, bytes
and SHA-256 of each part; concatenation is independently checked against the
full bundle SHA-256 before publication. A successful workflow produces
**one small manifest artifact and one GitHub artifact ZIP per actual part**
(typically five), retained for **two days**, with no write permissions.
Each artifact ZIP wraps exactly one part, keeping the connector download
under its observed **100 MiB** limit. Do not upload a single larger ZIP:
the first full-repository run successfully validated 8,117 commits but its
408,593,426-byte artifact could not cross to Drive (HTTP 413, max
104,857,600 bytes). That initial run is **not a Drive backup**.

An existing connected integration agent or manual integrator downloads each
exact artifact ZIP through GitHub and uploads the connector file references,
plus the manifest artifact, into the owner's private Drive
[03 Evidence Library](https://drive.google.com/drive/folders/1t0J4GT0N9PQEJkf2TqDt1P6lbYlLArx2).
Keep the set together, use stable run/source names and check IDs and sizes.
GitHub custody alone does **not** satisfy independent backup.

**Only claim an independently stored backup when the Drive upload succeeds**;
only claim a fully verified Drive restore after downloading **the Drive copy**
and checking the bundle SHA-256 and actual clone. Source-generation
self-verification alone does not prove the Drive copy's integrity. If
Connector artifact download/Drive upload fails, retain the exact failing
operation and report **Drive copy UNKNOWN**; do not delete the original
GitHub artifact or assert durable independent custody.

## Restore procedure

1. Obtain **all** the per-part ZIPs and the small manifest ZIP **from Drive**,
   and extract their contents into the same clean directory.
2. For every `transfer_parts` entry check filename, byte length and SHA-256,
   in the recorded order. Refuse missing, duplicated, reordered or altered parts.
3. Concatenate the ordered binary part files into
   `UR-Recomp-main-history.bundle`; verify its byte length and SHA-256
   against `bundle_bytes` and `bundle_sha256` in `manifest.json`.
4. `git clone --branch ur-restorable-main UR-Recomp-main-history.bundle recovered`.
   In `recovered` run `git fsck --no-reflogs --connectivity-only` and compare
   `git rev-parse HEAD` against `source_main_sha`.

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
