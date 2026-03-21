"""Stamp and Certify Co — Notary Assistant
Streamlit single-page app with sidebar navigation.
"""

import io
from datetime import date, datetime
from pathlib import Path

import streamlit as st

from notary import config as cfg
from notary.db import initialize_schema
from notary import journal, wedding, certificates, checklist, invoicing, sessions, records
from notary.log import get_logger, read_recent

log = get_logger("notary.app")

# ---------------------------------------------------------------------------
# Page config (must be first Streamlit call)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Stamp and Certify Co",
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
def render_setup_page():
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
            county = st.text_input("County", placeholder="Richland")
        with col_state:
            state = st.text_input("State", placeholder="SC")

        st.subheader("Business Information")
        business_name = st.text_input("Business Name", value="Stamp and Certify Co")
        legal_entity = st.text_input("Legal Entity Name", value="Roberts and Associates LLC")
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
    st.markdown(f"## 🖋️ {config.get('business_name', 'Stamp and Certify Co')}")
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
# Page: Notary Scholar
# ---------------------------------------------------------------------------
def _journal_link_options() -> list[str]:
    """Return recent journal entries formatted for a selectbox."""
    entries = journal.get_entries(limit=20)
    opts = ["(none)"]
    for e in entries:
        opts.append(f"#{e['id']} — {e['act_date']} — {e['signer_name']} ({e['act_type']})")
    return opts


def _parse_journal_id(option: str) -> int | None:
    if option == "(none)":
        return None
    try:
        return int(option.split("—")[0].strip().lstrip("#"))
    except (ValueError, IndexError):
        return None


