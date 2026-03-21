"""Notary Assistant — Streamlit app with sidebar navigation."""

from datetime import date

import streamlit as st

from notary import config as cfg
from notary.db import initialize_schema
from notary.log import get_logger
from notary.pages.scholar import render_scholar
from notary.pages.journal import render_journal
from notary.pages.fee_calculator import render_fee_calculator
from notary.pages.certificates import render_certificates
from notary.pages.checklist import render_checklist
from notary.pages.wedding import render_wedding
from notary.pages.settings import render_settings

log = get_logger("notary.app")

# ---------------------------------------------------------------------------
# Page config (must be first Streamlit call)
# cfg.load() is pure Python — safe to call before any st.* calls
# ---------------------------------------------------------------------------
_early_config = cfg.load()
st.set_page_config(
    page_title=_early_config.get("business_name") or "Notary Assistant",
    page_icon="🖋️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    .upl-banner {
        background-color: #fff3cd;
        border: 1px solid #ffc107;
        border-radius: 6px;
        padding: 10px 16px;
        margin-bottom: 12px;
        font-size: 0.88rem;
        color: #5a4a00;
    }
    .stChatMessage { border-radius: 8px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------
cfg.ensure_dirs()
initialize_schema()


# ---------------------------------------------------------------------------
# First-run setup page
# ---------------------------------------------------------------------------
def render_setup_page() -> None:
    st.title("🖋️ Welcome to Your Notary Assistant")
    st.markdown(
        "Let's get you set up. Fill in your information below — "
        "you can always change this later in **Settings**."
    )

    with st.form("setup_form"):
        st.subheader("API Key")
        gemini_key = st.text_input(
            "Gemini API Key *",
            type="password",
            help="Required. Get yours at https://aistudio.google.com/",
        )

        st.subheader("Your Notary Information")
        notary_name = st.text_input("Your Full Name *", placeholder="Jane Roberts")
        commission_number = st.text_input("Commission Number", placeholder="e.g., 12345678")
        commission_expires = st.date_input(
            "Commission Expiration Date",
            value=None,
            min_value=date.today(),
        )
        col_county, col_state = st.columns(2)
        with col_county:
            county = st.text_input("County", placeholder="e.g., Richland")
        with col_state:
            state = st.text_input("State", placeholder="e.g., SC")

        st.subheader("Business Information")
        business_name = st.text_input("Business Name", placeholder="e.g., Stamp and Certify Co")
        legal_entity = st.text_input("Legal Entity Name", placeholder="e.g., Roberts and Associates LLC")
        col_travel, col_fee = st.columns(2)
        with col_travel:
            travel_fee = st.number_input("Default Travel Fee ($)", min_value=0.0, value=0.0, step=5.0)
        with col_fee:
            fee_per_signature = st.number_input(
                "Statutory Fee per Signature ($)",
                min_value=0.01,
                value=5.0,
                step=0.50,
                help="Your state's maximum statutory notary fee per signature.",
            )

        submitted = st.form_submit_button("Save & Continue", type="primary")
        if submitted:
            if not gemini_key:
                st.error("Gemini API key is required.")
            elif not notary_name:
                st.error("Your name is required.")
            else:
                config = cfg.load()
                config.update(
                    {
                        "gemini_api_key": gemini_key,
                        "notary_name": notary_name,
                        "commission_number": commission_number,
                        "commission_expires": commission_expires.isoformat() if commission_expires else "",
                        "county": county,
                        "state": state,
                        "business_name": business_name,
                        "legal_entity": legal_entity,
                        "travel_fee_default": travel_fee,
                        "fee_per_signature": fee_per_signature,
                    }
                )
                cfg.save(config)
                st.success("Setup complete! Loading your assistant…")
                st.rerun()


# ---------------------------------------------------------------------------
# Guard: show setup if not configured
# ---------------------------------------------------------------------------
if not cfg.is_configured():
    render_setup_page()
    st.stop()

config = cfg.load()

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(f"## 🖋️ {config.get('business_name') or 'Notary Assistant'}")
    st.caption(config.get("legal_entity", ""))

    st.divider()

    page = st.radio(
        "Navigation",
        [
            "Notary Scholar",
            "Notarial Journal",
            "Fee Calculator & Invoice",
            "Certificate Generator",
            "Pre-Flight Checklist",
            "Wedding Officiant",
            "Settings",
        ],
        label_visibility="collapsed",
    )

    st.divider()

    # Commission expiry warning
    expires_str = config.get("commission_expires", "")
    if expires_str:
        try:
            expires = date.fromisoformat(expires_str)
            days_left = (expires - date.today()).days
            if days_left < 0:
                st.error(f"⚠️ Commission has EXPIRED ({expires.strftime('%m/%d/%Y')})")
            elif days_left < 90:
                st.warning(f"⚠️ Commission expires in {days_left} days ({expires.strftime('%m/%d/%Y')})")
        except ValueError:
            pass

    st.caption(
        "⚖️ This app is an administrative tool only. "
        "It does not provide legal advice and cannot be used to practice law."
    )

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------
log.debug("App rendered — page: %s", page)
if page == "Notary Scholar":
    render_scholar(config)
elif page == "Notarial Journal":
    render_journal(config)
elif page == "Fee Calculator & Invoice":
    render_fee_calculator(config)
elif page == "Certificate Generator":
    render_certificates(config)
elif page == "Pre-Flight Checklist":
    render_checklist(config)
elif page == "Wedding Officiant":
    render_wedding(config)
elif page == "Settings":
    render_settings(config)
