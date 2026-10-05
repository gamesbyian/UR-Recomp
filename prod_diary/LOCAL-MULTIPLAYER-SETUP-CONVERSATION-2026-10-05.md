# Local multiplayer setup conversation transcript

Captured: 2026-10-05

Source: October 5 local-multiplayer product conversations.

The local multiplayer lane first established a durable contract on `chatgpt/local-multiplayer-setup-contract-2026-10-05`: deterministic P1/P2 assignment, duplicate-device rejection, disconnect/reconnect semantics, fail-closed launch eligibility, stock two-player authority, reuse of Restart/rematch machinery and Authentic-mode inertness.

A follow-up model branch, `chatgpt/local-multiplayer-setup-model-2026-10-05`, added a pure `LocalMultiplayerSetupState` with deterministic assignment/reassignment/leave behavior and native tests. The useful work was later rescued and merged as PR #503, **Rescue local multiplayer setup contract and model**.