def render_scholar():
    st.title("⚖️ Notary Scholar")

    tab_chat, tab_sessions = st.tabs(["Chat", "Saved Sessions"])

    # ------------------------------------------------------------------ Chat
    with tab_chat:
        st.markdown(
            '<div class="upl-banner">'
            "<strong>Important:</strong> This assistant answers questions about SC notary law and procedures "
            "based on the SC Notary Public Reference Manual. It <strong>cannot</strong> draft documents, "
            "provide legal advice, or replace a licensed SC attorney."
            "</div>",
            unsafe_allow_html=True,
        )

        # --- Supplemental document uploader ---
        uploaded_file = st.file_uploader(
            "📎 Add a reference document (optional — drag & drop a PDF or text file)",
            type=["pdf", "md", "txt"],
            help="This document is held in memory only for this session. It is discarded when you clear the chat.",
        )

        # Discard stale agent objects from before app updates
        if "scholar" in st.session_state and not hasattr(st.session_state["scholar"], "get_transcript"):
            log.warning("Stale ScholarAgent detected (missing get_transcript) — reinitializing")
            del st.session_state["scholar"]
            st.session_state["scholar_history"] = []

        # Detect if the uploaded file changed — reinit agent if so
        uploaded_name = uploaded_file.name if uploaded_file else None
        prev_name = st.session_state.get("scholar_doc_name")

        if uploaded_name != prev_name:
            # File added, removed, or swapped — discard current agent
            if "scholar" in st.session_state:
                del st.session_state["scholar"]
            st.session_state["scholar_doc_name"] = uploaded_name
            st.session_state["scholar_history"] = []

        # Initialize agent (with or without supplemental doc)
        if "scholar" not in st.session_state:
            with st.spinner("Loading SC Notary Manual…"):
                try:
                    from notary.ai import ScholarAgent
                    if uploaded_file is not None:
                        sup_text = ScholarAgent.extract_uploaded_file(
                            uploaded_file.getvalue(), uploaded_file.name
                        )
                        st.session_state["scholar"] = ScholarAgent(
                            supplemental_content=sup_text,
                            supplemental_name=uploaded_file.name,
                        )
                        log.info("Scholar initialized with supplemental doc: %s", uploaded_file.name)
                        st.info(f"📎 Using supplemental doc: **{uploaded_file.name}**")
                    else:
                        st.session_state["scholar"] = ScholarAgent()
                        log.info("Scholar initialized (manual only)")
                    for w in st.session_state["scholar"].init_warnings:
                        st.warning(w)
                    st.session_state.setdefault("scholar_history", [])
                except Exception as e:
                    log.error("Scholar initialization failed: %s", e)
                    st.error(f"Could not start Notary Scholar: {e}")
                    return
        elif uploaded_file is not None and uploaded_name == prev_name:
            st.info(f"📎 Using supplemental doc: **{uploaded_file.name}**")

        # Toolbar
        col1, col2 = st.columns([6, 1])
        with col2:
            if st.button("Clear Chat", use_container_width=True):
                st.session_state["scholar"].reset()
                st.session_state["scholar_history"] = []
                st.session_state["show_save_form"] = False
                st.rerun()

        # Chat history display
        for msg in st.session_state.get("scholar_history", []):
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # Chat input
        if prompt := st.chat_input("Ask a question about SC notary law or procedures…"):
            st.session_state["scholar_history"].append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            with st.chat_message("assistant"):
                with st.spinner("Consulting the manual…"):
                    try:
                        response = st.session_state["scholar"].send(prompt)
                    except Exception as e:
                        response = f"Error communicating with Gemini: {e}"
                st.markdown(response)
                st.session_state["scholar_history"].append({"role": "assistant", "content": response})

        # Save session — only show when there's history
        if st.session_state.get("scholar_history"):
            st.divider()
            if st.button("💾 Save This Session", use_container_width=False):
                st.session_state["show_save_form"] = True

            if st.session_state.get("show_save_form"):
                with st.form("save_session_form"):
                    session_label = st.text_input(
                        "Session Label *",
                        placeholder="e.g., Smith deed of trust — acknowledgment question",
                    )
                    journal_option = st.selectbox(
                        "Link to Journal Entry (optional)",
                        options=_journal_link_options(),
                    )
                    save_submitted = st.form_submit_button("Save Session", type="primary")

                if save_submitted:
                    if not session_label:
                        st.error("Please enter a label for this session.")
                    else:
                        with st.spinner("Generating summary…"):
                            # Build transcript from session_state (always reliable)
                            history = st.session_state.get("scholar_history", [])
                            transcript_parts = []
                            for msg in history:
                                role = "Notary" if msg["role"] == "user" else "Scholar"
                                transcript_parts.append(f"{role}:\n{msg['content']}")
                            transcript = "\n\n---\n\n".join(transcript_parts)

                            try:
                                summary = st.session_state["scholar"].summarize()
                                log.info("Session summary generated for label: %s", session_label)
                            except Exception as e:
                                summary = "(Summary unavailable)"
                                log.error("Summary generation failed: %s", e)

                            journal_id = _parse_journal_id(journal_option)
                            sessions.save_session(
                                label=session_label,
                                transcript=transcript,
                                summary=summary,
                                journal_entry_id=journal_id,
                            )
                        log.info("Chat session saved: '%s' (journal_entry_id=%s)", session_label, journal_id)
                        st.success(f'Session "{session_label}" saved!')
                        st.session_state["show_save_form"] = False

    # -------------------------------------------------------- Saved Sessions
    with tab_sessions:
        st.subheader("Saved Chat Sessions")
        all_sessions = sessions.get_sessions()

        if not all_sessions:
            st.info("No sessions saved yet. Complete a chat and click 'Save This Session'.")
        else:
            for s in all_sessions:
                created = s["created_at"][:10]
                header = f"**{s['label']}** — {created}"
                if s.get("journal_entry_id"):
                    header += f" · 📒 Journal #{s['journal_entry_id']}"
                with st.expander(header):
                    if s.get("summary"):
                        st.markdown("**Summary**")
                        st.markdown(s["summary"])
                        st.divider()
                    full = sessions.get_session(s["id"])
                    if full:
                        st.markdown("**Full Transcript**")
                        st.markdown(full["transcript"])
                    col_dl, col_del = st.columns([3, 1])
                    with col_dl:
                        if full:
                            st.download_button(
                                "⬇️ Download Transcript",
                                data=full["transcript"],
                                file_name=f"session_{s['id']}_{s['label'][:30]}.txt",
                                mime="text/plain",
                                key=f"dl_session_{s['id']}",
                            )
                    with col_del:
                        if st.button("Delete", key=f"del_session_{s['id']}", type="secondary"):
                            sessions.delete_session(s["id"])
                            st.rerun()


