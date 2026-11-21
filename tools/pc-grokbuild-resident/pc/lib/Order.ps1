# Order front matter, sha256, lane, and FIFO selection.
# Windows PowerShell 5.1 compatible. Avoid pipeline chain operators and the null-coalescing operator.

Set-StrictMode -Version 2.0

$script:IrreversibleKinds = @('save', 'send', 'post', 'delete', 'publish', 'payment')

function ConvertFrom-Scalar {
    param([string]$Value)
    if ($null -eq $Value) { return '' }
    $v = $Value.Trim()
    if ($v.Length -ge 2) {
        $q = $v.Substring(0, 1)
        if (($q -eq '"' -or $q -eq "'") -and $v.Substring($v.Length - 1, 1) -eq $q) {
            return $v.Substring(1, $v.Length - 2)
        }
    }
    return $v
}

function Read-TextFile {
    param([Parameter(Mandatory = $true)][string]$Path)
    $bytes = [System.IO.File]::ReadAllBytes($Path)
    if ($bytes.Length -ge 2 -and (($bytes[0] -eq 0xFF -and $bytes[1] -eq 0xFE) -or ($bytes[0] -eq 0xFE -and $bytes[1] -eq 0xFF))) {
        throw 'UTF-16 orders are not supported; save as UTF-8'
    }
    if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
        return [System.Text.Encoding]::UTF8.GetString($bytes, 3, $bytes.Length - 3)
    }
    return [System.Text.Encoding]::UTF8.GetString($bytes)
}

function Write-Utf8File {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][AllowEmptyString()][string]$Text
    )
    $dir = [System.IO.Path]::GetDirectoryName($Path)
    if (-not [string]::IsNullOrWhiteSpace($dir)) {
        [void][System.IO.Directory]::CreateDirectory($dir)
    }
    $utf8 = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($Path, $Text, $utf8)
}

function Split-OrderText {
    param([Parameter(Mandatory = $true)][AllowEmptyString()][string]$Text)
    if ([string]::IsNullOrWhiteSpace($Text)) {
        throw 'front matter must start with --- and close with ---'
    }
    $norm = $Text -replace "`r`n", "`n" -replace "`r", "`n"
    $match = [regex]::Match($norm, '\A---\n(.*?)\n---(?:\n(.*))?\z', [System.Text.RegularExpressions.RegexOptions]::Singleline)
    if (-not $match.Success) {
        throw 'front matter must start with --- and close with ---'
    }
    $body = ''
    if ($match.Groups[2].Success) {
        $body = $match.Groups[2].Value
    }
    return [pscustomobject]@{
        Front      = $match.Groups[1].Value
        Body       = $body
        Normalized = $norm
    }
}

function Get-OrderBodySha256 {
    param([Parameter(Mandatory = $true)][AllowEmptyString()][string]$Body)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($Body)
        $hash = $sha.ComputeHash($bytes)
        return ([System.BitConverter]::ToString($hash)).Replace('-', '').ToLowerInvariant()
    }
    finally {
        $sha.Dispose()
    }
}

function ConvertFrom-OrderFrontMatter {
    param([Parameter(Mandatory = $true)][AllowEmptyString()][string]$Front)
    $meta = @{}
    $steps = New-Object System.Collections.Generic.List[object]
    $inSteps = $false
    $current = $null
    $lines = $Front -split "`n"
    foreach ($line in $lines) {
        if ($line -match '^\s*$' -or $line -match '^\s*#') { continue }
        if ($line -match '^steps:\s*$') {
            if ($inSteps) { throw 'duplicate steps block' }
            $inSteps = $true
            continue
        }
        if ($inSteps -and $line -match '^  - id:\s*(.*)$') {
            if ($null -ne $current) { $steps.Add($current) }
            $current = [pscustomobject]@{
                id      = (ConvertFrom-Scalar $Matches[1])
                mode    = ''
                kind    = ''
                summary = ''
            }
            continue
        }
        if ($inSteps -and $line -match '^    ([A-Za-z0-9_]+):\s*(.*)$') {
            if ($null -eq $current) { throw 'step field before a step id' }
            $key = $Matches[1]
            $val = ConvertFrom-Scalar $Matches[2]
            if ($key -eq 'mode' -or $key -eq 'kind' -or $key -eq 'summary' -or $key -eq 'id') {
                $current.$key = $val
            }
            continue
        }
        if ($line -match '^([A-Za-z0-9_]+):\s*(.*)$') {
            if ($inSteps) {
                if ($null -ne $current) {
                    $steps.Add($current)
                    $current = $null
                }
                $inSteps = $false
            }
            $key = $Matches[1]
            if ($meta.ContainsKey($key)) { throw "duplicate front matter key: $key" }
            $meta[$key] = ConvertFrom-Scalar $Matches[2]
            continue
        }
        throw "cannot parse front matter line: $line"
    }
    if ($null -ne $current) { $steps.Add($current) }
    $meta['steps'] = $steps
    return $meta
}

