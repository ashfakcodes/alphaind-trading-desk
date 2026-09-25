#!/usr/bin/env bash
echo "========================================================"
echo "  Starting Alphaind - AI Trading Desk (Frontend)"
echo "  Serving static web app on http://localhost:3000"
echo "  Connecting dynamically to backend on http://127.0.0.1:8000"
echo "========================================================"
python3 -m http.server 3000 --directory frontend
