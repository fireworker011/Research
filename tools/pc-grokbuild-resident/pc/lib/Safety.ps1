# Safety preamble, secret redaction, and the fixed grok.exe argument line.
# Windows PowerShell 5.1 compatible.

Set-StrictMode -Version 2.0

function ConvertTo-RedactedText {
    param([AllowNull()][AllowEmptyString()][string]$Text)
    if ([string]::IsNullOrEmpty($Text)) { return $Text }
    $out = [regex]::Replace(
        $Text,
        '(?i)(password|passwd|pwd|secret|api[_-]?key|access[_-]?key|token|cookie|authorization|session)\s*[:=]\s*("[^"]*"|''[^'']*''|\S+)',
        '$1=«redacted»'
    )
    $out = [regex]::Replace($out, '(?i)Bearer\s+\S+', 'Bearer «redacted»')
    $out = [regex]::Replace($out, '(?i)\bsk-[A-Za-z0-9_\-]{8,}\b', '«redacted»')
    $out = [regex]::Replace($out, '(?i)\bxox[baprs]-[A-Za-z0-9\-]{8,}\b', '«redacted»')
    return $out
}

function Format-ProcessArgument {
    param([AllowNull()][string]$Value)
    if ($null -eq $Value -or $Value.Length -eq 0) { return '""' }
    if ($Value -match '[\s"]') {
        return '"' + ($Value.Replace('"', '\"')) + '"'
    }
    return $Value
}

function Get-ResidentModelName {
    return 'grok-4.7'
}

function Get-GrokArgumentLine {
    param(
        [Parameter(Mandatory = $true)][string]$PromptFile,
        [Parameter(Mandatory = $true)][string]$Effort
    )
    if ($Effort -ne 'high' -and $Effort -ne 'xhigh') {
        throw 'reasoning effort must be high or xhigh'
    }
    $model = Get-ResidentModelName
    $parts = @(
        '--prompt-file',
        (Format-ProcessArgument $PromptFile),
        '--always-approve',
        '-m',
        $model,
        '--reasoning-effort',
        $Effort
    )
    $line = $parts -join ' '
    if ($line -match '(?i)(^|\s)--fast(\s|$)') {
        throw 'fast mode is forbidden'
    }
    return $line
}

function Escape-SingleQuotedPath {
    param([string]$Path)
    return ($Path -replace "'", "''")
}

function New-SafetyPreamble {
    param(
        [Parameter(Mandatory = $true)][string]$JobId,
        [Parameter(Mandatory = $true)][string]$ConfirmDir,
        [Parameter(Mandatory = $true)][int]$TimeoutSec,
        [Parameter(Mandatory = $true)][string]$Effort
    )
    $jsonPath = Join-Path $ConfirmDir ($JobId + '.json')
    $okPath = Join-Path $ConfirmDir ($JobId + '.ok')
    $ngPath = Join-Path $ConfirmDir ($JobId + '.ng')
    $jsonLit = Escape-SingleQuotedPath $jsonPath
    $okLit = Escape-SingleQuotedPath $okPath
    $ngLit = Escape-SingleQuotedPath $ngPath
    $model = Get-ResidentModelName

    $text = @"
SYSTEM PREAMBLE
This block is added by the Grok Build resident runner. Follow it exactly.

Job id: $JobId
Model: $model
Reasoning effort: $Effort
Confirm JSON: $jsonPath
Approve file: $okPath
Deny file: $ngPath
Confirm timeout seconds: $TimeoutSec

Rules:
1. Run read-only steps immediately. Do not wait for a confirm file before read-only work.
2. Before any irreversible step (save, send, post, delete, publish, payment), stop and write one UTF-8 JSON file to the Confirm JSON path. The file must describe exactly what will change: job_id, step_id, kind, target_url, and changes with field, before, and after. One file covers every irreversible step in this order. Do not perform those steps yet.
3. Wait until the Approve file or the Deny file appears. Check about every 2 seconds. The runner kills this process when the timeout expires, which aborts the job. If the Approve file appears, do only the changes written in the JSON. If the Deny file appears, do not perform them, write a short note, and exit.
4. Never print secrets, passwords, tokens, cookies, or session values in the JSON, the log, or the chat.
5. If a login page, a password form, or a 2FA challenge appears, stop immediately and report the page URL. Do not type credentials. Do not guess a code.
6. Do not add irreversible actions that the order did not list.
7. Stay on model $model and reasoning effort $Effort. Do not lower the effort.

Wait snippet (run this before the first irreversible step, after the JSON file is written):
`$decision = 'timeout'
`$deadline = (Get-Date).AddSeconds($TimeoutSec)
while ((Get-Date) -lt `$deadline) {
  if (Test-Path -LiteralPath '$okLit') { `$decision = 'ok'; break }
  if (Test-Path -LiteralPath '$ngLit') { `$decision = 'ng'; break }
  Start-Sleep -Seconds 2
}
Write-Output `$decision
If the output is ng or timeout, do not perform the irreversible steps.
"@
    return $text.TrimEnd()
}
