#!/usr/bin/env python3
"""Stage the established Modern Windows user-data-root contract into Baldosa.

Never create an alternate save store or rewrite the launcher.  The existing
UR-Recomp Windows run-uniracers.cmd already validates/creates the per-user root
and exports SNESRECOMP_USER_DATA_DIR.  This ports the corresponding *existing*
framework-path behavior to the pinned Baldosa dependency in a disposable build
checkout; stock Baldosa without that environment variable is unchanged.

When set, all framework-relative config/saves/mod paths use the canonical
user root; keybinds.ini must also follow that root, not argv[0].
An invalid or unwritable explicit root fails CLOSED, never to cwd/exe.
"""
from __future__ import annotations

import argparse
from pathlib import Path

MARK = "UR_BALDOSA_MODERN_USER_DATA_ROOT"

HOST_ANCHOR = """    get_exe_dir(dir, sizeof(dir));
    if (dir[0] == '.' &&
        (dir[1] == '/' || dir[1] == '\\\\' || dir[1] == '\\0'))
        return 0;
    if (!dir_is_writable(dir)) {"""

HOST_PROBE = """    if (snprintf(probe, sizeof(probe), "%s.snesrecomp_write_probe",
                 dir) >= (int)sizeof(probe))
        return 0;"""

HOST_MAIN_CONFIG = """  if (!config_file) {
    /* Anchor cwd to the binary's own directory FIRST."""

HOST_MAIN_CALL = """    int anchored = snesrecomp_anchor_to_exe_dir();
    if (!anchored) {"""

KEYBIND_ANCHOR = """static void derive_ini_path(const char *exe_path) {
    if (!exe_path || !*exe_path) {"""


def once(source: str, needle: str, replacement: str) -> str:
    if source.count(needle) != 1:
        raise ValueError(f"Pinned native Baldosa host diverged: {needle[:100]!r}")
    return source.replace(needle, replacement, 1)


def patch_host_paths(source: str) -> str:
    if MARK in source:
        return source
    # The unpatched probe accidentally writes beside the directory (not
    # inside it); preserve fail-closed writability checks at the selected root.
    source = once(
        source, HOST_PROBE,
        """    const size_t n = strlen(dir);
    const char *separator =
        n > 0 && (dir[n - 1] == '/' || dir[n - 1] == '\\\\') ? "" : "/";
    if (snprintf(probe, sizeof(probe),
                 "%s%s.snesrecomp_write_probe", dir, separator)
            >= (int)sizeof(probe))
        return 0;""")
    source = once(
        source, HOST_ANCHOR,
        """#if defined(_WIN32)
    /* The native Windows environment is UTF-16. Never convert a non-ACP
     * player directory through getenv/fopen/chdir's narrow code page. */
    const wchar_t *wide_root = _wgetenv(L"SNESRECOMP_USER_DATA_DIR");
    if (wide_root && *wide_root) {
        size_t length = wcslen(wide_root);
        if (length < 3) return 0;
        const int drive = ((wide_root[0] >= L'A' && wide_root[0] <= L'Z') ||
                           (wide_root[0] >= L'a' && wide_root[0] <= L'z')) &&
                          wide_root[1] == L':' &&
                          (wide_root[2] == L'/' || wide_root[2] == 92);
        const int unc = wide_root[0] == 92 && wide_root[1] == 92 &&
                        wide_root[2] != 0;
        if (!drive && !unc) return 0;
        wchar_t probe_wide[1024];
        const wchar_t *separator =
            (wide_root[length - 1] == L'/' || wide_root[length - 1] == 92)
                ? L"" : L"/";
        int count = swprintf(probe_wide, 1024,
                            L"%ls%ls.snesrecomp_write_probe",
                            wide_root, separator);
        if (count < 0 || count >= 1024) return 0;
        FILE *f = _wfopen(probe_wide, L"wb");
        if (!f) return 0;
        if (fclose(f) != 0) {
            _wremove(probe_wide);
            return 0;
        }
        if (_wremove(probe_wide) != 0 || _wchdir(wide_root) != 0)
            return 0;
        fprintf(stderr,
                "[Launcher] Config/saves anchored to native Windows user-data root.\\n");
        return 1;
    }
#endif
    const char *modern_root = getenv("SNESRECOMP_USER_DATA_DIR");
    if (modern_root && *modern_root) {
        /* """ + MARK + """: do not silently save beside the executable. */
        if (snprintf(dir, sizeof(dir), "%s", modern_root) >= (int)sizeof(dir))
            return 0;
#ifdef _WIN32
        /* Windows drive-absolute or UNC. The shipped .cmd performs the
         * stricter package-relative-root canonicalization independently. */
        const int drive = ((dir[0] >= 'A' && dir[0] <= 'Z') ||
                           (dir[0] >= 'a' && dir[0] <= 'z')) &&
                          dir[1] == ':' &&
                          (dir[2] == '/' || dir[2] == '\\\\');
        const int unc = (dir[0] == '\\\\' && dir[1] == '\\\\' &&
                         dir[2] != '\\0');
        if (!drive && !unc) return 0;
#else
        if (dir[0] != '/') return 0;
#endif
    } else {
        get_exe_dir(dir, sizeof(dir));
        if (dir[0] == '.' &&
            (dir[1] == '/' || dir[1] == '\\\\' || dir[1] == '\\0'))
            return 0;
    }
    if (!dir_is_writable(dir)) {""")
    # The C host has to include native wide-file/chdir declarations before
    # the function, not rely on the active code page or transitive headers.
    source = """#if defined(_WIN32)
#include <wchar.h>
#include <direct.h>
#endif
""" + source
    return source