# ---------------------------------------------------------------------------
# Page: Notarial Journal
# ---------------------------------------------------------------------------
def render_journal():
    st.title("📒 Notarial Journal")

    tab_log, tab_view, tab_export = st.tabs(["Log New Act", "View & Search", "Export"])

    # --- Log New Act ---
    with tab_log:
        with st.form("journal_form"):
            col1, col2 = st.columns(2)
            with col1:
                act_date = st.date_input("Date of Act *", value=date.today())
                act_time = st.time_input("Time of Act", value=None)
                signer_name = st.text_input("Signer's Full Name *")
                document_type = st.text_input("Document Type", placeholder="Deed, Affidavit, Power of Attorney…")
            with col2:
                act_type = st.selectbox(
                    "Act Type *",
                    ["Acknowledgment", "Jurat", "Oath/Affirmation", "Copy Certification", "Signature Witnessing", "Other"],
                )
                id_type = st.selectbox(
                    "ID Type",
                    ["", "Driver's License", "State ID", "Passport", "Military ID", "Other"],
                )
                id_number = st.text_input("ID Number (last 4 digits or identifier)")
                num_signatures = st.number_input("Number of Signatures", min_value=1, value=1)

            col3, col4 = st.columns(2)
            with col3:
                fee_charged = st.number_input(
                    "Notary Fee Charged ($)",
                    min_value=0.0,
                    value=float(num_signatures * config.get("fee_per_signature", invoicing.DEFAULT_FEE_PER_SIGNATURE)),
                    step=5.0,
                )
            with col4:
                travel_fee = st.number_input(
                    "Travel Fee ($)",
                    min_value=0.0,
                    value=float(config.get("travel_fee_default", 0.0)),
                    step=5.0,
                )

            notes = st.text_area("Notes", placeholder="Optional notes about this act…")

            submitted = st.form_submit_button("Save Journal Entry", type="primary")
            if submitted:
                if not signer_name:
                    st.error("Signer's name is required.")
                else:
                    journal.add_entry(
                        act_date=act_date.isoformat(),
                        signer_name=signer_name,
                        act_type=act_type,
                        act_time=act_time.strftime("%H:%M") if act_time else "",
                        document_type=document_type,
                        id_type=id_type,
                        id_number=id_number,
                        num_signatures=num_signatures,
                        fee_charged=fee_charged,
                        travel_fee=travel_fee,
                        notes=notes,
                    )
                    st.success(f"Journal entry saved for {signer_name}.")

    # --- View & Search ---
    with tab_view:
        stats = journal.get_summary_stats()
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Acts Recorded", stats["total_acts"])
        col2.metric(f"YTD Fees ({date.today().year})", f"${stats['ytd_fees']:.2f}")
        col3.metric("Act Types", len(stats["acts_by_type"]))

        st.divider()

        col_s, col_start, col_end = st.columns(3)
        with col_s:
            search = st.text_input("Search", placeholder="Name, document, act type…")
        with col_start:
            start_date = st.date_input("From", value=None, key="j_start")
        with col_end:
            end_date = st.date_input("To", value=None, key="j_end")

        entries = journal.get_entries(
            search=search,
            start_date=start_date.isoformat() if start_date else "",
            end_date=end_date.isoformat() if end_date else "",
        )

        if entries:
            st.dataframe(
                entries,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "id": st.column_config.NumberColumn("ID", width="small"),
                    "act_date": "Date",
                    "act_time": "Time",
                    "signer_name": "Signer",
                    "document_type": "Document",
                    "act_type": "Act Type",
                    "id_type": "ID Type",
                    "id_number": "ID #",
                    "num_signatures": st.column_config.NumberColumn("Sigs", width="small"),
                    "fee_charged": st.column_config.NumberColumn("Notary Fee", format="$%.2f"),
                    "travel_fee": st.column_config.NumberColumn("Travel Fee", format="$%.2f"),
                    "notes": "Notes",
                    "created_at": None,  # hide
                },
            )
            # Delete
            st.divider()
            del_id = st.number_input("Entry ID to delete", min_value=1, step=1, key="del_id")
            if st.button("Delete Entry", type="secondary"):
                journal.delete_entry(int(del_id))
                st.success(f"Entry #{del_id} deleted.")
                st.rerun()
        else:
            st.info("No journal entries found.")

    # --- Export ---
    with tab_export:
        st.markdown("Export your full journal to a CSV file for your records or tax preparation.")
        all_entries = journal.get_entries(limit=100_000)
        if all_entries:
            import csv, io as _io
            buf = _io.StringIO()
            writer = csv.DictWriter(buf, fieldnames=all_entries[0].keys())
            writer.writeheader()
            writer.writerows(all_entries)
            st.download_button(
                "⬇️ Download Journal CSV",
                data=buf.getvalue(),
                file_name=f"notary_journal_{date.today().isoformat()}.csv",
                mime="text/csv",
            )
        else:
            st.info("No entries to export yet.")


