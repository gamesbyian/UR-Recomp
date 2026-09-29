#@category UR-Recomp
# Import canonical UR-Recomp symbols into a ghidra-snes program.
#
# Headless example:
#   analyzeHeadless <project-dir> <project-name> -process <program> \
#     -postScript tools/ghidra_import_symbols.py analysis/generated/ghidra-symbols.json

import json
import os

from ghidra.program.model.symbol import SourceType

args = getScriptArgs()
if len(args) != 1:
    raise RuntimeError("expected one generated symbol JSON path")

path = args[0]
if not os.path.isabs(path):
    path = os.path.abspath(path)

with open(path, "r") as fp:
    data = json.load(fp)

if data.get("schema_version") != 1 or data.get("target") != "ghidra-snes":
    raise RuntimeError("unsupported UR-Recomp Ghidra symbol file")

space = currentProgram.getAddressFactory().getDefaultAddressSpace()
created = 0
skipped = 0

for row in data.get("entries", []):
    addr = space.getAddress(row["address"])
    if addr is None or currentProgram.getMemory().getBlock(addr) is None:
        printerr("skip unmapped address %s (%s)" % (row["address"], row["name"]))
        skipped += 1
        continue

    createLabel(addr, row["name"], True, SourceType.USER_DEFINED)
    comment = row.get("comment", "").replace("\\n", "\n")
    if comment:
        setPlateComment(addr, comment)
    created += 1

println("UR-Recomp symbols imported: %d created, %d skipped" % (created, skipped))
