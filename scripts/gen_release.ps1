# Zip Files using PowerShell
Push-Location (Join-Path $PWD "..")
Compress-Archive -Path "assets", "layout", "user_data", "LICENSE", "TSH.exe" -DestinationPath "release.zip"
Pop-Location