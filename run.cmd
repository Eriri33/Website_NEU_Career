@echo off
setlocal

set "ROOT=%~dp0"
cd /d "%ROOT%" || goto startup_failed

if not exist ".venv\Scripts\python.exe" (
    where py >nul 2>nul
    if not errorlevel 1 (
        py -3 -m venv "%ROOT%.venv"
    ) else (
        where python >nul 2>nul
        if errorlevel 1 (
            echo Python 3 was not found. Install Python and enable the py launcher.
            goto setup_failed
        )
        python -m venv "%ROOT%.venv"
    )
    if errorlevel 1 goto setup_failed
)

set "PYTHON=%ROOT%.venv\Scripts\python.exe"
"%PYTHON%" -c "import flask" >nul 2>nul
if errorlevel 1 (
    echo Installing project dependencies...
    "%PYTHON%" -m pip install -r "%ROOT%requirements.txt"
    if errorlevel 1 goto setup_failed
)

"%PYTHON%" -m flask --app run.py init-db
if errorlevel 1 goto startup_failed

if /I "%~1"=="--init-only" (
    echo Python environment and database are ready.
    exit /b 0
)

echo.
echo Career Connect is running at http://127.0.0.1:5000/
echo Press Ctrl+C to stop the server.
"%PYTHON%" run.py
exit /b %ERRORLEVEL%

:setup_failed
echo.
echo Python environment setup failed. Check the Python installation and try again.
pause
exit /b 1

:startup_failed
echo.
echo Application startup failed. Review the error above.
pause
exit /b 1
