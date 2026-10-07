# Recomp C practices

This document owns the project's coding contract for **first-party handwritten C and C ABI seams that touch recompiled guest behavior, guest memory, hardware-shaped state, or native reference harnesses**.

It does not impose a rewrite or formatting policy on vendored third-party source. Generated SNESRecomp output remains disposable implementation output and must not be hand-cleaned as if it were normal application source.

The governing principle is simple: in guest-facing code, C is a portable representation of machine semantics. Prefer code whose behavior is explicit in the C standard and obvious from the types over code that merely happens to behave correctly on today's compiler.

## Scope and ownership

Apply these rules to:

- project-owned C under `native/`;
- project-owned C ABI bridges between generated/recompiled code and C++;
- project-owned C reference/differential harnesses;
- any future project-owned C that reads or materializes guest WRAM/VRAM/OAM/register-shaped data.

Platform probes may use ordinary host C where they do not model guest behavior, but they must still avoid undefined behavior and unsafe narrowing.

Do not apply project warning cleanup mechanically to:

- `third_party/`;
- imported emulator/tool source under `reference/`;
- generated recompilation output.

If a generated-code pattern needs recurring correction, fix the generator/runtime integration or a narrow project-owned seam. Do not patch generated bulk output.

## Guest versus host authority

Guest behavior remains authoritative for simulation, progression, timers, RNG, collision, AI, and game-owned state.

First-party C may:

- observe guest state through documented addresses or typed runtime APIs;
- translate exact machine-shaped values through narrow ABI seams;
- materialize host-only presentation derived from proven guest state;
- fail closed when guest semantics are unknown or malformed.

First-party C must not:

- create a second gameplay/timing/progression authority;
- silently replace an uncertain guest rule with a convenient host rule;
- expose a general guest-memory mutation API merely to simplify Modern product work;
- let presentation-only state feed back into authoritative simulation unless a separately documented product decision explicitly requires it.

Default/pass-through behavior at enhancement seams should preserve stock behavior.

## Integer and address semantics

Use `stdint.h` fixed-width types for values whose width is part of the emulated/recompiled contract.

Do not rely on:

- the width of plain `int`, `long`, or pointers for guest values;
- signed overflow;
- left-shifting negative signed values;
- right-shifting negative signed values;
- narrowing conversions whose range has not been checked;
- host pointer representation as a guest address;
- native struct packing/alignment as serialized guest layout;
- host endianness for guest multi-byte values.

For guest addresses and offsets:

1. perform potentially growing arithmetic in a type wide enough to prove the complete operation;
2. validate the final byte range before narrowing;
3. only then convert to the address/index type used by the actual read or write;
4. document the required backing-buffer extent at public boundaries.

Unsigned wrap is allowed only when wrap itself is the intended machine semantic. It must not be used accidentally as a bounds-checking shortcut.

Where the guest machine wraps at 8, 16, or another explicit width, make the mask/cast part of the operation rather than relying on a wider host expression to truncate later.

## Memory access

Guest-memory readers must state which address space they require, for example full 128 KiB WRAM or full 64 KiB VRAM.

Dynamically derived addresses must be bounded before dereference even when canonical game state is known to make them valid. Corrupt, partial, or synthetic test state must fail closed rather than wrapping into another readable region.

Use explicit little-endian assembly/disassembly for SNES words. Do not type-pun byte buffers through wider pointers.

Avoid unaligned host loads unless the runtime API explicitly guarantees and encapsulates them.

## C ABI seams

C/C++ boundaries should remain narrow and typed.

Headers callable from both languages must use the existing `extern "C"` pattern. Prefer fixed-width scalar parameters, opaque handles, or explicitly documented buffers over ABI-sensitive structs.

Callback/filter seams should:

- have one clear lifecycle owner;
- default to exact stock pass-through when no Modern hook is installed;
- avoid hidden copies of guest authority;
- be resettable to stock behavior.

Do not add a second C ABI for an authority that already has one.

## Undefined and implementation-defined behavior

Guest-facing code should be written so compiler optimization cannot reinterpret a hardware behavior through C undefined behavior.

Treat these as defects in first-party guest-facing C unless mechanically proven unreachable and documented:

- signed overflow;
- invalid shifts;
- implementation-defined negative signed shifts;
- out-of-bounds pointer/index arithmetic;
- use-after-free or lifetime violations;
- incompatible pointer aliasing/type punning;
- unchecked integer-to-pointer or pointer-to-integer guest-address conversion;
- unchecked narrowing into a runtime API.

If an implementation-defined operation is intentional because a platform ABI requires it, isolate it behind a named helper and document the platform guarantee.

## Warning and sanitizer floor

Portable first-party C seams must compile as C11 under both GCC and Clang with the current strict warning floor:

`-Wall -Wextra -Wpedantic -Werror -Wconversion -Wsign-conversion -Wshadow -Wstrict-prototypes -Wmissing-prototypes`

The owning native unit harnesses should run pure/testable C seams under AddressSanitizer and UndefinedBehaviorSanitizer.

Do not weaken the repository-wide warning floor to admit one intentional construct. Prefer a local explicit cast, helper, assertion, or narrowly documented suppression.

Platform-specific C that requires a console SDK remains validated by that platform toolchain, but portable helpers extracted from it should follow the same warning/UB contract when practical.

## Validation expectations

For a guest-facing C change, use the cheapest combination that answers both questions:

1. Did the C implementation stay within defined, portable semantics?
2. Did the behavioral result remain faithful?

The first question is answered by strict compilation, sanitizers, bounds tests, and narrow unit tests.

The second is answered by the existing deterministic project oracle: stock pass-through tests, guest-state invariants, `snesref`/reference-emulator differentials, fixed-width state checks, or another owning acceptance surface.

Passing sanitizers is not a fidelity proof. Matching the ROM while relying on undefined host-C behavior is not an acceptable portability proof. Both layers matter.

## Review checklist

Before merging new first-party guest-facing C, verify:

- guest-sized values use explicit widths;
- every narrowing conversion is range-safe;
- every dynamic guest-memory address is checked before dereference;
- byte order is explicit;
- no signed-overflow or negative-shift behavior is relied upon;
- host-only state cannot become guest authority by accident;
- the C ABI is no wider than the feature requires;
- stock/pass-through behavior remains available;
- strict GCC/Clang compilation and sanitizer-backed unit coverage exercise the portable seam;
- the owning deterministic fidelity check still passes when behavior is changed.

## Current implementation note

The first hardened surfaces are `uniracers_challenge_generation_bridge.c` and the pure core of `uniracers_ws_margins.c`. The challenge bridge is the model for a narrow stock-pass-through ABI. The widescreen course reader demonstrates the required pattern for guest-memory address derivation: widen, validate the complete bank-relative address, then narrow and read.

Future C work should extend these practices rather than create a parallel style or validation regime.
