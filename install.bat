@echo off

:: Check if this is an update
if "%1"=="update" (
    echo 🔄 Updating KinOS...
    :: Pull latest changes
    git pull
    :: Update submodules to latest
    git submodule update --remote --merge
    echo ✓ Repository updated
)

:: Check Python availability
python -c "from utils.fs_utils import FSUtils; FSUtils.get_python_command()" >nul 2>&1
if errorlevel 1 (
    echo Error: Python 3.9+ is required but not found
    echo Please install Python 3.9 or later from https://www.python.org/downloads/
    exit /b 1
)

:: Verify Python version
set MIN_PYTHON_VERSION=3.9.0
for /f %%i in ('python -c "from utils.fs_utils import FSUtils; print(FSUtils.get_python_command())"') do set PYTHON_CMD=%%i
for /f %%i in ('%PYTHON_CMD% -c "import sys; print('.'.join(map(str, sys.version_info[:3])))"') do set CURRENT_VERSION=%%i

%PYTHON_CMD% -c "import sys; from packaging import version; sys.exit(0 if version.parse('%CURRENT_VERSION%') >= version.parse('%MIN_PYTHON_VERSION%') else 1)"
if errorlevel 1 (
    echo Error: Python %MIN_PYTHON_VERSION% or later is required
    echo Current version: %CURRENT_VERSION%
    echo Please upgrade Python from https://www.python.org/downloads/
    exit /b 1
)

:: Check for .env file (skip check if updating)
if not exist .env (
    echo Error: .env file not found
    echo Please copy .env.example to .env and configure your API keys
    exit /b 1
)

:: Check for required API keys
findstr /C:"OPENAI_API_KEY=sk-" .env >nul
if errorlevel 1 (
    echo Error: OpenAI API key not properly configured in .env
    exit /b 1
)
findstr /C:"PERPLEXITY_API_KEY=pplx-" .env >nul
if errorlevel 1 (
    echo Error: Perplexity API key not properly configured in .env
    exit /b 1
)

echo ✓ Environment configuration verified

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

:: Install/Update Python dependencies
for /f %%i in ('python -c "from utils.fs_utils import FSUtils; print(FSUtils.get_python_command())"') do set PYTHON_CMD=%%i
%PYTHON_CMD% -m pip install -r requirements.txt --user
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

:: Install/Update and build repo-visualizer
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