function ConvertTo-StepMode {
    param([string]$Mode)
    if ([string]::IsNullOrWhiteSpace($Mode)) { return $null }
    $v = $Mode.Trim().ToLowerInvariant()
    if ($v -eq 'read-only' -or $v -eq 'readonly' -or $v -eq 'read') { return 'read-only' }
    if ($v -eq 'irreversible' -or $v -eq 'write') { return 'irreversible' }
    return $null
}

function Resolve-ReasoningEffort {
    param([string]$Value)
    if ([string]::IsNullOrWhiteSpace($Value)) { return 'xhigh' }
    $v = $Value.Trim().ToLowerInvariant()
    if ($v -eq 'high' -or $v -eq 'xhigh') { return $v }
    return $null
}

function ConvertTo-SafeJobId {
    param([string]$Value)
    if ($Value -match '^[A-Za-z0-9][A-Za-z0-9._-]{0,80}$') { return $Value }
    return 'invalid-order'
}

function Test-OrderText {
    param([Parameter(Mandatory = $true)][AllowEmptyString()][string]$Text)
    $errors = New-Object System.Collections.Generic.List[string]
    $doc = [pscustomobject]@{
        Ok          = $false
        Errors      = @()
        Id          = $null
        Lane        = $null
        Reasoning   = 'xhigh'
        TimeoutSec  = 600
        Seq         = $null
        Steps       = @()
        Body        = ''
        Normalized  = ''
        Model       = 'grok-4.7'
        HasSha256   = $false
    }

    $split = $null
    try {
        $split = Split-OrderText $Text
    }
    catch {
        $errors.Add($_.Exception.Message)
        $doc.Errors = $errors.ToArray()
        return $doc
    }
    $doc.Normalized = $split.Normalized
    $doc.Body = $split.Body

    $meta = $null
    try {
        $meta = ConvertFrom-OrderFrontMatter $split.Front
    }
    catch {
        $errors.Add($_.Exception.Message)
        $doc.Errors = $errors.ToArray()
        return $doc
    }

    $id = $null
    if ($meta.ContainsKey('id')) { $id = [string]$meta['id'] }
    if ([string]::IsNullOrWhiteSpace($id) -or $id -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]{0,80}$') {
        $errors.Add('id must match ^[A-Za-z0-9][A-Za-z0-9._-]{0,80}$')
    }
    else {
        $doc.Id = $id
    }

    $effortValue = $null
    if ($meta.ContainsKey('reasoning')) { $effortValue = [string]$meta['reasoning'] }
    $effort = Resolve-ReasoningEffort $effortValue
    if ($null -eq $effort) {
        $errors.Add('reasoning must be high or xhigh')
    }
    else {
        $doc.Reasoning = $effort
    }

    if ($meta.ContainsKey('model')) {
        $model = ([string]$meta['model']).Trim()
        if ($model -ne 'grok-4.7') {
            $errors.Add('model must be grok-4.7')
        }
    }

    if ($meta.ContainsKey('fast')) {
        $fv = ([string]$meta['fast']).Trim().ToLowerInvariant()
        if ($fv -eq 'true' -or $fv -eq '1' -or $fv -eq 'yes') {
            $errors.Add('fast mode is not allowed')
        }
    }

    if ($meta.ContainsKey('confirm_timeout_sec')) {
        $rawTimeout = [string]$meta['confirm_timeout_sec']
        $parsedTimeout = 0
        if (-not [int]::TryParse($rawTimeout, [ref]$parsedTimeout) -or $parsedTimeout -lt 1 -or $parsedTimeout -gt 86400) {
            $errors.Add('confirm_timeout_sec must be an integer from 1 to 86400')
        }
        else {
            $doc.TimeoutSec = $parsedTimeout
        }
    }

    if ($meta.ContainsKey('seq')) {
        $rawSeq = [string]$meta['seq']
        $parsedSeq = 0
        if (-not [int]::TryParse($rawSeq, [ref]$parsedSeq)) {
            $errors.Add('seq must be an integer')
        }
        else {
            $doc.Seq = $parsedSeq
        }
    }

    if ($meta.ContainsKey('sha256')) {
        $doc.HasSha256 = $true
        $given = ([string]$meta['sha256']).Trim().ToLowerInvariant()
        $actual = Get-OrderBodySha256 $split.Body
        if ($given -notmatch '^[0-9a-f]{64}$' -or $given -ne $actual) {
            $errors.Add('sha256 mismatch')
        }
    }

    $stepObjects = New-Object System.Collections.Generic.List[object]
    $seenStep = @{}
    $irreversible = 0
    foreach ($step in $meta['steps']) {
        $stepId = [string]$step.id
        $mode = ConvertTo-StepMode ([string]$step.mode)
        if ([string]::IsNullOrWhiteSpace($stepId)) {
            $errors.Add('a step is missing id')
            continue
        }
        if ($seenStep.ContainsKey($stepId)) {
            $errors.Add("duplicate step id: $stepId")
        }
        $seenStep[$stepId] = $true
        if ($null -eq $mode) {
            $errors.Add("step ${stepId} mode must be read-only or irreversible")
        }
        if ([string]::IsNullOrWhiteSpace([string]$step.summary)) {
            $errors.Add("step ${stepId} needs a summary")
        }
        $kind = ''
        if (-not [string]::IsNullOrWhiteSpace([string]$step.kind)) {
            $kind = ([string]$step.kind).Trim().ToLowerInvariant()
        }
        if ($mode -eq 'irreversible') {
            $irreversible++
            if ($script:IrreversibleKinds -notcontains $kind) {
                $errors.Add("step ${stepId} kind must be save, send, post, delete, publish, or payment")
            }
        }
        $stepObjects.Add([pscustomobject]@{
                id      = $stepId
                mode    = $mode
                kind    = $kind
                summary = [string]$step.summary
            })
    }
    if ($stepObjects.Count -eq 0) {
        $errors.Add('order needs at least one step')
    }
    $doc.Steps = $stepObjects.ToArray()

    $laneRaw = $null
    if ($meta.ContainsKey('lane')) { $laneRaw = ([string]$meta['lane']).Trim().ToLowerInvariant() }
    $lane = $null
    if ([string]::IsNullOrWhiteSpace($laneRaw)) {
        if ($irreversible -gt 0) { $lane = 'main' } else { $lane = 'readonly' }
    }
    elseif ($laneRaw -eq 'main') {
        $lane = 'main'
    }
    elseif ($laneRaw -eq 'readonly' -or $laneRaw -eq 'read-only') {
        $lane = 'readonly'
    }
    else {
        $errors.Add('lane must be main or readonly')
    }
    if ($lane -eq 'readonly' -and $irreversible -gt 0) {
        $errors.Add('readonly lane cannot contain irreversible steps')
        $lane = $null
    }
    $doc.Lane = $lane

    $doc.Errors = $errors.ToArray()
    $doc.Ok = ($errors.Count -eq 0)
    return $doc
}

