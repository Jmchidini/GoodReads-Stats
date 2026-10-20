@echo off
setlocal
cd /d "%~dp0"
title Goodreads Explorer

set "PYTHON_CMD="
if exist ".venv\Scripts\python.exe" (
    set PYTHON_CMD="%~dp0.venv\Scripts\python.exe"
    goto :found
)
py -3.12 -c "import sys; sys.exit(0 if sys.version_info[:2] == (3, 12) else 1)" >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=py -3.12"
    goto :found
)
python -c "import sys; sys.exit(0 if sys.version_info[:2] == (3, 12) else 1)" >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=python"
    goto :found
)
for %%P in (
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "C:\Python312\python.exe"
) do (
    if exist %%P (
        set PYTHON_CMD=%%P
        goto :found
    )
)
echo ERROR: No se encontro Python 3.12. Instalalo desde https://www.python.org/downloads/
pause
exit /b 1

:found
%PYTHON_CMD% -c "import sys; sys.exit(0 if sys.version_info[:2] == (3, 12) else 1)"
if errorlevel 1 (
    echo ERROR: Se requiere Python 3.12. Revisa el entorno .venv si existe.
    pause
    exit /b 1
)
echo Verificando dependencias...
%PYTHON_CMD% -m pip install -r "%~dp0requirements.txt" --quiet
if errorlevel 1 (
    echo ERROR: No se pudieron instalar las dependencias. Revisa el mensaje anterior.
    pause
    exit /b 1
)
echo Abriendo Goodreads Explorer. Para cerrar, presiona Ctrl+C.
%PYTHON_CMD% -m streamlit run "%~dp0goodreads_explorer.py"
if errorlevel 1 (
    echo ERROR: La aplicacion no pudo ejecutarse.
    pause
    exit /b 1
)
pause
