@echo off
chcp 65001 >nul
setlocal EnableExtensions
cd /d "%~dp0"

echo ============================================
echo   NGOKAF TRANS — Build + Installateur
echo ============================================
echo.

where python >nul 2>&1
if errorlevel 1 (
  echo [ERREUR] Python introuvable dans le PATH.
  echo Installez Python 3.10+ 64-bit pour compiler le logiciel.
  exit /b 1
)

echo [1/5] Installation des dependances...
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo [ERREUR] Echec pip install.
  exit /b 1
)

echo.
echo [2/5] Generation de l'icone...
python scripts\make_icon.py
if errorlevel 1 (
  echo [ERREUR] Impossible de generer assets\icons\ngokaf.ico
  exit /b 1
)

echo.
echo [3/5] Nettoyage build precedent...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build

echo.
echo [4/5] PyInstaller (main.spec^)...
python -m PyInstaller --noconfirm main.spec
if errorlevel 1 (
  echo [ERREUR] Echec PyInstaller.
  exit /b 1
)

if not exist "dist\NGOKAF_TRANS\NGOKAF_TRANS.exe" (
  echo [ERREUR] Executable manquant: dist\NGOKAF_TRANS\NGOKAF_TRANS.exe
  exit /b 1
)

echo.
echo [5/5] Compilation Inno Setup (Setup_Ngokaf_Trans.exe^)...

set ISCC=
if exist "%LocalAppData%\Programs\Inno Setup 6\ISCC.exe" set ISCC=%LocalAppData%\Programs\Inno Setup 6\ISCC.exe
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe
if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe

if not defined ISCC (
  for /f "delims=" %%i in ('where ISCC.exe 2^>nul') do if not defined ISCC set ISCC=%%i
)

if not defined ISCC (
  echo.
  echo [ERREUR] Inno Setup 6 introuvable (ISCC.exe).
  echo.
  echo Telechargez et installez Inno Setup 6 :
  echo   https://jrsoftware.org/isdl.php
  echo.
  echo L'executable PyInstaller est pret :
  echo   dist\NGOKAF_TRANS\NGOKAF_TRANS.exe
  echo Relancez build.bat apres installation d'Inno Setup.
  exit /b 1
)

echo ISCC detected: "%ISCC%"
echo Utilisation: "%ISCC%"
"%ISCC%" "installer\setup.iss"
if errorlevel 1 (
  echo [ERREUR] Echec compilation Inno Setup.
  exit /b 1
)

echo.
echo ============================================
echo   BUILD TERMINE
echo ============================================
echo   App :     dist\NGOKAF_TRANS\NGOKAF_TRANS.exe
echo   Setup :   installer\Output\Setup_Ngokaf_Trans.exe
echo.
echo   Distribuez Setup_Ngokaf_Trans.exe aux postes clients.
echo   Python n'est PAS requis sur les postes clients.
echo   MySQL doit etre disponible (localhost ou serveur configure).
echo ============================================
exit /b 0
