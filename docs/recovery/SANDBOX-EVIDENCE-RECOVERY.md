# Recover Evidence Vault bytes when the agent sandbox blocks downloads

**Do not modify sandbox network allowlists or Google Drive permissions to follow this procedure.** The direct agent sandbox may receive proxy 403 responses from Drive and the Actions artifact storage domain. That does not imply a clean GitHub Actions runner cannot retrieve the material. The repository's verified public Drive workflow does the network download *on the runner*.

## Verified access and evidence

- [Evidence Library folder](https://drive.google.com/drive/folders/1t0J4GT0N9PQEJkf2TqDt1P6lbYlLArx2): authenticated Drive listing originally reported 66 direct items; gdown public-folder enumeration in the independent runner test returned 71 entries (not necessarily equivalent).
- [Evidence QA04 H26 pilot](https://drive.google.com/file/d/142bXAi_4D-928Wz7FntyRbVzTYvt_sJZ/view): 28,106,236 bytes, SHA-256 `601d6131f90b427f29c53d0cee5be69cb4bacde467fda45e45b8144d5b18be00`.
- [GitHub Actions proof run 40027157602](https://github.com/gamesbyian/UR-Recomp/actions/runs/40027157602): anonymously downloaded the archive and CRC-checked 33 ZIP members without uploading source files or raw archives.
- [Initial public Incoming bundle transfer](https://github.com/gamesbyian/UR-Recomp/actions/runs/40022473433): ZIP file downloaded and audited, reported zero errors.
- [Recurring Intake workflow](https://github.com/gamesbyian/UR-Recomp/actions/workflows/vault-recurring-intake.yml): scheduled audit and checkpoint/queue artifacts for **Incoming and Evidence independently** after the scoped matrix feature is merged.

## Path A: metadata-only triage (always start here)

Dispatch [Vault Direct Intake](https://github.com/gamesbyian/UR-Recomp/actions/workflows/vault-direct-intake.yml) with:

| Input | For QA04 H26 evidence |
| --- | --- |
| `folder_url` | `https://drive.google.com/drive/folders/1t0J4GT0N9PQEJkf2TqDt1P6lbYlLArx2` |
| `drive_file_id` | `142bXAi_4D-928Wz7FntyRbVzTYvt_sJZ` |
| `download_all` | `false` |
| `stage_sources` | `false` |
| `confirm_source_review` | `false` |

The runner downloads the ZIP and performs bounded source/member crosswalk checks, then prints `UR-TRIAGE-*` lines in the job log via `tools/vault_intake_relay.py`. Agents restricted to GitHub connector reads can consume the **job log** without reaching Drive or the artifact blob host. The normal metadata artifact is optional. Check member names, sizes, equality and provenance before choosing anything to publish. CRC/path limits may fail for archives not admitted by the stricter source crosswalk even though the basic original ZIP CRC proof passed; report this accurately and continue with other candidates.

## Path B: reviewed text-source handoff

Only after verifying the particular archive's rights, secrets/ROM restrictions, original publication holds and intended source files, manually dispatch the same workflow with `stage_sources=true` and `confirm_source_review=true`. The confirmed tool stages bounded, source-like, non-identical candidates; the relay prints `UR-STAGED-BEGIN`, `| `-prefixed UTF-8 lines and `UR-STAGED-END` in the job log. Reconstruct **only** the listed files and check the full SHA-256 and byte count before using them. The relay caps total printed text at 1.5 MB and explicitly marks omitted files; those are **not** recovered just because triage succeeded.

An agent with direct shell access should instead run the public Drive Python downloader locally. An agent with only connectors can read the Actions job log, not binary artifacts. Avoid unreviewed or bulk evidence replay into a publicly readable workflow log. For complex or larger source sets, work in individually reviewed batches; do not publish ROMs, test captures or private media.

## Scope and backlog discipline

Use `vault-recurring-state-evidence` for Evidence candidates and `vault-recurring-state-incoming` for Incoming candidates. Both are metadata/checkpoint artifacts, **not** recovered source. For Inbox, Work Journals and Integrated folders, `vault-direct-intake.yml` accepts a public folder URL, but anonymous access needs its own live check; do not silently expand a scheduled workflow across all six Vault areas.

The agent that previously inspected all 45 Incoming files reported the substantial Incoming bundles were already integrated/superseded and left three small CI-related ZIPs. Recheck its [issue #2088 dispositions](https://github.com/gamesbyian/UR-Recomp/issues/2088) against the latest main rather than repeating the entire round. The principal *newly reachable* target is Evidence, especially H26 QA04 pilot #2076. ROM/private proof and independent physical Windows QA requirements remain separate and **cannot** be satisfied merely by downloading archives.

Preserve each original Drive ID and archive SHA-256, compare member blobs to fresh main and open PRs, then integrate only unique authorized code through standard reviewed PRs. Report source-published, evidence-retained, already-integrated, superseded, or blocked with concrete provenance. Do not modify Drive permissions or discard preserved originals.
