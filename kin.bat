@echo off
set SCRIPT_DIR=%~dp0
set PYTHONPATH=%SCRIPT_DIR%;%PYTHONPATH%
for /f %%i in ('python -c "import sys; sys.path.insert(0, '%SCRIPT_DIR:\=/%'); from utils.fs_utils import FSUtils; print(FSUtils.get_python_command())"') do set PYTHON_CMD=%%i
%PYTHON_CMD% "%~dp0routes.py" %*
