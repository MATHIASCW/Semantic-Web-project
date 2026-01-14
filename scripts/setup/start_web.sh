#!/usr/bin/env bash
set -e

echo ""
echo "==============================================="
echo " Tolkien Knowledge Graph - Web Interface"
echo "==============================================="
echo " URLs:"
echo " - Home:     http://localhost:8000/"
echo " - Browse:   http://localhost:8000/browse"
echo " - API Docs: http://localhost:8000/docs"
echo ""

echo "Checking Fuseki..."
if curl -s http://localhost:3030/ > /dev/null 2>&1; then
  echo "Fuseki detected."
  echo ""
else
  echo ""
  echo "WARNING: Fuseki is not accessible at http://localhost:3030/"
  echo ""
  echo "To start Fuseki:"
  echo "  fuseki-server --mem /kg-tolkiengateway"
  echo ""
  sleep 3
fi

source .venv/bin/activate
python scripts/setup/run_web.py
