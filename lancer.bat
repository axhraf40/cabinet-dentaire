@echo off
cd /d "%~dp0"
echo === Installation des dependances ===
venv\Scripts\python.exe -m pip install -r requirements.txt
echo === Creation de la base de donnees ===
venv\Scripts\python.exe manage.py migrate
venv\Scripts\python.exe manage.py init_cabinet_info
venv\Scripts\python.exe manage.py create_sample_products
echo.
echo === Serveur lance : ouvre http://127.0.0.1:8000 ===
start "" http://127.0.0.1:8000
venv\Scripts\python.exe manage.py runserver
pause
