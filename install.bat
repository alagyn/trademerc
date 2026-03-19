py -m venv venv
set py="venv\Scripts\python.exe"
%py% -m pip install --upgrade pip
%py% -m pip install -r python_reqs.txt

cmd /k