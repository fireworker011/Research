BeforeAll {
    $parent = Join-Path -Path $PSScriptRoot -ChildPath '..'
    $script:Runner = (Resolve-Path (Join-Path -Path $parent -ChildPath 'night-runner.ps1')).Path
    $script:Installer = (Resolve-Path (Join-Path -Path $parent -ChildPath 'install-task.ps1')).Path
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

    It '時間外は grok も代替プロセスも起動しない' {
        $root = New-TestRoot
        New-JobFile -Root $root -Prio '1-video' -Name '10-a.md' -Lane 'chrome'
        $code = Invoke-NightRunner -Root $root -DryRun -PollSec 0 -MaxIterations 5 -Grok 'grok.exe' -NowProvider {
            [datetime]'2026-10-21T12:00:00'
        }
        $code | Should -Be 0
        $script:launches.Count | Should -Be 0
        Test-Path -LiteralPath (Join-Path (Join-Path (Join-Path $root 'queue') '1-video') '10-a.md') | Should -BeTrue
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

    It 'grok の引数は prompt-file / always-approve / background-wait-timeout の順' {
        $path = 'C:\Users\hp\Documents\grok build\queue\_running\10-a.md'
        $line = Get-GrokArgumentLine -JobPath $path
        $line | Should -Be '--prompt-file "C:\Users\hp\Documents\grok build\queue\_running\10-a.md" --always-approve --background-wait-timeout'
    }

    It 'DryRun は grok.exe を起動せず、ログに同じ引数を残す' {
        $root = New-TestRoot
        New-JobFile -Root $root -Prio '1-video' -Name '10-a.md' -Lane 'chrome'
        $code = Invoke-NightRunner -Root $root -DryRun -PollSec 0 -MaxIterations 10 -Grok 'grok.exe' -NowProvider {
            [datetime]'2026-10-21T21:00:00'
        }
        $code | Should -Be 0
        $script:launches.Count | Should -BeGreaterThan 0
        foreach ($launch in $script:launches) {
            $launch.FilePath | Should -Not -Be 'grok.exe'
        }
        $log = Get-Content -Raw -LiteralPath (Join-Path (Join-Path $root 'out') 'night-runner-20261021.log')
        $log | Should -Match 'grok\.exe --prompt-file ".*10-a\.md" --always-approve --background-wait-timeout'
        $log | Should -Not -Match 'Stop-Computer|Restart-Computer|shutdown'
        Test-Path -LiteralPath (Join-Path (Join-Path (Join-Path $root 'queue') '_needs-review') '10-a.md') | Should -BeTrue
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
        $log = Get-Content -Raw -LiteralPath (Join-Path (Join-Path $root 'out') 'night-runner-20261021.log')
        $starts = [regex]::Matches($log, '開始 \[none\] (\S+)')
        $starts.Count | Should -Be 3
        $starts[0].Groups[1].Value | Should -Be '1-video/90-video.md'
        $starts[1].Groups[1].Value | Should -Be '2-cg/01-cg.md'
        $starts[2].Groups[1].Value | Should -Be '3-sakura/01-sakura.md'
        $log | Should -Not -Match 'TEMPLATE-sakura'
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
        $script:launches.Count | Should -Be 2
        $log = Get-Content -Raw -LiteralPath (Join-Path (Join-Path $root 'out') 'night-runner-20261021.log')
        $log | Should -Match '開始 \[chrome\] 1-video/10-chrome-a.md'
        $log | Should -Match '開始 \[edge\] 1-video/30-edge.md'
        $log | Should -Not -Match '20-chrome-b.md'
        Test-Path -LiteralPath (Join-Path (Join-Path (Join-Path $root 'queue') '1-video') '20-chrome-b.md') | Should -BeTrue
        $state = Get-Content -Raw -LiteralPath (Join-Path (Join-Path $root 'out') 'night-state-20261021.json')
        $state.TrimStart() | Should -Match '^[\[]'
        @($state | ConvertFrom-Json).Count | Should -Be 2
    }

    It '03:30 ちょうどは新規開始しない。03:29 は開始する' {
        $lateRoot = New-TestRoot
        New-JobFile -Root $lateRoot -Prio '1-video' -Name '10-a.md' -Lane 'chrome'
        $late = Invoke-NightRunner -Root $lateRoot -DryRun -PollSec 0 -MaxIterations 5 -Grok 'grok.exe' -NowProvider {
            [datetime]'2026-10-22T03:30:00'
        }
        $late | Should -Be 0
        $script:launches.Count | Should -Be 0
        Test-Path -LiteralPath (Join-Path (Join-Path (Join-Path $lateRoot 'queue') '1-video') '10-a.md') | Should -BeTrue

        $script:launches = New-Object System.Collections.ArrayList
        $earlyRoot = New-TestRoot
        New-JobFile -Root $earlyRoot -Prio '1-video' -Name '10-a.md' -Lane 'chrome'
        $early = Invoke-NightRunner -Root $earlyRoot -DryRun -PollSec 0 -MaxIterations 5 -Grok 'grok.exe' -NowProvider {
            [datetime]'2026-10-22T03:29:00'
        }
        $early | Should -Be 0
        $script:launches.Count | Should -Be 1
    }

    It '04:00 は自分が起動したPIDだけを taskkill /PID /T で止める' {
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
        $script:launches.Count | Should -Be 1
        $script:kills.Count | Should -Be 1
        $script:kills[0] | Should -Be $script:launches[0].Id
        $log = Get-Content -Raw -LiteralPath (Join-Path (Join-Path $root 'out') 'night-runner-20261021.log')
        $log | Should -Match ('taskkill.exe /PID {0} /T /F' -f $script:launches[0].Id)
        $log | Should -Not -Match '/IM'
        Test-Path -LiteralPath (Join-Path (Join-Path (Join-Path $root 'queue') '_failed') '10-a.md') | Should -BeTrue
        $summary = Get-Content -Raw -LiteralPath (Join-Path (Join-Path $root 'out') 'night-summary-20261021.md')
        $summary | Should -Match '04:00で打ち切り'
        $summary | Should -Match 'シャットダウンしていない'
    }

    It '時間切れは記録したPIDだけ止めて失敗にする' {
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
        $script:kills.Count | Should -Be 1
        $script:kills[0] | Should -Be $script:launches[0].Id
        $summary = Get-Content -Raw -LiteralPath (Join-Path (Join-Path $root 'out') 'night-summary-20261021.md')
        $summary | Should -Match 'ジョブ時間切れ'
    }

    It 'requires が _needs-review に入るまで後続レーンを始めない' {
        $root = New-TestRoot
        New-JobFile -Root $root -Prio '1-video' -Name '10-a.md' -Lane 'chrome'
        New-JobFile -Root $root -Prio '1-video' -Name '20-b.md' -Lane 'edge' -Extra 'requires: 10-a.md'
        $code = Invoke-NightRunner -Root $root -DryRun -PollSec 0 -MaxIterations 10 -Grok 'grok.exe' -NowProvider {
            [datetime]'2026-10-21T21:00:00'
        }
        $code | Should -Be 0
        $log = Get-Content -Raw -LiteralPath (Join-Path (Join-Path $root 'out') 'night-runner-20261021.log')
        $a = $log.IndexOf('開始 [chrome] 1-video/10-a.md')
        $b = $log.IndexOf('開始 [edge] 1-video/20-b.md')
        $done = $log.IndexOf('終了 [chrome] 10-a.md')
        $a | Should -BeGreaterThan -1
        $done | Should -BeGreaterThan $a
        $b | Should -BeGreaterThan $done
    }

    It '依存が揃わないジョブは起動しない' {
        $root = New-TestRoot
        New-JobFile -Root $root -Prio '1-video' -Name '20-b.md' -Lane 'edge' -Extra 'requires: 10-a.md'
        $code = Invoke-NightRunner -Root $root -DryRun -PollSec 0 -MaxIterations 3 -Grok 'grok.exe' -NowProvider {
            [datetime]'2026-10-21T21:00:00'
        }
        $code | Should -Be 0
        $script:launches.Count | Should -Be 0
        Test-Path -LiteralPath (Join-Path (Join-Path (Join-Path $root 'queue') '1-video') '20-b.md') | Should -BeTrue
    }

    It '朝の起動は状態ファイルのPIDだけ止め、名前が違えば止めない' {
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
        $code = Invoke-NightRunner -Root $root -DryRun -PollSec 0 -MaxIterations 3 -Grok 'grok.exe' -NowProvider {
            [datetime]'2026-10-22T10:00:00'
        }
        $code | Should -Be 0
        $script:launches.Count | Should -Be 0
        $script:kills | Should -Be @(9999)

        $script:kills = New-Object System.Collections.ArrayList
        $other = New-TestRoot
        $otherOut = Join-Path $other 'out'
        New-Item -ItemType Directory -Force -Path $otherOut | Out-Null
        Set-Content -LiteralPath (Join-Path $otherOut 'night-state-20261021.json') -Value $state -Encoding UTF8
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
    }

    It 'Imagine の非0終了はまとめに出す。review false の成功は done' {
        $script:mockExit = 1
        $root = New-TestRoot
        New-JobFile -Root $root -Prio '1-video' -Name '10-a.md' -Lane 'chrome' -Extra 'imagine: true'
        $code = Invoke-NightRunner -Root $root -DryRun -PollSec 0 -MaxIterations 5 -Grok 'grok.exe' -NowProvider {
            [datetime]'2026-10-21T21:00:00'
        }
        $code | Should -Be 0
        $summary = Get-Content -Raw -LiteralPath (Join-Path (Join-Path $root 'out') 'night-summary-20261021.md')
        $summary | Should -Match 'Imagine異常'
        Test-Path -LiteralPath (Join-Path (Join-Path (Join-Path $root 'queue') '_failed') '10-a.md') | Should -BeTrue

        $script:mockExit = 0
        $script:launches = New-Object System.Collections.ArrayList
        $doneRoot = New-TestRoot
        New-JobFile -Root $doneRoot -Prio '1-video' -Name '05-push.md' -Lane 'none' -Extra 'review: false'
        Invoke-NightRunner -Root $doneRoot -DryRun -PollSec 0 -MaxIterations 5 -Grok 'grok.exe' -NowProvider {
            [datetime]'2026-10-21T21:00:00'
        } | Should -Be 0
        Test-Path -LiteralPath (Join-Path (Join-Path (Join-Path $doneRoot 'queue') '_done') '05-push.md') | Should -BeTrue
    }

    It '前回 _running に残ったジョブは失敗扱い' {
        $root = New-TestRoot
        $run = Join-Path (Join-Path $root 'queue') '_running'
        New-Item -ItemType Directory -Force -Path $run | Out-Null
        Set-Content -LiteralPath (Join-Path $run '09-old.md') -Value "lane: none`r`n# old`r`n" -Encoding UTF8
        $code = Invoke-NightRunner -Root $root -DryRun -PollSec 0 -MaxIterations 3 -Grok 'grok.exe' -NowProvider {
            [datetime]'2026-10-21T21:00:00'
        }
        $code | Should -Be 0
        Test-Path -LiteralPath (Join-Path (Join-Path (Join-Path $root 'queue') '_failed') '09-old.md') | Should -BeTrue
        $script:launches.Count | Should -Be 0
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
