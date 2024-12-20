Push-Location ..

New-Item -Path "TournamentStreamHelper" -ItemType Directory

Copy-Item -Recurse -Force "assets" "TournamentStreamHelper\assets"

# Already embedded inside release exe
Remove-Item -Path "TournamentStreamHelper\assets\versions.json" -Force
Remove-Item -Path "TournamentStreamHelper\assets\contributors.txt" -Force

# Copy layout excluding game_images and symlinks
Get-ChildItem -Path "layout" -Recurse | Where-Object {
    $_.FullName -notmatch "layout\\game_images" -and -not $_.Attributes.HasFlag([System.IO.FileAttributes]::ReparsePoint)
} | ForEach-Object {
    $destination = $_.FullName.Replace("layout", "TournamentStreamHelper\layout")
    if ($_.PSIsContainer) {
        New-Item -ItemType Directory -Path $destination -Force
    } else {
        Copy-Item -Path $_.FullName -Destination $destination -Force
    }
}

Copy-Item -Recurse -Force "user_data" "TournamentStreamHelper\user_data"
Copy-Item -Force "LICENSE" "TournamentStreamHelper\LICENSE"
Copy-Item -Force "TSH.exe" "TournamentStreamHelper\TSH.exe"

Compress-Archive -Path "TournamentStreamHelper" -DestinationPath "release.zip" -Update

Remove-Item -Recurse -Force "TournamentStreamHelper"

Pop-Location
