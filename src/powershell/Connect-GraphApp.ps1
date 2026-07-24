<#
.SYNOPSIS
    Connects to Microsoft Graph using app-only (client credentials) auth,
    and sets up an audit log helper used by the other scripts.

.DESCRIPTION
    Reads tenantId / clientId / clientSecret from config/config.json.
    Requires: Install-Module Microsoft.Graph -Scope CurrentUser
#>

function Connect-GraphApp {
    $configPath = Join-Path $PSScriptRoot "..\..\config\config.json"
    if (-not (Test-Path $configPath)) {
        throw "Missing $configPath. Copy config.example.json to config.json and fill it in."
    }

    $config = Get-Content $configPath | ConvertFrom-Json

    $secureSecret = ConvertTo-SecureString $config.clientSecret -AsPlainText -Force
    $credential = New-Object System.Management.Automation.PSCredential($config.clientId, $secureSecret)

    Connect-MgGraph -TenantId $config.tenantId -ClientSecretCredential $credential -NoWelcome

    return $config
}

function Write-AuditLog {
    param(
        [Parameter(Mandatory)] [string]$Action,
        [Parameter(Mandatory)] [string]$Target,
        [Parameter(Mandatory)] [string]$Outcome,
        [string]$LogPath = (Join-Path $PSScriptRoot "..\..\logs\audit.log")
    )

    $logDir = Split-Path $LogPath -Parent
    if (-not (Test-Path $logDir)) {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    }

    $entry = "{0} | {1} | target={2} | outcome={3}" -f (Get-Date -Format "o"), $Action, $Target, $Outcome
    Add-Content -Path $LogPath -Value $entry
    Write-Host $entry
}
