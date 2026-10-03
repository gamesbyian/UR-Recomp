# +16 Widescreen course-backed materializer acceptance

Date: 2026-10-03
Workflow run: 37094022986
Source PR: #260
Head: 835e8100cb8f440add38dc198a3f04e2f48f30f0

## Result

The accepted +8 guest path remains unchanged and supplies column +1. Column +2 is materialized directly into host-owned presentation storage from the live course presentation tables:

- coarse sector index: `7F:000F`;
- fine 4x4 packed-surface records: `7F:800F`;
- no future-stock data is read by the implementation;
- no synthetic guest descriptor lane is added;
- off-course and transient live sentinel cells are blank-filled to match stock presentation behavior.

## Acceptance

- accepted +8 unchanged: **true**
- +16 first-column events: **617**
- +16 host-shadow events: **617**
- provider misses: **0**
- same-view stock-comparable rows: **599**
- exact same-view payload matches: **599 / 599**
- vertical-view-transition rows: **18**
- all shadow rows classified: **617 / 617**
- first widened step stock-compatible: **true**
- second step ring-adjacent: **true**
- deterministic cleanup: **true**
- protected state differences: **none**
- +24 remains fail-closed at the bounded one-host-shadow-column capacity seam.

The independent later-stock control is an acceptance oracle only. Rows are compared only when the future stock observation samples the same effective fine-Y viewport; rows crossing a vertical camera/edge transition are classified separately rather than incorrectly requiring a current-view random-access strip to equal a different future viewport.

## Liveness

The same run retained 61 semantic liveness samples:

- protected differences: **none**
- control first progress event: `liveness-004`, frame 1231
- +16 first progress event: `liveness-004`, frame 1232
- progress payload identical
- frame delta: **+1**
- no earlier gameplay activation: **true**

## Conclusion

The test-only future-stock provider is no longer required for +16 content generation. The production direction is now demonstrated end-to-end for Dragster: host-owned column +2 can be generated randomly from authoritative live course presentation state while preserving the accepted +8 guest path and authoritative gameplay behavior.

The next widening step is to generalize this host materializer from one shadow column to additional host-owned columns and then test +24 / the final 16:9 presentation target.
