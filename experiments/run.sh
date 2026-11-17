#!/usr/bin/env bash
set -euo pipefail
OUT="${UR_EXPERIMENT_OUTPUT_DIR:?}"
mkdir -p "$OUT"
printf 'source_sha=%s\n' "$UR_EXPERIMENT_SOURCE_SHA" > "$OUT/producer-trace.txt"
printf '\n=== capture producer references ===\n' >> "$OUT/producer-trace.txt"
rg -n -i --glob '*.{c,cc,cpp,h,hpp,py,sh}' 'bgrx8888|rgb565|rgb555|state\.fb\.bmp|fb\.bgrx|snes9x|snesrecomp' tools src tests experiments 2>/dev/null | head -n 500 >> "$OUT/producer-trace.txt" || true
printf '\n=== candidate conversion source excerpts ===\n' >> "$OUT/producer-trace.txt"
rg -l -i --glob '*.{c,cc,cpp,h,hpp,py,sh}' 'bgrx8888|rgb565|state\.fb\.bmp|fb\.bgrx' tools src tests experiments 2>/dev/null | head -n 45 | while IFS= read -r file; do
 printf '\nFILE %s\n' "$file" >> "$OUT/producer-trace.txt"
 rg -n -C 8 -i 'bgrx8888|rgb565|state\.fb\.bmp|fb\.bgrx' "$file" | head -n 160 >> "$OUT/producer-trace.txt" || true
done
printf '\n=== pinned external source dependencies ===\n' >> "$OUT/producer-trace.txt"
rg -n -i 'snes9x|snesrecomp' .github tools scripts CMakeLists.txt 2>/dev/null | head -n 130 >> "$OUT/producer-trace.txt" || true
printf '\n=== relevant source filenames ===\n' >> "$OUT/producer-trace.txt"
find . -type f \( -iname '*capture*' -o -iname '*framebuffer*' -o -iname '*bmp*' -o -iname '*snes9x*' \) -not -path './.git/*' | head -n 150 >> "$OUT/producer-trace.txt"
wc -lc "$OUT/producer-trace.txt"
test -s "$OUT/producer-trace.txt"
