@{
    ExcludeRules = @(
        'PSAvoidUsingWriteHost'
        'PSUseShouldProcessForStateChangingFunctions'
    )
    Rules        = @{
        PSUseCompatibleSyntax  = @{
            Enable         = $true
            TargetVersions = @('5.1')
        }
        PSUseCompatibleCmdlets = @{
            Enable         = $true
            TargetVersions = @('5.1')
        }
    }
}
