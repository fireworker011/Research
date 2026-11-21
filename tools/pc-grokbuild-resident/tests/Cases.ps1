# Queue state machine checks. Windows PowerShell 5.1 syntax, run with pwsh on Linux.
Set-StrictMode -Version 2.0

$script:ToolRoot = Split-Path -Parent $PSScriptRoot
$script:PcDir = Join-Path $script:ToolRoot 'pc'
$script:ModulePath = Join-Path (Join-Path $script:PcDir 'lib') 'GrokBuildResident.psm1'
Import-Module $script:ModulePath -Force

$script:FailCount = 0

function Assert-True {
    param($Condition, [string]$Message)
    if (-not $Condition) { throw $Message }
}

function Assert-Eq {
    param($Actual, $Expected, [string]$Message)
    if ("$Actual" -ne "$Expected") {
        throw "$Message expected [$Expected] got [$Actual]"
    }
}

function New-TempRoot {
    $path = Join-Path ([System.IO.Path]::GetTempPath()) ('gbres-' + [guid]::NewGuid().ToString('N'))
    [void][System.IO.Directory]::CreateDirectory($path)
    Initialize-ResidentTree $path | Out-Null
    return $path
}

function New-OrderText {
    param(
        [string]$Id,
        [string]$Lane = '',
        [string]$Reasoning = '',
        [string]$Sha = '',
        $Timeout = $null,
        $Seq = $null,
        [string]$Model = '',
        [string]$Fast = '',
        [object[]]$Steps,
        [string]$Body = "Do the steps.`n"
    )
    $lines = New-Object System.Collections.Generic.List[string]
    [void]$lines.Add('---')
    [void]$lines.Add("id: $Id")
    if ($Lane) { [void]$lines.Add("lane: $Lane") }
    if ($Reasoning) { [void]$lines.Add("reasoning: $Reasoning") }
    if ($Model) { [void]$lines.Add("model: $Model") }
    if ($Fast) { [void]$lines.Add("fast: $Fast") }
    if ($null -ne $Timeout) { [void]$lines.Add("confirm_timeout_sec: $Timeout") }
    if ($null -ne $Seq) { [void]$lines.Add("seq: $Seq") }
    if ($Sha) { [void]$lines.Add("sha256: $Sha") }
    [void]$lines.Add('steps:')
    foreach ($step in $Steps) {
        [void]$lines.Add("  - id: $($step.id)")
        [void]$lines.Add("    mode: $($step.mode)")
        if (-not [string]::IsNullOrWhiteSpace([string]$step.kind)) {
            [void]$lines.Add("    kind: $($step.kind)")
        }
        [void]$lines.Add("    summary: $($step.summary)")
    }
    [void]$lines.Add('---')
    return (($lines -join "`n") + "`n" + $Body)
}

function New-ReadStep {
    param([string]$Id = 'look', [string]$Summary = 'read the page')
    return [pscustomobject]@{ id = $Id; mode = 'read-only'; kind = ''; summary = $Summary }
}

function New-SaveStep {
    param([string]$Id = 'save', [string]$Summary = 'save the field')
    return [pscustomobject]@{ id = $Id; mode = 'irreversible'; kind = 'save'; summary = $Summary }
}

function Put-Inbox {
    param([string]$Root, [string]$Name, [string]$Text)
    $path = Join-Path (Join-Path (Join-Path $Root 'queue') 'inbox') $Name
    Write-Utf8File -Path $path -Text $Text
}

function Read-Status {
    param([string]$Root, [string]$Id)
    $path = Join-Path (Join-Path (Join-Path $Root 'queue') 'status') ($Id + '.json')
    return Read-JsonFile $path
}

function New-TickState {
    param([string]$Root, [int]$DenyGraceSec = 60)
    Enable-FakeGrokProcess
    return New-ResidentState -Root $Root -GrokExe 'C:\Users\hp\.grok\bin\grok.exe' -HostName 'LAPTOP-PL4TICBO' -UserName 'hp' -DenyGraceSec $DenyGraceSec
}

function Invoke-Case {
    param([string]$Name, [scriptblock]$Body)
    try {
        & $Body
        Write-Host "PASS $Name"
    }
    catch {
        $script:FailCount++
        Write-Host "FAIL $Name :: $($_.Exception.Message)"
    }
}