# ---------------------------------------------------------------------------
# Page: Fee Calculator & Invoice
# ---------------------------------------------------------------------------
def render_fee_calculator():
    st.title("💰 Fee Calculator & Invoice")

    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("Fee Calculator")
        num_sigs = st.number_input("Number of Signatures", min_value=1, value=1, key="inv_sigs")
        travel = st.number_input(
            "Travel Fee ($)",
            min_value=0.0,
            value=float(config.get("travel_fee_default", 0.0)),
            step=5.0,
            key="inv_travel",
        )
        fee_per_sig = config.get("fee_per_signature", invoicing.DEFAULT_FEE_PER_SIGNATURE)
        breakdown = invoicing.calculate_fee(num_sigs, travel, fee_per_sig)

        st.divider()
        m1, m2, m3 = st.columns(3)
        m1.metric("Notary Fee", f"${breakdown['notary_fee']:.2f}")
        m2.metric("Travel Fee", f"${breakdown['travel_fee']:.2f}")
        m3.metric("Total Due", f"${breakdown['total']:.2f}")
        st.caption(f"Statutory maximum: ${fee_per_sig:.2f} per signature")

    with col_right:
        st.subheader("Generate Invoice")
        with st.form("invoice_form"):
            invoice_number = st.text_input(
                "Invoice Number",
                value=f"INV-{datetime.now().strftime('%Y%m%d-%H%M')}",
            )
            invoice_date = st.date_input("Invoice Date", value=date.today())
            client_name = st.text_input("Client Name *")
            doc_type = st.text_input("Document Type", placeholder="e.g., Deed of Trust")

            generate = st.form_submit_button("Generate Invoice", type="primary")

        if generate:
            if not client_name:
                st.error("Client name is required.")
            else:
                invoice_text = invoicing.generate_invoice_text(
                    invoice_number=invoice_number,
                    invoice_date=invoice_date.strftime("%B %d, %Y"),
                    client_name=client_name,
                    document_type=doc_type,
                    fee_breakdown=invoicing.calculate_fee(num_sigs, travel, fee_per_sig),
                    cfg=config,
                )
                st.text_area("Invoice Preview", value=invoice_text, height=350)
                st.download_button(
                    "⬇️ Download Invoice (.txt)",
                    data=invoice_text,
                    file_name=f"invoice_{invoice_number}.txt",
                    mime="text/plain",
                )


# ---------------------------------------------------------------------------
# Page: Certificate Generator
# ---------------------------------------------------------------------------
def render_certificates():
    st.title("📜 Certificate Generator")
    st.markdown(
        "Select the appropriate certificate type. The statutory wording will appear below. "
        "Fill in the blanks and attach to the document."
    )

    cert_choice = st.selectbox("Certificate Type", list(certificates.CERTIFICATE_OPTIONS.keys()))
    wording = certificates.CERTIFICATE_OPTIONS[cert_choice]

    st.text_area("Certificate Wording", value=wording, height=300)

    st.info(
        "Verify this wording against the current SC Notary Public Reference Manual "
        "before use. Statutory language may be amended."
    )

    # Print via browser
    if st.button("🖨️ Print Certificate Wording"):
        print_js = f"""
        <script>
        var w = window.open('', '_blank');
        w.document.write('<pre style="font-family:monospace;font-size:14px;padding:20px;">'
            + {repr(wording)} + '</pre>');
        w.document.close();
        w.print();
        </script>
        """
        st.components.v1.html(print_js, height=0)


