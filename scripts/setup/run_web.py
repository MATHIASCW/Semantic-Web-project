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
      - Host: tolkien-kg.org
      - Port: 80
      - Reload: Enabled (detects changes)

      URLs:
      - Home:        http://tolkien-kg.org/
      - Browse:      http://tolkien-kg.org/browse
      - API Docs:    http://tolkien-kg.org/docs
      - ReDoc:       http://tolkien-kg.org/redoc

      Press Ctrl+C to stop
    ===============================================
    """
    )

    project_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project_root))

    try:
        uvicorn.run(
            "web.main:app",
            host="tolkien-kg.org",
            port=80,
            reload=True,
            log_level="info",
            app_dir=str(project_root),
        )
    except KeyboardInterrupt:
        print("\n\nApplication stopped cleanly")
        sys.exit(0)
