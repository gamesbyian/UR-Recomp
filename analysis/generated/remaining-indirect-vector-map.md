# Remaining indirect vector sites at 00:8584 and 00:8599

SNESRecomp reconnaissance reports two unresolved long-indirect jumps in addition to the frontend command dispatcher at `80:C3C8`:

- `00:8584: JMP [$0073]`
- `00:8599: JMP [$0053]`

Nitrodon's bank listings make both pointer-storage patterns much narrower than an unconstrained dynamic jump.

## 00:8584 / vector $73:$75

The only explicit paired construction of the full 24-bit vector found in banks 80-83 is:

```
82:D73B  LDX #$85A4
82:D73E  LDA #$80
82:D740  STX $73
82:D742  STA $75
```

This constructs target **80:85A4**.

The call site itself is:

```
00:8584  JMP [$0073]
00:8587  RTL
```

The target `80:85A4` is immediately followed by the main PPU/input/update sequence beginning at `80:85A5`. This vector is established while interrupts are disabled in `82:D735`, alongside other interrupt/HDMA setup.

A bank-83 workspace routine also executes `STX $73`, but it does not pair that write with the vector bank byte at `$75`; it is therefore not evidence for a second complete 24-bit vector assignment.

**Current bound:** one explicit complete target construction, `80:85A4`.

## 00:8599 / vector $53:$55

Three explicit complete 24-bit assignments are present:

| Setter | Low word | Bank | Target |
|---|---:|---:|---|
| `80:A165-A16C` | `F60C` | `80` | `80:F60C` |
| `82:D74D-D754` | `8610` | `80` | `80:8610` |
| `82:DE1B-DE22` | `85A5` | `80` | `80:85A5` |

The vector is invoked from at least two interrupt wrappers:

```
00:8599  JMP [$0053]
80:B0DE  JMP [$0053]
```

Both wrappers preserve CPU state and resume through an RTI path after the selected handler returns/jumps back into the wrapper continuation.

As with `$73`, the bank-83 workspace routine writes the low word `$53` without constructing the paired bank byte `$55`; it is not counted as another explicit long-vector target.

**Current bound:** three explicit complete targets, `80:F60C`, `80:8610`, and `80:85A5`.

## Interpretation and stopping rule

These sites remain dynamically resolved in SNESRecomp because pointer values are runtime state, but the ROM's explicit vector construction is small and concrete. There is no present evidence for an open-ended target set.

Treat both analyzer gaps as **bounded indirect vectors**. Dynamic target logging is only worth adding if:

- a fidelity discrepancy occurs inside one of these interrupt/update paths;
- a specific LLE/AOT proof depends on excluding other pointer mutations; or
- a modern host/runtime change needs exact interrupt-mode ownership.

Otherwise the semantic-core effort should move to the LLE-only variants and explicit subsystem placeholders rather than spending more time proving a target set that is already operationally small.
