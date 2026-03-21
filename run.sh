#!/bin/bash
cd "$(dirname "$0")"
if [ ! -d ".venv" ]; then
    echo "ERROR: .venv not found. Run setup first:"
    echo "  python -m venv .venv && .venv/bin/pip install -r requirements.txt"
    exit 1
fi
source .venv/bin/activate
streamlit run app.py --server.headless false --browser.gatherUsageStats false
