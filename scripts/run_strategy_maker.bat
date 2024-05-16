:: batch magic to get cur dir
set SCRIPT_DIR=%~dp0
cd %SCRIPT_DIR%\..

venv\Scripts\python.exe -m cash_money.strategy_gui

cmd /k