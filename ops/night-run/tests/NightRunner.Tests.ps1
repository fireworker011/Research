BeforeAll {
    $parent = Join-Path -Path $PSScriptRoot -ChildPath '..'
    $script:Runner = (Resolve-Path (Join-Path -Path $parent -ChildPath 'night-runner.ps1')).Path
    $script:Installer = (Resolve-Path (Join-Path -Path $parent -ChildPath 'install-task.ps1')).Path
    $script:TestScript = Join-Path $PSScriptRoot 'NightRunner.Tests.ps1'
    . $script:Runner
    . $script:Installer

    function New-TestRoot {
        $root = Join-Path (Join-Path $TestDrive ([guid]::NewGuid().ToString('n'))) 'grok build'
        New-Item -ItemType Directory -Force -Path $root | Out-Null
        return $root
    }

    function New-JobFile {
        param(
            [Parameter(Mandatory = $true)][string]$Root,
            [Parameter(Mandatory = $true)][string]$Prio,
            [Parameter(Mandatory = $true)][string]$Name,
            [Parameter(Mandatory = $true)][string]$Lane,
            [string]$Extra = ''
        )
        $dir = Join-Path (Join-Path $Root 'queue') $Prio
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
        $text = "lane: $Lane`r`nreview: true`r`ntimeout_min: 30`r`n$Extra`r`n# $Name`r`n"
        Set-Content -LiteralPath (Join-Path $dir $Name) -Value $text -Encoding UTF8
    }

    function Get-RunnerLog {
        if ($null -eq $script:NightLog) {
            return ''
        }
        return ($script:NightLog -join "`n")
    }

    function Get-LeadingUtf8BomCount {
        param([byte[]]$Bytes)
        $count = 0
        while ($Bytes.Length -ge (($count + 1) * 3)) {
            $i = $count * 3
            $b0 = [int]$Bytes[$i]
            $b1 = [int]$Bytes[$i + 1]
            $b2 = [int]$Bytes[$i + 2]
            if (($b0 -eq 239) -and ($b1 -eq 187) -and ($b2 -eq 191)) {
                $count++
            }
            else {
                break
            }
        }
        return $count
    }

    function Get-QueuePath {
        param(
            [Parameter(Mandatory = $true)][string]$Root,
            [Parameter(Mandatory = $true)][string]$Folder,
            [Parameter(Mandatory = $true)][string]$Name
        )
        return (Join-Path (Join-Path (Join-Path $Root 'queue') $Folder) $Name)
    }
}

