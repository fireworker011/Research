# Queue folders, status files, and one tick of the resident state machine.
# Windows PowerShell 5.1 compatible.

Set-StrictMode -Version 2.0

function Get-ResidentTaskName {
    return 'GrokBuildResident'
}

function Get-ResidentPaths {
    param([Parameter(Mandatory = $true)][string]$Root)
    $queue = Join-Path $Root 'queue'
    return [pscustomobject]@{
        Root      = $Root
        Queue     = $queue
        Inbox     = Join-Path $queue 'inbox'
        Running   = Join-Path $queue 'running'
        Done      = Join-Path $queue 'done'
        Failed    = Join-Path $queue 'failed'
        Status    = Join-Path $queue 'status'
        Confirm   = Join-Path $queue 'confirm'
        Logs      = Join-Path $queue 'logs'
        Heartbeat = Join-Path $queue 'heartbeat.json'
        Stop      = Join-Path $queue 'STOP'
        Pid       = Join-Path $queue 'resident.pid'
    }
}

function Initialize-ResidentTree {
    param([Parameter(Mandatory = $true)][string]$Root)
    $paths = Get-ResidentPaths $Root
    foreach ($dir in @($paths.Inbox, $paths.Running, $paths.Done, $paths.Failed, $paths.Status, $paths.Confirm, $paths.Logs)) {
        [void][System.IO.Directory]::CreateDirectory($dir)
    }
    return $paths
}

function ConvertTo-IsoUtc {
    param([Parameter(Mandatory = $true)][datetime]$When)
    return $When.ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ss') + 'Z'
}

function Write-AtomicJson {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)]$Object
    )
    $json = ConvertTo-Json -InputObject $Object -Depth 8 -Compress
    $dir = [System.IO.Path]::GetDirectoryName($Path)
    if (-not [string]::IsNullOrWhiteSpace($dir)) {
        [void][System.IO.Directory]::CreateDirectory($dir)
    }
    $utf8 = New-Object System.Text.UTF8Encoding $false
    $tmp = $Path + '.' + [guid]::NewGuid().ToString('N') + '.tmp'
    [System.IO.File]::WriteAllText($tmp, $json, $utf8)
    if ([System.IO.File]::Exists($Path)) {
        [System.IO.File]::Delete($Path)
    }
    [System.IO.File]::Move($tmp, $Path)
}

function Read-JsonFile {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not [System.IO.File]::Exists($Path)) { return $null }
    $raw = [System.IO.File]::ReadAllText($Path)
    if ([string]::IsNullOrWhiteSpace($raw)) { return $null }
    return ($raw | ConvertFrom-Json)
}

function Write-ResidentLog {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][string]$Message
    )
    $path = Join-Path (Join-Path (Join-Path $Root 'queue') 'logs') 'resident.log'
    $dir = [System.IO.Path]::GetDirectoryName($path)
    [void][System.IO.Directory]::CreateDirectory($dir)
    $line = (ConvertTo-IsoUtc ([datetime]::UtcNow)) + ' ' + (ConvertTo-RedactedText $Message) + "`n"
    $utf8 = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::AppendAllText($path, $line, $utf8)
}

function Get-JobStatusPath {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][string]$Id
    )
    return (Join-Path (Join-Path (Join-Path $Root 'queue') 'status') ($Id + '.json'))
}

function New-ResidentState {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [string]$GrokExe = 'C:\Users\hp\.grok\bin\grok.exe',
        [string]$HostName = 'LAPTOP-PL4TICBO',
        [string]$UserName = 'hp',
        [int]$DenyGraceSec = 60
    )
    return [pscustomobject]@{
        Root         = $Root
        GrokExe      = $GrokExe
        HostName     = $HostName
        UserName     = $UserName
        DenyGraceSec = $DenyGraceSec
        Jobs         = @{}
        MainJobId    = $null
        ReadOnlyJobId = $null
    }
}

function Enable-FakeGrokProcess {
    $script:FakeMode = $true
    $script:FakeHandles = New-Object System.Collections.Generic.List[object]
    $script:LaunchLog = New-Object System.Collections.Generic.List[object]
}

