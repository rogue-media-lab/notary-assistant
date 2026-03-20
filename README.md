# Notary Assistant — Stamp and Certify Co

A local Streamlit app for SC Notary Public administrative work.

## Features

- **Notary Scholar** — Gemini-powered Q&A grounded in the SC Notary Public Reference Manual (UPL-safe); supports optional supplemental document upload (PDF, MD, TXT) per session; chat sessions can be saved with a label, linked to a journal entry, and downloaded as a transcript
- **Notarial Journal** — Log, search (by name/document/act type), and date-filter notarial acts; view summary stats (total acts, YTD fees, act types); export full journal to CSV; delete entries by ID
- **Fee Calculator & Invoice** — Auto-calculates SC statutory fees ($5.00/signature max); generates downloadable `.txt` invoices with invoice number, client name, and document type
- **Certificate Generator** — SC statutory certificate wording for all act types, ready to copy or print via browser print dialog
- **Pre-Flight Checklist** — 14-item workflow checklist before completing any notarial act; saves completed checklist records (with client name, document type, and optional journal link) for audit purposes
- **Wedding Officiant** — Log ceremonies with partner names, venue, and fee; manage reusable ceremony scripts; export ceremony log to CSV
- **Settings** — Business info, commission expiration, default travel fee, Gemini API key and model selection; built-in application log viewer
- **Sidebar** — Commission expiry warning shown automatically (alerts at 90 days, error when expired)

## Prerequisites

- **Python 3.11+** — required to run the app
- **Gemini API key** — this app is built on Google Gemini for the Notary Scholar. You'll need a free API key from [Google AI Studio](https://aistudio.google.com/) before launching for the first time. The key is stored locally in `~/.notary_assistant/config.json` and never leaves your machine.
- **Git** — to clone the repository

On first launch, a setup wizard will walk you through entering your notary information (name, commission number, expiration date, county), business name, and Gemini API key. No manual config file editing required. All of this can be updated later in the **Settings** page.

## Setup (one-time)

### Windows

1. Install [Python 3.11+](https://www.python.org/downloads/) — check **"Add Python to PATH"** during the installer
2. Clone this repo:
   ```
   git clone https://github.com/rogue-media-lab/notary-assistant.git
   cd notary-assistant
   ```
3. Create and activate a virtual environment:
   ```
   python -m venv .venv
   .venv\Scripts\activate
   ```
4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
5. Place `sc_notary_manual.pdf` (or `.md`) in the `knowledge/` folder (see [Knowledge File](#knowledge-file))
6. Launch the app:
   ```
   run.bat
   ```
   The browser will open automatically to `http://localhost:8501`.
7. Complete the first-run setup form (name, commission info, Gemini API key)
8. For easy daily access: right-click `run.bat` → **Send to → Desktop (Create Shortcut)**

### Linux

1. Install Python 3.11+ if not already present:
   ```
   sudo apt install python3.11 python3.11-venv   # Debian/Ubuntu
   # or: sudo dnf install python3.11              # Fedora/RHEL
   ```
2. Clone this repo:
   ```
   git clone https://github.com/rogue-media-lab/notary-assistant.git
   cd notary-assistant
   ```
3. Create and activate a virtual environment:
   ```
   python3.11 -m venv .venv
   source .venv/bin/activate
   ```
4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
5. Place `sc_notary_manual.pdf` (or `.md`) in the `knowledge/` folder (see [Knowledge File](#knowledge-file))
6. Launch the app:
   ```
   source .venv/bin/activate && streamlit run app.py --server.headless false --browser.gatherUsageStats false
   ```
   The browser will open automatically to `http://localhost:8501`.
7. Complete the first-run setup form (name, commission info, Gemini API key)
8. Optional — create a shell script for easy launching:
   ```bash
   #!/bin/bash
   cd "$(dirname "$0")"
   source .venv/bin/activate
   streamlit run app.py --server.headless false --browser.gatherUsageStats false
   ```
   Save it as `run.sh`, then `chmod +x run.sh` and run with `./run.sh`.

## Daily Use

**Windows:** Double-click the desktop shortcut (or `run.bat`). The browser opens automatically. No terminal needed.

**Linux:** Run `./run.sh` from the project folder (or your desktop launcher if configured).

## Data Storage

All data is stored in `~/.notary_assistant/` (your user home folder):
- `config.json` — settings
- `notary.db` — SQLite journal and wedding log

Git updates to this repo will never touch your data.

## What's Not in This Repo

The following are intentionally excluded from version control — here's what to do about each:

| Excluded | Why | What to do |
|---|---|---|
| `.venv/` | Virtual environments are machine-specific | Run `pip install -r requirements.txt` during setup — this recreates it |
| `knowledge/*.pdf` / `knowledge/*.md` | May be copyrighted material | Add the SC Notary Public Reference Manual manually on each machine (see below) |
| Your Gemini API key | Never committed — stored only on your machine | Entered through the first-run setup wizard; saved to `~/.notary_assistant/config.json` |
| `~/.notary_assistant/` | Your data lives outside the repo entirely | Not affected by cloning or pulling updates |

## Knowledge File

Place the SC Notary Public Reference Manual as:
```
knowledge/sc_notary_manual.pdf   ← preferred
knowledge/sc_notary_manual.md    ← also supported
```
PDF is checked first. Both are excluded from git (the manual may be copyrighted — add it manually on each machine). Without it, the Notary Scholar will still work but with limited SC-specific knowledge.

## Legal Disclaimer

This application is an administrative tool only. It does not provide legal advice and cannot be used to practice law. When in doubt, consult the SC Secretary of State's office or a licensed SC attorney.
