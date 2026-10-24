# Recovery agent: direct intake and integration handoff

**Status as of 2026-10-23:** Public 02 Incoming folder contains 45 direct children. GitHub Actions [run 40020834318](https://github.com/gamesbyian/UR-Recomp/actions/runs/40020834318) validated unauthenticated enumeration with gdown 6.4.2 and zero inventory errors, and produced [inventory artifact](https://github.com/gamesbyian/UR-Recomp/actions/runs/40020834318/artifacts/12529619027). **One real 2,688-byte ZIP was subsequently downloaded and inspected successfully on [run 40022473433](https://github.com/gamesbyian/UR-Recomp/actions/runs/40022473433); reviewed-source staging still requires separate qualification.** PR #2435 merged the fix and workflow-change PR smoke trigger.

**Evidence Library access newly verified (2026-10-23):** A clean GitHub runner downloaded the [28,106,236-byte QA04/H26 evidence ZIP](https://github.com/gamesbyian/UR-Recomp/actions/runs/40027157602), CRC-checked all 33 outer ZIP members, and printed its SHA-256 without any new network permissions, credentials or folder-sharing changes. The previous claim that Evidence was inaccessible to Actions is obsolete. `03 Evidence Library` URL: https://drive.google.com/drive/folders/1t0J4GT0N9PQEJkf2TqDt1P6lbYlLArx2. Use the scope-specific recurring evidence queue or the manual Direct Intake workflow's existing `folder_url` input. GitHub Actions artifacts or Logs are the connector-accessible review relay: direct downloads into the agent sandbox may remain blocked by proxy, so do not repeatedly attempt them.

**Recurring production intake (2026-10-24 UTC):** The first scheduled main run [40063845604](https://github.com/gamesbyian/UR-Recomp/actions/runs/40063845604) listed **45 Incoming and 71 Evidence gdown-enumerated entries**, audited **3 per folder**, transferred **7,862,501 Incoming + 22,151 Evidence accepted bytes**, and reported zero errors. These are enumerator counts, not independently verified direct-child counts, source integrations or branch merges.

- [#2467](https://github.com/gamesbyian/UR-Recomp/pull/2467) **merged** the scheduled-checkpoint restoration condition; earlier schedule runs skipped that step. The *next scheduled production run* must demonstrate restored per-folder checkpoints and positive carry-forward. PR smoke deliberately skips restoration and cannot prove it.
- [#2469](https://github.com/gamesbyian/UR-Recomp/pull/2469) **merged** a six-archive per-folder scheduled allowance (still 64 MiB accepted bytes per job), clearer review-lead summaries, and offline configuration regression coverage. Manual dispatch defaults and PR smoke limits are unchanged.
- [#2470](https://github.com/gamesbyian/UR-Recomp/pull/2470) is the separately tested oversized-package retry-cooldown improvement. Check its live merge state before assuming the behavior is on main.
- Download separate artifact names **`vault-recurring-state-incoming`** and **`vault-recurring-state-evidence`** from the newest completed [main workflow run](https://github.com/gamesbyian/UR-Recomp/actions/workflows/vault-recurring-intake.yml). Each provides `checkpoint.json`, `report.json` and `queue.json`. Review leads are unreviewed candidates, not rights approval, code recovered or release gate credit. Maintain per-member source disposition in [#2088](https://github.com/gamesbyian/UR-Recomp/issues/2088), coordinating with [#2468](https://github.com/gamesbyian/UR-Recomp/issues/2468) for verified-queue-to-PR automation.

## Mission
Recover useful first-party source and tests from the currently surviving Drive Vault into focused GitHub PRs with minimal manual byte transport. Treat the Vault as preservation, not as a release gate or separate project board. Prioritize unique, relevant Windows x64 product, modern UI/menus and independent release-validation code. Avoid colliding with current scheduled/Claude owner lanes. This is end-to-end integration work, not an inventory-only assignment.

## Read-first authorities
- Root `AGENTS.md`, `docs/WORK-QUEUE.md`, `docs/HOURLY-AGENT-LINES.md` and `docs/AGENT-COORDINATION.md`
- `docs/recovery/FIRST-PARTY-PUBLICATION-CONTRACT.md`, `docs/recovery/GITHUB-FIRST-PUBLICATION-RUNBOOK.md`, `docs/recovery/DIRECT-VAULT-INTAKE.md`
- `docs/recovery/README.md` and issue [#2088](https://github.com/gamesbyian/UR-Recomp/issues/2088), latest comments
- Live PRs, current main, source and unit tests before writing

## Direct transport (no conversational base64 bridge)
[02 Incoming](https://drive.google.com/drive/folders/1cdovDqle9IRYKX2lCt513mtWge75HywX) is the first source. Use `tools/vault_gdown_intake.py` with `gdown==6.4.2`. Prefer a shell runner and a fresh checkout of latest main:

```bash
python -m pip install 'gdown==6.4.2'
python tools/vault_gdown_intake.py --out /tmp/ur-index
python tools/vault_gdown_intake.py --out /tmp/ur-one --file-id EXACT_DRIVE_ID
# Only after rights/privacy and publication-hold review for the specific archive:
python tools/vault_gdown_intake.py --out /tmp/ur-reviewed --file-id REVIEWED_ID --stage-sources
python -m unittest tests.unit.test_vault_gdown_intake -v
```

The [manual Evidence/Incoming relay instructions](SANDBOX-EVIDENCE-RECOVERY.md) explain exact workflow inputs, traceable logs and review boundaries for tool-only agents. The manual [Vault Direct Intake workflow](https://github.com/gamesbyian/UR-Recomp/actions/workflows/vault-direct-intake.yml) can produce metadata-only or single-ID review artifacts. Its pull-request trigger is **restricted to PRs editing the workflow file** and runs inventory-only; opening an arbitrary PR does **not** dispatch a selected archive download. Don't create dummy PRs for each download or enable automatic unrestricted publication. If dispatch is unavailable, use direct Python via shell. When only GitHub connector actions are available and there is no shell, use the existing read-only inventory artifact and work on already accessible PR/branch source; report the inability to download raw files rather than transcribing large binary archives.

## Recover → reconcile → integrate
1. Confirm the exact Drive ID, file size, creation provenance and observed SHA-256. Start with the high-value still-unreviewed 2–28 MB bundles noted in recovery README, not already-integrated duplicate ZIPs.
2. Validate ZIP paths, CRCs, manifest/member SHA-256s and nested archives using `tools/strict_vault_manifest.py`, `tools/recovery_zip_admission.py`, `tools/recovery_member_blob_crosswalk.py` as applicable. Preserve unknown or malformed cases with explicit status rather than assuming safety or completeness.
3. Compare each source/test member against exact blobs on current main and open PRs, then evaluate behavioral supersession. Audit rights/privacy and prior publication incidents before public GitHub source placement. Do not include ROMs, proprietary media, secrets, restricted captures or bulk raw archives in public commits.
4. Publish legitimate missing source/tests in coherent fresh-main branches and draft/reviewable PRs; adapt preimages minimally and run targeted tests plus required CI. Merge only when allowed by the repository's branch protections and independent qualifications.
5. Record outcome per archive ID and relevant member in issue #2088: integrated exact (SHA+PR+tests), semantically superseded (specific source evidence), research/evidence retained, authorization hold, or unresolved with concrete next action. Leave originals in Drive. Don't resurrect owner-deleted legacy files or claim 0/45 USA events/Windows gates changed without separate acceptance evidence.

## Resume / stop rule
Keep work moving across disjoint candidates while a PR or CI runs. At session end, provide links to actual merged PRs, branches/draft PRs, workflow runs, source SHA/member dispositions, and unresolved blockers. Do not count 45 discovered files as 45 integrations. The direct downloader is a transport accelerator; first successful inventory alone is not proof of transfer or publication.
