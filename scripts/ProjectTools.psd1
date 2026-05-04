@{
    RootModule        = 'ProjectTools.psm1'
    ModuleVersion     = '1.0.0'
    GUID              = 'c2b7d3e0-4f8e-4d3c-9c2a-1e7a8b9c1234'
    Author            = 'Tuyen Duong'
    CompanyName       = 'textfsmgen'
    Copyright         = '(c) 2026'
    Description       = 'Developer tooling for cleaning, testing, formatting, and releasing the textfsmgen project.'

    FunctionsToExport = @(
        'Clean-Project',
        'DeepClean-Project'
    )

    CmdletsToExport   = @()
    VariablesToExport = @()
    AliasesToExport   = @()

    PrivateData = @{
        PSData = @{
            Tags = @('textfsmgen', 'developer-tools', 'cleanup', 'automation')
        }
    }
}