# ---------------------------------------------------------------------------
# Page: Pre-Flight Checklist
# ---------------------------------------------------------------------------
def render_checklist():
    st.title("✅ Pre-Flight Checklist")

    tab_check, tab_records = st.tabs(["Checklist", "Saved Records"])

    # ------------------------------------------------------------ Checklist
    with tab_check:
        st.markdown("Work through this checklist before completing each notarial act.")

        if "checklist_state" not in st.session_state:
            st.session_state["checklist_state"] = [False] * len(checklist.PREFLIGHT_ITEMS)

        checked = []
        for i, item in enumerate(checklist.PREFLIGHT_ITEMS):
            val = st.checkbox(item, value=st.session_state["checklist_state"][i], key=f"chk_{i}")
            checked.append(val)
            st.session_state["checklist_state"][i] = val

        num_checked = sum(checked)
        total = len(checklist.PREFLIGHT_ITEMS)
        progress = num_checked / total

        st.divider()
        st.progress(progress, text=f"{num_checked} / {total} items complete")

        if num_checked == total:
            st.success("All items confirmed. You are ready to complete this notarial act!")

            # Save record form appears only when checklist is complete
            st.divider()
            st.markdown("#### Save Record for This Client")
            with st.form("save_checklist_form"):
                col1, col2 = st.columns(2)
                with col1:
                    cl_client = st.text_input("Client Name *")
                    cl_doc_type = st.text_input("Document Type", placeholder="Deed, Affidavit…")
                with col2:
                    cl_date = st.date_input("Date of Act", value=date.today())
                    cl_journal = st.selectbox(
                        "Link to Journal Entry (optional)",
                        options=_journal_link_options(),
                    )
                cl_notes = st.text_input("Notes (optional)")
                cl_save = st.form_submit_button("Save Checklist Record", type="primary")

            if cl_save:
                if not cl_client:
                    st.error("Client name is required.")
                else:
                    records.save_record(
                        record_date=cl_date.isoformat(),
                        client_name=cl_client,
                        document_type=cl_doc_type,
                        items_checked=num_checked,
                        total_items=total,
                        journal_entry_id=_parse_journal_id(cl_journal),
                        notes=cl_notes,
                    )
                    st.success(f"Record saved for {cl_client}.")
                    st.session_state["checklist_state"] = [False] * total
                    st.rerun()

        elif num_checked > 0:
            st.info(f"{total - num_checked} item(s) remaining.")

        if st.button("Reset Checklist"):
            st.session_state["checklist_state"] = [False] * total
            st.rerun()

    # --------------------------------------------------------- Saved Records
    with tab_records:
        st.subheader("Saved Checklist Records")
        search = st.text_input("Search by client or document type", key="cl_search")
        all_records = records.get_records(search=search)

        if not all_records:
            st.info("No records saved yet.")
        else:
            st.dataframe(
                all_records,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "id": st.column_config.NumberColumn("ID", width="small"),
                    "record_date": "Date",
                    "client_name": "Client",
                    "document_type": "Document",
                    "items_checked": st.column_config.NumberColumn("✓", width="small"),
                    "total_items": st.column_config.NumberColumn("Total", width="small"),
                    "journal_entry_id": st.column_config.NumberColumn("Journal #", width="small"),
                    "notes": "Notes",
                    "created_at": None,
                },
            )
            st.divider()
            del_id = st.number_input("Record ID to delete", min_value=1, step=1, key="del_cl_id")
            if st.button("Delete Record", type="secondary", key="del_cl_btn"):
                records.delete_record(int(del_id))
                st.success(f"Record #{del_id} deleted.")
                st.rerun()


