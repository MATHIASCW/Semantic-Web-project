::
:: Tolkien Knowledge Graph - Batch Script for Windows
:: Starts the web server and opens the browser
::

@echo off
chcp 65001 > nul
cls

echo.
echo ╔══════════════════════════════════════════════════════════╗
echo ║   🧙 Tolkien Knowledge Graph - Web Interface             ║
echo ║                                                          ║
echo ▐   Starting server...                                   ▐
echo ▐                                                          ▐
echo ▐   Available URLs:                                      ▐
echo ▐   - Home:      http://localhost:8000/                ▐
echo ▐   - Browse:    http://localhost:8000/browse          ▐
echo ▐   - API Docs:  http://localhost:8000/docs            ▐
echo ▐                                                          ▐
echo ▐   Press Ctrl+C to stop                                ▐
echo ╚══════════════════════════════════════════════════════════╝
echo.

REM Check if Fuseki is accessible
echo Checking Fuseki...
curl -s http://localhost:3030/ > nul 2>&1
if errorlevel 1 (
    echo.
    echo ⚠️  WARNING: Fuseki is not accessible at http://localhost:3030/
    echo.
    echo Fuseki must be running before starting the web interface.
    echo.
    echo To start Fuseki (from the installation directory):
    echo   fuseki-server --mem /kg-tolkiengateway
    echo.
    timeout /t 5
) else (
    echo ✓ Fuseki detected
    echo.
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Start the server
python run_web.py

pause
