@echo off
REM ---------------------------------------------------------------------------
REM Launch the Dance Management Django dev server with the project virtualenv.
REM
REM Running a bare `python manage.py runserver` uses whatever `python` is first
REM on PATH (e.g. the system Python 3.13 install), which does NOT have the
REM project dependencies, and fails with:
REM     ModuleNotFoundError: No module named 'nepali_datetime'
REM This script always uses .venv\Scripts\python.exe instead.
REM
REM Usage:
REM   run.cmd                 -> serve on http://127.0.0.1:8000/
REM   run.cmd check           -> run any other manage.py command
REM ---------------------------------------------------------------------------
setlocal
set "ROOT=%~dp0"
set "PY=%ROOT%.venv\Scripts\python.exe"

if not exist "%PY%" (
    echo [run.cmd] Virtual environment not found at:
    echo [run.cmd]   %PY%
    echo [run.cmd] Create it first with:
    echo [run.cmd]   python -m venv .venv
    echo [run.cmd]   .venv\Scripts\python.exe -m pip install -r requirements.txt
    exit /b 1
)

set "DJANGO_SETTINGS_MODULE=manage_project.settings.dev"
set "PYTHONIOENCODING=utf-8"

if "%~1"=="" (
    "%PY%" "%ROOT%manage.py" runserver 127.0.0.1:8000
) else (
    "%PY%" "%ROOT%manage.py" %*
)

endlocal
