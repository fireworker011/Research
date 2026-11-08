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

function Write-Outputs([string]$Status, [string]$Id, [double]$Seconds, [string]$PrFlag, [string]$Report) {
    $durText = Format-Num $Seconds 1
    $line = "$Status | $Id.mp4 | ${durText}s | PR:$PrFlag"
    $utf8 = New-Object System.Text.UTF8Encoding $false
    $utf8bom = New-Object System.Text.UTF8Encoding $true
    [System.IO.File]::WriteAllText((Join-Path $Root "LAST_RESULT.txt"), ($line + "`n"), $utf8)
    [System.IO.File]::WriteAllText((Join-Path $Root "REPORT.md"), $Report, $utf8bom)
    Write-Host $line
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
    $ok = $okRes -and $okFps -and $okDur -and $hasAudio

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
    $report += "- 音声ストリーム: $audioLabel $(Mark $hasAudio)" + $nl
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
        Write-Outputs "PASS" $jobId $duration $prText $report
        exit 0
    }
    Write-Outputs "FAIL" $jobId $duration $prText $report
    exit 1
} catch {
    $message = $_.Exception.Message
    $nl = "`n"
    $report = "# yorunotana 検証レポート" + $nl + $nl + "失敗: $message" + $nl
    Write-Outputs "FAIL" $jobId $duration $prText $report
    Write-Host $message
    exit 1
}
