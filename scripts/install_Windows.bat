:: batch magic to get cur dir
set SCRIPT_DIR=%~dp0
cd %SCRIPT_DIR%\..

py -m venv venv

venv\Scripts\pip.exe install --upgrade pip
venv\Scripts\pip.exe install -r requirements.txt

cmd /k