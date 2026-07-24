<#
.SYNOPSIS
    Disables an Entra ID user, revokes their sign-in sessions, and removes
    them from all group memberships.

.EXAMPLE
    ./Offboard-User.ps1 -UserPrincipalName jdoe@contoso.onmicrosoft.com
#>

param(
    [Parameter(Mandatory)] [string]$UserPrincipalName
)

. "$PSScriptRoot\Connect-GraphApp.ps1"

Connect-GraphApp | Out-Null

try {
    Update-MgUser -UserId $UserPrincipalName -AccountEnabled:$false
    Write-AuditLog -Action "DisableAccount" -Target $UserPrincipalName -Outcome "SUCCESS"
}
catch {
    Write-AuditLog -Action "DisableAccount" -Target $UserPrincipalName -Outcome "FAILED: $_"
    throw
}

try {
    Revoke-MgUserSignInSession -UserId $UserPrincipalName
    Write-AuditLog -Action "RevokeSessions" -Target $UserPrincipalName -Outcome "SUCCESS"
}
catch {
    Write-AuditLog -Action "RevokeSessions" -Target $UserPrincipalName -Outcome "FAILED: $_"
}

$memberships = Get-MgUserMemberOf -UserId $UserPrincipalName

foreach ($group in $memberships) {
    try {
        Remove-MgGroupMemberByRef -GroupId $group.Id -DirectoryObjectId $UserPrincipalName
        Write-AuditLog -Action "RemoveGroup" -Target "$UserPrincipalName -> $($group.Id)" -Outcome "SUCCESS"
    }
    catch {
        Write-AuditLog -Action "RemoveGroup" -Target "$UserPrincipalName -> $($group.Id)" -Outcome "FAILED: $_"
    }
}
