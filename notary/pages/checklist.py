"""Pre-Flight Checklist page."""

from datetime import date

import streamlit as st

from notary import checklist as checklist_mod
from notary import records
from notary.pages.helpers import journal_link_options, parse_journal_id


def render_checklist(config: dict) -> None:
    st.title("✅ Pre-Flight Checklist")

    tab_check, tab_records = st.tabs(["Checklist", "Saved Records"])

    # ------------------------------------------------------------ Checklist
    with tab_check:
        st.markdown("Work through this checklist before completing each notarial act.")

        if "checklist_state" not in st.session_state:
            st.session_state["checklist_state"] = [False] * len(checklist_mod.PREFLIGHT_ITEMS)

        checked = []
        for i, item in enumerate(checklist_mod.PREFLIGHT_ITEMS):
            val = st.checkbox(item, value=st.session_state["checklist_state"][i], key=f"chk_{i}")
            checked.append(val)
            st.session_state["checklist_state"][i] = val

        num_checked = sum(checked)
        total = len(checklist_mod.PREFLIGHT_ITEMS)
        progress = num_checked / total

        st.divider()
        st.progress(progress, text=f"{num_checked} / {total} items complete")

        if num_checked == total:
            st.success("All items confirmed. You are ready to complete this notarial act!")

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
                        options=journal_link_options(),
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
                        journal_entry_id=parse_journal_id(cl_journal),
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
