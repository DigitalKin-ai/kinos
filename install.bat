@echo off

:: Update submodules
git submodule update --init --recursive

:: Install Python dependencies
pip install -r requirements.txt

:: Install custom aider
cd vendor\aider
pip install -e .
cd ..\..

:: Install and build repo-visualizer
cd vendor\repo-visualizer
call npm install --legacy-peer-deps
call npm install -g esbuild
if not exist dist mkdir dist
call npm run build
cd ..\..

:: Add to PATH (requires admin privileges)
setx PATH "%PATH%;%CD%" /M
