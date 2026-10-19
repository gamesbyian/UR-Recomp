# Git branch historical debt census (October 19, 2026)

**Complete branch-name listing, not a reachability/merge proof.** The linked GitHub connector returned **1,541 branch refs** across **17 cursor pages** (100 maximum per page; final page 41). This resolves the previous uncertainty about the size of the branch inventory. A ref's name alone cannot establish whether its commits are merged, whether it holds unique reproducible experiment evidence, or whether a closed PR used it. The connector used in this pass permits branch discovery and comparison, but exposes **no branch delete action**. No branch ref was deleted, reset or force-updated.

## Inventory counts by major prefix

| Prefix | Listed refs |
| --- | ---: |
| `chatgpt/` | 271 |
| `agent/` | 261 |
| `qa/` | 177 |
| `qa01/` | 155 |
| `graphics/` | 132 |
| `research/` | 112 |
| `integration/` | 54 |
| `product/` | 52 |
| `claude/` | 36 |
| `docs/` | 34 |
| `qa02/` | 28 |
| `qa08/` | 27 |
| `ci/` | 14 |
| `fix/` | 14 |
| `media/` | 13 |
| `experiment/` | 12 |
| Other prefixes, including single-branch experiment names and `main` | 149 |
| **Total** | **1,541** |

Counts describe the branch namespace *at census time* and do not guarantee a future invariant. The first 100 alphabetically ordered refs were mostly October 7–8 `agent/` experiments; recent `research/rf071`–`rf075` and QA work also remain. Both old and new names can contain unmerged evidence.

## Disposal policy, evidence and next operation

1. **Closed and merged PR branch**: compare with current `main` and confirm associated PR/candidate and artifacts; then the ref is generally an eligible cleanup candidate. Squash merges may retain unique commit IDs and cause naïve ahead/behind comparisons to report divergence; check *patch/evidence preservation*, not only commit ancestry.
2. **Closed unmerged temporary PR**: first record experiment outcome and exact archived artifacts/sha in the owning research authority. Closure does not make its branch automatically disposable when it contains the only job recipe or executable source provenance.
3. **No associated PR or ambiguous owner**: crosswalk against [orphan census #1711](https://github.com/gamesbyian/UR-Recomp/issues/1711), Git history and matched source-bound artifacts; record `merged equivalent / unique evidence / unknown`. Unknown stays untouched.
4. **Recent branch / active research promise**: protect, including disposable RF074 #1969 until qualified run disposition, RF062 #1911 before crosswalk, and independent QA #1967/#1976 before exact-head review.
5. **Delete only from a capable administrative environment**, with an explicit verified list and GitHub audit log. The GitHub connector here has no branch deletion action, and `update_ref` would **move** a branch, not delete it. Never use an update-ref/reset as a substitute for deletion.

This census **does not claim branch cleanup finished**. It closes the inventory-size question and establishes a safe, auditable disposition procedure. For historical research and draft ownership use [issue #1899](https://github.com/gamesbyian/UR-Recomp/issues/1899) and [issue #1711](https://github.com/gamesbyian/UR-Recomp/issues/1711). For current agents use [the work queue](WORK-QUEUE.md), not legacy names.
