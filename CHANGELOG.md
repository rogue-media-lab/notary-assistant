# Changelog

All notable changes to this project will be documented here.

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