function Disable-FakeGrokProcess {
    $script:FakeMode = $false
}

function Get-FakeGrokHandles {
    Write-Output -NoEnumerate $script:FakeHandles.ToArray()
}

function Get-GrokLaunchLog {
    Write-Output -NoEnumerate $script:LaunchLog.ToArray()
}

function New-FakeProcessHandle {
    param([int]$ProcessId = 9000)
    return [pscustomobject]@{
        Pid      = $ProcessId
        Process  = $null
        Exited   = $false
        ExitCode = $null
        KillCount = 0
    }
}

function Test-ProcessHandleExited {
    param($Handle)
    if ($null -eq $Handle) { return $true }
    if ($null -ne $Handle.Process) {
        return [bool]$Handle.Process.HasExited
    }
    return [bool]$Handle.Exited
}

function Get-ProcessHandleExitCode {
    param($Handle)
    if ($null -eq $Handle) { return 1 }
    if ($null -ne $Handle.Process) {
        return [int]$Handle.Process.ExitCode
    }
    if ($null -eq $Handle.ExitCode) { return 1 }
    return [int]$Handle.ExitCode
}

function Stop-ProcessHandle {
    param($Handle)
    if ($null -eq $Handle) { return }
    $Handle.KillCount = [int]$Handle.KillCount + 1
    if ($null -ne $Handle.Process) {
        $proc = $Handle.Process
        if (-not $proc.HasExited) {
            if ($env:OS -eq 'Windows_NT') {
                & taskkill.exe /PID $proc.Id /T /F | Out-Null
            }
            else {
                try { $proc.Kill() } catch { }
            }
        }
        return
    }
    $Handle.Exited = $true
    if ($null -eq $Handle.ExitCode) {
        $Handle.ExitCode = 20
    }
}

function Get-WindowsPowerShellExe {
    if ($env:OS -eq 'Windows_NT') {
        $sys = $env:SystemRoot
        if ([string]::IsNullOrWhiteSpace($sys)) { $sys = 'C:\Windows' }
        return ($sys + '\System32\WindowsPowerShell\v1.0\powershell.exe')
    }
    $cmd = Get-Command pwsh -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    return 'pwsh'
}

function Start-GrokProcess {
    param(
        [Parameter(Mandatory = $true)][string]$GrokExe,
        [Parameter(Mandatory = $true)][string]$PromptFile,
        [Parameter(Mandatory = $true)][string]$Effort,
        [Parameter(Mandatory = $true)][string]$LogPath
    )
    $argLine = Get-GrokArgumentLine -PromptFile $PromptFile -Effort $Effort
    if ($script:FakeMode) {
        $script:LaunchLog.Add([pscustomobject]@{
                Exe          = $GrokExe
                ArgumentLine = $argLine
                LogPath      = $LogPath
                PromptFile   = $PromptFile
                Effort       = $Effort
            })
        $procId = 9000 + $script:FakeHandles.Count
        $handle = New-FakeProcessHandle -ProcessId $procId
        $script:FakeHandles.Add($handle)
        return $handle
    }
    return Start-GrokLoggedProcess -GrokExe $GrokExe -PromptFile $PromptFile -Effort $Effort -LogPath $LogPath
}

function Start-GrokLoggedProcess {
    param(
        [string]$GrokExe,
        [string]$PromptFile,
        [string]$Effort,
        [string]$LogPath
    )
    $shell = Get-WindowsPowerShellExe
    $wrapper = Join-Path (Split-Path -Parent $script:ResidentLib) 'Run-GrokLogged.ps1'
    $arg = @(
        '-NoProfile',
        '-NonInteractive',
        '-ExecutionPolicy', 'Bypass',
        '-File', (Format-ProcessArgument $wrapper),
        '-GrokExe', (Format-ProcessArgument $GrokExe),
        '-PromptFile', (Format-ProcessArgument $PromptFile),
        '-Effort', (Format-ProcessArgument $Effort),
        '-LogPath', (Format-ProcessArgument $LogPath)
    ) -join ' '
    $proc = New-Object System.Diagnostics.Process
    $proc.StartInfo.FileName = $shell
    $proc.StartInfo.Arguments = $arg
    $proc.StartInfo.UseShellExecute = $false
    $proc.StartInfo.CreateNoWindow = $true
    [void]$proc.Start()
    return [pscustomobject]@{
        Pid       = [int]$proc.Id
        Process   = $proc
        Exited    = $false
        ExitCode  = $null
        KillCount = 0
    }
}

