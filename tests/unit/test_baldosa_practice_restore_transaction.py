#!/usr/bin/env python3
"""Compile the actual native Practice restore function against failure-injected save-root hooks.

This is ROM-free transactional source coverage, not a Windows or original-game acceptance.
"""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "tools/baldosa_native_modern_root.cpp"


def production_restore_function(source: str) -> str:
    marker = "bool restore_practice_session() {"
    start = source.index(marker)
    depth = 0
    for i in range(source.index("{", start), len(source)):
        if source[i] == "{":
            depth += 1
        elif source[i] == "}":
            depth -= 1
            if depth == 0:
                return source[start:i + 1]
    raise AssertionError("Unterminated native Practice restore function")


HARNESS_PREFIX = r'''
#include <algorithm>
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <string>
#include <string_view>
#include <vector>
namespace ur::product { constexpr std::size_t kStockSramBytes = 8192; }
std::vector<std::uint8_t> memory(8192, 0x22);
std::uint8_t* g_sram = memory.data();
int g_sram_size = 8192;
bool g_practice_session_active = true;
std::vector<std::uint8_t> g_practice_sram_snapshot(8192, 0x11);
std::string g_practice_previous_save_root = "saves/profile-one";
std::string live_root = "practice-session";
bool refuse_set_root = false;
unsigned set_root_calls = 0;
void RtlSetSaveRoot(const char* requested) {
    ++set_root_calls;
    if (!refuse_set_root) live_root = requested ? requested : "";
}
const char* RtlSaveRoot() { return live_root.c_str(); }
'''

HARNESS_SUFFIX = r'''
int main() {
    // If the host refuses the original root, do not overwrite live guest SRAM
    // with the career snapshot while the scratch root is still selected.
    refuse_set_root = true;
    assert(!restore_practice_session());
    assert(std::all_of(memory.begin(), memory.end(), [](auto b){ return b == 0x22; }));
    assert(live_root == "practice-session");
    assert(g_practice_session_active);
    assert(g_practice_sram_snapshot.size() == 8192);
    assert(g_practice_previous_save_root == "saves/profile-one");

    // A later acknowledged restoration commits the exact snapshot once.
    refuse_set_root = false;
    assert(restore_practice_session());
    assert(std::all_of(memory.begin(), memory.end(), [](auto b){ return b == 0x11; }));
    assert(live_root == "saves/profile-one");
    assert(!g_practice_session_active);
    assert(g_practice_sram_snapshot.empty());
    assert(g_practice_previous_save_root.empty());

    // A malformed snapshot must not even attempt a save-root switch.
    g_practice_session_active = true;
    g_practice_previous_save_root = "saves/profile-two";
    g_practice_sram_snapshot.assign(8191, 0x33);
    std::fill(memory.begin(), memory.end(), 0x44);
    live_root = "practice-session";
    const unsigned before = set_root_calls;
    assert(!restore_practice_session());
    assert(set_root_calls == before);
    assert(live_root == "practice-session");
    assert(std::all_of(memory.begin(), memory.end(), [](auto b){ return b == 0x44; }));
    return 0;
}
'''


class PracticeRestoreTransactionTests(unittest.TestCase):
    def test_failed_root_restore_does_not_commit_sram(self):
        compiler = shutil.which("g++") or shutil.which("clang++")
        if not compiler:
            self.skipTest("No C++17 compiler")
        body = production_restore_function(SOURCE.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cpp = root / "restore.cpp"
            binary = root / "restore"
            cpp.write_text(HARNESS_PREFIX + "\n" + body + "\n" + HARNESS_SUFFIX,
                           encoding="utf-8")
            subprocess.run([compiler, "-std=c++17", "-Wall", "-Wextra",
                            "-Werror", "-pedantic", str(cpp), "-o", str(binary)],
                           check=True, capture_output=True, text=True)
            subprocess.run([str(binary)], check=True, capture_output=True, text=True)


if __name__ == "__main__":
    unittest.main()
