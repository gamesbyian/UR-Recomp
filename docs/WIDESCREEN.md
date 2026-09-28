# Widescreen Architecture

No implementation until stock bring-up and differential validation work.

## Principle

Increase presentation width while keeping original simulation semantics.

Inspect logical camera, PPU/render viewport, sprite/OAM construction, background streaming, culling, object activation, opponent visibility, HUD anchoring and two-player behavior.

## Initial non-goals

Do not increase physics scope merely because more world is visible, alter collision bounds, change timing, expose objects early in ways that alter AI/gameplay, or replace the whole renderer before understanding the stock path.

Original 4:3 remains the canonical regression mode.