function Move-QueueFile {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$DestDir
    )
    if (-not [System.IO.File]::Exists($Source)) { return $null }
    $name = [System.IO.Path]::GetFileName($Source)
    $dest = Join-Path $DestDir $name
    if ([System.IO.File]::Exists($dest)) {
        $stem = [System.IO.Path]::GetFileNameWithoutExtension($name)
        $dest = Join-Path $DestDir ($stem + '-' + (Get-Date -Format 'yyyyMMddHHmmss') + [System.IO.Path]::GetExtension($name))
    }
    [System.IO.Directory]::CreateDirectory($DestDir) | Out-Null
    [System.IO.File]::Move($Source, $dest)
    return $dest
}

function New-StatusRecord {
    param(
        [string]$Id,
        [string]$StateName,
        [string]$Lane,
        [string]$Reasoning,
        [string]$Start,
        $End,
        $ExitCode,
        $ProcessId,
        [string]$OrderFile,
        [string]$ErrorText,
        [string]$ConfirmDecision,
        [string]$ConfirmSince,
        [string]$HostName,
        [string]$UserName
    )
    $err = $null
    if (-not [string]::IsNullOrWhiteSpace($ErrorText)) {
        $err = ConvertTo-RedactedText $ErrorText
    }
    $decision = $null
    if (-not [string]::IsNullOrWhiteSpace($ConfirmDecision)) { $decision = $ConfirmDecision }
    $since = $null
    if (-not [string]::IsNullOrWhiteSpace($ConfirmSince)) { $since = $ConfirmSince }
    return [pscustomobject]@{
        id                = $Id
        state             = $StateName
        lane              = $Lane
        reasoning         = $Reasoning
        model             = (Get-ResidentModelName)
        start             = $Start
        end               = $End
        exit_code         = $ExitCode
        pid               = $ProcessId
        order_file        = $OrderFile
        error             = $err
        confirm_decision  = $decision
        confirm_since     = $since
        host              = $HostName
        user              = $UserName
    }
}

function Publish-TerminalStatus {
    param(
        $State,
        [string]$Id,
        [string]$StateName,
        [string]$Lane,
        [string]$Reasoning,
        [string]$OrderFile,
        $ExitCode,
        [string]$ErrorText,
        [datetime]$Now
    )
    $iso = ConvertTo-IsoUtc $Now
    $record = New-StatusRecord -Id $Id -StateName $StateName -Lane $Lane -Reasoning $Reasoning `
        -Start $iso -End $iso -ExitCode $ExitCode -ProcessId $null -OrderFile $OrderFile `
        -ErrorText $ErrorText -ConfirmDecision '' -ConfirmSince '' -HostName $State.HostName -UserName $State.UserName
    Write-AtomicJson -Path (Get-JobStatusPath $State.Root $Id) -Object $record
}

