#requires -Version 5.1
# Copy the watcher under the grokbuild root and register a per-user logon task.
param(
    [string]$Root,
    [string]$UserName = 'hp',
    [string]$ComputerName = 'LAPTOP-PL4TICBO',
    [string]$GrokExe = 'C:\Users\hp\.grok\bin\grok.exe',
    [switch]$StartNow,
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
        throw 'Pass -Root. On the PC the default is Documents\grokbuild for the logged-in user.'
    }
}
if ($env:OS -eq 'Windows_NT' -and -not [string]::IsNullOrWhiteSpace($env:COMPUTERNAME)) {
    if ($ComputerName -eq 'LAPTOP-PL4TICBO' -and $env:COMPUTERNAME -ne 'LAPTOP-PL4TICBO') {
        $ComputerName = $env:COMPUTERNAME
    }
}

$dest = Join-Path $Root 'resident'
$destLib = Join-Path $dest 'lib'
[void][System.IO.Directory]::CreateDirectory($destLib)
Initialize-ResidentTree $Root | Out-Null

$names = @(
    'Resident.ps1',
    'Install-Resident.ps1',
    'Start-Resident.ps1',
    'Stop-Resident.ps1',
    'Uninstall-Resident.ps1',
    'Run-GrokLogged.ps1'
)
foreach ($name in $names) {
    Copy-Item -LiteralPath (Join-Path $here $name) -Destination (Join-Path $dest $name) -Force
}
Get-ChildItem -LiteralPath (Join-Path $here 'lib') -File | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $destLib $_.Name) -Force
}

$installedResident = Join-Path $dest 'Resident.ps1'
Write-Output ("installed " + $installedResident)

if ($SkipTask -or $env:OS -ne 'Windows_NT') {
    if ($env:OS -ne 'Windows_NT') {
        Write-Output 'Scheduled Task is Windows-only. Directories are ready.'
    }
    else {
        Write-Output 'SkipTask set. Scheduled Task was not registered.'
    }
    return
}

$shell = 'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe'
$arg = '-NoProfile -WindowStyle Hidden -NonInteractive -ExecutionPolicy Bypass -File "' + $installedResident + '" -Root "' + $Root + '" -UserName ' + $UserName + ' -HostName ' + $ComputerName + ' -GrokExe "' + $GrokExe + '"'
$action = New-ScheduledTaskAction -Execute $shell -Argument $arg
$account = $ComputerName + '\' + $UserName
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $account
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -MultipleInstances IgnoreNew -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit ([TimeSpan]::Zero)
$principal = New-ScheduledTaskPrincipal -UserId $account -LogonType Interactive -RunLevel Limited
$task = New-ScheduledTask -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description 'Watch the grokbuild inbox and run Grok Build orders.'
Register-ScheduledTask -TaskName (Get-ResidentTaskName) -InputObject $task -Force | Out-Null
Write-Output ("task " + (Get-ResidentTaskName) + " registered for " + $account)

if ($StartNow) {
    Start-ScheduledTask -TaskName (Get-ResidentTaskName)
    Write-Output 'task started'
}
