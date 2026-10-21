# night-runner.ps1 — 夜間自動実行（20:00〜04:00 JST）
# 対象: Windows PowerShell 5.1
# 優先順: queue\1-video → queue\2-cg → queue\3-sakura（各フォルダ内はファイル名順）
# レーン: chrome / edge / none。各レーン同時1本。ジョブmd先頭20行の lane で指定（無ければ none）
# 03:30以降は新規開始しない。04:00に、このスクリプトが記録したPIDだけ止める。
# Windowsはシャットダウンしない。電源断のコマンドは置かない。
# grok の起動引数: --prompt-file <job> --always-approve --background-wait-timeout
[CmdletBinding()]
param(
    [string]$Root = 'C:\Users\hp\Documents\grokbuild',
    [string]$Grok = 'grok.exe',
    [string]$StopNew = '03:30',
    [string]$KillAt = '04:00',
    [int]$PollSec = 60,
    [int]$MaxIterations = 0,
    [scriptblock]$NowProvider,
    [switch]$DryRun
)

function Get-JstNow {
    $tz = $null
    foreach ($id in @('Tokyo Standard Time', 'Asia/Tokyo')) {
        try {
            $tz = [TimeZoneInfo]::FindSystemTimeZoneById($id)
            break
        }
        catch {
            $tz = $null
        }
    }
    if ($null -eq $tz) {
        throw 'JSTのタイムゾーン（Tokyo Standard Time / Asia/Tokyo）が見つからない'
    }
    return [TimeZoneInfo]::ConvertTimeFromUtc([DateTime]::UtcNow, $tz)
}

function Get-NightNow {
    if ($null -ne $script:NowProvider) {
        return [datetime](& $script:NowProvider)
    }
    return (Get-JstNow)
}

function Get-NightStart {
    param([Parameter(Mandatory = $true)][datetime]$Now)
    if ($Now.Hour -lt 20) {
        return $Now.Date.AddDays(-1)
    }
    return $Now.Date
}

function Test-NightRunWindow {
    param([Parameter(Mandatory = $true)][datetime]$Now)
    return (($Now.Hour -ge 20) -or ($Now.Hour -lt 4))
}

function Get-NightMutexName {
    param([Parameter(Mandatory = $true)][string]$RootPath)
    $full = [IO.Path]::GetFullPath($RootPath).ToLowerInvariant()
    $md5 = [System.Security.Cryptography.MD5]::Create()
    try {
        $bytes = $md5.ComputeHash([Text.Encoding]::UTF8.GetBytes($full))
    }
    finally {
        $md5.Dispose()
    }
    $hex = ([BitConverter]::ToString($bytes)).Replace('-', '').Substring(0, 16).ToLowerInvariant()
    return "grokbuild-night-runner-$hex"
}

function New-NightMutex {
    param([Parameter(Mandatory = $true)][string]$Name)
    $candidates = @("Global\$Name", "Local\$Name", $Name)
    foreach ($candidate in $candidates) {
        try {
            return (New-Object System.Threading.Mutex($false, $candidate))
        }
        catch {
            continue
        }
    }
    throw "mutexを作れない: $Name"
}

function Write-NightLog {
    param([Parameter(Mandatory = $true)][string]$Message)
    $line = '{0} {1}' -f (Get-NightNow).ToString('yyyy-MM-dd HH:mm:ss'), $Message
    if ($script:Log) {
        Add-Content -LiteralPath $script:Log -Value $line -Encoding UTF8
    }
    Write-Host $line
}

