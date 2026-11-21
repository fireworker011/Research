#requires -Version 5.1
Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Cases.ps1')
$failed = Invoke-ResidentCases
if ($failed -gt 0) {
    Write-Output ("FAILED " + $failed)
    exit 1
}
Write-Output 'ALL PASS'
exit 0
