# One-time setup for PrivateDocs AI on Windows.
# Run in PowerShell from this folder:   powershell -ExecutionPolicy Bypass -File .\setup.ps1
Set-Location $PSScriptRoot

function Fail($message) { Write-Host "`nSTOP: $message" -ForegroundColor Red; exit 1 }
function Check($what) { if ($LASTEXITCODE -ne 0) { Fail "$what failed. Read the message above." } }

# 1. Programs that must already be installed
foreach ($tool in @(
    @{ name = "python"; help = "Install Python 3.11 or newer from python.org and tick 'Add python.exe to PATH'." },
    @{ name = "node";   help = "Install Node.js (LTS) from nodejs.org." },
    @{ name = "npm";    help = "Install Node.js (LTS) from nodejs.org." },
    @{ name = "ollama"; help = "Install Ollama from ollama.com." })) {
    if (-not (Get-Command $tool.name -ErrorAction SilentlyContinue)) { Fail "'$($tool.name)' was not found. $($tool.help)" }
}
$ok = python -c "import sys; print(sys.version_info >= (3, 11))"
if ($ok -ne "True") { Fail "Python 3.11 or newer is needed." }

# 2. Python environment and packages
if (-not (Test-Path ".venv")) { Write-Host "Creating the Python environment..."; python -m venv .venv; Check "Creating .venv" }
$py = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
Write-Host "Installing Python packages (a few minutes)..."
& $py -m pip install -r requirements.txt; Check "Installing Python packages"

# 3. Website packages
Write-Host "Installing website packages..."
Push-Location frontend; npm install; $code = $LASTEXITCODE; Pop-Location
if ($code -ne 0) { Fail "npm install failed." }

# 4. Local AI models (names are read from the code, so they never go out of date)
if (-not (Get-Process -Name "ollama" -ErrorAction SilentlyContinue)) {
    Start-Process "ollama" -ArgumentList "serve" -WindowStyle Minimized
    Start-Sleep -Seconds 4
}
$chat  = & $py -c "import ollama_client; print(ollama_client.CHAT_MODEL)"
$embed = & $py -c "import ollama_client; print(ollama_client.EMBED_MODEL)"
Write-Host "Downloading models $embed and $chat (several GB, only the first time)..."
ollama pull $embed; Check "Downloading $embed"
ollama pull $chat;  Check "Downloading $chat"

# 5. Quick self-test (uses a pretend AI model, so it is fast)
Write-Host "Running the automatic tests..."
& $py -m pytest tests -q
Check "The tests"

Write-Host "`nSetup finished. Next:  powershell -ExecutionPolicy Bypass -File .\reset_and_start.ps1" -ForegroundColor Green
