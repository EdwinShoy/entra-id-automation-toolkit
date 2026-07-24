<#
.SYNOPSIS
    Creates a new Entra ID user and assigns them to groups mapped to their department.

.EXAMPLE
    ./Onboard-User.ps1 -UserPrincipalName jdoe@contoso.onmicrosoft.com -DisplayName "Jane Doe" -Department Engineering
#>

param(
    [Parameter(Mandatory)] [string]$UserPrincipalName,
    [Parameter(Mandatory)] [string]$DisplayName,
    [Parameter(Mandatory)] [string]$Department
)

. "$PSScriptRoot\Connect-GraphApp.ps1"

$config = Connect-GraphApp

$tempPassword = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 16 | ForEach-Object { [char]$_ })

$passwordProfile = @{
    ForceChangePasswordNextSignIn = $true
    Password                      = $tempPassword
}

try {
    $user = New-MgUser -DisplayName $DisplayName `
        -UserPrincipalName $UserPrincipalName `
        -MailNickname ($UserPrincipalName.Split('@')[0]) `
        -AccountEnabled `
        -PasswordProfile $passwordProfile

    Write-AuditLog -Action "CreateUser" -Target $UserPrincipalName -Outcome "SUCCESS"
}
catch {
    Write-AuditLog -Action "CreateUser" -Target $UserPrincipalName -Outcome "FAILED: $_"
    throw
}

$groupIds = $config.defaultGroups.$Department
if (-not $groupIds) {
    Write-Host "No groups mapped for department '$Department' — skipping group assignment"
    return
}

foreach ($groupId in $groupIds) {
    try {
        New-MgGroupMember -GroupId $groupId -DirectoryObjectId $user.Id
        Write-AuditLog -Action "AssignGroup" -Target "$UserPrincipalName -> $groupId" -Outcome "SUCCESS"
    }
    catch {
        Write-AuditLog -Action "AssignGroup" -Target "$UserPrincipalName -> $groupId" -Outcome "FAILED: $_"
    }
}
