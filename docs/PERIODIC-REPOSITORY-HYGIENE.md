# Periodic repository hygiene

Purpose: recurring agent-driven entropy control for UR-Recomp.

Run weekly during heavy multi-agent work, every 1-2 weeks otherwise, and after large imports, migrations, tooling changes, or research campaigns. Execute from current `main`. This is an implementation task: make supported cleanup/hardening changes as you find them.

Core rule: **cover every hygiene domain; do not read every file by default.** Start from inventories, recent changes, compact authorities, workflow history, and obvious orphan signals. Escalate only where evidence warrants it.

## 1. Establish the baseline

Inspect:
- root files and directories;
- `AGENTS.md`, thin provider adapters, and `docs/README.md`;
- current queue/plan and specialist authorities;
- `tools/`, `tools/toolchain.json`, workflows, and submodule pins;
- `reference/`, `reference/`, and generated-analysis boundaries;
- recently completed experiments/imports/migrations.

Run:

```bash
python3 tools/check_repo_hygiene.py
git status --short
git submodule status
```

Use recent diffs before broad browsing.

## 2. Agent context and documentation

Check that an incoming agent can answer common routing questions from `AGENTS.md` without loading the whole repository.

Look for:
- current authorities turning into chronological diaries;
- the same mutable fact maintained in multiple places;
- stale paths, commands, hashes, tool pins, workflow names, or milestone claims;
- hand-maintained prose reproducing a machine-readable registry;
- completed plans still presented as current work;
- provider adapters accumulating shared guidance;
- giant required-reading surfaces where a compact index/query would work.

Classify docs as current authority, current reference, generated/machine authority, chronological evidence, imported/frozen evidence, archive/history, or obsolete. Preserve useful history before destructive consolidation.

Do not compact healthy documents merely because they are long. Act when size causes repeated agent cost, duplicated state, merge conflicts, or poor information architecture.

## 3. Repository boundaries and root hygiene

The root should contain entry points and genuine repository configuration, not a downloads folder.

Check:
- external research artifacts are under the provenance-managed tree;
- historical project-local tools are under `reference/tools/`;
- scratch files are deleted or ignored;
- generated/build/workbench output remains outside Git;
- ROMs exist only under the intentional private `reference/roms/` boundary;
- `reference/` and `reference/` remain semantically distinct and documented.

Do not relocate preserved artifacts without updating provenance/ledger paths.

## 4. Tooling

For every significant script/tool ask:
- Is it still used or plausibly reusable?
- Is its purpose discoverable?
- Does another tool supersede it?
- Is the pin/source/version reproducible?
- Is a GUI tool being mistaken for an automatable dependency?
- Does a one-off experiment deserve permanent bootstrap cost?
- Is important output compact and reproducible?

Prefer pinned, scriptable CLI tools. Heavy GUI workbenches may be catalogued without becoming default bootstrap dependencies.

Do not add all tools to CI. CI belongs to durable merge-safety invariants. On-demand research tools can remain on-demand.

## 5. Workflows and CI

Use `CI-WORKFLOW-BEST-PRACTICES.md` as the canonical workflow-design policy.

Classify each workflow as durable validation, final-main regression, reproducible analysis, manual research infrastructure, retained diagnostic instrument, or obsolete/one-off. Automatic status must be justified separately from mere usefulness.

Check:
- the latest 5-10 runs of each active automatic workflow when history exists, classifying actual failures separately from superseded cancellations;
- the first failed job/step and its bounded log before inferring a product regression;
- repeated cancellation churn from agents pushing several CI-triggering commits faster than useful gates can complete;
- dependent validators using `if: always()` and manufacturing secondary failures when producer artifacts were never created;
- UI acceptance routes whose literal cursor counts drifted after a menu row was inserted or reordered;
- policy/schema tests that rely on one live production object remaining in a temporary state rather than constructing the invalid fixture explicitly;
- monolithic smoke jobs where one volatile product acceptance causes most unrelated checks to be skipped;
- triggers still match the workflow's purpose and use the narrowest correct `paths`;
- expensive work is not selected by unrelated changes or prose-only documentation;
- specialist workflows use per-tool entry snapshots instead of `tools/toolchain.json` where possible;
- automatic read-only work cancels superseded runs;
- generated-evidence writers serialize instead of racing branch writes;
- emulator/native/build jobs have explicit job-level timeouts;
- closed acquisition/research workflows were either removed or made manual-only after their conclusion was promoted;
- branch-specific `push` triggers do not survive after the owning experiment closes;
- deferred-platform workflows remain manual while that platform is outside the active shipping path;
- automatic workflows still answer a current merge/shipping decision rather than only producing interesting evidence;
- the same native/toolchain candidate is not rebuilt by multiple jobs without a distinct invariant that requires it;
- matrix/shard jobs do not each repeat expensive setup/build work that could be shared once;
- PR validation is not needlessly repeated on the merge commit;
- repeated build/package setup is justified by wall-time evidence rather than habit;
- build caches and dependency installation remain reasonable;
- artifact/log output contains enough bounded evidence for an agent to diagnose failure;
- workflow names and docs match current behavior;
- deterministic local feedback exists where practical.

A successful workflow is not proof that it tested the intended executable/data path. Verify target identity and observable evidence.

## 6. Research/evidence hygiene

Check that claims remain traceable from current authorities to evidence.

Look for:
- external claims promoted to facts without local reproduction;
- generated reports whose producer changed without regeneration;
- lost source URLs/revisions/hashes;
- duplicate imported artifacts;
- ROM comparisons keyed only by offsets when content identity is safer;
- hypotheses presented as confirmed conclusions;
- useful negative findings missing from the ledger.

Keep observation, interpretation, hypothesis, and disposition distinct.

## 7. Naming and structure

Review newly introduced durable vocabulary. Prefer names describing present role/behavior over experiment nicknames, temporary phases, or implementation accidents.

Watch especially for:
- ambiguous `reference` / `references` usage;
- "generated", "baseline", "canonical", "prototype", "retail", "source", or "tool" labels used with inconsistent semantics;
- directories whose declared purpose no longer matches their contents;
- temporary filenames surviving after an artifact is understood.

Avoid mass renames without a concrete comprehension benefit.

## 8. Finish line

After changes:
1. rerun `python3 tools/check_repo_hygiene.py`;
2. run the cheapest relevant functional checks for changed scripts/docs/workflows, including `python3 -m unittest tests.unit.test_ci_trigger_policy -v` when workflow policy or triggers changed;
3. verify documentation links and moved artifact paths manually or mechanically;
4. inspect final diff for accidental generated/binary churn;
5. update the owning current authority if the hygiene pass changed project state.

Report only material findings, changes, remaining debt, and validation. Do not create a separate recurring hygiene diary.