function Publish-LiveStatus {
    param(
        $State,
        $Job,
        [string]$StateName,
        [datetime]$Now
    )
    $end = $null
    $exitCode = $null
    $confirmSince = ''
    if ($null -ne $Job.ConfirmSince) { $confirmSince = ConvertTo-IsoUtc $Job.ConfirmSince }
    $pidValue = $null
    if ($null -ne $Job.Proc) { $pidValue = [int]$Job.Proc.Pid }
    $record = New-StatusRecord -Id $Job.Id -StateName $StateName -Lane $Job.Lane -Reasoning $Job.Reasoning `
        -Start (ConvertTo-IsoUtc $Job.StartedAt) -End $end -ExitCode $exitCode -ProcessId $pidValue `
        -OrderFile $Job.FileName -ErrorText '' -ConfirmDecision $Job.ConfirmDecision -ConfirmSince $confirmSince `
        -HostName $State.HostName -UserName $State.UserName
    Write-AtomicJson -Path (Get-JobStatusPath $State.Root $Job.Id) -Object $record
    $Job.PublishedSnapshot = ($StateName + '|' + [string]$Job.ConfirmDecision + '|' + $confirmSince)
}

function Clear-JobSlot {
    param($State, $Job)
    if ($State.MainJobId -eq $Job.Id) { $State.MainJobId = $null }
    if ($State.ReadOnlyJobId -eq $Job.Id) { $State.ReadOnlyJobId = $null }
    if ($State.Jobs.ContainsKey($Job.Id)) {
        [void]$State.Jobs.Remove($Job.Id)
    }
}

function Complete-ResidentJob {
    param(
        $State,
        $Job,
        [string]$StateName,
        $ExitCode,
        [string]$ErrorText,
        [datetime]$Now
    )
    $paths = Get-ResidentPaths $State.Root
    $destDir = $paths.Failed
    if ($StateName -eq 'done' -or $StateName -eq 'denied') {
        $destDir = $paths.Done
    }
    if (-not (Test-ProcessHandleExited $Job.Proc)) {
        Stop-ProcessHandle $Job.Proc
    }
    [void](Move-QueueFile -Source $Job.RunningPath -DestDir $destDir)
    if (-not [string]::IsNullOrWhiteSpace($Job.PromptPath)) {
        [void](Move-QueueFile -Source $Job.PromptPath -DestDir $destDir)
    }
    $confirmSince = ''
    if ($null -ne $Job.ConfirmSince) { $confirmSince = ConvertTo-IsoUtc $Job.ConfirmSince }
    $pidValue = $null
    if ($null -ne $Job.Proc) { $pidValue = [int]$Job.Proc.Pid }
    $record = New-StatusRecord -Id $Job.Id -StateName $StateName -Lane $Job.Lane -Reasoning $Job.Reasoning `
        -Start (ConvertTo-IsoUtc $Job.StartedAt) -End (ConvertTo-IsoUtc $Now) -ExitCode $ExitCode -ProcessId $pidValue `
        -OrderFile $Job.FileName -ErrorText $ErrorText -ConfirmDecision $Job.ConfirmDecision -ConfirmSince $confirmSince `
        -HostName $State.HostName -UserName $State.UserName
    Write-AtomicJson -Path (Get-JobStatusPath $State.Root $Job.Id) -Object $record
    Write-ResidentLog -Root $State.Root -Message ("finish " + $Job.Id + " state=" + $StateName + " exit=" + $ExitCode)
    Clear-JobSlot -State $State -Job $Job
}

function Get-ConfirmSignal {
    param(
        [string]$ConfirmDir,
        [string]$JobId
    )
    return [pscustomobject]@{
        Json = [System.IO.File]::Exists((Join-Path $ConfirmDir ($JobId + '.json')))
        Ok   = [System.IO.File]::Exists((Join-Path $ConfirmDir ($JobId + '.ok')))
        Ng   = [System.IO.File]::Exists((Join-Path $ConfirmDir ($JobId + '.ng')))
    }
}

function Test-JobIdTaken {
    param($State, [string]$Id)
    if ($State.Jobs.ContainsKey($Id)) { return $true }
    return [System.IO.File]::Exists((Get-JobStatusPath $State.Root $Id))
}

