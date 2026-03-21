"""Certificate Generator page."""

import streamlit as st

from notary.certificates import get_certificate_options


def render_certificates(config: dict) -> None:
    st.title("📜 Certificate Generator")
    st.markdown(
        "Select the appropriate certificate type. The statutory wording will appear below. "
        "Fill in the blanks and attach to the document."
    )

    _state = config.get("state") or "your state"
    cert_options = get_certificate_options(_state)
    cert_choice = st.selectbox("Certificate Type", list(cert_options.keys()))
    wording = cert_options[cert_choice]

    st.text_area("Certificate Wording", value=wording, height=300)

    st.info(
        f"Verify this wording against the current {_state} Notary Public Reference Manual "
        "before use. Statutory language may be amended."
    )

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
