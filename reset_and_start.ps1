# One command: fresh demo data + backend + website + browser.
# Run from the privatedocs folder:   powershell -ExecutionPolicy Bypass -File .\reset_and_start.ps1
$root = $PSScriptRoot
Set-Location $root

# 0. Stop an old backend/website so the data folder is not in use
Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match "uvicorn main:app" -or $_.CommandLine -match "vite" } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Start-Sleep -Seconds 2

# 1. Ask for the demo password ONCE
$secure = Read-Host "Choose ONE password for all demo users (min 10 characters)" -AsSecureString
$env:PD_DEMO_PASSWORD = [System.Net.NetworkCredential]::new("", $secure).Password

# 2. Ollama
if (-not (Get-Process -Name "ollama" -ErrorAction SilentlyContinue)) {
    Start-Process "ollama" -ArgumentList "serve" -WindowStyle Minimized
    Start-Sleep -Seconds 3
}

# 3. Fresh database and users (old data is moved to data_backup_...)
& "$root\.venv\Scripts\python.exe" reset_demo.py
if ($LASTEXITCODE -ne 0) { Write-Host "Reset failed. Stopping."; exit 1 }

# 4. Backend and website in their own windows (they inherit the environment)
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root'; .\.venv\Scripts\Activate.ps1; uvicorn main:app --host 127.0.0.1 --port 8000"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\frontend'; npm run dev"

# 5. Wait until the backend answers
$ready = $false
for ($i = 0; $i -lt 30; $i++) {
    try { Invoke-WebRequest -Uri "http://127.0.0.1:8000/docs" -UseBasicParsing -TimeoutSec 2 | Out-Null; $ready = $true; break }
    catch { Start-Sleep -Seconds 2 }
}
if (-not $ready) { Write-Host "Backend did not start. Look at its window."; exit 1 }

# 6. Load the demo documents
& "$root\.venv\Scripts\python.exe" load_docs.py

# 7. Forget the password and open the browser
Remove-Item Env:PD_DEMO_PASSWORD
Start-Process "http://127.0.0.1:5173"
Write-Host "Ready. Log in as admin1, hr_anu, it_ravi or fin_meena."
