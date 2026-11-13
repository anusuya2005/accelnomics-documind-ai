# Starts Ollama (if needed), the backend, and the website. Run from the privatedocs folder.
$root = $PSScriptRoot

# 1. Ollama: start it if it is not already running
if (-not (Get-Process -Name "ollama" -ErrorAction SilentlyContinue)) {
    Start-Process "ollama" -ArgumentList "serve" -WindowStyle Minimized
    Start-Sleep -Seconds 3
}

# 2. Backend in its own window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root'; .\.venv\Scripts\Activate.ps1; uvicorn main:app --host 127.0.0.1 --port 8000"

# 3. Website in its own window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\frontend'; npm run dev"

# 4. Open the browser after the servers have had time to start
Start-Sleep -Seconds 8
Start-Process "http://127.0.0.1:5173"
Write-Host "Started. Close the two new windows to stop the app."