function Reject-InboxFile {
    param(
        $State,
        $File,
        $Doc,
        [datetime]$Now,
        [string]$Reason,
        [switch]$MakeUniqueId
    )
    $paths = Get-ResidentPaths $State.Root
    $id = $null
    if ($null -ne $Doc -and -not [string]::IsNullOrWhiteSpace($Doc.Id)) {
        $id = $Doc.Id
    }
    else {
        $id = ConvertTo-SafeJobId ([System.IO.Path]::GetFileNameWithoutExtension($File.Name))
    }
    if ($MakeUniqueId -or (Test-JobIdTaken -State $State -Id $id)) {
        $id = ConvertTo-SafeJobId ($id + '-dup-' + [guid]::NewGuid().ToString('N').Substring(0, 8))
    }
    $lane = 'main'
    $reasoning = 'xhigh'
    if ($null -ne $Doc -and -not [string]::IsNullOrWhiteSpace($Doc.Lane)) { $lane = $Doc.Lane }
    if ($null -ne $Doc -and -not [string]::IsNullOrWhiteSpace($Doc.Reasoning)) { $reasoning = $Doc.Reasoning }
    [void](Move-QueueFile -Source $File.FullName -DestDir $paths.Failed)
    Publish-TerminalStatus -State $State -Id $id -StateName 'rejected' -Lane $lane -Reasoning $reasoning `
        -OrderFile $File.Name -ExitCode 10 -ErrorText $Reason -Now $Now
    Write-ResidentLog -Root $State.Root -Message ("reject " + $id + " " + $Reason)
    return $id
}

function Start-ResidentJob {
    param($State, $Pick, [datetime]$Now)
    $paths = Get-ResidentPaths $State.Root
    $doc = $Pick.Doc
    $runningPath = Join-Path $paths.Running $Pick.Name
    [System.IO.File]::Move($Pick.FullName, $runningPath)
    $promptPath = Join-Path $paths.Running ($doc.Id + '.prompt.md')
    $preamble = New-SafetyPreamble -JobId $doc.Id -ConfirmDir $paths.Confirm -TimeoutSec $doc.TimeoutSec -Effort $doc.Reasoning
    $prompt = $preamble + "`n`n----- ORDER -----`n`n" + $doc.Normalized
    Write-Utf8File -Path $promptPath -Text $prompt
    $logPath = Join-Path $paths.Logs ($doc.Id + '.log')
    try {
        if (-not $script:FakeMode -and -not [System.IO.File]::Exists($State.GrokExe)) {
            throw 'grok.exe not found'
        }
        $handle = Start-GrokProcess -GrokExe $State.GrokExe -PromptFile $promptPath -Effort $doc.Reasoning -LogPath $logPath
        if ($null -eq $handle) { throw 'grok process did not start' }
    }
    catch {
        $failJob = [pscustomobject]@{
            Id               = $doc.Id
            Lane             = $doc.Lane
            FileName         = $Pick.Name
            RunningPath      = $runningPath
            PromptPath       = $promptPath
            Proc             = $null
            StartedAt        = $Now
            ConfirmSince     = $null
            ConfirmDecision  = $null
            Reasoning        = $doc.Reasoning
        }
        Complete-ResidentJob -State $State -Job $failJob -StateName 'failed' -ExitCode 12 -ErrorText $_.Exception.Message -Now $Now
        return
    }
    $job = [pscustomobject]@{
        Id                = $doc.Id
        Lane              = $doc.Lane
        FileName          = $Pick.Name
        RunningPath       = $runningPath
        PromptPath        = $promptPath
        LogPath           = $logPath
        Proc              = $handle
        StartedAt         = $Now
        ConfirmSince      = $null
        ConfirmDecision   = $null
        DenySince         = $null
        TimeoutSec        = [int]$doc.TimeoutSec
        Reasoning         = $doc.Reasoning
        PublishedSnapshot = ''
    }
    $State.Jobs[$doc.Id] = $job
    if ($doc.Lane -eq 'readonly') {
        $State.ReadOnlyJobId = $doc.Id
    }
    else {
        $State.MainJobId = $doc.Id
    }
    Publish-LiveStatus -State $State -Job $job -StateName 'running' -Now $Now
    Write-ResidentLog -Root $State.Root -Message ("start " + $doc.Id + " lane=" + $doc.Lane + " pid=" + $handle.Pid)
}

function Update-RunningJob {
    param($State, $Job, [datetime]$Now)
    $paths = Get-ResidentPaths $State.Root
    $signal = Get-ConfirmSignal -ConfirmDir $paths.Confirm -JobId $Job.Id
    $decision = $null
    if ($signal.Ng) {
        $decision = 'ng'
    }
    elseif ($signal.Ok -and $signal.Json) {
        $decision = 'ok'
    }
    if ($null -ne $decision -and $Job.ConfirmDecision -ne $decision) {
        $Job.ConfirmDecision = $decision
        if ($decision -eq 'ng' -and $null -eq $Job.DenySince) {
            $Job.DenySince = $Now
        }
    }
    elseif ($null -eq $decision -and $signal.Json -and $null -eq $Job.ConfirmSince) {
        $Job.ConfirmSince = $Now
    }

    if (-not (Test-ProcessHandleExited $Job.Proc) -and $null -eq $Job.ConfirmDecision -and $null -ne $Job.ConfirmSince) {
        $elapsed = ($Now - $Job.ConfirmSince).TotalSeconds
        if ($elapsed -ge [double]$Job.TimeoutSec) {
            Stop-ProcessHandle $Job.Proc
            Complete-ResidentJob -State $State -Job $Job -StateName 'aborted' -ExitCode 20 -ErrorText 'confirm timeout' -Now $Now
            return
        }
    }
    if (-not (Test-ProcessHandleExited $Job.Proc) -and $Job.ConfirmDecision -eq 'ng' -and $null -ne $Job.DenySince) {
        $denyElapsed = ($Now - $Job.DenySince).TotalSeconds
        if ($denyElapsed -ge [double]$State.DenyGraceSec) {
            Stop-ProcessHandle $Job.Proc
            Complete-ResidentJob -State $State -Job $Job -StateName 'denied' -ExitCode 21 -ErrorText 'denied and process stopped after grace' -Now $Now
            return
        }
    }
    if (Test-ProcessHandleExited $Job.Proc) {
        $code = Get-ProcessHandleExitCode $Job.Proc
        if ($Job.ConfirmDecision -eq 'ng' -and $code -eq 0) {
            Complete-ResidentJob -State $State -Job $Job -StateName 'denied' -ExitCode 0 -ErrorText '' -Now $Now
        }
        elseif ($code -eq 0) {
            Complete-ResidentJob -State $State -Job $Job -StateName 'done' -ExitCode 0 -ErrorText '' -Now $Now
        }
        else {
            Complete-ResidentJob -State $State -Job $Job -StateName 'failed' -ExitCode $code -ErrorText ("exit code " + $code) -Now $Now
        }
        return
    }

    $stateName = 'running'
    if ($null -eq $Job.ConfirmDecision -and $null -ne $Job.ConfirmSince) {
        $stateName = 'awaiting_confirm'
    }
    $confirmSince = ''
    if ($null -ne $Job.ConfirmSince) { $confirmSince = ConvertTo-IsoUtc $Job.ConfirmSince }
    $snapshot = ($stateName + '|' + [string]$Job.ConfirmDecision + '|' + $confirmSince)
    if ($snapshot -ne $Job.PublishedSnapshot) {
        Publish-LiveStatus -State $State -Job $Job -StateName $stateName -Now $Now
    }
}

function Invoke-ResidentTick {
    param(
        [Parameter(Mandatory = $true)]$State,
        [Parameter(Mandatory = $true)][datetime]$Now
    )
    $paths = Initialize-ResidentTree $State.Root
    $ids = New-Object System.Collections.Generic.List[object]
    foreach ($key in $State.Jobs.Keys) { $ids.Add($key) }
    foreach ($id in $ids) {
        if (-not $State.Jobs.ContainsKey($id)) { continue }
        Update-RunningJob -State $State -Job $State.Jobs[$id] -Now $Now
    }

    $files = @(Get-ChildItem -LiteralPath $paths.Inbox -Filter *.md -File | Sort-Object Name)
    $seen = @{}
    $candidates = New-Object System.Collections.Generic.List[object]
    foreach ($file in $files) {
        $text = ''
        $doc = $null
        try {
            $text = Read-TextFile $file.FullName
            $doc = Test-OrderText $text
        }
        catch {
            [void](Reject-InboxFile -State $State -File $file -Doc $null -Now $Now -Reason $_.Exception.Message)
            continue
        }
        if (-not $doc.Ok) {
            $reason = ($doc.Errors -join '; ')
            [void](Reject-InboxFile -State $State -File $file -Doc $doc -Now $Now -Reason $reason)
            continue
        }
        if ($seen.ContainsKey($doc.Id) -or (Test-JobIdTaken -State $State -Id $doc.Id)) {
            [void](Reject-InboxFile -State $State -File $file -Doc $doc -Now $Now -Reason 'duplicate job id' -MakeUniqueId)
            continue
        }
        $seen[$doc.Id] = $true
        $candidates.Add([pscustomobject]@{
                Name     = $file.Name
                FullName = $file.FullName
                Lane     = $doc.Lane
                Seq      = $doc.Seq
                Doc      = $doc
            })
    }

    $mainBusy = $null -ne $State.MainJobId
    $readBusy = $null -ne $State.ReadOnlyJobId
    $picks = Select-NextOrders -Candidates $candidates.ToArray() -MainBusy $mainBusy -ReadOnlyBusy $readBusy
    foreach ($pick in $picks) {
        if ($null -eq $pick) { continue }
        Start-ResidentJob -State $State -Pick $pick -Now $Now
    }
}

function Repair-OrphanedRunningOrders {
    param(
        [Parameter(Mandatory = $true)]$State,
        [Parameter(Mandatory = $true)][datetime]$Now
    )
    $paths = Initialize-ResidentTree $State.Root
    $files = @(Get-ChildItem -LiteralPath $paths.Running -File)
    foreach ($file in $files) {
        $isPrompt = $file.Name.EndsWith('.prompt.md')
        if ($isPrompt) {
            [void](Move-QueueFile -Source $file.FullName -DestDir $paths.Failed)
            continue
        }
        if ($file.Extension -ne '.md') { continue }
        $doc = $null
        try {
            $doc = Test-OrderText (Read-TextFile $file.FullName)
        }
        catch {
            $doc = $null
        }
        $id = ConvertTo-SafeJobId ([System.IO.Path]::GetFileNameWithoutExtension($file.Name))
        if ($null -ne $doc -and -not [string]::IsNullOrWhiteSpace($doc.Id)) { $id = $doc.Id }
        if ($State.Jobs.ContainsKey($id)) { continue }
        $lane = 'main'
        $reasoning = 'xhigh'
        if ($null -ne $doc -and $doc.Ok) {
            $lane = $doc.Lane
            $reasoning = $doc.Reasoning
        }
        [void](Move-QueueFile -Source $file.FullName -DestDir $paths.Failed)
        if (-not (Test-JobIdTaken -State $State -Id $id)) {
            Publish-TerminalStatus -State $State -Id $id -StateName 'aborted' -Lane $lane -Reasoning $reasoning `
                -OrderFile $file.Name -ExitCode 40 -ErrorText 'resident restarted while this job was running; it was not resumed' -Now $Now
        }
        Write-ResidentLog -Root $State.Root -Message ("orphan " + $id + " not resumed")
    }
}

