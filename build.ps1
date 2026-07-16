#Requires -Version 5.1
#
# Build NGOKAF_TRANS.exe (PyInstaller) then Setup_Ngokaf_Trans.exe (Inno Setup).
#
$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

Write-Host "============================================"
Write-Host "  NGOKAF TRANS - Build + Installateur"
Write-Host "============================================"

function Find-ISCC {
    $candidates = @(
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
        "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
    )
    foreach ($p in $candidates) {
        if (Test-Path $p) { return $p }
    }
    $cmd = Get-Command ISCC.exe -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    return $null
}

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python introuvable dans le PATH. Installez Python 3.10+ 64-bit."
}

Write-Host "`n[1/5] pip install..."
python -m pip install -r requirements.txt

Write-Host "`n[2/5] Icone..."
python scripts\make_icon.py
if (-not (Test-Path "assets\icons\ngokaf.ico")) {
    Write-Error "Icone manquante: assets\icons\ngokaf.ico"
}

Write-Host "`n[3/5] Nettoyage..."
if (Test-Path dist) { Remove-Item -Recurse -Force dist }
if (Test-Path build) { Remove-Item -Recurse -Force build }

Write-Host "`n[4/5] PyInstaller..."
python -m PyInstaller --noconfirm main.spec
$exe = "dist\NGOKAF_TRANS\NGOKAF_TRANS.exe"
if (-not (Test-Path $exe)) {
    Write-Error "Executable manquant: $exe"
}

Write-Host "`n[5/5] Inno Setup..."
$iscc = Find-ISCC
if (-not $iscc) {
    Write-Host ""
    Write-Host "[ERREUR] Inno Setup 6 introuvable (ISCC.exe)." -ForegroundColor Red
    Write-Host "Telechargez: https://jrsoftware.org/isdl.php"
    Write-Host "PyInstaller OK: $exe"
    exit 1
}
Write-Host "ISCC: $iscc"
& $iscc "installer\setup.iss"
if ($LASTEXITCODE -ne 0) {
    Write-Error "Echec compilation Inno Setup."
}

$setup = "installer\Output\Setup_Ngokaf_Trans.exe"
Write-Host ""
Write-Host "============================================"
Write-Host "  BUILD TERMINE"
Write-Host "============================================"
Write-Host "  App   : $exe"
Write-Host "  Setup : $setup"
Write-Host "  Python ne sera pas requis sur les clients."
Write-Host "============================================"
