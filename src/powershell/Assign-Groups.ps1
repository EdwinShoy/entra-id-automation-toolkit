<#
.SYNOPSIS
    Syncs a user's group membership to match the target role profile for
    their department, as defined in config.json -> defaultGroups.

.EXAMPLE
    ./Assign-Groups.ps1 -UserPrincipalName jdoe@contoso.onmicrosoft.com -Department Sales
#>

param(
    [Parameter(Mandatory)] [string]$UserPrincipalName,
    [Parameter(Mandatory)] [string]$Department
)

. "$PSScriptRoot\Connect-GraphApp.ps1"

$config = Connect-GraphApp

$user = Get-MgUser -UserId $UserPrincipalName
$targetGroupIds = @($config.defaultGroups.$Department)

if (-not $targetGroupIds) {
    Write-Host "No target groups configured for department '$Department'"
    return
}

$currentGroupIds = (Get-MgUserMemberOf -UserId $UserPrincipalName) | ForEach-Object { $_.Id }

$toAdd = $targetGroupIds | Where-Object { $_ -notin $currentGroupIds }
$toRemove = $currentGroupIds | Where-Object { $_ -notin $targetGroupIds }

foreach ($groupId in $toAdd) {
    try {
        New-MgGroupMember -GroupId $groupId -DirectoryObjectId $user.Id
        Write-AuditLog -Action "AssignGroup" -Target "$UserPrincipalName -> $groupId" -Outcome "SUCCESS"
    }
    catch {
        Write-AuditLog -Action "AssignGroup" -Target "$UserPrincipalName -> $groupId" -Outcome "FAILED: $_"
    }
}

foreach ($groupId in $toRemove) {
    try {
        Remove-MgGroupMemberByRef -GroupId $groupId -DirectoryObjectId $UserPrincipalName
        Write-AuditLog -Action "RemoveGroup" -Target "$UserPrincipalName -> $groupId" -Outcome "SUCCESS"
    }
    catch {
        Write-AuditLog -Action "RemoveGroup" -Target "$UserPrincipalName -> $groupId" -Outcome "FAILED: $_"
    }
}
