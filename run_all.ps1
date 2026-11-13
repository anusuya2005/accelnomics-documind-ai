# Does everything: checks programs, installs missing ones (with your permission), sets up, starts the app.
# Normally started by double-clicking START_HERE.bat
Set-Location $PSScriptRoot

function Refresh-Path {
    $machine = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $user = [Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = "$machine;$user;$env:LOCALAPPDATA\Programs\Ollama"
}

# --- 1. Programs this project needs
$programs = @(
    @{ cmd = "python"; id = "Python.Python.3.13";    label = "Python" },
    @{ cmd = "node";   id = "OpenJS.NodeJS.LTS";     label = "Node.js" },
    @{ cmd = "ollama"; id = "Ollama.Ollama";         label = "Ollama" })

Refresh-Path
$missing = $programs | Where-Object { -not (Get-Command $_.cmd -ErrorAction SilentlyContinue) }

if ($missing) {
    Write-Host "These programs are missing: $(($missing | ForEach-Object { $_.label }) -join ', ')" -ForegroundColor Yellow
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        Write-Host "Please install them yourself: python.org (tick 'Add python.exe to PATH'), nodejs.org, ollama.com. Then double-click START_HERE.bat again." -ForegroundColor Red
        exit 1
    }
    $answer = Read-Host "Install them now with Windows Package Manager? Windows may ask for permission. (Y/N)"
    if ($answer -notmatch "^[Yy]") { Write-Host "Cancelled. Install them and run this again."; exit 1 }
    foreach ($p in $missing) {
        Write-Host "Installing $($p.label)..."
        winget install -e --id $p.id --accept-package-agreements --accept-source-agreements
    }
    Refresh-Path
    $still = $programs | Where-Object { -not (Get-Command $_.cmd -ErrorAction SilentlyContinue) }
    if ($still) {
        Write-Host "Installed, but Windows needs a fresh window to see them. Close this window and double-click START_HERE.bat again." -ForegroundColor Yellow
        exit 1
    }
}

# --- 2. One-time setup (skipped when it was already done)
if (-not (Test-Path ".venv\Scripts\python.exe") -or -not (Test-Path "frontend\node_modules")) {
    & "$PSScriptRoot\setup.ps1"
    if ($LASTEXITCODE -ne 0) { Write-Host "Setup did not finish. Read the red message above." -ForegroundColor Red; exit 1 }
}

# --- 3. First time: make demo data. Later: just start.
if (-not (Test-Path "data\privatedocs.db")) {
    & "$PSScriptRoot\reset_and_start.ps1"
} else {
    & "$PSScriptRoot\start_all.ps1"
}