def patch_keybinds(source: str) -> str:
    if MARK in source:
        return source
    return once(
        source, KEYBIND_ANCHOR,
        """static void derive_ini_path(const char *exe_path) {
    /* """ + MARK + """: the host has already selected the explicit cwd.
     * Do not reach back into the immutable executable/package directory. */
#if defined(_WIN32)
    const wchar_t *wide_root = _wgetenv(L"SNESRECOMP_USER_DATA_DIR");
    const int explicit_root = wide_root && *wide_root;
#else
    const char *modern_root = getenv("SNESRECOMP_USER_DATA_DIR");
    const int explicit_root = modern_root && *modern_root;
#endif
    if (explicit_root) {
        strcpy(s_ini_path, "keybinds.ini");
        return;
    }
    if (!exe_path || !*exe_path) {""")


def patch_host_main(source: str) -> str:
    if MARK in source:
        return source
    source = once(
        source, HOST_MAIN_CONFIG,
        """  /* """ + MARK + """: also anchor for an explicit --config.
   * The existing Windows launcher uses absolute exe/ROM paths and selects
   * the mutable root; a failed explicit root must not fall back to cwd. */
#if defined(_WIN32)
  const wchar_t *wide_root = _wgetenv(L"SNESRECOMP_USER_DATA_DIR");
  const int explicit_root = wide_root && *wide_root;
#else
  const char *modern_root = getenv("SNESRECOMP_USER_DATA_DIR");
  const int explicit_root = modern_root && *modern_root;
#endif
  if (explicit_root && !snesrecomp_anchor_to_exe_dir()) {
    fprintf(stderr,
            "UR-STARTUP-SAVE-ROOT: invalid or unwritable native user-data root\\n");
    return 7;
  }
  if (!config_file) {
    /* Anchor cwd to the binary's own directory FIRST.""")
    source = once(
        source, HOST_MAIN_CALL,
        """    int anchored = explicit_root
        ? 1 : snesrecomp_anchor_to_exe_dir();
    if (!anchored) {""")
    return source


def plan(game: Path):
    paths = (
        (game / "snesrecomp/runner/src/host_paths.c", patch_host_paths),
        (game / "snesrecomp/runner/src/keybinds.c", patch_keybinds),
        (game / "snesrecomp/runner/src/desktop/host_main.c", patch_host_main),
    )
    pending = []
    # Atomic preparation: verify ALL pinned seams before changing any file.
    for path, change in paths:
        old = path.read_text(encoding="utf-8")
        pending.append((path, old, change(old)))
    return pending


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--game", type=Path, required=True)
    args = parser.parse_args()
    for path, before, after in plan(args.game.resolve()):
        if before != after:
            path.write_text(after, encoding="utf-8")
        print(f"{path}: {'already staged' if before == after else 'staged'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
