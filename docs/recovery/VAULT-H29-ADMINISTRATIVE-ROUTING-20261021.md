# Vault H29 administrative routing receipt (2026-10-21 UTC)

This is an immutable, **non-deletion** file-location checkpoint for the surviving six-folder UR-Recomp Agent Recovery Vault. It records metadata moves, not code integration or member-level adjudication. Base GitHub main when the routing PR was prepared: `bfc8420e628092e92009334a79a44ef1037f53d4`. Primary source of ongoing dispositions: [recovery index](README.md) and [#2088](https://github.com/gamesbyian/UR-Recomp/issues/2088).

## Direct-child census after routing

| Folder | Before | After |
| --- | ---: | ---: |
| 00 Integration Inbox | 0 | 0 |
| 02 Incoming | 45 | 29 |
| 03 Evidence Library | 21 | 34 |
| 01 Work Journals | 22 | 25 |
| 04 Integrated | 3 | 3 |
| 05 Superseded and Rejected | 0 | 0 |

The six-folder Vault root was already clean (six folders, no root files). Evidence's Git-history-backup subfolder is one direct child; its six backup items are nested and are not included as six Evidence direct children. The owner's **387 deliberately retired** old file IDs are excluded from all counts and any recovery work.

## Verified metadata moves, preserving exact Drive IDs

All sixteen files had their original `02 Incoming` parent `1cdovDqle9IRYKX2lCt513mtWge75HywX` independently read before the move. Each provider `files.update` returned `success=true`, the **same file ID** and the new sole parent; complete destination/source folder listings were rechecked afterward. The moves did not replace bytes, edit file contents, delete files, classify research as integrated, or alter publication holds.

| Destination | Exact Drive file IDs | Content class |
| --- | --- | --- |
| 03 Evidence Library (`1t0J4GT0N9PQEJkf2TqDt1P6lbYlLArx2`) | `1xA87vH9t79JTTBAwuD7g0jkpEcnTGf0J`, `1wleOh5FiXCB3OYt2X9RT6SUBj_Eg5QuB`, `1wpOXADiVplvrVqBmk0mz1PKqp0uAP7Bs`, `1lNvFQlF7_N3ZDRW30-LkTiwwG6YVTjiU` | Previous-run preflight JSON |
| 03 Evidence Library | `18Vf9dPLyfQlF_kUmmht2VPagaGXgGoiM`, `1UTGnCrqeEn_NV4_f44S0NHU7-WUzfXPc`, `1tqa8vFBWAbt5oi1B8fHmMpoSv2ogzznV`, `1qHkSTILSJbYzQAV2s1wAm-CeYDgdvZbA` | Prior cross-check, addendum, readback and resolution JSON |
| 03 Evidence Library | `1JNvMAuPBkP273XGJRdJ4x51kLW5FLiAo`, `1XnBXvWsM9mDyy3xsfKt_dHkfVNGE84QE`, `1IYBwv_OWk7aKfhvNfDeQUSLP7HaqXbD1`, `1kcgSq7omzpxsLqPUzFuQNAejtYzqhVO9`, `1ngXWIRgzx-x0GK3FeLOUXw35dTndSpyQ` | Earlier PR reconciliation, readback, publication/results and preserved H25 manifest |
| 01 Work Journals (`1QvlB3V-aa8so0HPx_1dTcV8jL9TeD3kr`) | `1VWLJUbPTFtc6EnyRLX5c0Zz6Zc8w0b7i`, `1ghvPj6jRluWgJP5Dw7lz96TB5I6PdyxQ`, `1kdTXTJScqcls0hA3KFslXvw54tZQcgZ7` | H25/H26 handoff and continuation Markdown |

The remaining **29** Incoming direct children consist of 21 ZIP recovery/source archives, three source patch files and five candidate JSON manifests. These are **not 29 independently missing implementations**. Each needs a source/member-level disposition under #2088; the absence of Inbox pointers does not award integration or justify deletion.

## Nested Git-history backup: evidence and limitation

Evidence contains `UR-Recomp Git History Backups` (folder `1nfjVLtyQEcOrghqZJnh5XIlS9KvddxA5`). Its direct listing has five ZIP transfer parts (four at 83,886,254 bytes and one at 73,066,754 bytes) plus a 945-byte manifest ZIP. The extracted manifest names source main `7e9a1be4016b7a094c93603e2bad116a7ebf6ba7`, 8,118 history commits, a 408,610,900-byte `git bundle`, and an original self-restore result of `true`. The manifest **explicitly says** `independent_drive_copy_verified=false`.

The manifest's original `independent_drive_copy_verified=false` describes its **creation-time state**. A later independent verification in this pickup downloaded all five actual Drive ZIP parts and the manifest ZIP, tested each CRC, compared all **five** extracted 80 MiB/final-part SHA-256 digests, concatenated the original bytes and matched the full **408,610,900-byte** bundle SHA-256 `322c4841ab82a4ed4434b8f4a442a922c2e78b3e28b6cd31fef014dbbdfbff49`.

The reconstructed Drive bundle was then tested **in a newly initialized bare Git repository** (not the creator's source repo): `git bundle verify` reported a complete history, `git fetch <bundle> refs/heads/ur-restorable-main:refs/heads/restored-main` succeeded, `git rev-parse refs/heads/restored-main` returned **`7e9a1be4016b7a094c93603e2bad116a7ebf6ba7`**, `git rev-list --count` returned **8,118**, and `git fsck --strict --full --no-reflogs` exited zero (the only note was that the fresh bare repository's default `HEAD` still pointed to the unborn `master`, independent of the verified restored ref). `git ls-tree` listed the expected project root. **Drive-byte integrity and independent historical-main cold-restore are now verified.** The original immutable manifest was not altered.

The backup remains a historical `main` backup, not a current complete repository backup: it excludes unmerged refs, PR/issues, Actions artifacts, LFS/submodules and Drive. It contains a copy of historical Git objects and must remain restricted. Do not describe it as independently restored or current-main-complete until an independent Drive-download/concatenation/hash/restore test succeeds.

## Boundary

No GitHub code changes, CI/test execution, ROM source moves, art approval or release/Windows/USA acceptance were performed by this receipt. Existing source-publication safety denials and project owner dispositions remain binding. The next eligible cleanup is member-level triage of retained source archives against exact current main, not another generation of general archive manifests.
