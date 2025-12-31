

set -e

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║   🧙 Tolkien Knowledge Graph - Web Interface             ║"
echo "║                                                          ║"
echo "║   Starting server...                                    ║"
echo "║                                                          ║"
echo "║   Available URLs:                                        ║"
echo "║   - Home:        http://localhost:8000/                ║"
echo "║   - Browse:      http://localhost:8000/browse          ║"
echo "║   - API Docs:    http://localhost:8000/docs            ║"
echo "║                                                          ║"
echo "║   Press Ctrl+C to stop                                  ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

echo "Checking Fuseki..."
if curl -s http://localhost:3030/ > /dev/null 2>&1; then
    echo "✓ Fuseki detected"
    echo ""
else
    echo ""
    echo "⚠️  WARNING: Fuseki is not accessible at http://localhost:3030/"
    echo ""
    echo "Fuseki must be running before starting the web interface."
    echo ""
    echo "To start Fuseki (from the installation directory):"
    echo "  fuseki-server --mem /kg-tolkiengateway"
    echo ""
    sleep 5
fi

source .venv/bin/activate

python run_web.py
