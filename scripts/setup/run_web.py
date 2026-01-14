"""
Tolkien Knowledge Graph - Web Interface Launcher
Start the FastAPI application with the web interface.
"""
import sys
from pathlib import Path

import uvicorn

if __name__ == "__main__":
    print(
        """
    ===============================================
      Tolkien Knowledge Graph - Web Interface

      Configuration:
      - Host: 127.0.0.1
      - Port: 8000
      - Reload: Enabled (detects changes)

      URLs:
      - Home:        http://localhost:8000/
      - Browse:      http://localhost:8000/browse
      - API Docs:    http://localhost:8000/docs
      - ReDoc:       http://localhost:8000/redoc

      Press Ctrl+C to stop
    ===============================================
    """
    )

    project_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project_root))

    try:
        uvicorn.run(
            "web.main:app",
            host="127.0.0.1",
            port=8000,
            reload=True,
            log_level="info",
            app_dir=str(project_root),
        )
    except KeyboardInterrupt:
        print("\n\nApplication stopped cleanly")
        sys.exit(0)
