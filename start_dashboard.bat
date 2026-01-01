@echo off
setlocal
title IA TRADING - Mobile Dashboard
echo ==========================================================
echo   IA TRADING - Iniciando...
echo ==========================================================
echo.

cd /d "%~dp0"

:: 1. Intentar detectar Python (probamos varios comandos)
set PYTHON_CMD=python

python --version >nul 2>&1
IF NOT ERRORLEVEL 1 GOTO FOUND_PYTHON

:: Si falla 'python', probamos 'py' (Launcher de Windows)
set PYTHON_CMD=py
py --version >nul 2>&1
IF NOT ERRORLEVEL 1 GOTO FOUND_PYTHON

:: Si falla todo
echo [ERROR] No se detecta Python en el sistema (ni 'python' ni 'py').
echo Por favor instala Python desde python.org y marca "Add to PATH".
pause
exit /b 1

:FOUND_PYTHON
echo Python detectado: %PYTHON_CMD%

set VENV_DIR=.venv_mobile

:: 2. Crear entorno si no existe
if not exist "%VENV_DIR%" (
  echo Creando entorno virtual...
  %PYTHON_CMD% -m venv "%VENV_DIR%"
)

:: 3. Definir ruta al python del entorno
set VENV_PY=%VENV_DIR%\Scripts\python.exe

:: 4. Verificar que se creo bien
if not exist "%VENV_PY%" (
  echo [ERROR] Fallo al crear el entorno virtual.
  pause
  exit /b 1
)

:: 5. Instalar dependencias si faltan
echo Verificando dependencias...
"%VENV_PY%" -m pip install pandas numpy scikit-learn yfinance matplotlib streamlit plotly >nul 2>&1

echo.
echo ==========================================================
echo   PARA ABRIR EN TU MOVIL:
echo   1. Conecta tu movil al mismo WiFi que esta PC.
echo   2. Tu direccion IP local es alguna de las siguientes:
ipconfig | findstr "IPv4"
echo.
echo   3. Abre Chrome/Safari en tu movil y escribe: http://TU_IP:8501
echo      (Ejemplo: http://192.168.1.35:8501)
echo.
echo   NOTA: Si aparece una ventana de Firewall, dale a "Permitir".
echo ==========================================================
echo.

echo Lanzando aplicacion...
"%VENV_PY%" -m streamlit run main.py --server.address=0.0.0.0

pause
