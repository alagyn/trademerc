:: batch magic to get cur dir
set SCRIPT_DIR=%~dp0
cd %SCRIPT_DIR%\..

venv\Scripts\python.exe -m unittest discover -v -s .\tests -p test_*.py