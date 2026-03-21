"""Fee Calculator & Invoice page."""

from datetime import date, datetime

import streamlit as st

from notary import invoicing


def render_fee_calculator(config: dict) -> None:
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
