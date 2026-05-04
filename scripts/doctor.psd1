@{
    RootModule        = 'doctor.psm1'
    ModuleVersion     = '1.0.0'
    GUID              = 'e3c2b1d0-9f4a-4b8e-8c3a-2d7a9b1c5678'
    Author            = 'Tuyen Mathew Duong'
    CompanyName       = 'textfsmgen'
    Description       = 'Environment diagnostics module for developer tooling.'

    FunctionsToExport = @(
        'Test-DevEnvironment'
    )

    CmdletsToExport   = @()
    VariablesToExport = @()
    AliasesToExport   = @()

    PrivateData = @{
        PSData = @{
            Tags = @('diagnostics', 'developer-tools', 'environment-check')
        }
    }
}
