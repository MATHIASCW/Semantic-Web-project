::
:: Tolkien Knowledge Graph - Batch Script pour Windows
:: Démarre le serveur web et ouvre le navigateur
::

@echo off
chcp 65001 > nul
cls

echo.
echo ╔══════════════════════════════════════════════════════════╗
echo ║   🧙 Tolkien Knowledge Graph - Web Interface             ║
echo ║                                                          ║
echo ║   Démarrage du serveur...                               ║
echo ║                                                          ║
echo ║   URLs disponibles:                                      ║
echo ║   - Accueil:      http://localhost:8000/                ║
echo ║   - Navigation:   http://localhost:8000/browse          ║
echo ║   - API Docs:     http://localhost:8000/docs            ║
echo ║                                                          ║
echo ║   Appuyer sur Ctrl+C pour arrêter                       ║
echo ╚══════════════════════════════════════════════════════════╝
echo.

REM Vérifier que Fuseki est accessible
echo Vérification de Fuseki...
curl -s http://localhost:3030/ > nul 2>&1
if errorlevel 1 (
    echo.
    echo ⚠️  ATTENTION: Fuseki n'est pas accessible sur http://localhost:3030/
    echo.
    echo Fuseki doit être en cours d'exécution avant de démarrer l'interface web.
    echo.
    echo Pour démarrer Fuseki (depuis le répertoire d'installation):
    echo   fuseki-server --mem /kg-tolkiengateway
    echo.
    timeout /t 5
) else (
    echo ✓ Fuseki détecté
    echo.
)

REM Activer l'environnement virtuel
call .venv\Scripts\activate.bat

REM Démarrer le serveur
python run_web.py

pause
