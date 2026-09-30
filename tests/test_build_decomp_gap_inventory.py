#!/usr/bin/env python3
from tools.build_decomp_gap_inventory import build

symbols = """
## Functions
| Address | Name | Confidence | Evidence / notes |
|---|---|---:|---|
| TBD | `TBD_MainLoop` | 0 | Not analyzed |
| `02:A968` (USA) | `Player_ApplyVerticalAcceleration` | 4 | known |
## RAM
"""

recon = """
- analysis roots: **9**
- exact variants: **54**
- AOT-eligible variants: **52**
- LLE-only variants: **2**
- decoded instruction instances across manifest nodes: **1,808**

- `00:8584` — four M/X variants, `JMP` indirect through operand `$0073`

## LLE-only variants
1. `80:91DC M1X0` — 119 decoded instructions
"""

r = build(symbols, recon)
assert r["coverage_dimensions"]["semantic_functions_named"] == 1
assert r["coverage_dimensions"]["semantic_placeholders"] == 1
assert r["coverage_dimensions"]["execution_analysis"]["exact_variants"] == 54
assert r["coverage_dimensions"]["execution_analysis"]["decoded_instruction_instances"] == 1808
assert r["coverage_dimensions"]["execution_analysis"]["unresolved_indirect_guest_sites"][0]["pc"] == "00:8584"
assert r["coverage_dimensions"]["execution_analysis"]["lle_examples"][0]["pc"] == "80:91DC"
assert [x["kind"] for x in r["gap_queue"]] == [
    "semantic_placeholder", "unresolved_indirect_dispatch", "lle_only_variant"
]
print("PASS: decomp gap inventory")
