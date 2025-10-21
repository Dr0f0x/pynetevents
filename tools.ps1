<#
.SYNOPSIS
    Utility script to run various tools.
.DESCRIPTION
    This script provides functions to:
    - Run addlicense to add license headers to source files.
#>
param (
    [ValidateSet("license")]
    [string]$Action
)

#-----------------------------
# Function: Run addlicense
#-----------------------------
function Run-AddLicense {
    [CmdletBinding()]
    param (
        [string]$RunDir = "./src/pynetevents",
        [string]$Ignore = "**/*.txt",
        [string]$Name = "Dominik Czekai",
        [string]$Year = "2025",
        [string]$licenseFile = "./LICENSE"
    )

    Write-Host "Running addlicense..."
    & addlicense  -c $Name -v -y $Year -ignore $Ignore -f $licenseFile $RunDir
}

#-----------------------------
# Main logic
#-----------------------------

switch ($Action) {
    "license" { Run-AddLicense }
    default { Write-Host "Please specify -Action heady, -Action license or -Action gcovr" }
}