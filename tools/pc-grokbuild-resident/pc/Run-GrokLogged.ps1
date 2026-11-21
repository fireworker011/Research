#requires -Version 5.1
# Child process: start grok.exe, redact its output, exit with grok's code.
param(
    [Parameter(Mandatory = $true)][string]$GrokExe,
    [Parameter(Mandatory = $true)][string]$PromptFile,
    [Parameter(Mandatory = $true)][string]$Effort,
    [Parameter(Mandatory = $true)][string]$LogPath
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Import-Module (Join-Path (Join-Path $here 'lib') 'GrokBuildResident.psm1') -Force

if ($Effort -ne 'high' -and $Effort -ne 'xhigh') {
    [Console]::Error.WriteLine('reasoning effort must be high or xhigh')
    exit 11
}

$argLine = Get-GrokArgumentLine -PromptFile $PromptFile -Effort $Effort
if ($argLine -match '(?i)(^|\s)--fast(\s|$)') {
    [Console]::Error.WriteLine('fast mode is forbidden')
    exit 13
}
if (-not (Test-Path -LiteralPath $GrokExe)) {
    [Console]::Error.WriteLine('grok.exe not found')
    exit 12
}

$utf8 = New-Object System.Text.UTF8Encoding $false
$dir = [System.IO.Path]::GetDirectoryName($LogPath)
if (-not [string]::IsNullOrWhiteSpace($dir)) {
    [void][System.IO.Directory]::CreateDirectory($dir)
}

# Same replacements as ConvertTo-RedactedText. Kept inline so the log runspace
# does not need the module.
$drain = @'
param($reader, $logPath, $mutexName)
$utf8 = New-Object System.Text.UTF8Encoding $false
$mutex = New-Object System.Threading.Mutex($false, $mutexName)
while ($null -ne ($line = $reader.ReadLine())) {
    $clean = [regex]::Replace($line, "(?i)(password|passwd|pwd|secret|api[_-]?key|access[_-]?key|token|cookie|authorization|session)\s*[:=]\s*(`"[^`"]*`"|'[^']*'|\S+)", '$1=«redacted»')
    $clean = [regex]::Replace($clean, '(?i)Bearer\s+\S+', 'Bearer «redacted»')
    $clean = [regex]::Replace($clean, '(?i)\bsk-[A-Za-z0-9_\-]{8,}\b', '«redacted»')
    $clean = [regex]::Replace($clean, '(?i)\bxox[baprs]-[A-Za-z0-9\-]{8,}\b', '«redacted»')
    [void]$mutex.WaitOne()
    try {
        [System.IO.File]::AppendAllText($logPath, $clean + [Environment]::NewLine, $utf8)
    }
    finally {
        $mutex.ReleaseMutex()
    }
}
$mutex.Dispose()
'@

$mutexName = 'GrokBuildLog' + $PID
[System.IO.File]::WriteAllText($LogPath, ("model=grok-4.7 effort=" + $Effort + [Environment]::NewLine), $utf8)

$proc = New-Object System.Diagnostics.Process
$proc.StartInfo.FileName = $GrokExe
$proc.StartInfo.Arguments = $argLine
$proc.StartInfo.UseShellExecute = $false
$proc.StartInfo.CreateNoWindow = $true
$proc.StartInfo.RedirectStandardOutput = $true
$proc.StartInfo.RedirectStandardError = $true
[void]$proc.Start()

function Start-LogDrain {
    param($Reader)
    $rs = [runspacefactory]::CreateRunspace()
    $rs.Open()
    $ps = [powershell]::Create()
    $ps.Runspace = $rs
    [void]$ps.AddScript($drain).AddArgument($Reader).AddArgument($LogPath).AddArgument($mutexName)
    return @{ Ps = $ps; Rs = $rs; Async = $ps.BeginInvoke() }
}

$outDrain = Start-LogDrain $proc.StandardOutput
$errDrain = Start-LogDrain $proc.StandardError
try {
    $proc.WaitForExit()
    $outDrain.Ps.EndInvoke($outDrain.Async) | Out-Null
    $errDrain.Ps.EndInvoke($errDrain.Async) | Out-Null
    $code = [int]$proc.ExitCode
}
finally {
    if (-not $proc.HasExited) {
        try { $proc.Kill() } catch { }
    }
    $outDrain.Ps.Dispose()
    $outDrain.Rs.Dispose()
    $errDrain.Ps.Dispose()
    $errDrain.Rs.Dispose()
    $proc.Dispose()
}
exit $code