function Add-OrderSha256Text {
    param([Parameter(Mandatory = $true)][AllowEmptyString()][string]$Text)
    $split = Split-OrderText $Text
    $hash = Get-OrderBodySha256 $split.Body
    $existing = [regex]::Matches($split.Front, '(?m)^sha256:\s*([0-9a-fA-F]+)\s*$')
    if ($existing.Count -gt 1) { throw 'duplicate sha256' }
    if ($existing.Count -eq 1) {
        if ($existing[0].Groups[1].Value.ToLowerInvariant() -ne $hash) {
            throw 'sha256 mismatch'
        }
        return $split.Normalized
    }
    $front = $split.Front.TrimEnd("`n")
    return "---`n$front`nsha256: $hash`n---`n$($split.Body)"
}

function Sort-OrderCandidates {
    param($Items)
    $list = New-Object System.Collections.Generic.List[object]
    if ($null -ne $Items) {
        foreach ($item in $Items) {
            if ($null -ne $item) { $list.Add($item) }
        }
    }
    if ($list.Count -le 1) {
        Write-Output -NoEnumerate $list.ToArray()
        return
    }
    $sorted = $list.ToArray() | Sort-Object -Property @{
        Expression = { if ($null -eq $_.Seq) { 1 } else { 0 } }
    }, @{
        Expression = { if ($null -eq $_.Seq) { 0 } else { [int]$_.Seq } }
    }, @{
        Expression = { [string]$_.Name }
    }
    $out = New-Object System.Collections.Generic.List[object]
    foreach ($item in $sorted) {
        if ($null -ne $item) { $out.Add($item) }
    }
    Write-Output -NoEnumerate $out.ToArray()
}

function Select-NextOrders {
    param(
        [array]$Candidates,
        [bool]$MainBusy,
        [bool]$ReadOnlyBusy
    )
    $sorted = Sort-OrderCandidates $Candidates
    $picked = New-Object System.Collections.Generic.List[object]
    $haveMain = $MainBusy
    $haveReadOnly = $ReadOnlyBusy
    foreach ($item in $sorted) {
        if ($item.Lane -eq 'main') {
            if (-not $haveMain) {
                $picked.Add($item)
                $haveMain = $true
            }
        }
        elseif ($item.Lane -eq 'readonly') {
            if (-not $haveReadOnly) {
                $picked.Add($item)
                $haveReadOnly = $true
            }
        }
    }
    Write-Output -NoEnumerate $picked.ToArray()
}
