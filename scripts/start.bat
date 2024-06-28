:: batch magic to get cur dir
set SCRIPT_DIR=%~dp0
cd %SCRIPT_DIR%\..

venv\Scripts\python.exe -m cash_money

set ERR=%errorlevel%

:: Jump to end if no error
if %ERR% EQU 0 goto end
:: Else log a message
echo Error: App exited with code: %ERR%
:: And keep the console open
cmd /k

:end