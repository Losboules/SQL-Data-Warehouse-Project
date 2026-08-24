$ErrorActionPreference = "Continue"

$checks = @(
    @{
        Name = "Git"
        Command = "git"
        Arguments = @("--version")
    },
    @{
        Name = "Python launcher"
        Command = "py"
        Arguments = @("--version")
    },
    @{
        Name = "Python"
        Command = "python"
        Arguments = @("--version")
    },
    @{
        Name = "VS Code"
        Command = "code"
        Arguments = @("--version")
    },
    @{
        Name = "PostgreSQL psql"
        Command = "psql"
        Arguments = @("--version")
    }
)

foreach ($check in $checks) {
    Write-Host "`n=== $($check.Name) ==="

    $installedCommand = Get-Command $check.Command -ErrorAction SilentlyContinue

    if ($null -eq $installedCommand) {
        Write-Warning "$($check.Name) was not found on PATH."
    }
    else {
        & $check.Command @($check.Arguments)
    }
}

Write-Host "`nThe following applications must also be checked through their interfaces:"
Write-Host "- SQL Server"
Write-Host "- SQL Server Management Studio"
Write-Host "- pgAdmin"
Write-Host "- Power BI Desktop"
Write-Host "- Databricks"
