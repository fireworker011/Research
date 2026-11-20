# install-task.ps1 — タスクスケジューラに「GrokBuild夜間実行」を登録する
# 対象: Windows PowerShell 5.1。管理者の PowerShell で1回実行する。
# 毎日 20:00（PCのローカル時刻。東京であること）と、ログオン時。
# スリープからの起動は許可する。Windowsのシャットダウンは登録しない。
[CmdletBinding()]
param(
    [string]$Root = 'C:\Users\hp\Documents\grokbuild',
    [string]$User = '',
    [string]$Grok = ''
)

function Get-DefaultNightUser {
    param([string]$AccountName = 'hp')
    $domain = $env:USERDOMAIN
    if (-not $domain) {
        $domain = $env:COMPUTERNAME
    }
    if (-not $domain) {
        $domain = '.'
    }
    return ($domain + '\' + $AccountName)
}

function Join-NightPath {
    param(
        [Parameter(Mandatory = $true)][string]$Parent,
        [Parameter(Mandatory = $true)][string]$Child
    )
    # Linux の pwsh は "C:" をドライブ名とみなして Join-Path に失敗する。
    # タスク引数は Windows パスの文字列なので、ドライブレターはそのまま繋ぐ。
    if ($Parent -match '^[A-Za-z]:\\' -or $Parent.Contains('\')) {
        return ($Parent.TrimEnd('\') + '\' + $Child.TrimStart('\'))
    }
    return (Join-Path -Path $Parent -ChildPath $Child)
}

function Get-NightRunnerArgument {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [string]$Grok
    )
    $runner = Join-NightPath -Parent $Root -Child 'night-runner.ps1'
    $argument = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$runner`""
    if ($Grok) {
        $quoted = $Grok.Replace('"', '`"')
        $argument = $argument + " -Grok `"$quoted`""
    }
    return $argument
}

function Test-TokyoTimeZone {
    $id = [string][TimeZoneInfo]::Local.Id
    try {
        $got = Get-TimeZone
        if ($got -and $got.Id) {
            $id = [string]$got.Id
        }
    }
    catch {
        Write-Host "Get-TimeZone は使えなかった。Local.Id=$id"
    }
    return (@('Tokyo Standard Time', 'Asia/Tokyo') -contains $id)
}

function Register-GrokBuildNightTask {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [string]$User,
        [string]$Grok
    )
    if (-not (Test-TokyoTimeZone)) {
        $id = [string][TimeZoneInfo]::Local.Id
        Write-Error "タイムゾーンが $id です。PCの時刻を東京（JST / Tokyo Standard Time）にしてから登録してください。Windowsはシャットダウンしません。"
        return 1
    }
    $runner = Join-NightPath -Parent $Root -Child 'night-runner.ps1'
    if (-not (Test-Path -LiteralPath $runner)) {
        Write-Error "night-runner.ps1 がありません: $runner"
        return 1
    }
    if (-not $User) {
        $User = Get-DefaultNightUser
    }
    $argument = Get-NightRunnerArgument -Root $Root -Grok $Grok
    $powershellExe = 'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe'
    if ($env:SystemRoot) {
        $powershellExe = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
    }
    $action = New-ScheduledTaskAction -Execute $powershellExe -Argument $argument -WorkingDirectory $Root
    $daily = New-ScheduledTaskTrigger -Daily -At '20:00'
    $logon = New-ScheduledTaskTrigger -AtLogOn -User $User
    $settingArgs = @{
        WakeToRun                  = $true
        StartWhenAvailable         = $true
        AllowStartIfOnBatteries    = $true
        DontStopIfGoingOnBatteries = $true
        DontStopOnIdleEnd          = $true
        RunOnlyIfIdle              = $false
        MultipleInstances          = 'IgnoreNew'
        ExecutionTimeLimit         = (New-TimeSpan -Hours 8 -Minutes 30)
    }
    $settings = New-ScheduledTaskSettingsSet @settingArgs
    $principal = New-ScheduledTaskPrincipal -UserId $User -LogonType Interactive -RunLevel Limited
    Register-ScheduledTask -TaskName 'GrokBuild夜間実行' -Action $action -Trigger @($daily, $logon) -Settings $settings -Principal $principal -Force | Out-Null
    Write-Host '登録しました。確認: Get-ScheduledTask -TaskName GrokBuild夜間実行'
    Write-Host 'スリープ解除を効かせるには、電源オプションの「スリープ解除タイマーの許可」を有効にしてください。このタスクはPCの電源を切りません。実行時間の上限は8時間30分（20:00起点で04:30）で、切るのはタスクのプロセスだけです。'
    return 0
}

if ($MyInvocation.InvocationName -ne '.') {
    if (-not $User) {
        $User = Get-DefaultNightUser
    }
    $exitCode = Register-GrokBuildNightTask -Root $Root -User $User -Grok $Grok
    exit $exitCode
}