Describe 'night-runner DryRun' {
    BeforeEach {
        $script:mockExited = $true
        $script:mockExit = 0
        $script:onStart = $null
        $script:launches = New-Object System.Collections.ArrayList
        $script:kills = New-Object System.Collections.ArrayList
        Mock Start-Process {
            if ($script:onStart) {
                & $script:onStart
            }
            $id = 5000 + $script:launches.Count
            [void]$script:launches.Add([pscustomobject]@{
                    FilePath     = [string]$FilePath
                    ArgumentList = [string]$ArgumentList
                    Id           = $id
                })
            return [pscustomobject]@{
                Id         = $id
                HasExited  = [bool]$script:mockExited
                ExitCode   = $script:mockExit
            }
        }
        Mock Invoke-TaskKill {
            [void]$script:kills.Add($ProcessId)
        }
    }

    It '時間外は grok も代替プロセスも起動せず、ファイルを動かさない' {
        $root = New-TestRoot
        New-JobFile -Root $root -Prio '1-video' -Name '10-a.md' -Lane 'chrome'
        $code = Invoke-NightRunner -Root $root -DryRun -PollSec 0 -MaxIterations 5 -Grok 'grok.exe' -NowProvider {
            [datetime]'2026-10-21T12:00:00'
        }
        $code | Should -Be 0
        $script:launches.Count | Should -Be 0
        $script:kills.Count | Should -Be 0
        Test-Path -LiteralPath (Get-QueuePath -Root $root -Folder '1-video' -Name '10-a.md') | Should -BeTrue
        Test-Path -LiteralPath (Join-Path (Join-Path $root 'out') 'night-state-20261021.json') | Should -BeFalse
    }

    It '20:00 は窓の内側、04:00 ちょうどと 19:59 は外側' {
        Test-NightRunWindow -Now ([datetime]'2026-10-21T20:00:00') | Should -BeTrue
        Test-NightRunWindow -Now ([datetime]'2026-10-22T03:59:00') | Should -BeTrue
        Test-NightRunWindow -Now ([datetime]'2026-10-22T04:00:00') | Should -BeFalse
        Test-NightRunWindow -Now ([datetime]'2026-10-21T19:59:00') | Should -BeFalse
    }

    It '夜の日付は 20:00 起点' {
        (Get-NightStart -Now ([datetime]'2026-10-21T21:00:00')).ToString('yyyy-MM-dd') | Should -Be '2026-10-21'
        (Get-NightStart -Now ([datetime]'2026-10-22T02:00:00')).ToString('yyyy-MM-dd') | Should -Be '2026-10-21'
        (Get-NightStart -Now ([datetime]'2026-10-22T10:00:00')).ToString('yyyy-MM-dd') | Should -Be '2026-10-21'
        (Get-NightStart -Now ([datetime]'2026-10-22T04:00:00')).ToString('yyyy-MM-dd') | Should -Be '2026-10-21'
    }

    It 'grok の引数は prompt-file / always-approve / background-wait-timeout 3600 の順' {
        $path = 'C:\Users\hp\Documents\grok build\queue\_running\10-a.md'
        $line = Get-GrokArgumentLine -JobPath $path
        $line | Should -Be '--prompt-file "C:\Users\hp\Documents\grok build\queue\_running\10-a.md" --always-approve --background-wait-timeout 3600'
    }

    It 'DryRun は grok.exe を起動せず、ファイルも状態も書かない' {
        $root = New-TestRoot
        New-JobFile -Root $root -Prio '1-video' -Name '10-a.md' -Lane 'chrome'
        $code = Invoke-NightRunner -Root $root -DryRun -PollSec 0 -MaxIterations 10 -Grok 'grok.exe' -NowProvider {
            [datetime]'2026-10-21T21:00:00'
        }
        $code | Should -Be 0
        $script:launches.Count | Should -Be 0
        $script:kills.Count | Should -Be 0
        $log = Get-RunnerLog
        $log | Should -Match 'grok\.exe --prompt-file ".*1-video.10-a\.md" --always-approve --background-wait-timeout 3600'
        $log | Should -Not -Match 'Stop-Computer|Restart-Computer|shutdown'
        $log | Should -Not -Match '_running'
        Test-Path -LiteralPath (Get-QueuePath -Root $root -Folder '1-video' -Name '10-a.md') | Should -BeTrue
        Test-Path -LiteralPath (Get-QueuePath -Root $root -Folder '_needs-review' -Name '10-a.md') | Should -BeFalse
        Test-Path -LiteralPath (Get-QueuePath -Root $root -Folder '_running' -Name '10-a.md') | Should -BeFalse
        Test-Path -LiteralPath (Join-Path (Join-Path $root 'out') 'night-runner-20261021.log') | Should -BeFalse
        Test-Path -LiteralPath (Join-Path (Join-Path $root 'out') 'night-state-20261021.json') | Should -BeFalse
        Test-Path -LiteralPath (Join-Path (Join-Path $root 'out') 'night-summary-20261021.md') | Should -BeFalse
        $script:LastSummary | Should -Match '10-a.md'
    }

    It '優先順は 1-video が 2-cg より先、3-sakura はその後。TEMPLATE は無視' {
        $root = New-TestRoot
        New-JobFile -Root $root -Prio '3-sakura' -Name '01-sakura.md' -Lane 'none'
        New-JobFile -Root $root -Prio '2-cg' -Name '01-cg.md' -Lane 'none'
        New-JobFile -Root $root -Prio '1-video' -Name '90-video.md' -Lane 'none'
        New-JobFile -Root $root -Prio '3-sakura' -Name 'TEMPLATE-sakura.md' -Lane 'none'
        $code = Invoke-NightRunner -Root $root -DryRun -PollSec 0 -MaxIterations 10 -Grok 'grok.exe' -NowProvider {
            [datetime]'2026-10-21T21:00:00'
        }
        $code | Should -Be 0
        $script:launches.Count | Should -Be 0
        $log = Get-RunnerLog
        $starts = [regex]::Matches($log, '開始 \[none\] (\S+)')
        $starts.Count | Should -Be 3
        $starts[0].Groups[1].Value | Should -Be '1-video/90-video.md'
        $starts[1].Groups[1].Value | Should -Be '2-cg/01-cg.md'
        $starts[2].Groups[1].Value | Should -Be '3-sakura/01-sakura.md'
        $log | Should -Not -Match 'TEMPLATE-sakura'
        Test-Path -LiteralPath (Get-QueuePath -Root $root -Folder '1-video' -Name '90-video.md') | Should -BeTrue
        Test-Path -LiteralPath (Get-QueuePath -Root $root -Folder '2-cg' -Name '01-cg.md') | Should -BeTrue
        Test-Path -LiteralPath (Get-QueuePath -Root $root -Folder '3-sakura' -Name '01-sakura.md') | Should -BeTrue
        Test-Path -LiteralPath (Get-QueuePath -Root $root -Folder '3-sakura' -Name 'TEMPLATE-sakura.md') | Should -BeTrue
    }

    It '同じレーンは同時に1本。別レーンは同時に起動できる' {
        $script:mockExited = $false
        $root = New-TestRoot
        New-JobFile -Root $root -Prio '1-video' -Name '10-chrome-a.md' -Lane 'chrome'
        New-JobFile -Root $root -Prio '1-video' -Name '20-chrome-b.md' -Lane 'chrome'
        New-JobFile -Root $root -Prio '1-video' -Name '30-edge.md' -Lane 'edge'
        $code = Invoke-NightRunner -Root $root -DryRun -PollSec 0 -MaxIterations 1 -Grok 'grok.exe' -NowProvider {
            [datetime]'2026-10-21T21:00:00'
        }
        $code | Should -Be 0
        $script:launches.Count | Should -Be 0
        $script:kills.Count | Should -Be 0
        $log = Get-RunnerLog
        $log | Should -Match '開始 \[chrome\] 1-video/10-chrome-a.md'
        $log | Should -Match '開始 \[edge\] 1-video/30-edge.md'
        $log | Should -Not -Match '20-chrome-b.md'
        Test-Path -LiteralPath (Get-QueuePath -Root $root -Folder '1-video' -Name '10-chrome-a.md') | Should -BeTrue
        Test-Path -LiteralPath (Get-QueuePath -Root $root -Folder '1-video' -Name '20-chrome-b.md') | Should -BeTrue
        Test-Path -LiteralPath (Get-QueuePath -Root $root -Folder '1-video' -Name '30-edge.md') | Should -BeTrue
        Test-Path -LiteralPath (Join-Path (Join-Path $root 'out') 'night-state-20261021.json') | Should -BeFalse
    }

    It '03:30 ちょうどは新規開始しない。03:29 は開始する' {
        $lateRoot = New-TestRoot
        New-JobFile -Root $lateRoot -Prio '1-video' -Name '10-a.md' -Lane 'chrome'
        $late = Invoke-NightRunner -Root $lateRoot -DryRun -PollSec 0 -MaxIterations 5 -Grok 'grok.exe' -NowProvider {
            [datetime]'2026-10-22T03:30:00'
        }
        $late | Should -Be 0
        $script:launches.Count | Should -Be 0
        (Get-RunnerLog) | Should -Not -Match '開始 \[chrome\]'
        Test-Path -LiteralPath (Get-QueuePath -Root $lateRoot -Folder '1-video' -Name '10-a.md') | Should -BeTrue

        $earlyRoot = New-TestRoot
        New-JobFile -Root $earlyRoot -Prio '1-video' -Name '10-a.md' -Lane 'chrome'
        $early = Invoke-NightRunner -Root $earlyRoot -DryRun -PollSec 0 -MaxIterations 5 -Grok 'grok.exe' -NowProvider {
            [datetime]'2026-10-22T03:29:00'
        }
        $early | Should -Be 0
        $script:launches.Count | Should -Be 0
        (Get-RunnerLog) | Should -Match '開始 \[chrome\] 1-video/10-a.md'
        Test-Path -LiteralPath (Get-QueuePath -Root $earlyRoot -Folder '1-video' -Name '10-a.md') | Should -BeTrue
    }

    It '04:00 の DryRun は記録したPIDをログに出すが、taskkill も移動もしない' {
        $script:mockExited = $false
        $script:phase = 'early'
        $script:onStart = { $script:phase = 'late' }
        $root = New-TestRoot
        New-JobFile -Root $root -Prio '1-video' -Name '10-a.md' -Lane 'chrome' -Extra 'timeout_min: 120'
        $code = Invoke-NightRunner -Root $root -DryRun -PollSec 0 -MaxIterations 5 -Grok 'grok.exe' -NowProvider {
            if ($script:phase -eq 'early') { return [datetime]'2026-10-22T03:00:00' }
            return [datetime]'2026-10-22T04:00:00'
        }
        $code | Should -Be 0
        $script:launches.Count | Should -Be 0
        $script:kills.Count | Should -Be 0
        $log = Get-RunnerLog
        $log | Should -Match '開始 \[chrome\] 1-video/10-a.md PID=5000'
        $log | Should -Match 'taskkill.exe /PID 5000 /T /F'
        $log | Should -Match 'DRYRUN のため taskkill しない'
        $log | Should -Not -Match '/IM'
        $script:LastSummary | Should -Match '04:00で打ち切り'
        $script:LastSummary | Should -Match 'シャットダウンしていない'
        Test-Path -LiteralPath (Get-QueuePath -Root $root -Folder '1-video' -Name '10-a.md') | Should -BeTrue
        Test-Path -LiteralPath (Get-QueuePath -Root $root -Folder '_failed' -Name '10-a.md') | Should -BeFalse
        Test-Path -LiteralPath (Join-Path (Join-Path $root 'out') 'night-summary-20261021.md') | Should -BeFalse
    }

    It '時間切れの DryRun は失敗をまとめに出し、ファイルは残す' {
        $script:mockExited = $false
        $script:phase = 'early'
        $script:onStart = { $script:phase = 'late' }
        $root = New-TestRoot
        New-JobFile -Root $root -Prio '1-video' -Name '10-a.md' -Lane 'none' -Extra 'timeout_min: 30'
        $code = Invoke-NightRunner -Root $root -DryRun -PollSec 0 -MaxIterations 5 -Grok 'grok.exe' -NowProvider {
            if ($script:phase -eq 'early') { return [datetime]'2026-10-21T21:00:00' }
            return [datetime]'2026-10-21T22:00:00'
        }
        $code | Should -Be 0
        $script:kills.Count | Should -Be 0
        $script:launches.Count | Should -Be 0
        (Get-RunnerLog) | Should -Match 'DRYRUN のため taskkill しない'
        $script:LastSummary | Should -Match 'ジョブ時間切れ'
        Test-Path -LiteralPath (Get-QueuePath -Root $root -Folder '1-video' -Name '10-a.md') | Should -BeTrue
        Test-Path -LiteralPath (Get-QueuePath -Root $root -Folder '_failed' -Name '10-a.md') | Should -BeFalse
    }

    It 'requires が仮想の確認待ちに入るまで後続レーンを始めない' {
        $root = New-TestRoot
        New-JobFile -Root $root -Prio '1-video' -Name '10-a.md' -Lane 'chrome'
        New-JobFile -Root $root -Prio '1-video' -Name '20-b.md' -Lane 'edge' -Extra 'requires: 10-a.md'
        $code = Invoke-NightRunner -Root $root -DryRun -PollSec 0 -MaxIterations 10 -Grok 'grok.exe' -NowProvider {
            [datetime]'2026-10-21T21:00:00'
        }
        $code | Should -Be 0
        $log = Get-RunnerLog
        $a = $log.IndexOf('開始 [chrome] 1-video/10-a.md')
        $b = $log.IndexOf('開始 [edge] 1-video/20-b.md')
        $done = $log.IndexOf('終了 [chrome] 10-a.md')
        $a | Should -BeGreaterThan -1
        $done | Should -BeGreaterThan $a
        $b | Should -BeGreaterThan $done
        Test-Path -LiteralPath (Get-QueuePath -Root $root -Folder '1-video' -Name '10-a.md') | Should -BeTrue
        Test-Path -LiteralPath (Get-QueuePath -Root $root -Folder '1-video' -Name '20-b.md') | Should -BeTrue
    }

    It '依存が揃わないジョブは起動しない' {
        $root = New-TestRoot
        New-JobFile -Root $root -Prio '1-video' -Name '20-b.md' -Lane 'edge' -Extra 'requires: 10-a.md'
        $code = Invoke-NightRunner -Root $root -DryRun -PollSec 0 -MaxIterations 3 -Grok 'grok.exe' -NowProvider {
            [datetime]'2026-10-21T21:00:00'
        }
        $code | Should -Be 0
        $script:launches.Count | Should -Be 0
        (Get-RunnerLog) | Should -Not -Match '開始 \[edge\]'
        Test-Path -LiteralPath (Get-QueuePath -Root $root -Folder '1-video' -Name '20-b.md') | Should -BeTrue
    }

    It '朝の DryRun は状態ファイルのPIDを止めず、バイト列も変えない' {
        $root = New-TestRoot
        $out = Join-Path $root 'out'
        New-Item -ItemType Directory -Force -Path $out | Out-Null
        $state = '[{"lane":"chrome","pid":9999,"name":"grok","job":"10-a.md","started":"2026-10-21T21:00:00"}]'
        $statePath = Join-Path $out 'night-state-20261021.json'
        Set-Content -LiteralPath $statePath -Value $state -Encoding UTF8
        $before = [Convert]::ToBase64String([IO.File]::ReadAllBytes($statePath))
        Mock Get-Process {
            return [pscustomobject]@{
                Id          = 9999
                ProcessName = 'grok'
                StartTime   = [datetime]'2026-10-21T21:00:05'
            }
        }
        $code = Invoke-NightRunner -Root $root -DryRun -PollSec 0 -MaxIterations 3 -Grok 'grok.exe' -NowProvider {
            [datetime]'2026-10-22T10:00:00'
        }
        $code | Should -Be 0
        $script:launches.Count | Should -Be 0
        $script:kills.Count | Should -Be 0
        (Get-RunnerLog) | Should -Match 'DRYRUN のため PID 9999 は止めない'
        ([Convert]::ToBase64String([IO.File]::ReadAllBytes($statePath))) | Should -Be $before
        Test-Path -LiteralPath (Join-Path $out 'night-runner-20261021.log') | Should -BeFalse

        $script:kills = New-Object System.Collections.ArrayList
        $other = New-TestRoot
        $otherOut = Join-Path $other 'out'
        New-Item -ItemType Directory -Force -Path $otherOut | Out-Null
        $otherState = Join-Path $otherOut 'night-state-20261021.json'
        Set-Content -LiteralPath $otherState -Value $state -Encoding UTF8
        $otherBefore = [Convert]::ToBase64String([IO.File]::ReadAllBytes($otherState))
        Mock Get-Process {
            return [pscustomobject]@{
                Id          = 9999
                ProcessName = 'explorer'
                StartTime   = [datetime]'2026-10-21T21:00:05'
            }
        }
        $code2 = Invoke-NightRunner -Root $other -DryRun -PollSec 0 -MaxIterations 3 -Grok 'grok.exe' -NowProvider {
            [datetime]'2026-10-22T10:00:00'
        }
        $code2 | Should -Be 0
        $script:kills.Count | Should -Be 0
        (Get-RunnerLog) | Should -Match 'explorer のため止めない'
        ([Convert]::ToBase64String([IO.File]::ReadAllBytes($otherState))) | Should -Be $otherBefore
    }

    It 'Imagine の非0終了はまとめに出す。review false の成功は done。どちらもファイルは残す' {
        $script:mockExit = 1
        $root = New-TestRoot
        New-JobFile -Root $root -Prio '1-video' -Name '10-a.md' -Lane 'chrome' -Extra 'imagine: true'
        $code = Invoke-NightRunner -Root $root -DryRun -PollSec 0 -MaxIterations 5 -Grok 'grok.exe' -NowProvider {
            [datetime]'2026-10-21T21:00:00'
        }
        $code | Should -Be 0
        $script:LastSummary | Should -Match 'Imagine異常'
        Test-Path -LiteralPath (Get-QueuePath -Root $root -Folder '1-video' -Name '10-a.md') | Should -BeTrue
        Test-Path -LiteralPath (Get-QueuePath -Root $root -Folder '_failed' -Name '10-a.md') | Should -BeFalse

        $script:mockExit = 0
        $doneRoot = New-TestRoot
        New-JobFile -Root $doneRoot -Prio '1-video' -Name '05-push.md' -Lane 'none' -Extra 'review: false'
        Invoke-NightRunner -Root $doneRoot -DryRun -PollSec 0 -MaxIterations 5 -Grok 'grok.exe' -NowProvider {
            [datetime]'2026-10-21T21:00:00'
        } | Should -Be 0
        (Get-RunnerLog) | Should -Match '05-push.md → done'
        Test-Path -LiteralPath (Get-QueuePath -Root $doneRoot -Folder '1-video' -Name '05-push.md') | Should -BeTrue
        Test-Path -LiteralPath (Get-QueuePath -Root $doneRoot -Folder '_done' -Name '05-push.md') | Should -BeFalse
    }

    It '前回 _running に残ったジョブを DryRun は動かさない' {
        $root = New-TestRoot
        $run = Join-Path (Join-Path $root 'queue') '_running'
        New-Item -ItemType Directory -Force -Path $run | Out-Null
        Set-Content -LiteralPath (Join-Path $run '09-old.md') -Value "lane: none`r`n# old`r`n" -Encoding UTF8
        $code = Invoke-NightRunner -Root $root -DryRun -PollSec 0 -MaxIterations 3 -Grok 'grok.exe' -NowProvider {
            [datetime]'2026-10-21T21:00:00'
        }
        $code | Should -Be 0
        (Get-RunnerLog) | Should -Match 'DRYRUN 前回中断は動かさない: 09-old.md'
        Test-Path -LiteralPath (Join-Path $run '09-old.md') | Should -BeTrue
        Test-Path -LiteralPath (Get-QueuePath -Root $root -Folder '_failed' -Name '09-old.md') | Should -BeFalse
        $script:launches.Count | Should -Be 0
        $script:kills.Count | Should -Be 0
    }

    It 'DryRun は報告ファイルが出ても移動も taskkill もしない' {
        $script:mockExited = $false
        $root = New-TestRoot
        New-JobFile -Root $root -Prio '1-video' -Name '10-a.md' -Lane 'chrome'
        $dir = Join-Path (Join-Path $root 'out') '10-a'
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
        Set-Content -LiteralPath (Join-Path $dir 'stdout.txt') -Value "running`r`n" -Encoding UTF8
        Set-Content -LiteralPath (Join-Path $dir 'REPORT.md') -Value "done`r`n" -Encoding UTF8
        $code = Invoke-NightRunner -Root $root -DryRun -PollSec 0 -MaxIterations 5 -Grok 'grok.exe' -NowProvider {
            [datetime]'2026-10-21T21:00:00'
        }
        $code | Should -Be 0
        $script:launches.Count | Should -Be 0
        $script:kills.Count | Should -Be 0
        $log = Get-RunnerLog
        $log | Should -Match '報告ファイルが出たので停止'
        $log | Should -Match 'REPORT.md'
        $log | Should -Match 'DRYRUN のため taskkill しない'
        Test-Path -LiteralPath (Get-QueuePath -Root $root -Folder '1-video' -Name '10-a.md') | Should -BeTrue
        Test-Path -LiteralPath (Get-QueuePath -Root $root -Folder '_needs-review' -Name '10-a.md') | Should -BeFalse
    }

    It '異常終了しても次の起動で mutex を取れる' {
        $root = New-TestRoot
        $first = Invoke-NightRunner -Root $root -DryRun -PollSec 0 -StopNew 'not-a-time' -NowProvider {
            [datetime]'2026-10-21T21:00:00'
        }
        $first | Should -Be 1
        $second = Invoke-NightRunner -Root $root -DryRun -PollSec 0 -MaxIterations 2 -Grok 'grok.exe' -NowProvider {
            [datetime]'2026-10-21T12:00:00'
        }
        $second | Should -Be 0
    }
}

