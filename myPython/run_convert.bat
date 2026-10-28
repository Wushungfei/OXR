@echo off
REM OXR batch PDF converter launcher
REM Usage: drag a PDF folder onto this bat, or double-click and type a path
REM Prefers system python, falls back to WorkBuddy built-in Python (where somark is installed)

setlocal
set "PYEXE="
where python >nul 2>nul && set "PYEXE=python"
if not defined PYEXE (
    if exist "C:\Users\Admin\.workbuddy\binaries\python\versions\3.13.12\python.exe" (
        set "PYEXE=C:\Users\Admin\.workbuddy\binaries\python\versions\3.13.12\python.exe"
    )
)
if not defined PYEXE (
    echo [ERROR] python not found. Please install Python first.
    pause
    exit /b 1
)

set "SCRIPT=%~dp0oxr_batch_convert.py"
if "%~1"=="" (
    echo ============================================
    echo   OXR Batch PDF Converter
    echo ============================================
    set /p TARGET=Enter PDF folder or file path:
) else (
    set "TARGET=%~1"
)

"%PYEXE%" "%SCRIPT%" "%TARGET%" --out "%~dp0converted" --recursive
echo.
pause
