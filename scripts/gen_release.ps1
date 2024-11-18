# Zip Files using PowerShell
Push-Location (Join-Path $PWD "..")

$excludeFiles = @(
    "assets\versions.json",
    "assets\contributors.txt"
)

$sourcePaths = @(
    "assets",
    "layout",
    "user_data",
    "LICENSE",
    "TSH.exe"
)

# Create a temporary list of files to include, excluding specific files
$filesToInclude = Get-ChildItem -Path $sourcePaths -Recurse | Where-Object {
    $excludeFiles -notcontains $_.FullName
}

# Compress the filtered files into a zip archive
$zipPath = "release.zip"
Compress-Archive -Path $filesToInclude -DestinationPath $zipPath

Pop-Location