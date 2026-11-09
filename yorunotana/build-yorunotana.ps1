# UTF-8 BOM. Windows PowerShell 5.1 が日本語を正しく読むための印。
param(
    [Parameter(Mandatory = $true)]
    [string]$JobFile,
    [switch]$DummyTts,
    [int]$Speaker = 13
)

$ErrorActionPreference = "Stop"
try { [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding $false } catch {}
$OutputEncoding = New-Object System.Text.UTF8Encoding $false

$Root = Split-Path -Parent $PSCommandPath
Set-Location -LiteralPath $Root

$jobId = "unknown"
$prText = "False"
$duration = 0.0

function Format-Num([double]$Number, [int]$Digits) {
    $culture = [System.Globalization.CultureInfo]::InvariantCulture
    $fmt = "{0:F" + $Digits + "}"
    return [string]::Format($culture, $fmt, $Number)
}

function Write-Outputs([string]$Status, [string]$Id, [double]$Seconds, [string]$PrFlag, [double]$Freeze, [double]$Silence, [string]$Report) {
    $line = "$Status | $Id.mp4 | $(Format-Num $Seconds 1)s | PR:$PrFlag | freeze=$(Format-Num $Freeze 2)s | silence=$(Format-Num $Silence 2)s"
    $utf8 = New-Object System.Text.UTF8Encoding $false
    $utf8bom = New-Object System.Text.UTF8Encoding $true
    [System.IO.File]::WriteAllText((Join-Path $Root "LAST_RESULT.txt"), ($line + "`n"), $utf8)
    [System.IO.File]::WriteAllText((Join-Path $Root "REPORT.md"), $Report, $utf8bom)
    Write-Host $line
}

function Add-Span([System.Collections.Generic.List[double]]$Spans, [double]$Value) {
    $Spans.Add($Value)
}

function Get-MediaMax([string]$OutName, [double]$Total) {
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $log = & ffmpeg -hide_banner -nostats -i $OutName -vf "freezedetect=n=-60dB:d=2" -af "silencedetect=n=-50dB:d=2" -f null - 2>&1 | ForEach-Object { "$_" }
    $ErrorActionPreference = $prev
    $culture = [System.Globalization.CultureInfo]::InvariantCulture
    $freezeStarts = New-Object System.Collections.Generic.List[double]
    $freezeEnds = New-Object System.Collections.Generic.List[double]
    $freezeDurs = New-Object System.Collections.Generic.List[double]
    $silenceStarts = New-Object System.Collections.Generic.List[double]
    $silenceEnds = New-Object System.Collections.Generic.List[double]
    $silenceDurs = New-Object System.Collections.Generic.List[double]
    foreach ($line in @($log)) {
        if ($line -match "freeze_start:\s*([0-9]+(?:\.[0-9]+)?)") { Add-Span $freezeStarts ([double]::Parse($Matches[1], $culture)) }
        if ($line -match "freeze_end:\s*([0-9]+(?:\.[0-9]+)?)") { Add-Span $freezeEnds ([double]::Parse($Matches[1], $culture)) }
        if ($line -match "freeze_duration:\s*([0-9]+(?:\.[0-9]+)?)") { Add-Span $freezeDurs ([double]::Parse($Matches[1], $culture)) }
        if ($line -match "silence_start:\s*([0-9]+(?:\.[0-9]+)?)") { Add-Span $silenceStarts ([double]::Parse($Matches[1], $culture)) }
        if ($line -match "silence_end:\s*([0-9]+(?:\.[0-9]+)?)") { Add-Span $silenceEnds ([double]::Parse($Matches[1], $culture)) }
        if ($line -match "silence_duration:\s*([0-9]+(?:\.[0-9]+)?)") { Add-Span $silenceDurs ([double]::Parse($Matches[1], $culture)) }
    }
    $freezeList = New-Object System.Collections.Generic.List[string]
    $silenceList = New-Object System.Collections.Generic.List[string]
    $freezeMax = 0.0
    $silenceMax = 0.0
    function Consider([double]$Value, [System.Collections.Generic.List[string]]$Shown, [ref]$Max) {
        $Shown.Add((Format-Num $Value 2))
        if ($Value -gt $Max.Value) { $Max.Value = $Value }
    }
    $useFreezeDur = ($freezeDurs.Count -ge $freezeStarts.Count -and $freezeDurs.Count -gt 0)
    if ($useFreezeDur) {
        foreach ($value in $freezeDurs) { Consider $value $freezeList ([ref]$freezeMax) }
    } else {
        for ($i = 0; $i -lt $freezeStarts.Count; $i++) {
            if ($i -lt $freezeEnds.Count) { $value = $freezeEnds[$i] - $freezeStarts[$i] }
            elseif ($i -lt $freezeDurs.Count) { $value = $freezeDurs[$i] }
            else { $value = $Total - $freezeStarts[$i] }
            Consider $value $freezeList ([ref]$freezeMax)
        }
    }
    $useSilenceDur = ($silenceDurs.Count -ge $silenceStarts.Count -and $silenceDurs.Count -gt 0)
    if ($useSilenceDur) {
        foreach ($value in $silenceDurs) { Consider $value $silenceList ([ref]$silenceMax) }
    } else {
        for ($i = 0; $i -lt $silenceStarts.Count; $i++) {
            if ($i -lt $silenceEnds.Count) { $value = $silenceEnds[$i] - $silenceStarts[$i] }
            elseif ($i -lt $silenceDurs.Count) { $value = $silenceDurs[$i] }
            else { $value = $Total - $silenceStarts[$i] }
            Consider $value $silenceList ([ref]$silenceMax)
        }
    }
    return @{
        Freeze = $freezeMax
        Silence = $silenceMax
        FreezeList = ($freezeList -join ", ")
        SilenceList = ($silenceList -join ", ")
    }
}

try {
    if (-not [System.IO.Path]::IsPathRooted($JobFile)) {
        $JobFileFull = Join-Path $Root $JobFile
    } else {
        $JobFileFull = $JobFile
    }
    if (-not (Test-Path -LiteralPath $JobFileFull)) {
        throw "ジョブファイルがありません: $JobFileFull"
    }
    $utf8read = New-Object System.Text.UTF8Encoding $false
    $job = [System.IO.File]::ReadAllText($JobFileFull, $utf8read) | ConvertFrom-Json
    $jobId = [string]$job.job_id
    if ($job.pr_badge) { $prText = "True" } else { $prText = "False" }

    $audioArgs = @("src/build_audio.py", "--job", $JobFileFull, "--speaker", "$Speaker")
    if ($DummyTts) { $audioArgs += "--dummy-tts" }
    & python @audioArgs
    if ($LASTEXITCODE -ne 0) { throw "build_audio.py が終了コード $LASTEXITCODE で失敗しました" }

    $outName = "out/$jobId.mp4"
    & python src/render_frames.py --job $JobFileFull --timing "out/temp_audio/audio_timing.json" --audio "out/temp_audio/master_audio.wav" --out $outName
    if ($LASTEXITCODE -ne 0) { throw "render_frames.py が終了コード $LASTEXITCODE で失敗しました" }
    if (-not (Test-Path -LiteralPath (Join-Path $Root $outName))) { throw "MP4が出力されませんでした: $outName" }

    $probeRaw = & ffprobe -v error -print_format json -show_format -show_streams $outName
    if ($LASTEXITCODE -ne 0) { throw "ffprobe が失敗しました" }
    $probe = ($probeRaw | Out-String) | ConvertFrom-Json
    $videoStream = $probe.streams | Where-Object { $_.codec_type -eq "video" } | Select-Object -First 1
    $audioStream = $probe.streams | Where-Object { $_.codec_type -eq "audio" } | Select-Object -First 1
    $width = 0
    $height = 0
    $fps = 0.0
    if ($null -ne $videoStream) {
        $width = [int]$videoStream.width
        $height = [int]$videoStream.height
        $rate = [string]$videoStream.r_frame_rate
        if ($rate -match "^(\d+)/(\d+)$" -and [double]$Matches[2] -ne 0) {
            $fps = [double]$Matches[1] / [double]$Matches[2]
        }
    }
    $duration = [double]$probe.format.duration
    $hasAudio = $null -ne $audioStream
    $okRes = ($width -eq 1080 -and $height -eq 1920)
    $okFps = ([math]::Abs($fps - 60.0) -lt 0.05)
    $okDur = ($duration -ge 75.0 -and $duration -le 95.0)
    $detected = Get-MediaMax $outName $duration
    $freezeMax = [double]$detected.Freeze
    $silenceMax = [double]$detected.Silence
    $okFreeze = ($freezeMax -lt 2.0)
    $okSilence = ($silenceMax -lt 2.0)
    $ok = $okRes -and $okFps -and $okDur -and $hasAudio -and $okFreeze -and $okSilence

    $timing = [System.IO.File]::ReadAllText((Join-Path $Root "out\temp_audio\audio_timing.json"), $utf8read) | ConvertFrom-Json
    $cutLines = New-Object System.Collections.Generic.List[string]
    foreach ($item in @($timing.items)) {
        $length = [double]$item.end_sec - [double]$item.start_sec
        $label = [string]$item.kind
        if ($null -ne $item.segment_id -and "$($item.segment_id)" -ne "") {
            $label = "$label #$($item.segment_id) $($item.scene)"
        }
        $cutLines.Add(("- {0}: {1}s ({2}-{3})" -f $label, (Format-Num $length 2), (Format-Num ([double]$item.start_sec) 2), (Format-Num ([double]$item.end_sec) 2)))
    }

    $reasons = New-Object System.Collections.Generic.List[string]
    if (-not $okRes) { $reasons.Add("解像度が ${width}x${height}") }
    if (-not $okFps) { $reasons.Add("フレームレートが $(Format-Num $fps 3)") }
    if (-not $okDur) { $reasons.Add("尺が $(Format-Num $duration 3)秒") }
    if (-not $hasAudio) { $reasons.Add("音声ストリームがない") }
    if (-not $okFreeze) { $reasons.Add("フリーズが $(Format-Num $freezeMax 2)秒") }
    if (-not $okSilence) { $reasons.Add("無音が $(Format-Num $silenceMax 2)秒") }

    function Mark([bool]$Flag) { if ($Flag) { "OK" } else { "NG" } }
    $audioLabel = "なし"
    if ($hasAudio) { $audioLabel = "あり" }
    $nl = "`n"
    $report = "# yorunotana 検証レポート" + $nl + $nl
    $report += "- ジョブファイル: $JobFileFull" + $nl
    $report += "- job_id: $jobId" + $nl
    $report += "- 出力: $outName" + $nl
    $report += "- 解像度: ${width}x${height} （基準 1080x1920） $(Mark $okRes)" + $nl
    $report += "- フレームレート: $(Format-Num $fps 3) （基準 60） $(Mark $okFps)" + $nl
    $report += "- 尺: $(Format-Num $duration 3)秒 （基準 75.0〜95.0） $(Mark $okDur)" + $nl
    $freezeShown = $detected.FreezeList
    if (-not $freezeShown) { $freezeShown = "なし" }
    $silenceShown = $detected.SilenceList
    if (-not $silenceShown) { $silenceShown = "なし" }
    $report += "- 音声ストリーム: $audioLabel $(Mark $hasAudio)" + $nl
    $report += "- 最長フリーズ: $(Format-Num $freezeMax 2)秒 （基準 2.0秒未満、noise=-60dB d=2） $(Mark $okFreeze)" + $nl
    $report += "- 検出したフリーズ: $freezeShown" + $nl
    $report += "- 最長無音: $(Format-Num $silenceMax 2)秒 （基準 2.0秒未満、noise=-50dB d=2） $(Mark $okSilence)" + $nl
    $report += "- 検出した無音: $silenceShown" + $nl
    $report += "- PRバッジ（ジョブ指定）: $prText" + $nl
    if ($ok) { $report += "- 総合: PASS" + $nl } else { $report += "- 総合: FAIL" + $nl }
    $report += $nl + "## 各カット" + $nl
    foreach ($cut in $cutLines) { $report += $cut + $nl }
    $report += $nl + "## A8提出前チェック" + $nl
    $report += "- 画面は 1080x1920 の縦動画" + $nl
    $report += "- 尺は 75.0秒以上 95.0秒以下" + $nl
    $report += "- 音声トラックがある" + $nl
    $report += "- pr_badge が true のジョブは、右上に PR を全編出す（描画側の責務）" + $nl
    $report += "- アフィリエイトのURLは、リポジトリにも完成動画の中にも置かない" + $nl
    $report += $nl + "## メモ" + $nl
    if ($reasons.Count -eq 0) {
        $report += "- なし" + $nl
    } else {
        foreach ($reason in $reasons) { $report += "- $reason" + $nl }
    }

    if ($ok) {
        Write-Outputs "PASS" $jobId $duration $prText $freezeMax $silenceMax $report
        exit 0
    }
    Write-Outputs "FAIL" $jobId $duration $prText $freezeMax $silenceMax $report
    exit 1
} catch {
    $message = $_.Exception.Message
    $nl = "`n"
    $report = "# yorunotana 検証レポート" + $nl + $nl + "失敗: $message" + $nl
    Write-Outputs "FAIL" $jobId $duration $prText 0.0 0.0 $report
    Write-Host $message
    exit 1
}