Describe 'night-runner 実処理' {
    BeforeEach {
        $script:mockExited = $true
        $script:mockExit = 0
        $script:onStart = $null
        $script:launches = New-Object System.Collections.ArrayList
        $script:kills = New-Object System.Collections.ArrayList
        Mock Start-Process {
            if ($script:onStart) {
                & $script:onStart
            }
            $id = 5000 + $script:launches.Count
            [void]$script:launches.Add([pscustomobject]@{
                    FilePath     = [string]$FilePath
                    ArgumentList = [string]$ArgumentList
                    Id           = $id
                })
            return [pscustomobject]@{
                Id         = $id
                HasExited  = [bool]$script:mockExited
                ExitCode   = $script:mockExit
            }
        }
        Mock Invoke-TaskKill {
            [void]$script:kills.Add($ProcessId)
        }
    }

    It 'stdout.txt だけでは止めず、REPORT.md が出たら自分のPIDだけ止めて確認待ちへ移す' {
        $script:mockExited = $false
        $root = New-TestRoot
        New-JobFile -Root $root -Prio '1-video' -Name '10-a.md' -Lane 'chrome'
        $script:onStart = {
            $dir = Join-Path $script:Out '10-a'
            Set-Content -LiteralPath (Join-Path $dir 'stdout.txt') -Value "running`r`n" -Encoding UTF8
        }
        Mock Get-Process {
            param($Id)
            return [pscustomobject]@{
                Id          = $Id
                ProcessName = 'grok'
                StartTime   = [datetime]'2026-10-21T21:00:00'
            }
        }
        $stdoutOnly = Invoke-NightRunner -Root $root -PollSec 0 -MaxIterations 2 -Grok 'grok.exe' -NowProvider {
            [datetime]'2026-10-21T21:00:00'
        }
        $stdoutOnly | Should -Be 0
        $script:kills.Count | Should -Be 0
        $script:launches.Count | Should -Be 1
        Test-Path -LiteralPath (Get-QueuePath -Root $root -Folder '_running' -Name '10-a.md') | Should -BeTrue
        Test-Path -LiteralPath (Get-QueuePath -Root $root -Folder '_needs-review' -Name '10-a.md') | Should -BeFalse

        $script:launches = New-Object System.Collections.ArrayList
        $script:kills = New-Object System.Collections.ArrayList
        $reportRoot = New-TestRoot
        New-JobFile -Root $reportRoot -Prio '1-video' -Name '10-a.md' -Lane 'chrome'
        $script:onStart = {
            $dir = Join-Path $script:Out '10-a'
            Set-Content -LiteralPath (Join-Path $dir 'stdout.txt') -Value "running`r`n" -Encoding UTF8
            Set-Content -LiteralPath (Join-Path $dir 'REPORT.md') -Value "done`r`n" -Encoding UTF8
        }
        $code = Invoke-NightRunner -Root $reportRoot -PollSec 0 -MaxIterations 5 -Grok 'grok.exe' -NowProvider {
            [datetime]'2026-10-21T21:00:00'
        }
        $code | Should -Be 0
        $script:launches.Count | Should -Be 1
        $script:kills.Count | Should -Be 1
        $script:kills[0] | Should -Be $script:launches[0].Id
        $log = Get-Content -Raw -LiteralPath (Join-Path (Join-Path $reportRoot 'out') 'night-runner-20261021.log')
        $log | Should -Match '報告ファイルが出たので停止'
        $log | Should -Match ('taskkill.exe /PID {0} /T /F' -f $script:launches[0].Id)
        $log | Should -Not -Match '/IM'
        $log | Should -Match 'background-wait-timeout 3600'
        Test-Path -LiteralPath (Get-QueuePath -Root $reportRoot -Folder '_needs-review' -Name '10-a.md') | Should -BeTrue
        Test-Path -LiteralPath (Get-QueuePath -Root $reportRoot -Folder '_running' -Name '10-a.md') | Should -BeFalse
        Test-Path -LiteralPath (Get-QueuePath -Root $reportRoot -Folder '_failed' -Name '10-a.md') | Should -BeFalse
    }

    It '朝の実処理は名前が grok の記録PIDだけ止める' {
        $root = New-TestRoot
        $out = Join-Path $root 'out'
        New-Item -ItemType Directory -Force -Path $out | Out-Null
        $state = '[{"lane":"chrome","pid":9999,"name":"grok","job":"10-a.md","started":"2026-10-21T21:00:00"}]'
        Set-Content -LiteralPath (Join-Path $out 'night-state-20261021.json') -Value $state -Encoding UTF8
        Mock Get-Process {
            return [pscustomobject]@{
                Id          = 9999
                ProcessName = 'grok'
                StartTime   = [datetime]'2026-10-21T21:00:05'
            }
        }
        $code = Invoke-NightRunner -Root $root -PollSec 0 -MaxIterations 3 -Grok 'grok.exe' -NowProvider {
            [datetime]'2026-10-22T10:00:00'
        }
        $code | Should -Be 0
        $script:launches.Count | Should -Be 0
        $script:kills | Should -Be @(9999)
        $log = Get-Content -Raw -LiteralPath (Join-Path $out 'night-runner-20261021.log')
        $log | Should -Match 'taskkill.exe /PID 9999 /T /F'
        $log | Should -Not -Match '/IM'
    }

    It '前回 _running に残ったジョブは失敗フォルダへ移す' {
        $root = New-TestRoot
        $run = Join-Path (Join-Path $root 'queue') '_running'
        New-Item -ItemType Directory -Force -Path $run | Out-Null
        Set-Content -LiteralPath (Join-Path $run '09-old.md') -Value "lane: none`r`n# old`r`n" -Encoding UTF8
        $code = Invoke-NightRunner -Root $root -PollSec 0 -MaxIterations 3 -Grok 'grok.exe' -NowProvider {
            [datetime]'2026-10-21T21:00:00'
        }
        $code | Should -Be 0
        Test-Path -LiteralPath (Get-QueuePath -Root $root -Folder '_failed' -Name '09-old.md') | Should -BeTrue
        Test-Path -LiteralPath (Join-Path $run '09-old.md') | Should -BeFalse
        $script:launches.Count | Should -Be 0
    }
}

