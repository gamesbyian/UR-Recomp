# USJO v8 X/tabletop transient runtime evidence

Source: Actions run `36776825024`, job `110096726905`, artifact `11126785345`.

The matched eight-frame SNES X intervention produces a transition sequence at `7E:042F` that is absent from the jump-only control:

- native: frames 1263, 1265, 1267, 1269, 1271: **0→1→2→3→4→0**
- pinned Snes9x: frames 1255, 1257, 1259, 1261, 1263: **0→1→2→3→4→0**
- normalized to each runtime's first causal transition: **0, +2, +4, +6, +8 frames**

The absolute frame numbers differ because the deterministic menu/scene script reaches equivalent semantic boundaries at slightly different global frame indices. The causal transition sequence and cadence are identical.

This is direct runtime evidence that the recovered USJO v8 `numtabletops` read at `7E:042F` is X/tabletop-related. It also refines the unit question: the byte behaves here as a transient 1–4 progression that clears to zero, so **"completed tabletop count" is too strong a description from this fixture alone**. USJO v8 only needs nonzero detection to decide that its tabletop attempt worked.

Next discriminator: reproduce the recovered v8 tabletop pulse cadence and observe `042F` through landing/boost award to determine whether the values encode stunt progress, rotation phase, or a short-lived count/state used by scoring.
