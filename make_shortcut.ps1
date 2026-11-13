# make_shortcut.ps1 - puts a "Accelnomics DocuMind AI" icon on the desktop. Run it once.
$root = $PSScriptRoot
$desktop = [Environment]::GetFolderPath("Desktop")
$shell = New-Object -ComObject WScript.Shell
$link = $shell.CreateShortcut((Join-Path $desktop "Accelnomics DocuMind AI.lnk"))
$link.TargetPath = "powershell.exe"
$link.Arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$root\start_app.ps1`""
$link.WorkingDirectory = $root
$link.IconLocation = "$root\privatedocs.ico"
$link.Description = "Start Accelnomics DocuMind AI and open it"
$link.Save()
Write-Host "Created the desktop icon: Accelnomics DocuMind AI"
