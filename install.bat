@echo off

:: Check for required dependencies
where git >nul 2>&1
if errorlevel 1 (
    echo Error: Git is required but not installed
    echo Please install Git from https://git-scm.com/
    exit /b 1
)

where node >nul 2>&1
if errorlevel 1 (
    echo Error: Node.js is required but not installed
    echo Please install Node.js from https://nodejs.org/
    exit /b 1
)

where python >nul 2>&1
if errorlevel 1 (
    echo Error: Python is required but not installed
    echo Please install Python from https://python.org/
    exit /b 1
)

:: Update submodules
git submodule update --init --recursive
if errorlevel 1 (
    echo Error: Submodule update failed
    exit /b 1
)

:: Install Python dependencies
pip install -r requirements.txt --user
if errorlevel 1 (
    echo Error: Python dependencies installation failed
    exit /b 1
)

:: Check for Cairo installation
echo Checking for Cairo installation...
where gdk-pixbuf-query-loaders >nul 2>&1
if errorlevel 1 (
    echo Warning: Cairo graphics library not found
    echo Please install GTK3 runtime from https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer
)

:: Install and build repo-visualizer
cd vendor\repo-visualizer
call npm install --legacy-peer-deps
if errorlevel 1 (
    echo Error: repo-visualizer dependencies installation failed
    exit /b 1
)

call npm install -g esbuild
if errorlevel 1 (
    echo Error: esbuild installation failed
    exit /b 1
)

if not exist dist mkdir dist
call npm run build
if errorlevel 1 (
    echo Error: repo-visualizer build failed
    exit /b 1
)
cd ..\..

:: Add to user PATH more safely
echo Adding KinOS to user PATH...
for /f "tokens=2*" %%a in ('reg query HKCU\Environment /v PATH') do set "userpath=%%b"
setx PATH "%userpath%;%CD%"
