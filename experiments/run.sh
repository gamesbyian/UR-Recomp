#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PY'
import os, pathlib, re
out = pathlib.Path(os.environ["UR_EXPERIMENT_OUTPUT_DIR"])
out.mkdir(parents=True, exist_ok=True)
roots = ["tools", "src", "native", "tests", "experiments", "scripts", ".github"]
extensions = {".c", ".cc", ".cpp", ".h", ".hpp", ".py", ".sh", ".yml", ".yaml", ".json"}
pattern = re.compile(r"bgrx8888|rgb565|rgb555|state\\.fb\\.bmp|fb\\.bgrx|snes9x|snesrecomp|framebuffer|color.convert|colour.convert", re.I)
lines = ["source_sha=" + os.environ["UR_EXPERIMENT_SOURCE_SHA"], "method=stdlib source scan, existing directories only"]
matched = 0
for root in roots:
    base = pathlib.Path(root)
    if not base.is_dir():
        lines.append("missing_optional_root=" + root)
        continue
    for path in sorted(base.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in extensions or path.stat().st_size > 2000000:
            continue
        try:
            source = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        hits = [i for i, line in enumerate(source) if pattern.search(line)]
        if not hits:
            continue
        matched += len(hits)
        lines.append("FILE " + str(path) + " hits=" + str(len(hits)))
        selected = set()
        for i in hits[:24]:
            selected.update(range(max(0,i-3), min(len(source),i+4)))
        for i in sorted(selected):
            lines.append(f"{i+1}: {source[i][:300]}")
        if len(lines) > 6000:
            lines.append("TRUNCATED after 6000 lines")
            break
    if len(lines) > 6000:
        break
lines.append("matched_lines=" + str(matched))
(out / "producer-trace.txt").write_text("\n".join(lines)+"\n")
print("producer-trace matched_lines=",matched,"output_lines=",len(lines))
if matched == 0:
    raise SystemExit("No source matches: acquisition failed")
PY
