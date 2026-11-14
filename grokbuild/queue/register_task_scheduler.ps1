# Registers the local queue runner with Windows Task Scheduler.
# Running this file does not edit job instruction documents.
# The task is not started unless -RunNow is passed.
param(
    [string]$Python = "python",
    [string]$TaskName = "GrokbuildQueueRunner",
    [ValidateSet("HOURLY", "MINUTE", "ONLOGON")]
    [string]$Schedule = "HOURLY",
    [switch]$RunNow
)

$ErrorActionPreference = "Stop"
$runner = Join-Path $PSScriptRoot "queue_runner.py"
if (-not (Test-Path -LiteralPath $runner)) {
    throw "queue_runner.py not found: $runner"
}

$taskRun = "`"$Python`" `"$runner`""
& schtasks.exe /Create /F /TN $TaskName /SC $Schedule /TR $taskRun
if ($LASTEXITCODE -ne 0) {
    throw "schtasks exited with $LASTEXITCODE"
}

if ($RunNow) {
    & schtasks.exe /Run /TN $TaskName
    if ($LASTEXITCODE -ne 0) {
        throw "schtasks /Run exited with $LASTEXITCODE"
    }
}