function Stop-ResidentJobs {
    param(
        [Parameter(Mandatory = $true)]$State,
        [Parameter(Mandatory = $true)][datetime]$Now,
        [string]$Reason = 'stop requested'
    )
    $ids = New-Object System.Collections.Generic.List[object]
    foreach ($key in $State.Jobs.Keys) { $ids.Add($key) }
    foreach ($id in $ids) {
        if (-not $State.Jobs.ContainsKey($id)) { continue }
        $job = $State.Jobs[$id]
        if (-not (Test-ProcessHandleExited $job.Proc)) {
            Stop-ProcessHandle $job.Proc
        }
        Complete-ResidentJob -State $State -Job $job -StateName 'aborted' -ExitCode 30 -ErrorText $Reason -Now $Now
    }
}

function Write-ResidentHeartbeat {
    param(
        [Parameter(Mandatory = $true)]$State,
        [Parameter(Mandatory = $true)][datetime]$Now,
        [int]$IntervalSec = 10
    )
    $paths = Get-ResidentPaths $State.Root
    $record = [pscustomobject]@{
        host         = $State.HostName
        user         = $State.UserName
        pid          = $PID
        updated      = (ConvertTo-IsoUtc $Now)
        interval_sec = $IntervalSec
        slots        = [pscustomobject]@{
            main     = $State.MainJobId
            readonly = $State.ReadOnlyJobId
        }
    }
    Write-AtomicJson -Path $paths.Heartbeat -Object $record
}
