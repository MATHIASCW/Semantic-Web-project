"""
Tolkien Knowledge Graph - Web Interface Launcher
Démarrer l'application FastAPI avec l'interface web
"""
import uvicorn
import sys

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║   🧙 Tolkien Knowledge Graph - Web Interface             ║
    ║                                                          ║
    ║   Configuration:                                         ║
    ║   - Host: 127.0.0.1                                    ║
    ║   - Port: 8000                                         ║
    ║   - Reload: Activé (détecte changements)               ║
    ║                                                          ║
    ║   URLs:                                                  ║
    ║   - Accueil:      http://localhost:8000/                ║
    ║   - Navigation:   http://localhost:8000/browse          ║
    ║   - API Docs:     http://localhost:8000/docs            ║
    ║   - ReDoc:        http://localhost:8000/redoc           ║
    ║                                                          ║
    ║   Appuyer sur Ctrl+C pour arrêter                       ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    try:
        uvicorn.run(
            "web.main:app",
            host="127.0.0.1",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\n✓ Application arrêtée proprement")
        sys.exit(0)
