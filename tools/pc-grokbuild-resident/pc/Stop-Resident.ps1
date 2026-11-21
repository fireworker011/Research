#requires -Version 5.1
param(
    [string]$Root,
    [int]$WaitSec = 15
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Import-Module (Join-Path (Join-Path $here 'lib') 'GrokBuildResident.psm1') -Force

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

$paths = Initialize-ResidentTree $Root
$utf8 = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($paths.Stop, "stop`n", $utf8)

if ($env:OS -eq 'Windows_NT') {
    $task = Get-ScheduledTask -TaskName (Get-ResidentTaskName) -ErrorAction SilentlyContinue
    if ($null -ne $task -and [string]$task.State -eq 'Running') {
        Stop-ScheduledTask -TaskName (Get-ResidentTaskName)
    }
}

$oldPid = 0
if ([System.IO.File]::Exists($paths.Pid)) {
    $rawPid = ([System.IO.File]::ReadAllText($paths.Pid)).Trim()
    [void][int]::TryParse($rawPid, [ref]$oldPid)
}

$deadline = [datetime]::UtcNow.AddSeconds($WaitSec)
while ($oldPid -gt 0 -and [datetime]::UtcNow -lt $deadline) {
    $alive = Get-Process -Id $oldPid -ErrorAction SilentlyContinue
    if ($null -eq $alive) { break }
    Start-Sleep -Milliseconds 300
}

$still = $null
if ($oldPid -gt 0) {
    $still = Get-Process -Id $oldPid -ErrorAction SilentlyContinue
}
if ($null -ne $still) {
    if ($env:OS -eq 'Windows_NT') {
        & taskkill.exe /PID $oldPid /T /F | Out-Null
    }
    else {
        Stop-Process -Id $oldPid -Force -ErrorAction SilentlyContinue
    }
    Write-Output ("stopped pid " + $oldPid)
}
else {
    Write-Output 'stop requested'
}
