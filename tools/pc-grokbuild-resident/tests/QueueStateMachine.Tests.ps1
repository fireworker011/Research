#requires -Version 5.1
BeforeAll {
    . (Join-Path $PSScriptRoot 'Cases.ps1')
}

Describe 'queue state machine' {
    It 'passes the resident self-test cases' {
        $failed = Invoke-ResidentCases
        $failed | Should -Be 0
    }
}
