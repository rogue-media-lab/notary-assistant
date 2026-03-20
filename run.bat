@echo off
title Stamp and Certify Co - Notary Assistant
cd /d "%~dp0"
if exist ".venv\Scripts\activate.bat" call .venv\Scripts\activate.bat
streamlit run app.py --server.headless false --browser.gatherUsageStats false
pause
