"""Notary Scholar page — Gemini-powered Q&A."""

import streamlit as st

from notary import sessions
from notary.log import get_logger
from notary.pages.helpers import journal_link_options, parse_journal_id

log = get_logger("notary.pages.scholar")


def render_scholar(config: dict) -> None:
    st.title("⚖️ Notary Scholar")

    tab_chat, tab_sessions = st.tabs(["Chat", "Saved Sessions"])

    # ------------------------------------------------------------------ Chat
    with tab_chat:
        _state = config.get("state") or "your state"
        st.markdown(
            '<div class="upl-banner">'
            f"<strong>Important:</strong> This assistant answers questions about {_state} notary law and procedures "
            f"based on your state's Notary Public Reference Manual. It <strong>cannot</strong> draft documents, "
            f"provide legal advice, or replace a licensed {_state} attorney."
            "</div>",
            unsafe_allow_html=True,
        )

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
            if "scholar" in st.session_state:
                del st.session_state["scholar"]
            st.session_state["scholar_doc_name"] = uploaded_name
            st.session_state["scholar_history"] = []

        # Initialize agent (with or without supplemental doc)
        if "scholar" not in st.session_state:
            with st.spinner("Loading Notary Manual…"):
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
        if prompt := st.chat_input(f"Ask a question about {_state} notary law or procedures…"):
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
                        options=journal_link_options(),
                    )
                    save_submitted = st.form_submit_button("Save Session", type="primary")

                if save_submitted:
                    if not session_label:
                        st.error("Please enter a label for this session.")
                    else:
                        with st.spinner("Generating summary…"):
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

                            journal_id = parse_journal_id(journal_option)
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
