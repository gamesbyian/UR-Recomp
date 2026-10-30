# Read-only resource telemetry for the owner's Windows x64 GitHub runner.
# Only aggregate memory/CPU numbers and relevant System event metadata are emitted.
# CPU estimates are host-wide, never per-application attribution.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('Start','Sample','Stop')]
    [string]$Mode,
    [string]$OutputPath,
    [string]$StopPath
)
$ErrorActionPreference = 'Stop'
if ($env:RUNNER_NAME -ine 'hpmini-ur-recomp') { throw 'HP_MONITOR_UNEXPECTED_RUNNER' }
if (-not $env:RUNNER_WORKSPACE -or -not $env:GITHUB_RUN_ID -or -not $env:GITHUB_RUN_ATTEMPT) {
    throw 'HP_MONITOR_MISSING_RUN_CONTEXT'
}
$root = Join-Path $env:RUNNER_WORKSPACE '.ur-recomp-hp-native-monitor'
$stem = "$env:GITHUB_RUN_ID-$env:GITHUB_RUN_ATTEMPT"
$csv = Join-Path $root "$stem.csv"
$stop = Join-Path $root "$stem.stop"

if ($Mode -eq 'Sample') {
    if ($OutputPath -ne $csv -or $StopPath -ne $stop) {
        throw 'HP_MONITOR_INVALID_SAMPLE_TARGET'
    }
    $deadline = (Get-Date).AddMinutes(50)
    # WMI LoadPercentage is a one-second snapshot; taking it every ten
    # seconds can miss short compiler bursts. Independently sample the
    # Windows host-wide Processor(_Total) performance counter: NextValue()
    # averages CPU busy time since its preceding call. No process names,
    # process inventory or user activity are accessed.
    $cpuWindowCounter = $null
    try {
        $cpuWindowCounter = [System.Diagnostics.PerformanceCounter]::new('Processor', '% Processor Time', '_Total')
        [void]$cpuWindowCounter.NextValue() # Prime; never report this first value.
    } catch {
        $cpuWindowCounter = $null # Optional counter; retain memory and WMI.
    }
    $cpuWindowWarmup = $true
    'timestamp_utc,free_virtual_mb,total_virtual_mb,free_physical_mb,cpu_load_pct_est,logical_processors,cpu_pct_window_avg' | Set-Content -LiteralPath $csv -Encoding ASCII
    while ((Get-Date) -lt $deadline -and -not (Test-Path -LiteralPath $stop)) {
        try {
            $os = Get-CimInstance Win32_OperatingSystem -ErrorAction Stop
            $utc = (Get-Date).ToUniversalTime().ToString('o')
            # Coarse host-wide CPU estimate, weighted by logical processors.
            # -1 denotes unavailable. Never discard valid memory samples.
            $cpuLoadPct = -1
            $logicalProcessors = -1
            try {
                $cpus = @(Get-CimInstance Win32_Processor -ErrorAction Stop)
                $logicalTotal = 0
                $weightedLoad = 0.0
                foreach ($cpu in $cpus) {
                    $count = [int]$cpu.NumberOfLogicalProcessors
                    if ($count -le 0 -or $null -eq $cpu.LoadPercentage) { continue }
                    $load = [int]$cpu.LoadPercentage
                    if ($load -lt 0 -or $load -gt 100) { continue }
                    $logicalTotal += $count
                    $weightedLoad += $load * $count
                }
                if ($logicalTotal -gt 0) {
                    $cpuLoadPct = [int][math]::Round($weightedLoad / $logicalTotal)
                    $logicalProcessors = $logicalTotal
                }
            } catch {
                # Sampling errors must not reveal process activity or paths.
            }
            # Interval mean (not a 1-second point estimate). A failed
            # performance counter is optional and never blocks the build.
            $cpuWindowPct = '-1'
            if ($null -ne $cpuWindowCounter) {
                try {
                    if ($cpuWindowWarmup) {
                        # No interval has elapsed at the initial sample.
                        # Discard rather than blend a near-zero window into
                        # the mean of ten-second compile samples.
                        [void]$cpuWindowCounter.NextValue()
                        $cpuWindowWarmup = $false
                    } else {
                        $observedPct = [double]$cpuWindowCounter.NextValue()
                        if (-not [double]::IsNaN($observedPct) -and -not [double]::IsInfinity($observedPct)) {
                            $boundedPct = [math]::Max(0.0, [math]::Min(100.0, $observedPct))
                            $cpuWindowPct = $boundedPct.ToString('F1', [System.Globalization.CultureInfo]::InvariantCulture)
                        }
                    }
                } catch {
                    $cpuWindowCounter = $null
                }
            }
            ('{0},{1},{2},{3},{4},{5},{6}' -f $utc, [math]::Round($os.FreeVirtualMemory / 1024), [math]::Round($os.TotalVirtualMemorySize / 1024), [math]::Round($os.FreePhysicalMemory / 1024), $cpuLoadPct, $logicalProcessors, $cpuWindowPct) | Add-Content -LiteralPath $csv -Encoding ASCII
        } catch {
            # Sampling errors must not interfere with a useful native build.
            # Avoid leaking paths or user applications from exception messages.
        }
        Start-Sleep -Seconds 10
    }
    exit 0
}

