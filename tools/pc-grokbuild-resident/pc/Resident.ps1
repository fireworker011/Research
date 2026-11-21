#requires -Version 5.1
# Long-running inbox watcher. One main job, plus one read-only job.
param(
    [string]$Root,
    [string]$GrokExe = 'C:\Users\hp\.grok\bin\grok.exe',
    [int]$PollMs = 1000,
    [int]$HeartbeatSec = 10,
    [switch]$Once,
    [string]$HostName = 'LAPTOP-PL4TICBO',
    [string]$UserName = 'hp'
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Import-Module (Join-Path (Join-Path $here 'lib') 'GrokBuildResident.psm1') -Force

if (-not [string]::IsNullOrWhiteSpace($env:GROKBUILD_GROK_EXE) -and $GrokExe -eq 'C:\Users\hp\.grok\bin\grok.exe') {
    $GrokExe = $env:GROKBUILD_GROK_EXE
}
if ([string]::IsNullOrWhiteSpace($Root)) {
    if (-not [string]::IsNullOrWhiteSpace($env:GROKBUILD_ROOT)) {
        $Root = $env:GROKBUILD_ROOT
    }
    elseif ($env:OS -eq 'Windows_NT' -and -not [string]::IsNullOrWhiteSpace($env:USERPROFILE)) {
        $Root = Join-Path (Join-Path $env:USERPROFILE 'Documents') 'grokbuild'
    }
    else {
        throw 'Pass -Root or set GROKBUILD_ROOT. On the PC the default is Documents\grokbuild.'
    }
}
if ($PollMs -lt 200) { $PollMs = 200 }
if ($HeartbeatSec -lt 1) { $HeartbeatSec = 1 }

$paths = Initialize-ResidentTree $Root
$utf8 = New-Object System.Text.UTF8Encoding $false

if ([System.IO.File]::Exists($paths.Pid)) {
    $rawPid = ([System.IO.File]::ReadAllText($paths.Pid)).Trim()
    $oldPid = 0
    if ([int]::TryParse($rawPid, [ref]$oldPid) -and $oldPid -gt 0) {
        $alive = Get-Process -Id $oldPid -ErrorAction SilentlyContinue
        if ($alive) {
            Write-Error "resident already running pid $oldPid"
            exit 1
        }
    }
}

$mutex = $null
if ($env:OS -eq 'Windows_NT') {
    $mutex = New-Object System.Threading.Mutex($false, 'Local\GrokBuildResident')
    if (-not $mutex.WaitOne(0)) {
        Write-Error 'resident already running'
        exit 1
    }
}

[System.IO.File]::WriteAllText($paths.Pid, ([string]$PID + "`n"), $utf8)
$state = New-ResidentState -Root $Root -GrokExe $GrokExe -HostName $HostName -UserName $UserName

try {
    Repair-OrphanedRunningOrders -State $state -Now ([datetime]::UtcNow)
    Write-ResidentLog -Root $Root -Message ("resident start pid=" + $PID)
    $lastBeat = [datetime]::MinValue
    while ($true) {
        if ([System.IO.File]::Exists($paths.Stop)) {
            Stop-ResidentJobs -State $state -Now ([datetime]::UtcNow) -Reason 'stop requested'
            Write-ResidentLog -Root $Root -Message 'resident stop'
            break
        }
        $now = [datetime]::UtcNow
        try {
            Invoke-ResidentTick -State $state -Now $now | Out-Null
        }
        catch {
            Write-ResidentLog -Root $Root -Message ("tick error: " + $_.Exception.Message)
        }
        $due = ($lastBeat -eq [datetime]::MinValue)
        if (-not $due) {
            $due = (($now - $lastBeat).TotalSeconds -ge $HeartbeatSec)
        }
        if ($due) {
            Write-ResidentHeartbeat -State $state -Now $now -IntervalSec $HeartbeatSec
            $lastBeat = $now
        }
        if ($Once) { break }
        Start-Sleep -Milliseconds $PollMs
    }
}
finally {
    if ([System.IO.File]::Exists($paths.Pid)) {
        Remove-Item -LiteralPath $paths.Pid -Force
    }
    if ($null -ne $mutex) {
        try { $mutex.ReleaseMutex() } catch { }
        $mutex.Dispose()
    }
}
exit 0
