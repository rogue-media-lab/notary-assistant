"""Settings page."""

from datetime import date

import streamlit as st

from notary import config as cfg
from notary import invoicing
from notary.log import get_logger, read_recent

log = get_logger("notary.pages.settings")


def render_settings(config: dict) -> None:
    st.title("⚙️ Settings")

    with st.form("settings_form"):
        st.subheader("Notary Information")
        col1, col2 = st.columns(2)
        with col1:
            notary_name = st.text_input("Your Full Name", value=config.get("notary_name", ""))
            commission_number = st.text_input("Commission Number", value=config.get("commission_number", ""))
            col_county, col_state = st.columns(2)
            with col_county:
                county = st.text_input("County", value=config.get("county", ""))
            with col_state:
                state = st.text_input("State", value=config.get("state", ""))
        with col2:
            exp_str = config.get("commission_expires", "")
            exp_val = date.fromisoformat(exp_str) if exp_str else None
            commission_expires = st.date_input("Commission Expiration Date", value=exp_val)
            travel_fee_default = st.number_input(
                "Default Travel Fee ($)",
                min_value=0.0,
                value=float(config.get("travel_fee_default", 0.0)),
                step=5.0,
            )
            fee_per_signature = st.number_input(
                "Statutory Fee per Signature ($)",
                min_value=0.01,
                value=float(config.get("fee_per_signature", invoicing.DEFAULT_FEE_PER_SIGNATURE)),
                step=0.50,
                help="Your state's maximum statutory notary fee per signature.",
            )

        st.subheader("Business Information")
        business_name = st.text_input("Business Name", value=config.get("business_name", ""))
        legal_entity = st.text_input("Legal Entity Name", value=config.get("legal_entity", ""))

        st.subheader("API Configuration")
        gemini_key = st.text_input(
            "Gemini API Key",
            value=config.get("gemini_api_key", ""),
            type="password",
            help="Your Google Gemini API key.",
        )
        _model_options = ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash-lite"]
        _current_model = config.get("gemini_model", "gemini-2.5-flash")
        gemini_model = st.selectbox(
            "Gemini Model",
            _model_options,
            index=_model_options.index(_current_model) if _current_model in _model_options else 0,
            help="gemini-2.0-flash works on the free tier and is recommended.",
        )

        saved = st.form_submit_button("Save Settings", type="primary")
        if saved:
            updated = cfg.load()
            updated.update(
                {
                    "notary_name": notary_name,
                    "commission_number": commission_number,
                    "commission_expires": commission_expires.isoformat() if commission_expires else "",
                    "county": county,
                    "state": state,
                    "travel_fee_default": travel_fee_default,
                    "fee_per_signature": fee_per_signature,
                    "business_name": business_name,
                    "legal_entity": legal_entity,
                    "gemini_api_key": gemini_key,
                    "gemini_model": gemini_model,
                }
            )
            cfg.save(updated)
            log.info("Settings saved by user")
            # Reset scholar agent so it picks up new key/model
            if "scholar" in st.session_state:
                del st.session_state["scholar"]
                del st.session_state["scholar_history"]
            st.success("Settings saved!")
            st.rerun()

    # --- Application Log ---
    st.divider()
    st.subheader("📋 Application Log")
    st.caption("Log file: `~/.notary_assistant/app.log`")
    log_lines = st.number_input("Lines to show", min_value=20, max_value=500, value=50, step=10)
    log_content = read_recent(int(log_lines))
    st.text_area("Recent log entries", value=log_content, height=300, label_visibility="collapsed")
    if st.button("Refresh Log"):
        st.rerun()
