@echo off
for /f %%i in ('python -c "from utils.fs_utils import FSUtils; print(FSUtils.get_python_command())"') do set PYTHON_CMD=%%i
%PYTHON_CMD% "%~dp0routes.py" %*
