# Uniracers / Unirally NTSC-PAL switch conversation transcript

Captured: 2026-10-05

Source: project conversation **NTSC PAL Switching Feasibility**.

The user proposed a secret title-screen switch between Uniracers and Unirally, initially via typed `NTSC` / `PAL`, then asked how non-keyboard users should access it. A comfortable controller sequence was preferred over an awkward hold chord, and the requested scope was explicitly presentation-focused because retail NTSC/PAL gameplay/code differences were expected to be largely invisible to ordinary players.

The conversation expanded into a retail NTSC-versus-PAL presentation catalog, persistence policy where platform storage permits, and a stock-style animated transition plan. PR #500 added the regional presentation substrate. PR #508, **Plan stock-style transition for Uniracers / Unirally switch**, documented directional PAL/NTSC transition behavior, preferred stock horizontal movement, fallback fade/title-transition options and capture requirements without retiming the guest or rebooting it.

The user specifically wanted the regional state to persist across relaunches on platforms where that is practical.
