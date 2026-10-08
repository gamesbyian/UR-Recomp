#!/usr/bin/env python3
"""Fail closed when the portable Windows executable requires unshipped DLLs.

The release ZIP deliberately contains no DLLs: SDL3 and the MSVC runtime are
linked statically. Check the final PE's imports, not the CMake configuration.
This is a fixed Windows 10+/11 inbox-DLL policy, independent of what happens
to be installed on a GitHub-hosted Visual Studio runner.
"""
from __future__ import annotations

import argparse
import re
import struct
from pathlib import Path


# Only system DLLs available in supported stock Windows 10/11 installations.
# Do not whitelist VC redistributables, OpenMP, SDL, Clang/MinGW libraries or
# developer-machine PATH dependencies, even if CI happens to provide them.
WINDOWS_INBOX_DLLS = frozenset(
    """
    advapi32 amsi avrt bcrypt cabinet cfgmgr32 comctl32 comdlg32 crypt32
    cryptnet cryptui d3d9 d3d11 d3d12 dbghelp dcomp dinput8 dnsapi
    dsound dwmapi dxgi dxguid gdi32 hid imm32 iphlpapi kernel32
    ksuser mf mfcore mfplat mfreadwrite mmdevapi mpr msacm32
    msctf msi msimg32 ncrypt netapi32 normaliz ntdll ole32 oleacc
    oleaut32 opengl32 powrprof propsys psapi rasapi32 rpcrt4
    secur32 sensapi setupapi shcore shell32 shlwapi sspicli
    ucrtbase urlmon user32 userenv usp10 uxtheme version
    winhttp wininet winmm winspool ws2_32 wtsapi32 xinput1_4
    xinput9_1_0 xaudio2_9
    """.split()
)
IMPORT_LINE = re.compile(r"[A-Za-z0-9_.-]+\.dll", re.IGNORECASE)
IMPORT_HEADER = re.compile(
    r"^\s*Image has the following (?:delay load )?dependencies:\s*$",
    re.IGNORECASE,
)


def check_pe_x64(executable: Path) -> None:
    """Read only the DOS/PE headers, without loading the executable."""
    with executable.open("rb") as stream:
        dos = stream.read(64)
        if len(dos) != 64 or dos[:2] != b"MZ":
            raise ValueError("portable executable is not a Windows PE file")
        pe_offset = struct.unpack_from("<I", dos, 0x3C)[0]
        if pe_offset < 64 or pe_offset > 16 * 1024 * 1024:
            raise ValueError("portable executable has an invalid PE header offset")
        stream.seek(pe_offset)
        header = stream.read(26)
    if len(header) != 26 or header[:4] != b"PE\0\0":
        raise ValueError("portable executable has no valid PE signature")
    machine = struct.unpack_from("<H", header, 4)[0]
    optional_magic = struct.unpack_from("<H", header, 24)[0]
    if machine != 0x8664 or optional_magic != 0x20B:
        raise ValueError(
            "portable executable must be AMD64 PE32+ "
            f"(machine=0x{machine:04x}, optional=0x{optional_magic:04x})"
        )


def imported_dlls(dumpbin_text: str) -> tuple[str, ...]:
    """Parse dumpbin /dependents, including delay-load dependencies."""
    found: set[str] = set()
    in_section = False
    sections = 0
    for line in dumpbin_text.splitlines():
        if IMPORT_HEADER.fullmatch(line):
            in_section = True
            sections += 1
            continue
        if in_section and line.strip().lower().startswith("summary"):
            in_section = False
        if not in_section:
            continue
        token = line.strip()
        if IMPORT_LINE.fullmatch(token):
            found.add(token.lower())
    if not sections or not found:
        raise ValueError(
            "dumpbin output has no readable PE dependency list; "
            "cannot certify portable launch"
        )
    return tuple(sorted(found))


def check_dependencies(dumpbin_text: str) -> tuple[str, ...]:
    imports = imported_dlls(dumpbin_text)
    external = [
        dll for dll in imports
        if dll.removesuffix(".dll") not in WINDOWS_INBOX_DLLS
        and not dll.startswith(("api-ms-win-", "ext-ms-win-"))
    ]
    if external:
        raise ValueError(
            "portable executable imports non-inbox DLLs that are not "
            "delivered in the ZIP: " + ", ".join(external)
            + ". Link these dependencies statically or explicitly revise "
            "the release payload and verifier before shipping."
        )
    return imports


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--dependencies", type=Path, required=True)
    args = parser.parse_args()
    try:
        check_pe_x64(args.exe)
        imports = check_dependencies(
            args.dependencies.read_text(encoding="utf-8-sig")
        )
    except (OSError, ValueError) as exc:
        parser.exit(1, f"WINDOWS_PORTABLE_BINARY_REJECTED: {exc}\n")
    print(
        "WINDOWS_PORTABLE_BINARY_VERIFIED machine=AMD64 imports="
        + ",".join(imports)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
