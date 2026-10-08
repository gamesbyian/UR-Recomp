# Modern onboarding / Help visual hierarchy

Status: first stock-derived hierarchy integrated on Windows x64; final artwork and motion review remain outstanding.

The existing F1/onboarding panel keeps the authoritative live GamepadMap-derived labels, keyboard bindings, jumping/braking/stunt guidance and Quick Practice/Profile/Tour/Options shortcuts. This is purely a host presentation change. Authentic, guest input, progression and gameplay are unchanged.

The first Windows painting slice uses the measured palette roles from `analysis/generated/menu-visual-language.json` through the shared `modern_stock_menu_palette.hpp` authority: a stock-yellow, enlarged "HOW TO RIDE" heading, grey table subtitle, blue semantic action labels, and a yellow speed tip. Bound physical/keyboard labels remain white, not invented vendor glyphs. A charcoal panel and grey frame replace the black diagnostic slab without pretending to reproduce the original animated blue 3D arrow.

The 256px logical view keeps the existing 240×206 panel. Wide Modern view permits up to 324px of panel width; at very narrow sizes the title falls back to the 8px logical glyph pitch. Long help shortcuts are clipped to the actual text-cell envelope, with the same 1x–4x host presentation density and no guest-owned state change. A focused C++ fixture locks palette roles, responsive widths, title/fixed-line fit and footer separation.

This closes a bounded implementation gap, **not** the project's final UI-art gate. The original menu uses its own 16px authored font, yellow shading ramp, moving cursor and visual transitions. Packaged-Windows screenshots at 4:3 and wide presentation and review against those stock reference frames remain required before declaring the Help design final.
