# Runs in: Windows PowerShell
# Purpose: show which required command-line tools Windows can find.
$ErrorActionPreference = "Continue"

$checks = @(
    @{ Name = "Git"; Command = "git --version" },
    @{ Name = "Python launcher"; Command = "py --version" },
    @{ Name = "Python"; Command = "python --version" },
    @{ Name = "VS Code"; Command = "code --version" },
    @{ Name = "PostgreSQL psql"; Command = "psql --version" }
)

foreach ($check in $checks) {
    Write-Host "`n=== $($check.Name) ==="
    try {
        Invoke-Expression $check.Command
    }
    catch {
        Write-Warning "$($check.Name) was not found on PATH. Read Phase 2 before changing PATH manually."
    }
}

Write-Host "`nSQL Server, SSMS, pgAdmin, Power BI Desktop, and Databricks are verified through their user interfaces."
