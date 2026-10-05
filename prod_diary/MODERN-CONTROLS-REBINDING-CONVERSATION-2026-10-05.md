# Modern Controls rebinding conversation transcript

Captured: 2026-10-05

Source: October 5 controls-rebinding conversations, including the current **complete player-facing control rebinding** lane.

The user required Windows x64-first rebinding through the existing Modern Controls surface, using SNESRecomp's real binding authority rather than another input map or config format. The framework APIs such as `keybinds_set_button`, `keybinds_reset_player` and the existing save/reload authority were to remain canonical.

An earlier pure-state/model pass merged as PR #498, **Add framework-authoritative controls rebind model**. The current product-integration conversation then required live capture/edit presentation, cancel/clear/reset behavior, durable persistence/reload and native acceptance through the existing Controls UI.

While this archive pass was running, PR #512, **Complete player-facing Modern Controls rebinding**, opened on `chatgpt/modern-controls-rebinding-2026-10-05`. It is recorded here as active work, not as a completed/merged result.
