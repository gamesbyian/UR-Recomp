# Toolchain trigger snapshots

These files are generated from `tools/toolchain.json` by
`python3 tools/export_toolchain_entries.py`.

GitHub Actions workflows watch the snapshot for the specific tool they use
instead of watching the whole manifest. This prevents an unrelated toolchain
edit from fanning out into expensive emulator, trace, audio, and race jobs.

Do not edit the JSON snapshots by hand. Run the exporter after changing the
toolchain manifest. `toolchain-bootstrap.yml` verifies that the snapshots are
current.