Describe 'ps1 の UTF-8 BOM' {
    It '先頭の BOM が2つなら 2 と数える' {
        $sample = [byte[]](0xEF, 0xBB, 0xBF, 0xEF, 0xBB, 0xBF, 0x23)
        (Get-LeadingUtf8BomCount -Bytes $sample) | Should -Be 2
        $single = [byte[]](0xEF, 0xBB, 0xBF, 0x23)
        (Get-LeadingUtf8BomCount -Bytes $single) | Should -Be 1
        $none = [byte[]](0x23, 0x20)
        (Get-LeadingUtf8BomCount -Bytes $none) | Should -Be 0
    }

    It 'night-runner と install-task とテストは BOM がちょうど1つ' {
        foreach ($path in @($script:Runner, $script:Installer, $script:TestScript)) {
            $bytes = [System.IO.File]::ReadAllBytes($path)
            (Get-LeadingUtf8BomCount -Bytes $bytes) | Should -Be 1
            $b3 = [int]$bytes[3]
            $b4 = [int]$bytes[4]
            $b5 = [int]$bytes[5]
            (($b3 -eq 239) -and ($b4 -eq 187) -and ($b5 -eq 191)) | Should -BeFalse
        }
    }
}

Describe 'install-task' {
    It 'タスク引数は 5.1 の powershell へ night-runner を渡し、Grok を足せる' {
        $arg = Get-NightRunnerArgument -Root 'C:\Users\hp\Documents\grokbuild' -Grok 'C:\Tools\grok.exe'
        $arg | Should -Be '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "C:\Users\hp\Documents\grokbuild\night-runner.ps1" -Grok "C:\Tools\grok.exe"'
    }

    It '既定ユーザーは hp で終わる' {
        (Get-DefaultNightUser) | Should -Match '\\hp$'
    }

    It 'スクリプト本体に電源断とイメージ指定の kill が無い' {
        foreach ($path in @($script:Runner, $script:Installer)) {
            $text = Get-Content -Raw -LiteralPath $path
            $text | Should -Not -Match 'Stop-Computer'
            $text | Should -Not -Match 'Restart-Computer'
            $text | Should -Not -Match 'shutdown\.exe'
            $text | Should -Not -Match '(?i)taskkill(\.exe)?[^\r\n]*/IM'
        }
    }
}
