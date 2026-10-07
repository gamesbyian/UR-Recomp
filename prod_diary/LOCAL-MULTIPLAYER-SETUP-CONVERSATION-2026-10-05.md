# Local multiplayer setup conversation transcript

Captured: 2026-10-05

Source: October 5 local-multiplayer product conversations.

The local multiplayer lane first established a durable contract on `chatgpt/local-multiplayer-setup-contract-2026-10-05`: deterministic P1/P2 assignment, duplicate-device rejection, disconnect/reconnect semantics, fail-closed launch eligibility, stock two-player authority, reuse of Restart/rematch machinery and Authentic-mode inertness.

A follow-up model branch, `chatgpt/local-multiplayer-setup-model-2026-10-05`, added a pure `LocalMultiplayerSetupState` with deterministic assignment/reassignment/leave behavior and native tests. The useful work was later rescued and merged as PR #503, **Rescue local multiplayer setup contract and model**.

## Follow-through captured 2026-10-06

The contract did not remain a paper model. A later Windows x64 slice added a source-aware gamepad callback and a Modern two-seat join overlay on verified stock `TWO_PLAYER_SELECT`, while leaving the framework's seat assignment and stock rider-selection authority intact. That work later exposed a CI/parity edge: deterministic controllerless scripted routes were unintentionally entering the new overlay. PR #561 fixed the seam by requiring an actually connected physical controller source before the Modern join surface can open.

This was a useful agent-process example. The original feature was locally coherent, but a repository-wide deterministic route exercised a context the feature agent did not naturally encounter. The durable fix came from making the ownership precondition explicit rather than teaching the tests to tolerate the new behavior.
