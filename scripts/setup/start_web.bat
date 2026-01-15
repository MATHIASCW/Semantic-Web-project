@echo off
setlocal
chcp 65001 > nul
cls

echo.
echo ===============================================
echo  Tolkien Knowledge Graph - Web Interface
echo ===============================================
echo  URLs:
echo  - Home:     http://tolkien-kg.org/
echo  - Browse:   http://tolkien-kg.org/browse
echo  - API Docs: http://tolkien-kg.org/docs
echo.

echo Checking Fuseki...
curl -s http://localhost:3030/ > nul 2>&1
if errorlevel 1 (
    echo.
    echo WARNING: Fuseki is not accessible at http://localhost:3030/
    echo.
    echo To start Fuseki:
    echo   fuseki-server --mem /kg-tolkiengateway
    echo.
    timeout /t 3
) else (
    echo Fuseki detected.
    echo.
)

call .venv\Scripts\activate.bat
python scripts\setup\run_web.py

pause