function Invoke-ResidentCases {
    $script:FailCount = 0
    $utc = [datetime]::Parse('2026-11-21T00:00:00Z', $null, [System.Globalization.DateTimeStyles]::AdjustToUniversal)

    Invoke-Case 'sha256 of empty body' {
        Assert-Eq (Get-OrderBodySha256 '') 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855' 'empty hash'
    }

    Invoke-Case 'default reasoning is xhigh and read-only lane' {
        $text = New-OrderText -Id 'ro1' -Steps @(New-ReadStep)
        $doc = Test-OrderText $text
        Assert-True $doc.Ok ($doc.Errors -join '; ')
        Assert-Eq $doc.Reasoning 'xhigh' 'reasoning'
        Assert-Eq $doc.Lane 'readonly' 'lane'
        Assert-Eq $doc.Model 'grok-4.7' 'model'
    }

    Invoke-Case 'high is accepted and fast is rejected' {
        $high = Test-OrderText (New-OrderText -Id 'hi1' -Reasoning 'high' -Steps @(New-ReadStep))
        Assert-True $high.Ok ($high.Errors -join '; ')
        Assert-Eq $high.Reasoning 'high' 'high'
        $fast = Test-OrderText (New-OrderText -Id 'bad1' -Reasoning 'fast' -Steps @(New-ReadStep))
        Assert-True (-not $fast.Ok) 'fast reasoning should fail'
        $flag = Test-OrderText (New-OrderText -Id 'bad2' -Fast 'true' -Steps @(New-ReadStep))
        Assert-True (-not $flag.Ok) 'fast: true should fail'
        $model = Test-OrderText (New-OrderText -Id 'bad3' -Model 'grok-4' -Steps @(New-ReadStep))
        Assert-True (-not $model.Ok) 'other model should fail'
    }

    Invoke-Case 'irreversible step requires a known kind' {
        $bad = Test-OrderText (New-OrderText -Id 'k1' -Steps @([pscustomobject]@{ id = 's'; mode = 'irreversible'; kind = ''; summary = 'save' }))
        Assert-True (-not $bad.Ok) 'missing kind'
        $ok = Test-OrderText (New-OrderText -Id 'k2' -Steps @(New-SaveStep))
        Assert-True $ok.Ok ($ok.Errors -join '; ')
        Assert-Eq $ok.Lane 'main' 'lane'
    }

    Invoke-Case 'readonly lane cannot hold an irreversible step' {
        $doc = Test-OrderText (New-OrderText -Id 'mix1' -Lane 'readonly' -Steps @(New-SaveStep))
        Assert-True (-not $doc.Ok) 'mixed readonly lane'
    }

    Invoke-Case 'sha256 match and mismatch' {
        $text = New-OrderText -Id 'sha1' -Steps @(New-ReadStep) -Body "キーワード`n"
        $stamped = Add-OrderSha256Text $text
        $ok = Test-OrderText $stamped
        Assert-True $ok.Ok ($ok.Errors -join '; ')
        Assert-True $ok.HasSha256 'has sha'
        $bad = $stamped -replace 'sha256: [0-9a-f]+', ('sha256: ' + ('11' * 32))
        $rejected = Test-OrderText $bad
        Assert-True (-not $rejected.Ok) 'mismatch should fail'
        Assert-True (($rejected.Errors -join ';') -match 'sha256 mismatch') 'mismatch message'
    }

    Invoke-Case 'python stamp matches PowerShell' {
        $raw = "---`r`nid: hash-me`r`nsteps:`r`n  - id: s`r`n    mode: read-only`r`n    summary: see`r`n---`r`nキーワード`n"
        $dir = New-TempRoot
        $path = Join-Path $dir 'hash-me.md'
        $utf8 = New-Object System.Text.UTF8Encoding $false
        [System.IO.File]::WriteAllText($path, $raw, $utf8)
        $fromPs = Add-OrderSha256Text (Read-TextFile $path)
        $stamp = Join-Path (Join-Path $script:ToolRoot 'linux') 'order_stamp.py'
        $pyOut = Join-Path $dir 'stamped-py.md'
        $proc = New-Object System.Diagnostics.Process
        $proc.StartInfo.FileName = 'python3'
        $proc.StartInfo.Arguments = ($stamp + ' stamp ' + $path)
        $proc.StartInfo.UseShellExecute = $false
        $proc.StartInfo.RedirectStandardOutput = $true
        $proc.StartInfo.RedirectStandardError = $true
        [void]$proc.Start()
        $fromPy = $proc.StandardOutput.ReadToEnd()
        $pyErr = $proc.StandardError.ReadToEnd()
        $proc.WaitForExit()
        if ($proc.ExitCode -ne 0) { throw $pyErr }
        [System.IO.File]::WriteAllText($pyOut, $fromPy)
        Assert-Eq $fromPy $fromPs 'stamp bytes'
    }

    Invoke-Case 'fifo by file name' {
        $root = New-TempRoot
        $state = New-TickState $root
        Put-Inbox $root 'b-job.md' (New-OrderText -Id 'job-b' -Lane 'main' -Steps @(New-ReadStep))
        Put-Inbox $root 'a-job.md' (New-OrderText -Id 'job-a' -Lane 'main' -Steps @(New-ReadStep))
        Invoke-ResidentTick -State $state -Now $utc | Out-Null
        Assert-Eq $state.MainJobId 'job-a' 'first id'
        Assert-True (Test-Path (Join-Path (Join-Path (Join-Path $root 'queue') 'inbox') 'b-job.md')) 'second stays'
        $st = Read-Status $root 'job-a'
        Assert-Eq $st.state 'running' 'state'
        Assert-Eq $st.pid '9000' 'pid'
        Assert-Eq $st.model 'grok-4.7' 'model'
        Assert-Eq $st.host 'LAPTOP-PL4TICBO' 'host'
        Assert-True ($null -eq $st.end) 'end empty'
        Assert-True ($null -eq $st.exit_code) 'exit empty'
    }

    Invoke-Case 'seq beats file name' {
        $root = New-TempRoot
        $state = New-TickState $root
        Put-Inbox $root 'a-job.md' (New-OrderText -Id 'job-a' -Lane 'main' -Seq 2 -Steps @(New-ReadStep))
        Put-Inbox $root 'b-job.md' (New-OrderText -Id 'job-b' -Lane 'main' -Seq 1 -Steps @(New-ReadStep))
        Invoke-ResidentTick -State $state -Now $utc | Out-Null
        Assert-Eq $state.MainJobId 'job-b' 'seq winner'
    }

    Invoke-Case 'readonly lane runs beside the main lane' {
        $root = New-TempRoot
        $state = New-TickState $root
        Put-Inbox $root 'm.md' (New-OrderText -Id 'main-1' -Steps @(New-SaveStep))
        Put-Inbox $root 'r.md' (New-OrderText -Id 'ro-1' -Steps @(New-ReadStep))
        Put-Inbox $root 'm2.md' (New-OrderText -Id 'main-2' -Steps @(New-SaveStep))
        Invoke-ResidentTick -State $state -Now $utc | Out-Null
        Assert-Eq $state.MainJobId 'main-1' 'main slot'
        Assert-Eq $state.ReadOnlyJobId 'ro-1' 'readonly slot'
        Assert-True (Test-Path (Join-Path (Join-Path (Join-Path $root 'queue') 'inbox') 'm2.md')) 'second main waits'
        Assert-Eq (Get-FakeGrokHandles).Count '2' 'two processes'
    }

    Invoke-Case 'grok args stay on grok-4.7 and never use fast' {
        $root = New-TempRoot
        $state = New-TickState $root
        Put-Inbox $root 'hi.md' (New-OrderText -Id 'hi-job' -Reasoning 'high' -Steps @(New-ReadStep -Summary 'look only'))
        Invoke-ResidentTick -State $state -Now $utc | Out-Null
        $launch = (Get-GrokLaunchLog)[0]
        $line = [string]$launch.ArgumentLine
        Assert-True ($line -match '--prompt-file') 'prompt flag'
        Assert-True ($line -match '--always-approve') 'approve flag'
        Assert-True ($line -match '-m grok-4\.7') 'model flag'
        Assert-True ($line -match '--reasoning-effort high') 'effort flag'
        Assert-True ($line -notmatch '(?i)(^|\s)--fast(\s|$)') 'no fast'
        $promptPath = Join-Path (Join-Path (Join-Path $root 'queue') 'running') 'hi-job.prompt.md'
        $prompt = [System.IO.File]::ReadAllText($promptPath)
        Assert-True ($prompt -match 'Run read-only steps immediately') 'preamble read-only'
        Assert-True ($prompt -match 'Never print secrets') 'preamble secrets'
        Assert-True ($prompt -match '2FA') 'preamble 2fa'
        Assert-True ($prompt -match 'login') 'preamble login'
        Assert-True ($prompt -match 'save, send, post, delete, publish, payment') 'kinds'
        Assert-True ($prompt -match '"steps":\[') 'preamble writes steps array'
        Assert-True ($prompt -match 'hi-job') 'job id'
        Assert-True ($prompt -notmatch '«redacted»') 'preamble not redacted'
        Assert-True ($prompt -notmatch '(?i)(^|\s)--fast(\s|$)') 'prompt has no fast flag'
    }

    Invoke-Case 'sha mismatch does not start grok' {
        $root = New-TempRoot
        $state = New-TickState $root
        $text = New-OrderText -Id 'badsha' -Sha ('ab' * 32) -Steps @(New-ReadStep)
        Put-Inbox $root 'bad.md' $text
        Invoke-ResidentTick -State $state -Now $utc | Out-Null
        Assert-Eq (Get-GrokLaunchLog).Count '0' 'no launch'
        $st = Read-Status $root 'badsha'
        Assert-Eq $st.state 'rejected' 'state'
        Assert-Eq $st.exit_code '10' 'exit'
        Assert-True (Test-Path (Join-Path (Join-Path (Join-Path $root 'queue') 'failed') 'bad.md')) 'moved'
    }

    Invoke-Case 'exit 0 moves the order to done' {
        $root = New-TempRoot
        $state = New-TickState $root
        Put-Inbox $root 'ok.md' (New-OrderText -Id 'ok-job' -Steps @(New-ReadStep))
        Invoke-ResidentTick -State $state -Now $utc | Out-Null
        $handle = (Get-FakeGrokHandles)[0]
        $handle.Exited = $true
        $handle.ExitCode = 0
        Invoke-ResidentTick -State $state -Now $utc.AddMinutes(1) | Out-Null
        $st = Read-Status $root 'ok-job'
        Assert-Eq $st.state 'done' 'state'
        Assert-Eq $st.exit_code '0' 'exit'
        $rawStatus = [System.IO.File]::ReadAllText((Get-JobStatusPath $root 'ok-job'))
        Assert-True ($rawStatus -match '"end":"2026-11-21T00:01:00Z"') 'end'
        Assert-True ($null -eq $state.ReadOnlyJobId) 'slot freed'
        Assert-True (Test-Path (Join-Path (Join-Path (Join-Path $root 'queue') 'done') 'ok.md')) 'done file'
    }

    Invoke-Case 'confirm timeout aborts and kills the process' {
        $root = New-TempRoot
        $state = New-TickState $root
        Put-Inbox $root 'c.md' (New-OrderText -Id 'conf-job' -Timeout 10 -Steps @(New-SaveStep))
        Invoke-ResidentTick -State $state -Now $utc | Out-Null
        $json = Join-Path (Join-Path (Join-Path $root 'queue') 'confirm') 'conf-job.json'
        Write-Utf8File -Path $json -Text '{"job_id":"conf-job","steps":[{"step_id":"save","kind":"save","target_url":"https://example.com/item","changes":[{"field":"title","before":"old","after":"new"}]}]}'
        Invoke-ResidentTick -State $state -Now $utc | Out-Null
        $st = Read-Status $root 'conf-job'
        Assert-Eq $st.state 'awaiting_confirm' 'waiting'
        Invoke-ResidentTick -State $state -Now $utc.AddSeconds(10) | Out-Null
        $st2 = Read-Status $root 'conf-job'
        Assert-Eq $st2.state 'aborted' 'aborted'
        Assert-Eq $st2.exit_code '20' 'exit'
        $handle = (Get-FakeGrokHandles)[0]
        Assert-True ([int]$handle.KillCount -ge 1) 'killed'
        Assert-True (Test-Path (Join-Path (Join-Path (Join-Path $root 'queue') 'failed') 'c.md')) 'failed file'
    }

    Invoke-Case 'confirm reader accepts steps and flat shapes' {
        $steps = '{"job_id":"shape-job","steps":[{"step_id":"save-a","kind":"save","target_url":"https://example.com/a","changes":[{"field":"title","before":"old","after":"new"}]},{"step_id":"post-b","kind":"POST","target_url":"https://example.com/b","changes":[{"field":"pin","before":"","after":"note"}]}]}'
        $readSteps = Test-ConfirmJsonText -Text $steps -ExpectedJobId 'shape-job'
        Assert-True $readSteps.Valid 'steps valid'
        Assert-Eq $readSteps.Shape 'steps' 'steps shape'
        $flat = '{"job_id":"shape-job","step_id":"save-a","kind":"save","target_url":"https://example.com/a","changes":[{"field":"title","before":"old","after":"new"}]}'
        $readFlat = Test-ConfirmJsonText -Text $flat -ExpectedJobId 'shape-job'
        Assert-True $readFlat.Valid 'flat valid'
        Assert-Eq $readFlat.Shape 'flat' 'flat shape'
        $wrong = Test-ConfirmJsonText -Text $flat -ExpectedJobId 'other-job'
        Assert-True (-not $wrong.Valid) 'job id mismatch'
        $emptySteps = Test-ConfirmJsonText -Text '{"job_id":"shape-job","steps":[]}' -ExpectedJobId 'shape-job'
        Assert-True (-not $emptySteps.Valid) 'empty steps'
        $garbage = Test-ConfirmJsonText -Text '{"job_id":"shape-job","changes":[]}' -ExpectedJobId 'shape-job'
        Assert-True (-not $garbage.Valid) 'missing step fields'

        $root = New-TempRoot
        $state = New-TickState $root
        Put-Inbox $root 'bad.md' (New-OrderText -Id 'bad-shape' -Steps @(New-SaveStep))
        Invoke-ResidentTick -State $state -Now $utc | Out-Null
        $dir = Join-Path (Join-Path $root 'queue') 'confirm'
        Write-Utf8File -Path (Join-Path $dir 'bad-shape.json') -Text '{"job_id":"bad-shape","note":"not a step"}'
        Write-Utf8File -Path (Join-Path $dir 'bad-shape.ok') -Text 'ok'
        Invoke-ResidentTick -State $state -Now $utc.AddSeconds(2) | Out-Null
        $st = Read-Status $root 'bad-shape'
        Assert-Eq $st.state 'running' 'bad shape stays running'
        Assert-True ([string]::IsNullOrWhiteSpace([string]$st.confirm_decision)) 'bad shape is not approval'
        $log = [System.IO.File]::ReadAllText((Join-Path (Join-Path (Join-Path $root 'queue') 'logs') 'resident.log'))
        Assert-True ($log -match 'confirm json needs steps') 'parse error logged'
    }

    Invoke-Case 'approve file without json does not count' {
        $root = New-TempRoot
        $state = New-TickState $root
        Put-Inbox $root 'c.md' (New-OrderText -Id 'early-ok' -Steps @(New-SaveStep))
        Invoke-ResidentTick -State $state -Now $utc | Out-Null
        $ok = Join-Path (Join-Path (Join-Path $root 'queue') 'confirm') 'early-ok.ok'
        Write-Utf8File -Path $ok -Text '{"decision":"ok"}'
        Invoke-ResidentTick -State $state -Now $utc.AddSeconds(5) | Out-Null
        $st = Read-Status $root 'early-ok'
        Assert-Eq $st.state 'running' 'still running'
        Assert-True ([string]::IsNullOrWhiteSpace([string]$st.confirm_decision)) 'no decision'
    }

    Invoke-Case 'ok returns to running and ng then exit is denied' {
        $root = New-TempRoot
        $state = New-TickState $root
        Put-Inbox $root 'c.md' (New-OrderText -Id 'ok-conf' -Steps @(New-SaveStep))
        Invoke-ResidentTick -State $state -Now $utc | Out-Null
        $dir = Join-Path (Join-Path $root 'queue') 'confirm'
        Write-Utf8File -Path (Join-Path $dir 'ok-conf.json') -Text '{"job_id":"ok-conf","step_id":"save","kind":"save","target_url":"https://example.com/item","changes":[{"field":"title","before":"old","after":"new"}]}'
        Write-Utf8File -Path (Join-Path $dir 'ok-conf.ok') -Text '{"decision":"ok"}'
        Invoke-ResidentTick -State $state -Now $utc.AddSeconds(3) | Out-Null
        $st = Read-Status $root 'ok-conf'
        Assert-Eq $st.state 'running' 'running after ok'
        Assert-Eq $st.confirm_decision 'ok' 'decision'
        Assert-Eq ([int](Get-FakeGrokHandles)[0].KillCount) '0' 'not killed'

        $root2 = New-TempRoot
        $state2 = New-TickState $root2
        Put-Inbox $root2 'n.md' (New-OrderText -Id 'ng-conf' -Steps @(New-SaveStep))
        Invoke-ResidentTick -State $state2 -Now $utc | Out-Null
        Write-Utf8File -Path (Join-Path (Join-Path (Join-Path $root2 'queue') 'confirm') 'ng-conf.ng') -Text '{"decision":"ng"}'
        $handle = (Get-FakeGrokHandles)[0]
        $handle.Exited = $true
        $handle.ExitCode = 0
        Invoke-ResidentTick -State $state2 -Now $utc.AddSeconds(2) | Out-Null
        $st2 = Read-Status $root2 'ng-conf'
        Assert-Eq $st2.state 'denied' 'denied'
        Assert-Eq $st2.exit_code '0' 'exit'
        Assert-True (Test-Path (Join-Path (Join-Path (Join-Path $root2 'queue') 'done') 'n.md')) 'clean deny lands in done'
    }

    Invoke-Case 'deny grace kills a stuck process' {
        $root = New-TempRoot
        $state = New-TickState $root 5
        Put-Inbox $root 'n.md' (New-OrderText -Id 'stuck-ng' -Steps @(New-SaveStep))
        Invoke-ResidentTick -State $state -Now $utc | Out-Null
        Write-Utf8File -Path (Join-Path (Join-Path (Join-Path $root 'queue') 'confirm') 'stuck-ng.ng') -Text '{"decision":"ng"}'
        Invoke-ResidentTick -State $state -Now $utc | Out-Null
        Invoke-ResidentTick -State $state -Now $utc.AddSeconds(5) | Out-Null
        $st = Read-Status $root 'stuck-ng'
        Assert-Eq $st.state 'denied' 'denied'
        Assert-Eq $st.exit_code '21' 'exit'
    }

    Invoke-Case 'orphan in running is not resumed' {
        $root = New-TempRoot
        $running = Join-Path (Join-Path $root 'queue') 'running'
        Write-Utf8File -Path (Join-Path $running 'old.md') -Text (New-OrderText -Id 'old-job' -Steps @(New-SaveStep))
        $state = New-TickState $root
        Repair-OrphanedRunningOrders -State $state -Now $utc
        Assert-Eq (Get-GrokLaunchLog).Count '0' 'no relaunch'
        $st = Read-Status $root 'old-job'
        Assert-Eq $st.state 'aborted' 'state'
        Assert-Eq $st.exit_code '40' 'exit'
        Assert-True ($st.error -match 'not resumed') 'error'
    }

    Invoke-Case 'stop aborts the active job' {
        $root = New-TempRoot
        $state = New-TickState $root
        Put-Inbox $root 's.md' (New-OrderText -Id 'stop-job' -Steps @(New-ReadStep))
        Invoke-ResidentTick -State $state -Now $utc | Out-Null
        Stop-ResidentJobs -State $state -Now $utc.AddMinutes(1) -Reason 'stop requested'
        $st = Read-Status $root 'stop-job'
        Assert-Eq $st.state 'aborted' 'state'
        Assert-Eq $st.exit_code '30' 'exit'
    }

    Invoke-Case 'heartbeat and secret redaction' {
        $root = New-TempRoot
        $state = New-TickState $root
        Put-Inbox $root 's.md' (New-OrderText -Id 'beat-job' -Lane 'main' -Steps @(New-ReadStep))
        Invoke-ResidentTick -State $state -Now $utc | Out-Null
        Write-ResidentHeartbeat -State $state -Now $utc -IntervalSec 10
        $beat = Read-JsonFile (Join-Path (Join-Path $root 'queue') 'heartbeat.json')
        Assert-Eq $beat.host 'LAPTOP-PL4TICBO' 'host'
        Assert-Eq $beat.user 'hp' 'user'
        Assert-Eq $beat.interval_sec '10' 'interval'
        Assert-Eq $beat.slots.main 'beat-job' 'slot'
        $dirty = ConvertTo-RedactedText "password=hunter2 Bearer abc.def.ghi sk-abcdefghij"
        Assert-True ($dirty -notmatch 'hunter2') 'password hidden'
        Assert-True ($dirty -notmatch 'abc\.def') 'bearer hidden'
        Assert-True ($dirty -notmatch 'sk-abcdefghij') 'sk hidden'
        Write-ResidentLog -Root $root -Message 'token=hunter2'
        $log = [System.IO.File]::ReadAllText((Join-Path (Join-Path (Join-Path $root 'queue') 'logs') 'resident.log'))
        Assert-True ($log -notmatch 'hunter2') 'log hidden'
    }

    Invoke-Case 'duplicate job id is rejected' {
        $root = New-TempRoot
        $state = New-TickState $root
        Put-Inbox $root 'a.md' (New-OrderText -Id 'same' -Lane 'main' -Steps @(New-ReadStep))
        Put-Inbox $root 'b.md' (New-OrderText -Id 'same' -Lane 'readonly' -Steps @(New-ReadStep))
        Invoke-ResidentTick -State $state -Now $utc | Out-Null
        Assert-Eq (Get-GrokLaunchLog).Count '1' 'one launch'
        $dup = Get-ChildItem (Join-Path (Join-Path $root 'queue') 'status') -Filter 'same-dup-*.json'
        Assert-Eq @($dup).Count '1' 'dup status'
    }

    Invoke-Case 'playbook orders and examples validate' {
        $files = @(Get-ChildItem (Join-Path $script:ToolRoot 'playbooks') -Filter '*.md' -File)
        $files += @(Get-ChildItem (Join-Path $script:ToolRoot 'examples') -Filter '*.md' -File)
        Assert-True ($files.Count -ge 4) 'files present'
        foreach ($file in $files) {
            $text = [System.IO.File]::ReadAllText($file.FullName)
            if ($file.Directory.Name -eq 'examples') {
                $doc = Test-OrderText $text
                Assert-True $doc.Ok ("example " + $file.Name + ' ' + ($doc.Errors -join '; '))
            }
            else {
                Assert-True ($text -match '2FA') ($file.Name + ' mentions 2FA')
                Assert-True ($text -match 'ログイン') ($file.Name + ' mentions login')
                $matches = [regex]::Matches($text, '(?s)```order\r?\n(.*?)```')
                Assert-True ($matches.Count -ge 1) ($file.Name + ' has an order')
                foreach ($m in $matches) {
                    $doc = Test-OrderText $m.Groups[1].Value
                    Assert-True $doc.Ok ($file.Name + ' ' + ($doc.Errors -join '; '))
                }
            }
        }
    }

    Invoke-Case 'install creates queue and a script copy' {
        $root = New-TempRoot
        & (Join-Path $script:PcDir 'Install-Resident.ps1') -Root $root -SkipTask | Out-Null
        Assert-True (Test-Path (Join-Path (Join-Path $root 'queue') 'inbox')) 'inbox'
        Assert-True (Test-Path (Join-Path (Join-Path $root 'queue') 'confirm')) 'confirm'
        Assert-True (Test-Path (Join-Path (Join-Path (Join-Path $root 'resident') 'lib') 'GrokBuildResident.psm1')) 'module copy'
        Assert-True (Test-Path (Join-Path (Join-Path $root 'resident') 'Resident.ps1')) 'resident copy'
        Assert-True (-not (Test-Path (Join-Path (Join-Path (Join-Path $root 'resident') 'lib') 'lib'))) 'no nested lib'
    }

    Invoke-Case 'scripts parse and avoid PowerShell 7-only operators' {
        $scripts = @(Get-ChildItem $script:PcDir -Recurse -Include '*.ps1', '*.psm1' -File)
        Assert-True ($scripts.Count -ge 8) 'script count'
        foreach ($file in $scripts) {
            $tokens = $null
            $errors = $null
            [void][System.Management.Automation.Language.Parser]::ParseFile($file.FullName, [ref]$tokens, [ref]$errors)
            if ($errors -and @($errors).Count -gt 0) {
                throw ($file.Name + ' ' + $errors[0].ToString())
            }
            $text = [System.IO.File]::ReadAllText($file.FullName)
            Assert-True ($text -notmatch '&&') ($file.Name + ' has &&')
            Assert-True ($text -notmatch '\?\?') ($file.Name + ' has ??')
            Assert-True ($text -notmatch '-AsHashtable') ($file.Name + ' has AsHashtable')
            Assert-True ($text -notmatch 'Join-String') ($file.Name + ' has Join-String')
            Assert-True ($text -notmatch '-Parallel') ($file.Name + ' has Parallel')
            Assert-True ($text -notmatch 'LeafBase') ($file.Name + ' has LeafBase')
        }
    }

    Invoke-Case 'wrapper redacts grok output and refuses fast' {
        $dir = New-TempRoot
        $fake = Join-Path $dir 'fake-grok.sh'
        $utf8 = New-Object System.Text.UTF8Encoding $false
        [System.IO.File]::WriteAllText($fake, "#!/bin/sh`necho password=hunter2`necho 'Bearer supersecrettoken' >&2`nexit 0`n", $utf8)
        & chmod +x $fake
        $prompt = Join-Path $dir 'prompt.md'
        [System.IO.File]::WriteAllText($prompt, "hello`n", $utf8)
        $log = Join-Path $dir 'job.log'
        $wrapper = Join-Path $script:PcDir 'Run-GrokLogged.ps1'
        & pwsh -NoProfile -File $wrapper -GrokExe $fake -PromptFile $prompt -Effort xhigh -LogPath $log | Out-Null
        Assert-Eq $LASTEXITCODE '0' 'wrapper exit'
        $logged = [System.IO.File]::ReadAllText($log)
        Assert-True ($logged -match 'model=grok-4.7') 'model line'
        Assert-True ($logged -match 'effort=xhigh') 'effort line'
        Assert-True ($logged -notmatch 'hunter2') 'no password'
        Assert-True ($logged -notmatch 'supersecrettoken') 'no bearer'
        & pwsh -NoProfile -File $wrapper -GrokExe $fake -PromptFile $prompt -Effort fast -LogPath (Join-Path $dir 'no.log') | Out-Null
        Assert-Eq $LASTEXITCODE '11' 'fast exit'
    }

    Invoke-Case 'resident once fails closed when grok.exe is missing' {
        $root = New-TempRoot
        $running = Join-Path (Join-Path $root 'queue') 'running'
        Write-Utf8File -Path (Join-Path $running 'old.md') -Text (New-OrderText -Id 'orphan-1' -Steps @(New-SaveStep))
        Put-Inbox $root 'new.md' (New-OrderText -Id 'missing-exe' -Steps @(New-ReadStep))
        $resident = Join-Path $script:PcDir 'Resident.ps1'
        & pwsh -NoProfile -File $resident -Root $root -Once -GrokExe '/no/such/grok.exe' -HostName 'LAPTOP-PL4TICBO' -UserName 'hp' -HeartbeatSec 10 | Out-Null
        Assert-Eq $LASTEXITCODE '0' 'resident exit'
        $orphan = Read-Status $root 'orphan-1'
        Assert-Eq $orphan.state 'aborted' 'orphan state'
        Assert-Eq $orphan.exit_code '40' 'orphan exit'
        $missing = Read-Status $root 'missing-exe'
        Assert-Eq $missing.state 'failed' 'missing state'
        Assert-Eq $missing.exit_code '12' 'missing exit'
        $beat = Read-JsonFile (Join-Path (Join-Path $root 'queue') 'heartbeat.json')
        Assert-Eq $beat.host 'LAPTOP-PL4TICBO' 'heartbeat host'
        Assert-Eq $beat.interval_sec '10' 'heartbeat interval'
        Assert-True (-not (Test-Path (Join-Path (Join-Path $root 'queue') 'resident.pid'))) 'pid removed'
    }

    Disable-FakeGrokProcess
    return $script:FailCount
}
