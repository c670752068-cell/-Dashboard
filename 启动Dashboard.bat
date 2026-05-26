@echo off
chcp 65001 >nul
title Stock Trend Dashboard
cd /d "%~dp0"

echo ============================================================
echo   Stock Trend Dashboard - Windows Launcher
echo ============================================================
echo.

REM ===== Find Python =====
set PY=
where python >nul 2>&1
if %errorlevel%==0 (
    set PY=python
    goto found_py
)
where py >nul 2>&1
if %errorlevel%==0 (
    set PY=py
    goto found_py
)

echo [ERROR] Python not found.
echo.
echo Please install Python 3.10 or later from:
echo   https://www.python.org/downloads/
echo.
echo *** IMPORTANT: Check "Add Python to PATH" during install ***
echo.
pause
exit /b 1

:found_py
echo Using Python:
%PY% --version
echo.

REM ===== First run: create venv and install deps =====
if not exist "venv\Scripts\activate.bat" (
    echo [First run] Creating virtual environment...
    %PY% -m venv venv
    if errorlevel 1 goto error

    echo [First run] Installing dependencies: streamlit, yfinance, pandas, numpy, matplotlib
    echo             This takes about 2-3 minutes. Please wait...
    echo.
    call venv\Scripts\activate.bat
    python -m pip install --quiet --upgrade pip
    python -m pip install --quiet streamlit yfinance pandas numpy matplotlib
    if errorlevel 1 (
        echo.
        echo [INFO] Default mirror failed, retrying with Tsinghua mirror...
        python -m pip install --quiet -i https://pypi.tuna.tsinghua.edu.cn/simple streamlit yfinance pandas numpy matplotlib
        if errorlevel 1 goto error
    )
    echo [DONE] Dependencies installed.
    echo.
) else (
    call venv\Scripts\activate.bat
)

REM ===== Skip Streamlit email prompt =====
if not exist "%USERPROFILE%\.streamlit" mkdir "%USERPROFILE%\.streamlit"
if not exist "%USERPROFILE%\.streamlit\credentials.toml" (
    echo [general]> "%USERPROFILE%\.streamlit\credentials.toml"
    echo email = "">> "%USERPROFILE%\.streamlit\credentials.toml"
)

echo ============================================================
echo   Starting Dashboard...
echo.
echo   Browser will open http://localhost:8501 automatically.
echo   To stop: close this window or press Ctrl+C
echo ============================================================
echo.

streamlit run app.py --browser.gatherUsageStats false

goto end

:error
echo.
echo ============================================================
echo   [ERROR] Launch failed.
echo ============================================================
echo Please screenshot the error message above and send to Claude.
echo.
pause
exit /b 1

:end
echo.
echo Dashboard stopped.
pause
