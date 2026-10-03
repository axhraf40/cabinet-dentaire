@echo off
setlocal
cd /d "%~dp0"

rem --- Trouver Python ---
set "PY=python"
where python >nul 2>nul || set "PY=py"
%PY% --version >nul 2>nul || (
    echo [ERREUR] Python est introuvable. Installe-le depuis https://www.python.org/downloads/
    echo          et coche "Add python.exe to PATH" pendant l'installation.
    goto erreur
)

rem --- Environnement virtuel (recree s'il est casse) ---
if exist venv\Scripts\python.exe (
    venv\Scripts\python.exe -m pip --version >nul 2>nul || (
        echo === pip absent du venv, tentative de reparation ===
        venv\Scripts\python.exe -m ensurepip --upgrade >nul 2>nul
    )
    venv\Scripts\python.exe -m pip --version >nul 2>nul || (
        echo === venv casse, recreation ===
        rmdir /s /q venv
    )
)
if not exist venv\Scripts\python.exe (
    echo === Creation de l'environnement virtuel ===
    %PY% -m venv venv || goto erreur
)

echo === Installation des dependances ===
venv\Scripts\python.exe -m pip install --upgrade pip >nul
venv\Scripts\python.exe -m pip install -r requirements.txt || goto erreur

echo === Creation de la base de donnees ===
venv\Scripts\python.exe manage.py migrate || goto erreur
venv\Scripts\python.exe manage.py init_cabinet_info || goto erreur
venv\Scripts\python.exe manage.py create_sample_products || goto erreur

echo.
echo === Serveur lance : ouvre http://127.0.0.1:8000  (Ctrl+C pour arreter) ===
start "" http://127.0.0.1:8000
venv\Scripts\python.exe manage.py runserver
goto fin

:erreur
echo.
echo [ERREUR] Le lancement a echoue. Lis le message ci-dessus.

:fin
pause
