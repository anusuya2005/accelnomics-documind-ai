   function Get-Ok($url, $pattern) {
     try {
       $r = Invoke-WebRequest $url -UseBasicParsing -TimeoutSec 4
       if ($pattern) { return [bool]($r.Content -match $pattern) }
       return ($r.StatusCode -eq 200)
     } catch { return $false }
   }
   "Backend: " + (Get-Ok 'http://127.0.0.1:8000/api/login-options')
   "Ollama:  " + (Get-Ok 'http://127.0.0.1:11434/api/tags')
   "Website: " + (Get-Ok 'http://127.0.0.1:8000/' 'id=.root.')