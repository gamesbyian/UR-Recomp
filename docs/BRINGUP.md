# Bring-up Log

Chronological record of attempts to execute Uniracers/Unirally under the recompilation stack. Keep this empirical: what happened, what changed, and what evidence supports the conclusion.

## 2026-09-28 — Project scaffold

- Repository created as `gamesbyian/UR-Recomp`.
- Current SNESRecomp bootstrap pin selected: `cd5875cbdaf19f5e324272b1f8051d671fce9215`.
- No ROM committed.
- No compatibility claim yet.
- First technical objective: analyzer reconnaissance, then first boot.

### Known prospective compatibility concern

Uniracers has historically required special emulator handling around OAM/HDMA behavior. Treat this as a test target, not as proof the recomp runtime will fail.

### Working rule

Generated C is disposable. Permanent fixes belong in configuration, hand-authored integration code, or the underlying runtime/framework.
