"""Guard actual stock-core byte retention before RF065 instrumented recompilation."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


def validate_retention_contract(workflow: str) -> None:
    stage = '      - name: Stage genuine original CPU/stack probes'
    build = '      - name: Build exact pinned uninstrumented original core'
    stock = 'cp -- "$SRC/libretro/snes9x_libretro.so" "$RUNNER_TEMP/rf065/stock-original-libretro.so"'
    compare = 'cmp -s "$SRC/libretro/snes9x_libretro.so" "$RUNNER_TEMP/rf065/stock-original-libretro.so"'
    stock_sha = 'sha256sum "$SRC/libretro/snes9x_libretro.so" > "$RUNNER_TEMP/rf065/stock-core-sha256.txt"'
    for marker in (stage, build, stock, compare, stock_sha):
        if workflow.count(marker) != 1:
            raise ValueError(f"missing or duplicated stock-core stage marker: {marker}")
    if not (workflow.index(build) < workflow.index(stock_sha)
            < workflow.index(stock) < workflow.index(compare) < workflow.index(stage)):
        raise ValueError("stock core must be hashed and byte-retained before instrumentation")
    if ('name: rf065-original-stack-source-build-receipt' not in workflow
            or 'path: ${{ runner.temp }}/rf065/' not in workflow):
        raise ValueError("stock ELF must be included in existing RF065 artifact")


class StockCoreRetentionTests(unittest.TestCase):
    def test_current_workflow_retains_exact_stock_core(self):
        workflow = (ROOT / '.github/workflows/qa01-original-stack-producer-compile.yml').read_text()
        validate_retention_contract(workflow)

    def test_missing_or_post_instrumentation_copy_fails(self):
        good = '\n'.join([
            '      - name: Build exact pinned uninstrumented original core',
            'sha256sum "$SRC/libretro/snes9x_libretro.so" > "$RUNNER_TEMP/rf065/stock-core-sha256.txt"',
            'cp -- "$SRC/libretro/snes9x_libretro.so" "$RUNNER_TEMP/rf065/stock-original-libretro.so"',
            'cmp -s "$SRC/libretro/snes9x_libretro.so" "$RUNNER_TEMP/rf065/stock-original-libretro.so"',
            '      - name: Stage genuine original CPU/stack probes',
            'name: rf065-original-stack-source-build-receipt',
            'path: ${{ runner.temp }}/rf065/',
        ])
        validate_retention_contract(good)
        for bad in (
            good.replace('cp -- "$SRC/libretro/snes9x_libretro.so" "$RUNNER_TEMP/rf065/stock-original-libretro.so"', ''),
            good.replace('      - name: Stage genuine original CPU/stack probes', '')
                .replace('sha256sum "$SRC/libretro/snes9x_libretro.so" > "$RUNNER_TEMP/rf065/stock-core-sha256.txt"',
                         '      - name: Stage genuine original CPU/stack probes\nsha256sum "$SRC/libretro/snes9x_libretro.so" > "$RUNNER_TEMP/rf065/stock-core-sha256.txt"'),
            good.replace('path: ${{ runner.temp }}/rf065/', 'path: ${{ runner.temp }}/rf083/'),
        ):
            with self.subTest(bad=bad[-100:]), self.assertRaises(ValueError):
                validate_retention_contract(bad)


if __name__ == '__main__':
    unittest.main()
