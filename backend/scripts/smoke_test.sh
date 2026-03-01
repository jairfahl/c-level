#!/bin/bash
BASE_URL="${BASE_URL:-http://localhost:8000}"
echo "Smoke test: $BASE_URL"
echo ""
echo "1. Health check..."
curl -sf "$BASE_URL/health" | python3 -m json.tool
echo ""
echo "Smoke test concluido"
