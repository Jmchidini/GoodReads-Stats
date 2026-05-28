@echo off
title Goodreads Explorer

echo ============================================
echo     Goodreads Explorer - Iniciando app...
echo ============================================
echo.

:: Intentar encontrar Python en ubicaciones comunes
set PYTHON_CMD=

:: 1. Probar "python" directo (si esta en PATH)
python --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=python
    goto :found
)

:: 2. Probar "py" (launcher de Windows)
py --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=py
    goto :found
)

:: 3. Buscar en rutas tipicas de instalacion
for %%P in (
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python39\python.exe"
    "C:\Python313\python.exe"
    "C:\Python312\python.exe"
    "C:\Python311\python.exe"
    "C:\Python310\python.exe"
    "%APPDATA%\Python\Python313\python.exe"
) do (
    if exist %%P (
        set PYTHON_CMD=%%P
        goto :found
    )
)

:: 4. Buscar con where
for /f "delims=" %%i in ('where python 2^>nul') do (
    set PYTHON_CMD=%%i
    goto :found
)

echo ERROR: No se pudo encontrar Python.
echo Descargalo desde https://www.python.org/downloads/
echo Al instalarlo, tilda la opcion "Add Python to PATH"
pause
exit /b

:found
echo Python encontrado: %PYTHON_CMD%
echo.

:: Instalar dependencias
echo Verificando dependencias...
%PYTHON_CMD% -m pip install streamlit plotly pandas --quiet
echo.

echo Abriendo la app en el navegador...
echo Para cerrarla, presiona Ctrl+C en esta ventana.
echo.

cd /d "%~dp0"
%PYTHON_CMD% -m streamlit run goodreads_explorer.py

pause