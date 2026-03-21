"""Shared helpers used by multiple page modules."""

from notary import journal as journal_mod


def journal_link_options() -> list[str]:
    """Return recent journal entries formatted for a selectbox."""
    entries = journal_mod.get_entries(limit=20)
    opts = ["(none)"]
    for e in entries:
        opts.append(f"#{e['id']} — {e['act_date']} — {e['signer_name']} ({e['act_type']})")
    return opts


def parse_journal_id(option: str) -> int | None:
    if option == "(none)":
        return None
    try:
        return int(option.split("—")[0].strip().lstrip("#"))
    except (ValueError, IndexError):
        return None
