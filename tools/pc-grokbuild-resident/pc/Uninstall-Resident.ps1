#requires -Version 5.1
# Stop the watcher and remove the logon task. Queue files stay on disk.
param(
    [string]$Root
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
& (Join-Path $here 'Stop-Resident.ps1') -Root $Root

if ($env:OS -eq 'Windows_NT') {
    Import-Module (Join-Path (Join-Path $here 'lib') 'GrokBuildResident.psm1') -Force
    $task = Get-ScheduledTask -TaskName (Get-ResidentTaskName) -ErrorAction SilentlyContinue
    if ($null -ne $task) {
        Unregister-ScheduledTask -TaskName (Get-ResidentTaskName) -Confirm:$false
        Write-Output 'scheduled task removed'
    }
}
else {
    Write-Output 'No Scheduled Task on this OS. Queue data was left in place.'
}