# ---------------------------------------------------------------------------
# Page: Wedding Officiant
# ---------------------------------------------------------------------------
def render_wedding():
    st.title("💍 Wedding Officiant")

    tab_log, tab_view, tab_scripts = st.tabs(["Log Ceremony", "View Ceremonies", "Ceremony Scripts"])

    # --- Log Ceremony ---
    with tab_log:
        with st.form("wedding_form"):
            col1, col2 = st.columns(2)
            with col1:
                ceremony_date = st.date_input("Ceremony Date *", value=date.today())
                ceremony_time = st.time_input("Ceremony Time", value=None)
                partner_1 = st.text_input("Partner 1 Name *")
                partner_2 = st.text_input("Partner 2 Name *")
            with col2:
                location = st.text_input("Venue / Location")
                city = st.text_input("City")
                state = st.text_input("State", value=config.get("state", ""))
                fee_charged = st.number_input("Fee Charged ($)", min_value=0.0, value=0.0, step=25.0)

            scripts = wedding.get_all_scripts()
            script_names = [s["script_name"] for s in scripts]
            script_used = st.selectbox(
                "Script Used",
                options=["(none)"] + script_names,
            )
            notes = st.text_area("Notes")

            submitted = st.form_submit_button("Save Ceremony Record", type="primary")
            if submitted:
                if not partner_1 or not partner_2:
                    st.error("Both partner names are required.")
                else:
                    wedding.add_ceremony(
                        ceremony_date=ceremony_date.isoformat(),
                        partner_1_name=partner_1,
                        partner_2_name=partner_2,
                        ceremony_time=ceremony_time.strftime("%H:%M") if ceremony_time else "",
                        location=location,
                        city=city,
                        state=state,
                        fee_charged=fee_charged,
                        script_used=script_used if script_used != "(none)" else "",
                        notes=notes,
                    )
                    st.success(f"Ceremony for {partner_1} & {partner_2} saved!")

    # --- View Ceremonies ---
    with tab_view:
        search = st.text_input("Search ceremonies", placeholder="Name, location, city…")
        ceremonies = wedding.get_ceremonies(search=search)

        if ceremonies:
            st.dataframe(
                ceremonies,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "id": st.column_config.NumberColumn("ID", width="small"),
                    "ceremony_date": "Date",
                    "ceremony_time": "Time",
                    "partner_1_name": "Partner 1",
                    "partner_2_name": "Partner 2",
                    "location": "Venue",
                    "city": "City",
                    "state": "State",
                    "fee_charged": st.column_config.NumberColumn("Fee", format="$%.2f"),
                    "script_used": "Script",
                    "notes": "Notes",
                    "created_at": None,
                },
            )
            st.divider()
            buf = io.StringIO()
            import csv as _csv
            writer = _csv.DictWriter(buf, fieldnames=ceremonies[0].keys())
            writer.writeheader()
            writer.writerows(ceremonies)
            st.download_button(
                "⬇️ Export Ceremonies CSV",
                data=buf.getvalue(),
                file_name=f"weddings_{date.today().isoformat()}.csv",
                mime="text/csv",
            )
        else:
            st.info("No ceremony records found.")

    # --- Ceremony Scripts ---
    with tab_scripts:
        scripts = wedding.get_all_scripts()
        script_names = [s["script_name"] for s in scripts]

        st.subheader("View / Edit Script")
        if script_names:
            selected = st.selectbox("Select Script", script_names, key="script_select")
            existing_text = wedding.get_script_by_name(selected)
            edited_text = st.text_area("Script Text", value=existing_text, height=400, key="script_edit")
            col_save, col_del = st.columns(2)
            with col_save:
                if st.button("Save Changes", type="primary"):
                    wedding.save_script(selected, edited_text)
                    st.success(f'"{selected}" saved.')
            with col_del:
                if st.button("Delete This Script", type="secondary"):
                    wedding.delete_script(selected)
                    st.success(f'"{selected}" deleted.')
                    st.rerun()
        else:
            st.info("No scripts yet. Add one below.")

        st.divider()
        st.subheader("Add New Script")
        with st.form("new_script_form"):
            new_name = st.text_input("Script Name *")
            new_text = st.text_area("Script Text *", height=300)
            if st.form_submit_button("Add Script", type="primary"):
                if not new_name or not new_text:
                    st.error("Both name and text are required.")
                else:
                    wedding.save_script(new_name, new_text)
                    st.success(f'"{new_name}" added.')
                    st.rerun()


# ---------------------------------------------------------------------------
# Page: Settings
# ---------------------------------------------------------------------------
def render_settings():
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
                value=float(config.get("fee_per_signature", 5.0)),
                step=0.50,
                help="Your state's maximum statutory notary fee per signature.",
            )

        st.subheader("Business Information")
        business_name = st.text_input("Business Name", value=config.get("business_name", "Stamp and Certify Co"))
        legal_entity = st.text_input("Legal Entity Name", value=config.get("legal_entity", "Roberts and Associates LLC"))

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
    st.caption(f"Log file: `~/.notary_assistant/app.log`")
    log_lines = st.number_input("Lines to show", min_value=20, max_value=500, value=50, step=10)
    log_content = read_recent(int(log_lines))
    st.text_area("Recent log entries", value=log_content, height=300, label_visibility="collapsed")
    if st.button("Refresh Log"):
        st.rerun()


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------
log.debug("App rendered — page: %s", page)
if page == "Notary Scholar":
    render_scholar()
elif page == "Notarial Journal":
    render_journal()
elif page == "Fee Calculator & Invoice":
    render_fee_calculator()
elif page == "Certificate Generator":
    render_certificates()
elif page == "Pre-Flight Checklist":
    render_checklist()
elif page == "Wedding Officiant":
    render_wedding()
elif page == "Settings":
    render_settings()
