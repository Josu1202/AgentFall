@echo off
setlocal
cd /d "%~dp0"

rem Explicitly select Python 3.13 instead of an unrelated active environment.
py -3.13 --version >nul 2>&1
if errorlevel 1 (
    echo No se encontro Python 3.13 de 64 bits.
    echo Instala Python 3.13 desde https://www.python.org/downloads/windows/
    echo Consulta README.md para los pasos de instalacion.
    goto failed
)

if not exist ".venv313\Scripts\python.exe" (
    echo Creando el entorno de Python 3.13...
    py -3.13 -m venv .venv313
    if errorlevel 1 goto failed
)

rem Never silently reuse an environment created with a different interpreter.
".venv313\Scripts\python.exe" -c "import sys, struct; sys.exit(0 if sys.version_info[:2] == (3, 13) and struct.calcsize('P') == 8 else 1)"
if errorlevel 1 (
    echo El entorno .venv313 no corresponde a Python 3.13 de 64 bits.
    echo Renombra esa carpeta y vuelve a ejecutar este archivo.
    goto failed
)

echo Comprobando dependencias...
".venv313\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed

".venv313\Scripts\python.exe" main.py %*
if errorlevel 1 goto failed
exit /b 0

:failed
echo.
echo No se pudo iniciar Agentfall. Revisa el mensaje anterior.
pause
exit /b 1
