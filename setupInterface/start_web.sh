

set -e

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║   🧙 Tolkien Knowledge Graph - Web Interface             ║"
echo "║                                                          ║"
echo "║   Démarrage du serveur...                               ║"
echo "║                                                          ║"
echo "║   URLs disponibles:                                      ║"
echo "║   - Accueil:      http://localhost:8000/                ║"
echo "║   - Navigation:   http://localhost:8000/browse          ║"
echo "║   - API Docs:     http://localhost:8000/docs            ║"
echo "║                                                          ║"
echo "║   Appuyer sur Ctrl+C pour arrêter                       ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

echo "Vérification de Fuseki..."
if curl -s http://localhost:3030/ > /dev/null 2>&1; then
    echo "✓ Fuseki détecté"
    echo ""
else
    echo ""
    echo "⚠️  ATTENTION: Fuseki n'est pas accessible sur http://localhost:3030/"
    echo ""
    echo "Fuseki doit être en cours d'exécution avant de démarrer l'interface web."
    echo ""
    echo "Pour démarrer Fuseki (depuis le répertoire d'installation):"
    echo "  fuseki-server --mem /kg-tolkiengateway"
    echo ""
    sleep 5
fi

source .venv/bin/activate

python run_web.py