function Get-GrokArgumentLine {
    param([Parameter(Mandatory = $true)][string]$JobPath)
    $quoted = $JobPath.Replace('"', '\"')
    return "--prompt-file `"$quoted`" --always-approve --background-wait-timeout"
}

function Get-JobMeta {
    param([Parameter(Mandatory = $true)][string]$Path)
    $meta = @{
        lane        = 'none'
        requires    = @()
        review      = 'true'
        imagine     = 'false'
        timeout_min = 0
    }
    $lines = @(Get-Content -LiteralPath $Path -TotalCount 20 -Encoding UTF8)
    foreach ($line in $lines) {
        if ($line -match '^\s*(lane|requires|review|imagine|timeout_min)\s*:\s*(.+?)\s*$') {
            $key = $Matches[1]
            $value = ($Matches[2] -replace '\s+#.*$', '').Trim()
            if ($key -eq 'requires') {
                $meta[$key] = @($value -split '\s*,\s*' | Where-Object { $_ })
            }
            elseif ($key -eq 'timeout_min') {
                $parsed = 0
                if ([int]::TryParse($value, [ref]$parsed)) {
                    $meta[$key] = $parsed
                }
            }
            else {
                $meta[$key] = $value.ToLowerInvariant()
            }
        }
    }
    if (@('chrome', 'edge', 'none') -notcontains $meta.lane) {
        $meta.lane = 'none'
    }
    return $meta
}

function Get-NextReadyJob {
    param([Parameter(Mandatory = $true)][string]$Lane)
    foreach ($prio in @('1-video', '2-cg', '3-sakura')) {
        $dir = Join-Path $script:Queue $prio
        if (-not (Test-Path -LiteralPath $dir)) {
            continue
        }
        $files = @(Get-ChildItem -LiteralPath $dir -Filter *.md -ErrorAction SilentlyContinue | Sort-Object Name)
        foreach ($file in $files) {
            if ($file.Name -like 'TEMPLATE*') {
                continue
            }
            $meta = Get-JobMeta -Path $file.FullName
            if ($meta.lane -ne $Lane) {
                continue
            }
            $ready = $true
            foreach ($required in @($meta.requires)) {
                if (-not $required) {
                    continue
                }
                $inDone = Test-Path -LiteralPath (Join-Path $script:Done $required)
                $inReview = Test-Path -LiteralPath (Join-Path $script:Rev $required)
                if ((-not $inDone) -and (-not $inReview)) {
                    $ready = $false
                    break
                }
            }
            if ($ready) {
                return @{ file = $file; meta = $meta; prio = $prio }
            }
        }
    }
    return $null
}

function ConvertTo-NightJson {
    param($Items)
    $list = New-Object System.Collections.ArrayList
    foreach ($item in @($Items)) {
        if ($null -ne $item) {
            [void]$list.Add($item)
        }
    }
    if ($list.Count -eq 0) {
        return '[]'
    }
    if ($list.Count -eq 1) {
        $one = ConvertTo-Json -InputObject $list[0] -Depth 4 -Compress
        return "[$one]"
    }
    return (ConvertTo-Json -InputObject @($list.ToArray()) -Depth 4 -Compress)
}

function Read-NightState {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        return @()
    }
    $raw = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
    if ([string]::IsNullOrWhiteSpace($raw)) {
        return @()
    }
    $obj = $raw | ConvertFrom-Json
    if ($null -eq $obj) {
        return @()
    }
    return @($obj)
}

function Save-NightState {
    $items = New-Object System.Collections.ArrayList
    foreach ($lane in @($script:Running.Keys)) {
        $entry = $script:Running[$lane]
        [void]$items.Add([pscustomobject]@{
                lane    = [string]$lane
                pid     = [int]$entry.pid
                name    = [string]$entry.name
                job     = [string]$entry.job
                started = ([datetime]$entry.start).ToString('yyyy-MM-ddTHH:mm:ss')
            })
    }
    $json = ConvertTo-NightJson -Items $items.ToArray()
    Set-Content -LiteralPath $script:State -Value $json -Encoding UTF8
}

function Add-NightResult {
    param(
        [Parameter(Mandatory = $true)][string]$Job,
        [Parameter(Mandatory = $true)][string]$Status,
        [string]$Note
    )
    [void]$script:Results.Add([pscustomobject]@{
            time   = (Get-NightNow).ToString('HH:mm')
            job    = $Job
            status = $Status
            note   = $Note
        })
}

function Invoke-TaskKill {
    param([Parameter(Mandatory = $true)][int]$ProcessId)
    if (Get-Variable -Name PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
        $PSNativeCommandUseErrorActionPreference = $false
    }
    & taskkill.exe /PID $ProcessId /T /F | Out-Null
}

function Stop-HeldProcess {
    param(
        [Parameter(Mandatory = $true)]$Entry,
        [Parameter(Mandatory = $true)][string]$Why
    )
    $procId = [int]$Entry.pid
    if (-not $script:DryRun) {
        $proc = $null
        try {
            $proc = Get-Process -Id $procId -ErrorAction Stop
        }
        catch {
            $proc = $null
        }
        if ($null -eq $proc) {
            Write-NightLog "PID $procId は既にいない ($Why)"
            return
        }
        if ($Entry.name -and ($proc.ProcessName -ne [string]$Entry.name)) {
            Write-NightLog "PID $procId は $($proc.ProcessName) のため止めない（記録は $($Entry.name)）"
            return
        }
    }
    Write-NightLog "停止 [$Why] PID=$procId $($Entry.job)"
    Write-NightLog "taskkill.exe /PID $procId /T /F"
    $script:KilledAny = $true
    Invoke-TaskKill -ProcessId $procId
}

function Stop-SavedNightProcess {
    param([Parameter(Mandatory = $true)][string]$Why)
    $items = @(Read-NightState -Path $script:State)
    foreach ($item in $items) {
        $procId = 0
        if (-not [int]::TryParse([string]$item.pid, [ref]$procId)) {
            continue
        }
        $expectedName = [string]$item.name
        if (-not $expectedName) {
            Write-NightLog "PID $procId はプロセス名の記録が無いため止めない"
            continue
        }
        $expectedStart = $null
        if ($item.PSObject.Properties.Name -contains 'started' -and $item.started) {
            $parsed = [datetime]::MinValue
            $styles = [Globalization.DateTimeStyles]::None
            $culture = [Globalization.CultureInfo]::InvariantCulture
            if ([datetime]::TryParse([string]$item.started, $culture, $styles, [ref]$parsed)) {
                $expectedStart = $parsed
            }
        }
        $proc = $null
        try {
            $proc = Get-Process -Id $procId -ErrorAction Stop
        }
        catch {
            $proc = $null
        }
        if ($null -eq $proc) {
            Write-NightLog "PID $procId は既にいない ($Why)"
            continue
        }
        if ($proc.ProcessName -ne $expectedName) {
            Write-NightLog "PID $procId は $($proc.ProcessName) のため止めない（記録は $expectedName）"
            continue
        }
        if ($null -ne $expectedStart) {
            $delta = [Math]::Abs(($proc.StartTime - $expectedStart).TotalSeconds)
            if ($delta -gt 120) {
                Write-NightLog "PID $procId の開始時刻が記録と違うため止めない"
                continue
            }
        }
        $jobName = [string]$item.job
        if (-not $jobName) {
            $jobName = "pid-$procId"
        }
        Write-NightLog "停止 [$Why] PID=$procId $jobName"
        Write-NightLog "taskkill.exe /PID $procId /T /F"
        $script:KilledAny = $true
        Invoke-TaskKill -ProcessId $procId
        Add-NightResult -Job $jobName -Status 'failed' -Note "記録したPID $procId を停止 ($Why)"
    }
    Save-NightState
}

function Complete-NightJob {
    param(
        [Parameter(Mandatory = $true)][string]$Lane,
        [Parameter(Mandatory = $true)]$Entry,
        [Parameter(Mandatory = $true)][int]$Code,
        [string]$Note
    )
    $name = [string]$Entry.job
    $jobOut = Join-Path $script:Out ([IO.Path]::GetFileNameWithoutExtension($name))
    $crash = ''
    if (($Entry.meta.imagine -eq 'true') -and ($Code -ne 0)) {
        $crash = "【Imagine異常の可能性: 終了コード $Code】"
    }
    $blocked = Join-Path $jobOut 'BLOCKED.png'
    if (Test-Path -LiteralPath $blocked) {
        $Note = "$Note BLOCKED.pngあり（人の操作待ち）"
    }
    $clean = ''
    if ($Note) {
        $clean = $Note.Trim()
    }
    if (($Code -eq 0) -and (-not $clean)) {
        if ($Entry.meta.review -eq 'true') {
            $dest = $script:Rev
            $status = 'needs-review'
        }
        else {
            $dest = $script:Done
            $status = 'done'
        }
    }
    else {
        $dest = $script:Fail
        $status = 'failed'
    }
    if (Test-Path -LiteralPath $Entry.path) {
        Move-Item -LiteralPath $Entry.path -Destination (Join-Path $dest $name) -Force
    }
    $minutes = [int]((Get-NightNow) - [datetime]$Entry.start).TotalMinutes
    $full = ("$crash 終了コード=$Code 所要${minutes}分 $Note").Trim()
    Add-NightResult -Job $name -Status $status -Note $full
    Write-NightLog "終了 [$Lane] $name → $status（コード=$Code, ${minutes}分）$crash $Note"
}

function Start-QueuedJob {
    param(
        [Parameter(Mandatory = $true)]$Next,
        [Parameter(Mandatory = $true)][string]$Lane,
        [Parameter(Mandatory = $true)][datetime]$Now
    )
    $dst = Join-Path $script:Run $Next.file.Name
    Move-Item -LiteralPath $Next.file.FullName -Destination $dst -Force
    $jobOut = Join-Path $script:Out ([IO.Path]::GetFileNameWithoutExtension($Next.file.Name))
    New-Item -ItemType Directory -Force -Path $jobOut | Out-Null
    $argumentLine = Get-GrokArgumentLine -JobPath $dst
    Write-NightLog "起動コマンド: $($script:Grok) $argumentLine"
    try {
        if ($script:DryRun) {
            $child = Start-Process -FilePath $script:DryRunExe -ArgumentList '-NoProfile -Command exit 0' -WorkingDirectory $script:Root -WindowStyle Hidden -PassThru -ErrorAction Stop
            $image = 'powershell'
        }
        else {
            $stdout = Join-Path $jobOut 'stdout.txt'
            $stderr = Join-Path $jobOut 'stderr.txt'
            foreach ($path in @($stdout, $stderr)) {
                if (Test-Path -LiteralPath $path) {
                    Remove-Item -LiteralPath $path -Force
                }
            }
            $child = Start-Process -FilePath $script:Grok -ArgumentList $argumentLine -WorkingDirectory $script:Root -WindowStyle Hidden -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr -ErrorAction Stop
            $image = 'grok'
        }
    }
    catch {
        Write-NightLog "起動失敗 $($Next.file.Name): $($_.Exception.Message)"
        if (Test-Path -LiteralPath $dst) {
            Move-Item -LiteralPath $dst -Destination (Join-Path $script:Fail $Next.file.Name) -Force
        }
        Add-NightResult -Job $Next.file.Name -Status 'failed' -Note "起動失敗: $($_.Exception.Message)"
        return
    }
    if ($null -eq $child) {
        Write-NightLog "起動失敗 $($Next.file.Name): プロセスを取得できない"
        if (Test-Path -LiteralPath $dst) {
            Move-Item -LiteralPath $dst -Destination (Join-Path $script:Fail $Next.file.Name) -Force
        }
        Add-NightResult -Job $Next.file.Name -Status 'failed' -Note '起動失敗: プロセスを取得できない'
        return
    }
    $script:Running[$Lane] = @{
        proc  = $child
        pid   = [int]$child.Id
        name  = $image
        job   = $Next.file.Name
        path  = $dst
        start = $Now
        meta  = $Next.meta
    }
    Write-NightLog "開始 [$Lane] $($Next.prio)/$($Next.file.Name) PID=$($child.Id)"
    Save-NightState
}

function Restore-InterruptedJob {
    $left = @(Get-ChildItem -LiteralPath $script:Run -Filter *.md -ErrorAction SilentlyContinue)
    foreach ($file in $left) {
        Move-Item -LiteralPath $file.FullName -Destination (Join-Path $script:Fail $file.Name) -Force
        Write-NightLog "前回中断のジョブを失敗扱い: $($file.Name)（PC停止/クラッシュの可能性）"
        Add-NightResult -Job $file.Name -Status 'failed' -Note '前回の夜に途中で止まった（PC停止・クラッシュの可能性）'
    }
}

function Get-RemainingJob {
    foreach ($prio in @('1-video', '2-cg', '3-sakura')) {
        $dir = Join-Path $script:Queue $prio
        $files = @(Get-ChildItem -LiteralPath $dir -Filter *.md -ErrorAction SilentlyContinue |
                Where-Object { $_.Name -notlike 'TEMPLATE*' } |
                Sort-Object Name)
        foreach ($file in $files) {
            Write-Output "$prio/$($file.Name)"
        }
    }
}

function Write-NightSummary {
    $left = @(Get-RemainingJob)
    $created = (Get-NightNow).ToString('yyyy-MM-dd HH:mm')
    $md = New-Object System.Collections.ArrayList
    [void]$md.Add("# 夜間実行まとめ $($script:Stamp)")
    [void]$md.Add('')
    [void]$md.Add("作成: $created JST / ログ: night-runner-$($script:Stamp).log")
    [void]$md.Add('Windowsはシャットダウンしていない。止めたプロセスは、この実行が記録したPIDだけ。')
    [void]$md.Add('')
    foreach ($pair in @(
            @('done', '完了'),
            @('needs-review', 'ナオミチ確認待ち'),
            @('failed', '失敗')
        )) {
        [void]$md.Add("## $($pair[1])（$($pair[0])）")
        $rows = @($script:Results | Where-Object { $_.status -eq $pair[0] })
        if ($rows.Count -eq 0) {
            [void]$md.Add('- なし')
        }
        else {
            foreach ($row in $rows) {
                [void]$md.Add("- [$($row.time)] $($row.job) — $($row.note)")
            }
        }
        [void]$md.Add('')
    }
    [void]$md.Add('## 未着手（次の夜へ持ち越し）')
    if ($left.Count -eq 0) {
        [void]$md.Add('- なし')
    }
    else {
        foreach ($item in $left) {
            [void]$md.Add("- $item")
        }
    }
    [void]$md.Add('')
    [void]$md.Add('## Imagine の異常')
    $imagine = @($script:Results | Where-Object { $_.note -match 'Imagine異常' })
    if ($imagine.Count -eq 0) {
        [void]$md.Add('- 検知なし')
    }
    else {
        foreach ($row in $imagine) {
            [void]$md.Add("- $($row.job): $($row.note)")
        }
    }
    $text = ($md.ToArray() -join "`r`n")
    Set-Content -LiteralPath $script:Summary -Value $text -Encoding UTF8
    Write-NightLog "まとめ書き出し: $($script:Summary)"
}

function Initialize-NightPath {
    param([Parameter(Mandatory = $true)][string]$RootPath)
    $script:Root = $RootPath
    $script:Queue = Join-Path $RootPath 'queue'
    $script:Out = Join-Path $RootPath 'out'
    $script:Run = Join-Path $script:Queue '_running'
    $script:Done = Join-Path $script:Queue '_done'
    $script:Fail = Join-Path $script:Queue '_failed'
    $script:Rev = Join-Path $script:Queue '_needs-review'
    $dirs = @(
        $script:Out,
        $script:Run,
        $script:Done,
        $script:Fail,
        $script:Rev,
        (Join-Path $script:Queue '1-video'),
        (Join-Path $script:Queue '2-cg'),
        (Join-Path $script:Queue '3-sakura')
    )
    foreach ($dir in $dirs) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
    }
}

function Invoke-NightRunner {
    [CmdletBinding()]
    [OutputType([int])]
    param(
        [string]$Root = 'C:\Users\hp\Documents\grokbuild',
        [string]$Grok = 'grok.exe',
        [string]$StopNew = '03:30',
        [string]$KillAt = '04:00',
        [int]$PollSec = 60,
        [int]$MaxIterations = 0,
        [scriptblock]$NowProvider,
        [switch]$DryRun
    )

    $ErrorActionPreference = 'Stop'
    $script:NowProvider = $NowProvider
    $script:DryRun = [bool]$DryRun
    $script:Grok = $Grok
    $script:Log = $null
    $script:KilledAny = $false
    $script:Results = New-Object System.Collections.ArrayList
    $script:Running = @{}
    if ($env:SystemRoot) {
        $script:DryRunExe = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
    }
    else {
        $script:DryRunExe = 'powershell.exe'
    }

    $mutex = $null
    $acquired = $false
    try {
        $mutex = New-NightMutex -Name (Get-NightMutexName -RootPath $Root)
        try {
            $acquired = $mutex.WaitOne(0)
        }
        catch [System.Threading.AbandonedMutexException] {
            $acquired = $true
        }
        if (-not $acquired) {
            Write-Host 'すでに動作中のため終了'
            return 0
        }

        $stopSpan = [TimeSpan]::Zero
        $killSpan = [TimeSpan]::Zero
        if (-not [TimeSpan]::TryParse($StopNew, [ref]$stopSpan)) {
            throw "StopNew を解釈できない: $StopNew"
        }
        if (-not [TimeSpan]::TryParse($KillAt, [ref]$killSpan)) {
            throw "KillAt を解釈できない: $KillAt"
        }
        if ($killSpan -le $stopSpan) {
            throw 'KillAt は StopNew より後である必要がある'
        }

        Initialize-NightPath -RootPath $Root
        $now = Get-NightNow
        $night = Get-NightStart -Now $now
        $script:Stamp = $night.ToString('yyyyMMdd')
        $script:StopNewTime = $night.AddDays(1).Add($stopSpan)
        $script:KillAtTime = $night.AddDays(1).Add($killSpan)
        $script:Log = Join-Path $script:Out "night-runner-$($script:Stamp).log"
        $script:Summary = Join-Path $script:Out "night-summary-$($script:Stamp).md"
        $script:State = Join-Path $script:Out "night-state-$($script:Stamp).json"
        if (-not (Test-Path -LiteralPath $script:State)) {
            Set-Content -LiteralPath $script:State -Value '[]' -Encoding UTF8
        }

        Write-NightLog "開始 夜=$($script:Stamp) 新規停止=$($script:StopNewTime.ToString('MM/dd HH:mm')) 強制停止=$($script:KillAtTime.ToString('MM/dd HH:mm')) DryRun=$($script:DryRun) （Windowsはシャットダウンしない）"

        if (-not (Test-NightRunWindow -Now $now)) {
            Restore-InterruptedJob
            Stop-SavedNightProcess -Why '時間外の起動'
            if (($script:Results.Count -gt 0) -or $script:KilledAny) {
                Write-NightSummary
            }
            else {
                Write-NightLog '時間外（20:00〜04:00 JST のみ）。新規開始しない。Windowsはシャットダウンしない'
            }
            return 0
        }

        Restore-InterruptedJob
        Stop-SavedNightProcess -Why '起動時の残りPID'

        $iterations = 0
        while ($true) {
            $now = Get-NightNow
            $finished = New-Object System.Collections.ArrayList
            foreach ($lane in @($script:Running.Keys)) {
                $entry = $script:Running[$lane]
                if ($entry.proc.HasExited) {
                    $code = $entry.proc.ExitCode
                    if ($null -eq $code) {
                        $code = -1
                    }
                    Complete-NightJob -Lane $lane -Entry $entry -Code ([int]$code) -Note ''
                    [void]$finished.Add($lane)
                }
            }
            foreach ($lane in @($finished.ToArray())) {
                $script:Running.Remove($lane)
            }
            if ($finished.Count -gt 0) {
                Save-NightState
            }

            if ($now -ge $script:KillAtTime) {
                foreach ($lane in @($script:Running.Keys)) {
                    $entry = $script:Running[$lane]
                    Stop-HeldProcess -Entry $entry -Why '04:00'
                    Complete-NightJob -Lane $lane -Entry $entry -Code -2 -Note '04:00で打ち切り（途中まで）'
                    $script:Running.Remove($lane)
                }
                Save-NightState
                break
            }

            $timedOut = New-Object System.Collections.ArrayList
            foreach ($lane in @($script:Running.Keys)) {
                $entry = $script:Running[$lane]
                $limit = [int]$entry.meta.timeout_min
                if (($limit -gt 0) -and (($now - [datetime]$entry.start).TotalMinutes -gt $limit)) {
                    Stop-HeldProcess -Entry $entry -Why "時間切れ${limit}分"
                    Complete-NightJob -Lane $lane -Entry $entry -Code -1 -Note 'ジョブ時間切れ'
                    [void]$timedOut.Add($lane)
                }
            }
            foreach ($lane in @($timedOut.ToArray())) {
                $script:Running.Remove($lane)
            }
            if ($timedOut.Count -gt 0) {
                Save-NightState
            }

            if ($now -lt $script:StopNewTime) {
                foreach ($lane in @('chrome', 'edge', 'none')) {
                    if ($script:Running.ContainsKey($lane)) {
                        continue
                    }
                    $next = Get-NextReadyJob -Lane $lane
                    if ($null -eq $next) {
                        continue
                    }
                    Start-QueuedJob -Next $next -Lane $lane -Now $now
                }
            }
            elseif ($script:Running.Count -eq 0) {
                Write-NightLog '03:30以降で実行中なし → 終了'
                break
            }

            $waiting = $false
            foreach ($lane in @('chrome', 'edge', 'none')) {
                if ($null -ne (Get-NextReadyJob -Lane $lane)) {
                    $waiting = $true
                }
            }
            if (($script:Running.Count -eq 0) -and (-not $waiting)) {
                Write-NightLog 'キューが空 → 終了'
                break
            }

            $iterations++
            if (($MaxIterations -gt 0) -and ($iterations -ge $MaxIterations)) {
                Write-NightLog "MaxIterations=$MaxIterations に達したのでループを抜ける"
                break
            }
            if ($PollSec -gt 0) {
                Start-Sleep -Seconds $PollSec
            }
        }

        Write-NightSummary
        return 0
    }
    catch {
        $message = $_.Exception.Message
        if ($script:Log) {
            Write-NightLog "異常終了: $message"
        }
        else {
            Write-Host "異常終了: $message"
        }
        return 1
    }
    finally {
        if ($acquired -and ($null -ne $mutex)) {
            try {
                $mutex.ReleaseMutex()
            }
            catch {
                Write-Host "mutex解放をスキップ: $($_.Exception.Message)"
            }
        }
        if ($null -ne $mutex) {
            $mutex.Dispose()
        }
    }
}

if ($MyInvocation.InvocationName -ne '.') {
    $bound = @{}
    foreach ($key in $PSBoundParameters.Keys) {
        $bound[$key] = $PSBoundParameters[$key]
    }
    $exitCode = Invoke-NightRunner @bound
    exit $exitCode
}
