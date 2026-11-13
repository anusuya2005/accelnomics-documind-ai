# Makes a clean zip for reviewers: your code and demo documents, but NO data, passwords, .venv or node_modules.
# Run from the project folder:   powershell -ExecutionPolicy Bypass -File .\make_package.ps1
Set-Location $PSScriptRoot
$out = Join-Path ([Environment]::GetFolderPath("Desktop")) "PrivateDocsAI.zip"
$tmp = Join-Path $env:TEMP "PrivateDocsAI_pkg"
Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue

robocopy . $tmp /E /XD .venv data "data_backup_*" node_modules dist __pycache__ .pytest_cache learning .git /XF password.txt .env *.env *.db *.sqlite3 | Out-Null
if ($LASTEXITCODE -ge 8) { Write-Host "Copy failed." -ForegroundColor Red; exit 1 }

# Safety check: stop if anything private slipped in
$bad = Get-ChildItem $tmp -Recurse -Force -File | Where-Object {
    $_.Name -ieq "password.txt" -or $_.Extension -in ".db", ".sqlite", ".sqlite3" -or $_.FullName -match "\\chroma\\" }
if ($bad) { Write-Host "STOP: private files found in the package:" -ForegroundColor Red; $bad | ForEach-Object { $_.FullName }; exit 1 }

Compress-Archive -Path "$tmp\*" -DestinationPath $out -Force
Remove-Item $tmp -Recurse -Force
Write-Host "Created $out" -ForegroundColor Green
Write-Host "Size: $([math]::Round((Get-Item $out).Length / 1MB, 1)) MB. Open it and check there is no 'data' folder."
