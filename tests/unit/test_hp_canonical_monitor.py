"""Guard durable, privacy-bounded HP telemetry without slowing product builds."""
import unittest
from pathlib import Path

from tools.ci.check_windows_smoke_upload_policy import check_workflow

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "windows-native-smoke.yml"
SCRIPT = ROOT / "tools" / "devnode_benchmark" / "monitor_hp_commit.ps1"


class CanonicalHpMonitorTests(unittest.TestCase):
    def test_source_current_windows_build_is_not_throttled_or_cancelled(self):
        source = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn('cmake --build "$ROOT/build" --config Release --parallel "$HP_BUILD_JOBS"', source)
        self.assertIn("HP_BUILD_JOBS=4", source)
        self.assertIn("HP_BUILD_JOBS=6", source)
        self.assertIn('if [[ "${{ inputs.run_on_hp }}" == "true" ]]', source)
        self.assertIn("HP_COMPILE_PROBE jobs=$HP_BUILD_JOBS phase=build_start", source)
        self.assertIn("HP_COMPILE_PROBE jobs=$HP_BUILD_JOBS phase=build_end", source)
        self.assertIn("build_start,%s", source)
        self.assertIn("build_end,%s", source)
        self.assertNotIn('cmake --build "$ROOT/build" --config Release --parallel 12', source)
        self.assertIn("cancel-in-progress: ${{ !inputs.run_on_hp }}", source)
        self.assertNotIn("HP_MEMORY_RECENT_EXHAUSTION", source)
        self.assertNotIn("HP_MEMORY_COMMIT_INSUFFICIENT", source)

    def test_multitooltask_is_hp_only_and_globally_bounded(self):
        source = WORKFLOW.read_text(encoding="utf-8")
        marker = "HP_COMPILE_SCHEDULER mode=MultiToolTask"
        self.assertEqual(source.count(marker), 1)
        start = source.index('if [[ "${{ inputs.run_on_hp }}" == "true" ]]; then',
                             source.index("HP_COMPILE_PROBE jobs=$HP_BUILD_JOBS phase=build_start"))
        end = source.index('          if [[ "${{ inputs.run_on_hp }}" == "true" ]]; then',
                           source.index(marker))
        block = source[start:end]
        self.assertIn('if [[ "${{ inputs.run_on_hp }}" == "true" ]]; then', block)
        self.assertIn("UseMultiToolTask=true", block)
        self.assertIn("EnforceProcessCountAcrossBuilds=true", block)
        self.assertIn("CL_MPCount=10", block)
        self.assertIn("MultiProcMaxCount=10", block)
        self.assertIn("max_compilers=10", block)
        self.assertEqual(block.count("UseMultiToolTask=true"), 1)
        self.assertEqual(block.count('cmake --build "$ROOT/build"'), 2)
        self.assertIn("          else\n"
                      '            cmake --build "$ROOT/build" --config Release '
                      '--parallel "$HP_BUILD_JOBS"\n'
                      '          fi', block)
        self.assertLess(block.index("UseMultiToolTask=true"), block.index("          else"))
        # Build subprocess environment, not machine/user settings or hard
        # failures based on a weak sampled host CPU estimate.
        self.assertNotIn("setx", block)
        self.assertNotIn("HP_MEMORY_RECENT_EXHAUSTION", block)

    def test_start_and_cleanup_are_hp_only_and_bound_to_artifact(self):
        source = WORKFLOW.read_text(encoding="utf-8")
        monitor = "tools/devnode_benchmark/monitor_hp_commit.ps1"
        self.assertEqual(source.count(monitor), 2)
        start = source.index("      - name: Start durable HP memory and reboot telemetry")
        build = source.index("      - name: Configure and build")
        stop = source.index("      - name: Preserve HP resource telemetry")
        upload = source.index("      - name: Upload Windows evidence")
        self.assertLess(start, build)
        self.assertLess(build, stop)
        self.assertLess(stop, upload)
        self.assertIn("        if: inputs.run_on_hp", source[start:build])
        self.assertIn("if: ${{ always() && inputs.run_on_hp }}", source[stop:upload])
        self.assertIn("${{ runner.temp }}/hp-commit-pressure.csv", source)
        check_workflow(source)

    def test_hp_compile_phase_reports_bounded_observed_load(self):
        source = WORKFLOW.read_text(encoding="utf-8")
        script = SCRIPT.read_text(encoding="utf-8")
        build = source.index("      - name: Configure and build")
        preserve = source.index("      - name: Preserve HP resource telemetry")
        self.assertLess(build, preserve)
        self.assertEqual(source.count("hp-compile-phase.csv"), 3)
        self.assertIn("phase,timestamp_utc", source)
        self.assertIn("HP_COMPILE_CPU_SUMMARY", script)
        self.assertIn("hp-compile-phase.csv", script)
        self.assertIn("Import-Csv -LiteralPath $phaseFile", script)
        self.assertIn("if ($begins.Count -eq 1 -and $ends.Count -eq 1)", script)
        self.assertIn("if ($endUtc -le $beginUtc)", script)
        self.assertIn("$observed -ge $beginUtc -and $observed -le $endUtc", script)
        self.assertIn("unavailable=incomplete_phase_markers", script)
        self.assertIn("unavailable=no_valid_cpu_samples", script)
        self.assertNotIn("Get-Process", script)
        self.assertNotIn("Stop-Process", script)
        # Phase markers are private temporary files. The only telemetry
        # artifact remains the existing allowlisted numeric resource CSV.
        self.assertNotIn("${{ runner.temp }}/hp-compile-phase.csv", source)

    def test_cpu_observer_is_aggregate_numeric_optional_and_backward_compatible(self):
        script = SCRIPT.read_text(encoding="utf-8")
        # No workload throttling, process enumeration or arbitrary uploads.
        self.assertIn(
            "timestamp_utc,free_virtual_mb,total_virtual_mb,free_physical_mb,"
            "cpu_load_pct_est,logical_processors", script)
        self.assertIn("Get-CimInstance Win32_Processor", script)
        self.assertIn("NumberOfLogicalProcessors", script)
        self.assertIn("LoadPercentage", script)
        self.assertIn("$logicalTotal += $count", script)
        self.assertIn("$weightedLoad += $load * $count", script)
        self.assertIn("$cpuLoadPct = -1", script)
        self.assertIn("$logicalProcessors = -1", script)
        self.assertIn("HP_CPU_SUMMARY", script)
        self.assertIn("HP_PREVIOUS_CPU", script)
        # Existing crash logs contain only the original four CSV columns;
        # optional CPU properties must not break old recovery.
        self.assertIn("HP_PREVIOUS_MONITOR", script)
        self.assertIn("cpu_load_pct_est -match", script)
        self.assertIn("if ($cpuRows.Count -gt 0)", script)
        self.assertNotIn("Stop-Process", script)
        self.assertNotRegex(script, r"\bWin32_Process\b")
        self.assertNotIn("Get-Process", script)
        self.assertNotIn("Get-Counter", script)

    def test_sampler_does_not_expose_local_user_activity(self):
        script = SCRIPT.read_text(encoding="utf-8")
        for expected in (
            ".ur-recomp-hp-native-monitor",
            "Get-CimInstance Win32_OperatingSystem",
            "Get-WinEvent",
            "FreeVirtualMemory",
            "FreePhysicalMemory",
            "Start-Sleep -Seconds 10",
            "AddMinutes(50)",
            "HP_PREVIOUS_MONITOR",
            "HP_MONITOR_SUMMARY",
            "HP_SYSTEM_EVENT",
            "'interrupted_or_incomplete'",
        ):
            self.assertIn(expected, script)
        self.assertNotIn("Get-Process", script)
        self.assertNotRegex(script, r"\bWin32_Process\b")
        self.assertNotIn("Select-String", script)
        self.assertNotIn("Get-Content", script)
        self.assertNotIn("Stop-Process", script)


if __name__ == "__main__":
    unittest.main()
