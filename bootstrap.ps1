param([switch]$Setup)

$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot

function Find-Python {
    $ErrorActionPreference = 'SilentlyContinue'
    $candidates = @($env:TANDEMFORGE_PYTHON)
    foreach ($launcher in @(Get-Command py.exe -ErrorAction SilentlyContinue)) {
        $path = & $launcher.Source -3 -c 'import sys; print(sys.executable)' 2>$null
        if ($LASTEXITCODE -eq 0) { $candidates += $path }
    }
    $candidates += @(Get-Command python.exe -ErrorAction SilentlyContinue |
        Where-Object { $_.Source -notlike '*\WindowsApps\*' } | ForEach-Object Source)
    foreach ($key in @('HKCU:\Software\Python\PythonCore', 'HKLM:\Software\Python\PythonCore')) {
        $candidates += @(Get-ChildItem -LiteralPath $key -ErrorAction SilentlyContinue | ForEach-Object {
            $install = Join-Path $_.PSPath 'InstallPath'
            $value = Get-ItemProperty -LiteralPath $install -Name ExecutablePath -ErrorAction SilentlyContinue
            if ($value) { $value.ExecutablePath }
        })
    }
    foreach ($candidate in $candidates | Where-Object { $_ } | Select-Object -Unique) {
        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            $check = 'import sys; raise SystemExit(sys.version_info < (3, 13))'
            if ($Setup) { $check = 'import sys, tkinter; raise SystemExit(sys.version_info < (3, 13))' }
            & $candidate -c $check 2>$null
            if ($LASTEXITCODE -eq 0) { return $candidate }
        }
    }
}

$python = Find-Python
if (!$python -and $Setup) {
    $answer = Read-Host 'Install Python 3.13 for TandemForge via Windows Package Manager? [Y/N]'
    if ($answer -notmatch '^[yY]$') { exit 0 }
    $winget = Get-Command winget.exe -ErrorAction SilentlyContinue
    if (!$winget) { throw 'Windows App Installer (winget) is required. Install it or install Python 3.13 from python.org, then open Setup again.' }
    & $winget.Source install --exact --id Python.Python.3.13 --source winget --scope user --silent --disable-interactivity --accept-package-agreements --accept-source-agreements
    $python = Find-Python
}
if (!$python) { throw 'Python 3.13 or newer is required. Run Setup TandemForge.cmd.' }
if ($Setup) { & $python -X utf8 (Join-Path $PSScriptRoot 'setup.py') }
else { & $python -X utf8 (Join-Path $PSScriptRoot 'studio.py') --open }
exit $LASTEXITCODE
