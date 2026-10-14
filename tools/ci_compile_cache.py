#!/usr/bin/env python3
"""Content-addressed compile cache for CI unit tests (g++/clang++/gcc shim).

Hundreds of unit tests compile-and-link the same native/product sources with
one combined command. This shim, installed first on PATH under the compiler
names, splits an eligible multi-source command into per-source `-c` compiles
whose objects are cached by the *preprocessed* translation unit plus every
compile-relevant flag, then links. Anything it does not fully understand is
passed straight to the real compiler, so it can only ever reduce work.

Enabled only when UR_COMPILE_CACHE_DIR is set; correctness never depends on the
cache (a miss, a corrupt entry or an unknown flag falls back to the compiler).
"""
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SRC_EXT = {".c", ".cc", ".cpp", ".cxx"}
LINK_ONLY_PREFIX = ("-l", "-L", "-Wl,")
LINK_ONLY_EXACT = {"-static", "-shared", "-rdynamic", "-pie", "-no-pie"}
UNSAFE_PREFIX = ("@", "-M", "-x", "-E", "-S", "-save-temps", "-pipe", "-flto", "-fprofile", "--coverage", "-fsanitize")
UNSAFE_EXACT = {"-c", "-v", "--version", "-###", "-print-search-dirs"}


def real_compiler(name: str) -> str:
    """First `name` on PATH that is not (a symlink to) this shim, so nested or
    stacked shims can never recurse into each other."""
    me = Path(__file__).resolve()
    for d in os.environ.get("PATH", "").split(os.pathsep):
        cand = Path(d) / name if d else None
        try:
            if cand and cand.is_file() and os.access(cand, os.X_OK) and cand.resolve() != me:
                return str(cand)
        except OSError:
            continue
    sys.exit(f"ci_compile_cache: real {name} not found")


def passthrough(real: str, args: list[str]) -> None:
    os.execv(real, [real, *args])


def parse(args: list[str]):
    """Return (sources, compile_flags, link_flags, output) or None if ineligible."""
    sources, compile_flags, link_flags, output = [], [], [], None
    i = 0
    while i < len(args):
        a = args[i]
        if a == "-o":
            if i + 1 >= len(args):
                return None
            output = args[i + 1]
            i += 2
            continue
        if a in UNSAFE_EXACT or a.startswith(UNSAFE_PREFIX):
            return None
        if a in ("-I", "-D", "-U", "-include", "-isystem", "-iquote", "-idirafter"):
            if i + 1 >= len(args):
                return None
            compile_flags += [a, args[i + 1]]
            i += 2
            continue
        if a.startswith(LINK_ONLY_PREFIX) or a in LINK_ONLY_EXACT:
            link_flags.append(a)
        elif a.startswith("-"):
            compile_flags.append(a)
            link_flags.append(a)
        elif Path(a).suffix in SRC_EXT:
            sources.append(a)
        else:  # objects, archives or anything unrecognised: link-time input
            link_flags.append(a)
        i += 1
    if not sources or output is None:
        return None
    return sources, compile_flags, link_flags, output


def compile_cached(real, cache, src, flags, version, workdir):
    pre = subprocess.run([real, *flags, "-E", src], capture_output=True)
    if pre.returncode != 0:
        return None  # let the real compiler report the error in context
    h = hashlib.sha256()
    for part in (version, real, "\0".join(flags), Path(src).suffix):
        h.update(part.encode() + b"\1")
    h.update(pre.stdout)
    key = h.hexdigest()
    obj_cached, err_cached = cache / f"{key}.o", cache / f"{key}.err"
    obj = Path(workdir) / (hashlib.sha256(src.encode()).hexdigest()[:16] + ".o")
    if obj_cached.is_file():
        shutil.copyfile(obj_cached, obj)
        if err_cached.is_file():
            sys.stderr.buffer.write(err_cached.read_bytes())
        return str(obj)
    res = subprocess.run([real, *flags, "-c", src, "-o", str(obj)], capture_output=True)
    sys.stderr.buffer.write(res.stderr)
    if res.returncode != 0:
        sys.stdout.flush()
        sys.exit(res.returncode)
    tmp = cache / f".{key}.{os.getpid()}"
    shutil.copyfile(obj, tmp.with_suffix(".o"))
    err_tmp = tmp.with_suffix(".err")
    err_tmp.write_bytes(res.stderr)
    os.replace(err_tmp, err_cached)
    os.replace(tmp.with_suffix(".o"), obj_cached)
    return str(obj)


def main() -> int:
    name = Path(sys.argv[0]).name
    real = real_compiler(name)
    args = sys.argv[1:]
    cache_dir = os.environ.get("UR_COMPILE_CACHE_DIR")
    parsed = parse(args) if cache_dir else None
    if parsed is None:
        passthrough(real, args)
    sources, compile_flags, link_flags, output = parsed
    cache = Path(cache_dir)
    try:
        cache.mkdir(parents=True, exist_ok=True)
        version = subprocess.run([real, "-dumpfullversion", "-dumpmachine"],
                                 capture_output=True, text=True).stdout
    except OSError:
        passthrough(real, args)
    with tempfile.TemporaryDirectory() as work:
        objs = []
        for src in sources:
            obj = compile_cached(real, cache, src, compile_flags, version, work)
            if obj is None:
                passthrough(real, args)
            objs.append(obj)
        return subprocess.run([real, *objs, *link_flags, "-o", output]).returncode


if __name__ == "__main__":
    raise SystemExit(main())
