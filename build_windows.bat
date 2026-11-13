@echo off
setlocal
cd /d "%~dp0"

echo [1/4] Installing dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo [2/4] Running tests...
python -m pytest -q
if errorlevel 1 (
    echo Tests failed. Build stopped.
    exit /b 1
)

echo [3/4] Building Windows application...
rem Back up existing writable data folders if present so rebuilds never destroy data
if exist "dist\InstaReciprocal\data" (
    if not exist ".build_backup" mkdir ".build_backup"
    xcopy /e /i /y "dist\InstaReciprocal\data" ".build_backup\data" >nul
)
if exist "dist\InstaReciprocal\exports" (
    if not exist ".build_backup" mkdir ".build_backup"
    xcopy /e /i /y "dist\InstaReciprocal\exports" ".build_backup\exports" >nul
)

python -m PyInstaller --noconfirm --clean InstaReciprocal.spec

if errorlevel 1 (
    echo PyInstaller build failed.
    if exist ".build_backup\data" xcopy /e /i /y ".build_backup\data" "dist\InstaReciprocal\data" >nul
    if exist ".build_backup\exports" xcopy /e /i /y ".build_backup\exports" "dist\InstaReciprocal\exports" >nul
    if exist ".build_backup" rmdir /s /q ".build_backup" 2>nul
    exit /b 1
)

echo [4/4] Preparing writable data folders...
if not exist "dist\InstaReciprocal\data" mkdir "dist\InstaReciprocal\data"
if not exist "dist\InstaReciprocal\exports" mkdir "dist\InstaReciprocal\exports"

if exist ".build_backup\data" (
    xcopy /e /i /y ".build_backup\data" "dist\InstaReciprocal\data" >nul
    rmdir /s /q ".build_backup\data" 2>nul
)
if exist ".build_backup\exports" (
    xcopy /e /i /y ".build_backup\exports" "dist\InstaReciprocal\exports" >nul
    rmdir /s /q ".build_backup\exports" 2>nul
)
if exist ".build_backup" rmdir /s /q ".build_backup" 2>nul

if not exist "dist\InstaReciprocal\data\whitelist.json" (
    if exist "data\whitelist.json" (
        copy /y "data\whitelist.json" "dist\InstaReciprocal\data\whitelist.json" >nul
    ) else (
        echo []> "dist\InstaReciprocal\data\whitelist.json"
    )
)
if not exist "dist\InstaReciprocal\data\instareciprocal.db" (
    if exist "data\instareciprocal.db" (
        copy /y "data\instareciprocal.db" "dist\InstaReciprocal\data\instareciprocal.db" >nul
    )
)

echo.
echo Build complete:
echo dist\InstaReciprocal\InstaReciprocal.exe
echo.
echo Keep the entire InstaReciprocal folder together. Do not move only the EXE.
if "%NO_PAUSE%"=="" pause
