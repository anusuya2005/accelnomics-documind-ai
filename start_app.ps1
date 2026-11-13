# start_app.ps1 - starts Accelnomics DocuMind AI on ONE port (8000) and opens it in an app-style window.
# Needs: the website built once (cd frontend; npm run build), the .venv, and Ollama installed.
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

# When started from the desktop icon the window is hidden, so problems are shown in a message box.
function Fail($text) {
    Write-Host $text -ForegroundColor Red
    try {
        Add-Type -AssemblyName System.Windows.Forms
        [System.Windows.Forms.MessageBox]::Show($text, "Accelnomics DocuMind AI") | Out-Null
    } catch { }
    exit 1
}

if (-not (Test-Path ".\frontend\dist\index.html")) {
    Fail "The website is not built yet. Open PowerShell in the project folder and run: cd frontend ; npm run build"
}

# 1. Ollama: start it only if it is not already running.
if (-not (Get-Process -Name "ollama" -ErrorAction SilentlyContinue)) {
    Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 3
}

# 2. Backend (also serves the website): start it only if port 8000 is free.
New-Item -ItemType Directory -Force ".\logs" | Out-Null
$busy = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
if (-not $busy) {
    $py = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
    Start-Process -FilePath $py `
        -ArgumentList "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000" `
        -WindowStyle Hidden `
        -RedirectStandardOutput ".\logs\backend.log" -RedirectStandardError ".\logs\backend-error.log"
}

# 3. Wait until the backend answers (up to 60 seconds).
$url = "http://127.0.0.1:8000"
$ready = $false
for ($i = 0; $i -lt 60; $i++) {
    try {
        Invoke-WebRequest -UseBasicParsing "$url/api/login-options" -TimeoutSec 2 | Out-Null
        $ready = $true
        break
    } catch { Start-Sleep -Seconds 1 }
}
if (-not $ready) {
    Fail "The backend did not start. Look at logs\backend-error.log in the DocuMind folder."
}

# 4. Open the app window (Edge app mode); fall back to the normal browser.
try { Start-Process "msedge" "--app=$url" } catch { Start-Process $url }
Write-Host "Accelnomics DocuMind AI is running at $url"
