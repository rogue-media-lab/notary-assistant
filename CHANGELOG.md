# Changelog

All notable changes to this project will be documented here.

---

## [1.0.0] — 2026-03-20

### Changed
- **Modular architecture** — all page render functions moved from `app.py` into
  dedicated `notary/pages/` modules (`scholar.py`, `journal.py`, `fee_calculator.py`,
  `certificates.py`, `checklist.py`, `wedding.py`, `settings.py`). `app.py` is now a
  thin orchestrator (~150 lines: bootstrap, sidebar, router)
- `app.py` page title now reads business name from config instead of being hardcoded
- Sidebar business name fallback is now "Notary Assistant" instead of a personal name

### Fixed
- Completed state-agnostic migration: certificate wording, UPL banner, chat placeholder,
  and certificate info message all read state from config
- `certificates.py` — replaced static SC dict with `get_certificate_options(state)`
- Personal business name and legal entity removed from all source-code defaults and
  fallbacks — new users see blank fields in setup, not someone else's company name
- `db.py` default ceremony script and table schema no longer reference South Carolina
- `pyproject.toml` — corrected package name (`google-generativeai` → `google-genai`)
  and added missing `pypdf>=4.0.0` dependency
- `run.bat` — removed hardcoded business name from window title
- `run.sh` — added `.venv` existence check with helpful error message (matches `run.bat`)
- Pre-flight checklist fee item no longer hardcodes SC statutory maximum
- Commission number setup placeholder no longer says `SC-XXXXXXXX`
- Wedding form state field now defaults from config
- `fee_per_signature` minimum raised to `$0.01` to prevent accidental $0 entry
- Added `init_warnings` to `ScholarAgent` — multiple PDFs in `knowledge/` now surfaces
  a visible warning instead of silently using the first file

### Added
- Version badge in README

---

## [0.1.1] — 2026-03-20

### Fixed
- Removed all hardcoded South Carolina references — the app now works for notaries in any US state
- `SC_FEE_PER_SIGNATURE` constant renamed to `DEFAULT_FEE_PER_SIGNATURE`; fee is now configurable per user
- Invoice no longer hardcodes "South Carolina" — state is pulled from user settings
- Notary Scholar system prompt now uses the user's configured state name instead of "South Carolina"
- Knowledge file fallback message no longer references `sc_notary_manual.pdf` — any filename is accepted
- README Knowledge File section clarified: any `.pdf` or `.md` filename works, no renaming required

### Added
- `state` field added to notary information in the setup wizard and Settings page
- `fee_per_signature` field added to setup wizard and Settings page — set your state's statutory maximum
- `run.sh` included in the repo so Linux users don't have to write it manually
- Git install link added to Prerequisites section in README
- Gemini model selection guidance added to README

---

## [0.1.0] — 2026-03-20

### Added
- Initial release
- **Notary Scholar** — Gemini-powered Q&A with state notary manual as context; supplemental document upload; saved chat sessions with labels and journal linking
- **Notarial Journal** — Log, search, date-filter, and export notarial acts; summary stats; CSV export
- **Fee Calculator & Invoice** — Statutory fee calculation; downloadable plain-text invoices
- **Certificate Generator** — Statutory certificate wording for all act types; browser print support
- **Pre-Flight Checklist** — 14-item pre-notarization checklist; saved checklist records
- **Wedding Officiant** — Ceremony log with partner names, venue, fee; reusable ceremony scripts; CSV export
- **Settings** — Full configuration page with Gemini model selector and application log viewer
- Commission expiry warning in sidebar (alert at 90 days, error when expired)
- All data stored in `~/.notary_assistant/` — never touched by git updates
