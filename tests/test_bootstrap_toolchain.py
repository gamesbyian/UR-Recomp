#!/usr/bin/env python3
"""ROM-free regression tests for tools/bootstrap_toolchain.py."""

from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "bootstrap_toolchain.py"
MANIFEST = ROOT / "tools" / "toolchain.json"

spec = importlib.util.spec_from_file_location("bootstrap_toolchain", TOOL)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)


def expect_invalid(manifest: dict, needle: str) -> None:
    try:
        mod.validate_manifest(manifest)
    except ValueError as exc:
        assert needle in str(exc), (needle, str(exc))
    else:
        raise AssertionError(f"expected invalid manifest containing {needle!r}")


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    mod.validate_manifest(manifest)

    subprocess.run([sys.executable, str(TOOL), "--validate"], check=True)
    subprocess.run([sys.executable, str(TOOL), "--list"], check=True)

    assert mod.canonical_git_url("https://github.com/example/repo.git") == "https://github.com/example/repo"
    assert mod.canonical_git_url("https://github.com/example/repo/") == "https://github.com/example/repo"

    expanded = mod.expand_command(
        ["cmake", "--build", "build", "-j{jobs}", "{python}", "literal;not-shell"],
        jobs=7,
        python=Path("/tmp/python with spaces"),
    )
    assert expanded == [
        "cmake", "--build", "build", "-j7",
        "/tmp/python with spaces", "literal;not-shell",
    ]

    bad = copy.deepcopy(manifest)
    bad["install_root"] = "../escape"
    expect_invalid(bad, "inside the repository")

    bad = copy.deepcopy(manifest)
    bad["tools"][0]["revision"] = "main"
    expect_invalid(bad, "40-hex commit")

    bad = copy.deepcopy(manifest)
    bad["tools"][0]["url"] = "http://github.com/example/tool"
    expect_invalid(bad, "https://github.com")

    bad = copy.deepcopy(manifest)
    bad["tools"][1]["id"] = bad["tools"][0]["id"]
    expect_invalid(bad, "duplicate tool id")

    bad = copy.deepcopy(manifest)
    bad["tools"][0]["install_mode"] = "mystery"
    expect_invalid(bad, "install_mode")

    bad = copy.deepcopy(manifest)
    bad["tools"][0]["build"] = ["make -j8"]
    expect_invalid(bad, "argv list")

    bad = copy.deepcopy(manifest)
    bad["tools"][0]["build"] = [["make", "-j{mystery}"]]
    expect_invalid(bad, "unsupported build placeholder")

    with __import__("tempfile").TemporaryDirectory() as td:
        td = Path(td)
        (td / "present.bin").write_bytes(b"x")
        mod.verify_artifacts({"id": "x", "artifacts": ["present.bin"]}, td)
        try:
            mod.verify_artifacts({"id": "x", "artifacts": ["missing.bin"]}, td)
        except SystemExit as exc:
            assert "missing.bin" in str(exc)
        else:
            raise AssertionError("missing artifact was not rejected")

    print("PASS: toolchain manifest schema, argv expansion, artifact checks and safety guards")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
