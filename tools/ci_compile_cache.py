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
import json
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
    for part in (version, real, "\\0".join(flags), Path(src).suffix):
        h.update(part.encode() + b"\\1")
    h.update(pre.stdout)
    key = h.hexdigest()
    obj_cached = cache / f"{key}.o"
    err_cached = cache / f"{key}.err"
    receipt = cache / f"{key}.receipt.json"
    obj = Path(workdir) / (hashlib.sha256(src.encode()).hexdigest()[:16] + ".o")

    # A cache key authenticates *inputs*, not persisted object contents.
    # Require the atomic, final-published receipt and verify BOTH objects
    # and stored compiler diagnostics. Legacy/partial/malformed entries miss.
    try:
        if obj_cached.is_file() and err_cached.is_file() and receipt.is_file():
            manifest = json.loads(receipt.read_text(encoding="utf-8"))
            contents = obj_cached.read_bytes()
            diagnostics = err_cached.read_bytes()
            if (type(manifest) is dict
                    and set(manifest) == {"schema", "object_sha256", "stderr_sha256"}
                    and manifest["schema"] == "ur-ci-compile-cache/1"
                    and contents
                    and manifest["object_sha256"] == hashlib.sha256(contents).hexdigest()
                    and manifest["stderr_sha256"] == hashlib.sha256(diagnostics).hexdigest()):
                obj.write_bytes(contents)
                sys.stderr.buffer.write(diagnostics)
                return str(obj)
    except (OSError, ValueError, UnicodeError):
        pass  # a corrupt/missing/partial hit is NEVER compiled output

    res = subprocess.run([real, *flags, "-c", src, "-o", str(obj)],
                         capture_output=True)
    sys.stderr.buffer.write(res.stderr)
    if res.returncode != 0:
        sys.stdout.flush()
        sys.exit(res.returncode)

    # Unique per-process temporary directory avoids collision on concurrent
    # identical-key compilers. Publish the receipt *last* and atomically, so
    # interrupted saves cannot attest half-written or mismatched bytes.
    # A cache publication failure must not invalidate the real compiled .o.
    try:
        with tempfile.TemporaryDirectory(prefix=f".{key}.", dir=cache) as tmp:
            root = Path(tmp)
            staged_obj = root / "object.o"
            staged_err = root / "stderr.err"
            staged_receipt = root / "receipt.json"
            contents = obj.read_bytes()
            staged_obj.write_bytes(contents)
            staged_err.write_bytes(res.stderr)
            staged_receipt.write_text(json.dumps({
                "schema": "ur-ci-compile-cache/1",
                "object_sha256": hashlib.sha256(contents).hexdigest(),
                "stderr_sha256": hashlib.sha256(res.stderr).hexdigest(),
            }, sort_keys=True) + "\\n", encoding="utf-8")
            os.replace(staged_err, err_cached)
            os.replace(staged_obj, obj_cached)
            os.replace(staged_receipt, receipt)
    except OSError:
        pass
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
