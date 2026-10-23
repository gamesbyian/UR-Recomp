# Recovery agent: direct intake and integration handoff

**Status as of 2026-10-23:** Public 02 Incoming folder contains 45 direct children. GitHub Actions [run 40020834318](https://github.com/gamesbyian/UR-Recomp/actions/runs/40020834318) validated unauthenticated enumeration with gdown 6.4.2 and zero inventory errors, and produced [inventory artifact](https://github.com/gamesbyian/UR-Recomp/actions/runs/40020834318/artifacts/12529619027). **Actual ZIP transfer and staging have not yet been qualified.** PR #2435 merged the fix and workflow-change PR smoke trigger.

## Mission
Recover useful first-party source and tests from the currently surviving Drive Vault into focused GitHub PRs with minimal manual byte transport. Treat the Vault as preservation, not as a release gate or separate project board. Prioritize unique, relevant Windows x64 product, modern UI/menus and independent release-validation code. Avoid colliding with current scheduled/Claude owner lanes. This is end-to-end integration work, not an inventory-only assignment.

## Read-first authorities
- Root `AGENTS.md`, `docs/WORK-QUEUE.md`, `docs/HOURLY-AGENT-LINES.md` and `docs/AGENT-COORDINATION.md`
- `docs/recovery/FIRST-PARTY-PUBLICATION-CONTRACT.md`, `docs/recovery/GITHUB-FIRST-PUBLICATION-RUNBOOK.md`, `docs/recovery/DIRECT-VAULT-INTAKE.md`
- `docs/recovery/README.md` and issue [#2088](https://github.com/gamesbyian/UR-Recomp/issues/2088), latest comments
- Live PRs, current main, source and unit tests before writing

## Direct transport (no conversational base64 bridge)
Public [02 Incoming](https://drive.google.com/drive/folders/1cdovDqle9IRYKX2lCt513mtWge75HywX) is the first source. Use `tools/vault_gdown_intake.py` with `gdown==6.4.2`. Prefer a shell runner and a fresh checkout of latest main:

```bash
python -m pip install 'gdown==6.4.2'
python tools/vault_gdown_intake.py --out /tmp/ur-index
python tools/vault_gdown_intake.py --out /tmp/ur-one --file-id EXACT_DRIVE_ID
# Only after rights/privacy and publication-hold review for the specific archive:
python tools/vault_gdown_intake.py --out /tmp/ur-reviewed --file-id REVIEWED_ID --stage-sources
python -m unittest tests.unit.test_vault_gdown_intake -v
```

The manual [Vault Direct Intake workflow](https://github.com/gamesbyian/UR-Recomp/actions/workflows/vault-direct-intake.yml) can produce metadata-only or single-ID review artifacts. Its pull-request trigger is **restricted to PRs editing the workflow file** and runs inventory-only; opening an arbitrary PR does **not** dispatch a selected archive download. Don't create dummy PRs for each download or enable automatic unrestricted publication. If dispatch is unavailable, use direct Python via shell. When only GitHub connector actions are available and there is no shell, use the existing read-only inventory artifact and work on already accessible PR/branch source; report the inability to download raw files rather than transcribing large binary archives.

## Recover → reconcile → integrate
1. Confirm the exact Drive ID, file size, creation provenance and observed SHA-256. Start with the high-value still-unreviewed 2–28 MB bundles noted in recovery README, not already-integrated duplicate ZIPs.
2. Validate ZIP paths, CRCs, manifest/member SHA-256s and nested archives using `tools/strict_vault_manifest.py`, `tools/recovery_zip_admission.py`, `tools/recovery_member_blob_crosswalk.py` as applicable. Preserve unknown or malformed cases with explicit status rather than assuming safety or completeness.
3. Compare each source/test member against exact blobs on current main and open PRs, then evaluate behavioral supersession. Audit rights/privacy and prior publication incidents before public GitHub source placement. Do not include ROMs, proprietary media, secrets, restricted captures or bulk raw archives in public commits.
4. Publish legitimate missing source/tests in coherent fresh-main branches and draft/reviewable PRs; adapt preimages minimally and run targeted tests plus required CI. Merge only when allowed by the repository's branch protections and independent qualifications.
5. Record outcome per archive ID and relevant member in issue #2088: integrated exact (SHA+PR+tests), semantically superseded (specific source evidence), research/evidence retained, authorization hold, or unresolved with concrete next action. Leave originals in Drive. Don't resurrect owner-deleted legacy files or claim 0/45 USA events/Windows gates changed without separate acceptance evidence.

## Resume / stop rule
Keep work moving across disjoint candidates while a PR or CI runs. At session end, provide links to actual merged PRs, branches/draft PRs, workflow runs, source SHA/member dispositions, and unresolved blockers. Do not count 45 discovered files as 45 integrations. The direct downloader is a transport accelerator; first successful inventory alone is not proof of transfer or publication.
