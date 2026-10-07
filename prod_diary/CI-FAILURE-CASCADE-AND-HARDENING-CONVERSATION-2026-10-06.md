# CI failure cascade and hardening conversation transcript

Captured: 2026-10-06

Source: project conversations **CI Failure Cause Report** and **Fixed Smoke Workflow Failures**.

October 6 became a prolonged CI repair day. The user repeatedly reported new red workflows after each apparent fix and explicitly asked agents not to stop at the first failure, not to babysit Actions, and eventually to audit the workflow system for the structural causes behind the cascade.

The failures were not one bug. They included stale patch hashes, malformed framework patches, shell-continuation hazards, stateful fixture assumptions, workflow assertions that encoded old implementation shapes, controllerless UI routes affected by a new multiplayer overlay, Native UI topology assumptions, aggregate jobs that cascaded after skipped/failed prerequisites, broad trigger surfaces and long serial acceptance paths.

The key corrective PR was #563, **Harden CI architecture and refocus native smoke**. It converted Native build/boot smoke from roughly fifteen minutes of serial product journeys into a bounded fast gate with an approximately four-minute target and an eight-minute hard timeout; moved long product acceptances back to their owning workflows; changed Native UI evidence to build one candidate and fan that exact artifact out to five capture shards; prevented aggregate validators from producing secondary failures when prerequisites had failed; added structured log assertions; narrowed specialist workflow triggers/toolchains; islandized ROM Baseline onto the pinned offline source; serialized evidence writers; and added mechanical CI-policy tests for the failure classes encountered that day.

PR #560 reconciled stale tooling tests with current policy, while PR #561 fixed the multiplayer-overlay parity regression by requiring a real connected controller source. PRs #557–#559 closed remaining startup/manifest/evidence contract failures.

The process lesson is uncomfortable but useful. AI agents can repair individual CI symptoms extremely quickly, which can encourage a “one more patch” loop. When the feedback cycle is remote and slow, that local speed becomes a trap: each small guess costs another full run and reveals the next hidden assumption. The successful turn came when the task changed from fixing the latest red to reducing the number of assumptions, shortening the gate, separating specialist acceptance from smoke, and mechanically banning known fragility patterns.
