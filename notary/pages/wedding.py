"""Wedding Officiant page."""

import csv
import io
from datetime import date

import streamlit as st

from notary import wedding as wedding_mod


def render_wedding(config: dict) -> None:
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

            scripts = wedding_mod.get_all_scripts()
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
                    wedding_mod.add_ceremony(
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
        ceremonies = wedding_mod.get_ceremonies(search=search)

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
            writer = csv.DictWriter(buf, fieldnames=ceremonies[0].keys())
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
        scripts = wedding_mod.get_all_scripts()
        script_names = [s["script_name"] for s in scripts]

        st.subheader("View / Edit Script")
        if script_names:
            selected = st.selectbox("Select Script", script_names, key="script_select")
            existing_text = wedding_mod.get_script_by_name(selected)
            edited_text = st.text_area("Script Text", value=existing_text, height=400, key="script_edit")
            col_save, col_del = st.columns(2)
            with col_save:
                if st.button("Save Changes", type="primary"):
                    wedding_mod.save_script(selected, edited_text)
                    st.success(f'"{selected}" saved.')
            with col_del:
                if st.button("Delete This Script", type="secondary"):
                    wedding_mod.delete_script(selected)
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
                    wedding_mod.save_script(new_name, new_text)
                    st.success(f'"{new_name}" added.')
                    st.rerun()
