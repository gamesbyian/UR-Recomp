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
        ["cmake", "--build", "build", "-j{jobs}", "{python}", "{root}/tools/helper.py", "literal;not-shell"],
        jobs=7,
        python=Path("/tmp/python with spaces"),
    )
    assert expanded == [
        "cmake", "--build", "build", "-j7",
        "/tmp/python with spaces", str(ROOT / "tools/helper.py"), "literal;not-shell",
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
    bad["tools"][0]["headless"]["status"] = "mystery"
    expect_invalid(bad, "headless.status")

    bad = copy.deepcopy(manifest)
    bad["tools"][0]["headless"] = {"status": "manual", "note": "interactive only"}
    expect_invalid(bad, "build-mode tool cannot be headless.manual")

    bad = copy.deepcopy(manifest)
    bad["tools"][0]["build"] = ["make -j8"]
    expect_invalid(bad, "argv list")

    bad = copy.deepcopy(manifest)
    bad["tools"][0]["build"] = [["make", "-j{mystery}"]]
    expect_invalid(bad, "unsupported build placeholder")

    build_tool = next(t for t in manifest["tools"] if t.get("artifacts"))
    bad = copy.deepcopy(manifest)
    target = next(t for t in bad["tools"] if t["id"] == build_tool["id"])
    target["artifacts"] = [{"path": "../escape", "kind": "executable"}]
    expect_invalid(bad, "must stay inside checkout")

    bad = copy.deepcopy(manifest)
    target = next(t for t in bad["tools"] if t["id"] == build_tool["id"])
    target["artifacts"] = [{"path": "thing", "kind": "mystery"}]
    expect_invalid(bad, "invalid kind")

    bad = copy.deepcopy(manifest)
    target = next(t for t in bad["tools"] if t["id"] == build_tool["id"])
    target["artifacts"] = [{"path": "thing", "kind": "executable", "root": "mystery"}]
    expect_invalid(bad, "invalid root")

    with __import__("tempfile").TemporaryDirectory() as td:
        td = Path(td)
        fake_python = td / "venvs" / "alpha" / ("Scripts/python.exe" if __import__("os").name == "nt" else "bin/python")
        fake_python.parent.mkdir(parents=True)
        fake_python.write_bytes(b"")
        assert mod.ensure_venv(td, "alpha") == fake_python
        assert (td / "venvs" / "beta") != fake_python.parent.parent

        exe = td / "tool"
        exe.write_bytes(b"#!/bin/sh\nexit 0\n")
        exe.chmod(0o755)
        mod.verify_artifacts(
            {"id": "x", "artifacts": [{"path": "tool", "kind": "executable"}]},
            td,
        )

        lib = td / "tool.so"
        if __import__("os").name == "nt":
            lib.write_bytes(b"MZxx")
        elif sys.platform == "darwin":
            lib.write_bytes(b"\xcf\xfa\xed\xfex")
        else:
            lib.write_bytes(b"\x7fELFx")
        mod.verify_artifacts(
            {"id": "x", "artifacts": [{"path": "tool.so", "kind": "shared-library"}]},
            td,
        )

        venv_cli = fake_python.parent / "demo-cli"
        venv_cli.write_bytes(b"#!/bin/sh\nexit 0\n")
        venv_cli.chmod(0o755)
        mod.verify_artifacts(
            {"id": "x", "artifacts": [{"path": "bin/demo-cli", "kind": "executable", "root": "venv"}]},
            td,
            fake_python,
        )

        for spec, needle in [
            ({"path": "missing.bin", "kind": "executable"}, "missing.bin"),
            ({"path": "bad.so", "kind": "shared-library"}, "bad.so"),
        ]:
            if spec["path"] == "bad.so":
                (td / "bad.so").write_bytes(b"text")
            try:
                mod.verify_artifacts({"id": "x", "artifacts": [spec]}, td)
            except SystemExit as exc:
                assert needle in str(exc)
            else:
                raise AssertionError(f"invalid artifact was not rejected: {spec}")

    print("PASS: toolchain manifest schema, argv expansion, artifact checks and safety guards")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
