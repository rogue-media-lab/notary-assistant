"""Notarial Journal page."""

import csv
import io
from datetime import date

import streamlit as st

from notary import journal as journal_mod
from notary import invoicing


def render_journal(config: dict) -> None:
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
                    journal_mod.add_entry(
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
        stats = journal_mod.get_summary_stats()
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

        entries = journal_mod.get_entries(
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
            st.divider()
            del_id = st.number_input("Entry ID to delete", min_value=1, step=1, key="del_id")
            if st.button("Delete Entry", type="secondary"):
                journal_mod.delete_entry(int(del_id))
                st.success(f"Entry #{del_id} deleted.")
                st.rerun()
        else:
            st.info("No journal entries found.")

    # --- Export ---
    with tab_export:
        st.markdown("Export your full journal to a CSV file for your records or tax preparation.")
        all_entries = journal_mod.get_entries(limit=100_000)
        if all_entries:
            buf = io.StringIO()
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
