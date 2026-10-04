# Widescreen runtime hook conversation transcript

Captured: 2026-10-02

Source: UR-Recomp project conversation on the first native Widescreen strip-preparation hook.

The user directed a presentation-only Widescreen runtime seam while preserving stock 4:3 behavior and forbidding camera, simulation, progression, or gameplay changes. The requested progression was +8 first, then +16/+24, stopping at the first real architectural constraint.

The first native attempt exposed an unnecessary NMI/runtime dependency, narrowing the design around stock preparation machinery and cleanup rather than widened authoritative guest state.
