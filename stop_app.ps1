# stop_app.ps1 - stops the PrivateDocs backend (port 8000). Ollama is left running.
$conn = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
if ($conn) {
    $conn | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
    Write-Host "Stopped."
} else {
    Write-Host "Nothing was running on port 8000."
}
