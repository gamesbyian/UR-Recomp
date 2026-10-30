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
        self.assertIn('cmake --build "$ROOT/build" --config Release --parallel 4', source)
        self.assertIn("cancel-in-progress: ${{ !inputs.run_on_hp }}", source)
        self.assertNotIn("HP_MEMORY_RECENT_EXHAUSTION", source)
        self.assertNotIn("HP_MEMORY_COMMIT_INSUFFICIENT", source)

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