if ($Mode -eq 'Start') {
    New-Item -ItemType Directory -Path $root -Force | Out-Null
    Get-ChildItem -LiteralPath $root -Filter '*.csv' -File |
        Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 3 | ForEach-Object {
            try {
                $rows = @(Import-Csv -LiteralPath $_.FullName)
                $minimum = if ($rows.Count -gt 0) {
                    ($rows | Measure-Object -Property free_virtual_mb -Minimum).Minimum
                } else { 'none' }
                $stopFile = [IO.Path]::ChangeExtension($_.FullName, '.stop')
                $state = if (Test-Path -LiteralPath $stopFile) { 'stopped' } else { 'interrupted_or_incomplete' }
                Write-Output ('HP_PREVIOUS_MONITOR run={0} samples={1} minimum_free_virtual_mb={2} state={3}' -f $_.BaseName, $rows.Count, $minimum, $state)
                # Memory-only legacy runs remain valid; CPU is optional.
                $cpuRows = @($rows | Where-Object {
                    $_.cpu_load_pct_est -match '^(100|[0-9]{1,2})$'
                })
                if ($cpuRows.Count -gt 0) {
                    $peak = ($cpuRows | Measure-Object -Property cpu_load_pct_est -Maximum).Maximum
                    Write-Output ('HP_PREVIOUS_CPU run={0} samples={1} peak_host_cpu_pct_est={2}' -f $_.BaseName, $cpuRows.Count, $peak)
                }
            } catch {
                Write-Output ('HP_PREVIOUS_MONITOR run={0} parse=unavailable' -f $_.BaseName)
            }
        }
    try {
        $os = Get-CimInstance Win32_OperatingSystem
        Write-Output ('HP_CURRENT_MEMORY free_virtual_mb={0} free_physical_mb={1}' -f [math]::Round($os.FreeVirtualMemory / 1024), [math]::Round($os.FreePhysicalMemory / 1024))
    } catch {
        Write-Output 'HP_CURRENT_MEMORY unavailable'
    }
    try {
        $events = @(Get-WinEvent -FilterHashtable @{
            LogName = 'System'
            StartTime = (Get-Date).AddHours(-48)
            Id = @(41,6008,2004)
        } -MaxEvents 80 -ErrorAction Stop | Where-Object {
            $_.ProviderName -match '^(Microsoft-Windows-Kernel-Power|EventLog|Microsoft-Windows-Resource-Exhaustion-Detector)$'
        } | Select-Object -First 12)
        foreach ($event in $events) {
            Write-Output ('HP_SYSTEM_EVENT utc={0} id={1} provider={2}' -f $event.TimeCreated.ToUniversalTime().ToString('o'), $event.Id, $event.ProviderName)
        }
    } catch {
        Write-Output 'HP_SYSTEM_EVENT none_or_unavailable'
    }
    Remove-Item -LiteralPath $csv, $stop -ErrorAction SilentlyContinue
    $quotedScript = '"' + $PSCommandPath + '"'
    $arguments = '-NoProfile -NonInteractive -ExecutionPolicy Bypass -File ' + $quotedScript + ' -Mode Sample -OutputPath "' + $csv + '" -StopPath "' + $stop + '"'
    $worker = Start-Process powershell.exe -ArgumentList $arguments -WindowStyle Hidden -PassThru
    Write-Output ('HP_MONITOR_STARTED run={0} pid={1} interval_seconds=10 limit_minutes=50' -f $stem, $worker.Id)
    exit 0
}

