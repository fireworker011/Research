#requires -Version 5.1
param(
    [string]$Root,
    [string]$UserName = 'hp',
    [string]$HostName = 'LAPTOP-PL4TICBO',
    [string]$GrokExe = 'C:\Users\hp\.grok\bin\grok.exe',
    [switch]$SkipTask
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
if ([System.IO.File]::Exists($paths.Stop)) {
    Remove-Item -LiteralPath $paths.Stop -Force
}

$startedTask = $false
if (-not $SkipTask -and $env:OS -eq 'Windows_NT') {
    $task = Get-ScheduledTask -TaskName (Get-ResidentTaskName) -ErrorAction SilentlyContinue
    if ($null -ne $task) {
        if ([string]$task.State -ne 'Running') {
            Start-ScheduledTask -TaskName (Get-ResidentTaskName)
        }
        $startedTask = $true
        Write-Output 'scheduled task started'
    }
}
if ($startedTask) { return }

$resident = Join-Path $here 'Resident.ps1'
$arg = '-NoProfile -NonInteractive -ExecutionPolicy Bypass -File "' + $resident + '" -Root "' + $Root + '" -UserName ' + $UserName + ' -HostName ' + $HostName + ' -GrokExe "' + $GrokExe + '"'
if ($env:OS -eq 'Windows_NT') {
    $shell = 'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe'
    Start-Process -FilePath $shell -ArgumentList $arg -WindowStyle Hidden | Out-Null
}
else {
    $shell = (Get-Command pwsh -ErrorAction Stop).Source
    Start-Process -FilePath $shell -ArgumentList $arg | Out-Null
}
Write-Output 'resident process started'
