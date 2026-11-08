# Exercise discovery and bootstrap branches without installing software or editing the registry.
$ErrorActionPreference = 'Stop'
$source = Get-Content -LiteralPath (Join-Path $PSScriptRoot '../bootstrap.ps1') -Raw
$ast = [System.Management.Automation.Language.Parser]::ParseInput($source, [ref]$null, [ref]$null)
$definition = $ast.Find({ param($node) $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq 'Find-Python' }, $true)
if (!$definition) { throw 'Find-Python definition missing' }
$actualPython = (& python.exe -c 'import sys; print(sys.executable)').Trim()
$oldOverride = $env:TANDEMFORGE_PYTHON
$fixture = Join-Path ([IO.Path]::GetTempPath()) ('TandemForge-bootstrap-test-' + [Guid]::NewGuid().ToString('N'))
[IO.Directory]::CreateDirectory($fixture) | Out-Null
try {
    function Get-Command { param($Name) return @() }
    function Get-ChildItem { param($LiteralPath) return @() }
    Invoke-Expression $definition.Extent.Text
    $Setup = $true
    $env:TANDEMFORGE_PYTHON = ''
    if (Find-Python) { throw 'Missing Python should not resolve' }
    $env:TANDEMFORGE_PYTHON = $actualPython
    if ((Find-Python) -ne $actualPython) { throw 'Explicit Python with Tk did not resolve' }
    $env:TANDEMFORGE_PYTHON = ''
    function Get-ChildItem { param($LiteralPath) return [pscustomobject]@{PSPath='HKCU:\Software\Python\PythonCore\3.13'} }
    function Get-ItemProperty { param($LiteralPath, $Name) return [pscustomobject]@{ExecutablePath=$actualPython} }
    if ((Find-Python) -ne $actualPython) { throw 'Registry discovery did not resolve Python after PATH was absent' }

    $marker = Join-Path $fixture 'installed.flag'
    $fakeWinget = Join-Path $fixture 'winget.cmd'
    [IO.File]::WriteAllText($fakeWinget, "@echo off`r`necho %* > `"%~dp0args.txt`"`r`necho installed > `"%~dp0installed.flag`"`r`nexit /b 0`r`n")
    function Find-Python { if ([IO.File]::Exists($marker)) { return $actualPython }; return $null }
    function Read-Host { param($Prompt) return 'Y' }
    function Get-Command { param($Name) if ($Name -eq 'winget.exe') { return [pscustomobject]@{Source=$fakeWinget} }; return @() }
    $start = $source.IndexOf('$python = Find-Python')
    $end = $source.IndexOf('if ($Setup) { & $python')
    $bootstrap = $source.Substring($start, $end - $start)
    Invoke-Expression $bootstrap
    if ($python -ne $actualPython) { throw 'Post-winget Python discovery failed' }
    $arguments = [IO.File]::ReadAllText((Join-Path $fixture 'args.txt'))
    if ($arguments -notmatch '--id Python.Python.3.13' -or $arguments -notmatch '--scope user') { throw 'Unexpected winget arguments' }
    [IO.File]::Delete($marker)
    function Get-Command { param($Name) return @() }
    $missingWinget = $false
    try { Invoke-Expression $bootstrap } catch { $missingWinget = $_.Exception.Message -like '*App Installer*' }
    if (!$missingWinget) { throw 'Missing winget did not give an actionable failure' }
    Write-Output 'BOOTSTRAP BRANCH CHECKS PASSED (simulated absence; not a clean Windows installation)'
} finally {
    $env:TANDEMFORGE_PYTHON = $oldOverride
}
