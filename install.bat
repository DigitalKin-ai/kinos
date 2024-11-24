@echo off

:: Update submodules
git submodule update --init --recursive

:: Install Python dependencies
pip install -r requirements.txt
if errorlevel 1 (
    echo Error: Python dependencies installation failed
    exit /b 1
)

:: Install custom aider
cd vendor\aider
pip install -e .
if errorlevel 1 (
    echo Error: Aider installation failed
    exit /b 1
)
cd ..\..

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

:: Add to PATH (requires admin privileges)
setx PATH "%PATH%;%CD%" /M
