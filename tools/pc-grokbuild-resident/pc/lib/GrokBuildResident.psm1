# Grok Build resident queue. Dot-sourced parts stay Windows PowerShell 5.1 compatible.
Set-StrictMode -Version 2.0

$script:ResidentLib = $PSScriptRoot
$script:FakeMode = $false
$script:FakeHandles = New-Object System.Collections.Generic.List[object]
$script:LaunchLog = New-Object System.Collections.Generic.List[object]

. (Join-Path $PSScriptRoot 'Order.ps1')
. (Join-Path $PSScriptRoot 'Safety.ps1')
. (Join-Path $PSScriptRoot 'Queue.ps1')

Export-ModuleMember -Function @(
    'Read-TextFile',
    'Write-Utf8File',
    'Split-OrderText',
    'Get-OrderBodySha256',
    'ConvertFrom-OrderFrontMatter',
    'Resolve-ReasoningEffort',
    'ConvertTo-SafeJobId',
    'Test-OrderText',
    'Add-OrderSha256Text',
    'Select-NextOrders',
    'ConvertTo-RedactedText',
    'Format-ProcessArgument',
    'Get-ResidentModelName',
    'Get-GrokArgumentLine',
    'New-SafetyPreamble',
    'Get-ResidentTaskName',
    'Get-ResidentPaths',
    'Initialize-ResidentTree',
    'ConvertTo-IsoUtc',
    'Write-AtomicJson',
    'Read-JsonFile',
    'Write-ResidentLog',
    'Get-JobStatusPath',
    'New-ResidentState',
    'Enable-FakeGrokProcess',
    'Disable-FakeGrokProcess',
    'Get-FakeGrokHandles',
    'Get-GrokLaunchLog',
    'New-FakeProcessHandle',
    'Invoke-ResidentTick',
    'Repair-OrphanedRunningOrders',
    'Stop-ResidentJobs',
    'Write-ResidentHeartbeat'
)