if ($Mode -eq 'Stop') {
    if (-not (Test-Path -LiteralPath $root)) {
        Write-Output 'HP_MONITOR_MISSING not_started'
        exit 0
    }
    New-Item -ItemType File -Path $stop -Force | Out-Null
    if (-not (Test-Path -LiteralPath $csv)) {
        Write-Output 'HP_MONITOR_MISSING no_samples'
        exit 0
    }
    Start-Sleep -Seconds 1
    try {
        $rows = @(Import-Csv -LiteralPath $csv)
        if ($rows.Count -gt 0) {
            $minimum = ($rows | Measure-Object -Property free_virtual_mb -Minimum).Minimum
            $minPhysical = ($rows | Measure-Object -Property free_physical_mb -Minimum).Minimum
            Write-Output ('HP_MONITOR_SUMMARY run={0} samples={1} min_free_virtual_mb={2} min_free_physical_mb={3}' -f $stem, $rows.Count, $minimum, $minPhysical)
            $cpuRows = @($rows | Where-Object {
                $_.cpu_load_pct_est -match '^(100|[0-9]{1,2})$'
            })
            if ($cpuRows.Count -gt 0) {
                $load = $cpuRows | Measure-Object -Property cpu_load_pct_est -Maximum -Average
                $logical = ($cpuRows | Select-Object -Last 1).logical_processors
                Write-Output ('HP_CPU_SUMMARY run={0} samples={1} peak_host_cpu_pct_est={2} mean_host_cpu_pct_est={3} logical_processors={4}' -f $stem, $cpuRows.Count, $load.Maximum, [math]::Round($load.Average, 1), $logical)
            } else {
                Write-Output ('HP_CPU_SUMMARY run={0} samples=0 unavailable' -f $stem)
            }
            # Independently report the ten-second integrated CPU load.
            # Older memory/WMI-only CSVs have no such column and stay valid.
            $cpuWindowRows = @($rows | Where-Object {
                $_.cpu_pct_window_avg -match '^(100(\.0)?|[0-9]{1,2}(\.[0-9])?)$'
            })
            if ($cpuWindowRows.Count -gt 0) {
                $windowStats = $cpuWindowRows | Measure-Object -Property cpu_pct_window_avg -Maximum -Average
                Write-Output ('HP_CPU_WINDOW_SUMMARY run={0} samples={1} mean_host_cpu_pct_10s={2} peak_host_cpu_pct_10s={3}' -f $stem, $cpuWindowRows.Count, [math]::Round($windowStats.Average, 1), $windowStats.Maximum)
            } else {
                Write-Output ('HP_CPU_WINDOW_SUMMARY run={0} samples=0 unavailable' -f $stem)
            }
            # The build stage writes private, per-job phase timestamps. Only
            # aggregate CPU/memory samples inside the exact compile window
            # count toward the concurrency comparison. On incomplete or
            # interrupted builds, report unavailable rather than making up a
            # phase result. No new artifact or personal process data is stored.
            if ($env:RUNNER_TEMP) {
                $phaseFile = Join-Path $env:RUNNER_TEMP 'hp-compile-phase.csv'
                if (Test-Path -LiteralPath $phaseFile) {
                    try {
                        $marks = @(Import-Csv -LiteralPath $phaseFile)
                        $begins = @($marks | Where-Object { $_.phase -eq 'build_start' })
                        $ends = @($marks | Where-Object { $_.phase -eq 'build_end' })
                        if ($begins.Count -eq 1 -and $ends.Count -eq 1) {
                            $beginUtc = [datetimeoffset]::Parse($begins[0].timestamp_utc)
                            $endUtc = [datetimeoffset]::Parse($ends[0].timestamp_utc)
                            if ($endUtc -le $beginUtc) {
                                throw 'invalid_build_phase_order'
                            }
                            $compileRows = @($cpuRows | Where-Object {
                                try {
                                    $observed = [datetimeoffset]::Parse($_.timestamp_utc)
                                    $observed -ge $beginUtc -and $observed -le $endUtc
                                } catch {
                                    $false
                                }
                            })
                            if ($compileRows.Count -gt 0) {
                                $cpuStats = $compileRows | Measure-Object -Property cpu_load_pct_est -Average -Maximum
                                $compileMinVirtual = ($compileRows | Measure-Object -Property free_virtual_mb -Minimum).Minimum
                                $elapsedSeconds = [math]::Round(($endUtc - $beginUtc).TotalSeconds)
                                Write-Output ('HP_COMPILE_CPU_SUMMARY run={0} elapsed_seconds={1} samples={2} mean_host_cpu_pct_est={3} peak_host_cpu_pct_est={4} min_free_virtual_mb={5}' -f $stem, $elapsedSeconds, $compileRows.Count, [math]::Round($cpuStats.Average, 1), $cpuStats.Maximum, $compileMinVirtual)
                                $compileWindowRows = @($cpuWindowRows | Where-Object {
                                    try {
                                        $observed = [datetimeoffset]::Parse($_.timestamp_utc)
                                        $observed -ge $beginUtc -and $observed -le $endUtc
                                    } catch { $false }
                                })
                                if ($compileWindowRows.Count -gt 0) {
                                    $compileWindowStats = $compileWindowRows | Measure-Object -Property cpu_pct_window_avg -Average -Maximum
                                    Write-Output ('HP_COMPILE_CPU_WINDOW_SUMMARY run={0} elapsed_seconds={1} samples={2} mean_host_cpu_pct_10s={3} peak_host_cpu_pct_10s={4}' -f $stem, $elapsedSeconds, $compileWindowRows.Count, [math]::Round($compileWindowStats.Average, 1), $compileWindowStats.Maximum)
                                } else {
                                    Write-Output ('HP_COMPILE_CPU_WINDOW_SUMMARY run={0} unavailable=no_valid_interval_samples' -f $stem)
                                }
                            } else {
                                Write-Output ('HP_COMPILE_CPU_SUMMARY run={0} unavailable=no_valid_cpu_samples' -f $stem)
                            }
                        } else {
                            Write-Output ('HP_COMPILE_CPU_SUMMARY run={0} unavailable=incomplete_phase_markers' -f $stem)
                        }
                    } catch {
                        Write-Output ('HP_COMPILE_CPU_SUMMARY run={0} unavailable=invalid_phase_data' -f $stem)
                    }
                }
            }
        } else {
            Write-Output 'HP_MONITOR_SUMMARY no_complete_samples'
        }
        if ($env:RUNNER_TEMP) {
            Copy-Item -LiteralPath $csv -Destination (Join-Path $env:RUNNER_TEMP 'hp-commit-pressure.csv') -Force
        }
    } catch {
        Write-Output 'HP_MONITOR_SUMMARY unavailable_but_original_retained'
    }
}
