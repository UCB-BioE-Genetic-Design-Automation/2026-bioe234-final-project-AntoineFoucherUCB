from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

import streamlit as st
from dotenv import load_dotenv

from mcp_gemini_engine import MCPGeminiEngine, EngineState, ToolEvent


PROJECT_DIR = Path(__file__).parent
UPLOAD_DIR = PROJECT_DIR / "uploads"


def _ensure_upload_dir() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _get_engine() -> MCPGeminiEngine:
    if "engine" not in st.session_state:
        load_dotenv()
        st.session_state.engine = MCPGeminiEngine(project_dir=PROJECT_DIR)
    return st.session_state.engine


def _init_session_state() -> None:
    st.session_state.setdefault("mode", "menu")
    st.session_state.setdefault("uploaded_file_path", None)
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("last_doc_path", None)


def _append_message(role: str, text: str) -> None:
    st.session_state.messages.append({"role": role, "text": text})


def _rerun() -> None:
    # Streamlit >=1.27 uses st.rerun(); keep fallback for older builds.
    if hasattr(st, "rerun"):
        st.rerun()
    elif hasattr(st, "experimental_rerun"):
        st.experimental_rerun()


async def _send_and_render(user_text: str) -> None:
    engine = _get_engine()
    _append_message("user", user_text)
    reply, state = await engine.send_message(user_text)
    if reply:
        _append_message("assistant", reply)
    if state.last_generated_doc_path:
        st.session_state.last_doc_path = state.last_generated_doc_path


def _render_chat_area() -> None:
    st.subheader("Questionnaire chat")
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f"**You:** {msg['text']}")
        else:
            st.markdown(f"**Assistant:** {msg['text']}")

    user_input = st.text_input("Your message", key="chat_input")
    if st.button("Send", type="primary"):
        if user_input.strip():
            asyncio.run(_send_and_render(user_input.strip()))
            _rerun()


def _render_debug_panel(state: Optional[EngineState]) -> None:
    if state is None:
        return
    with st.expander("Debug details"):
        st.write("Last generated doc path:", state.last_generated_doc_path)
        if state.last_tool_events:
            st.write("Last tool calls:")
            for ev in state.last_tool_events[-5:]:
                st.json(
                    {
                        "tool_name": ev.tool_name,
                        "args": ev.args,
                        "response_preview": str(ev.response)[:500],
                    }
                )


def main() -> None:
    st.set_page_config(page_title="BUA Generator", layout="wide")
    _ensure_upload_dir()
    _init_session_state()
    engine = _get_engine()

    st.title("Biological Use Authorization (BUA) Assistant")

    col_left, col_right = st.columns([2, 1])

    with col_left:
        if st.session_state.mode == "menu":
            st.markdown("Choose how you want to start:")
            if st.button("Start questionnaire"):
                st.session_state.mode = "questionnaire"
                asyncio.run(_send_and_render("Start the BUA questionnaire."))
                _rerun()

            uploaded = st.file_uploader(
                "Upload existing BUA / biosafety document (PDF, DOCX, etc.)",
                type=["pdf", "docx", "txt"],
            )
            if uploaded is not None and st.button("Use uploaded document"):
                _ensure_upload_dir()
                dest = UPLOAD_DIR / uploaded.name
                dest.write_bytes(uploaded.read())
                st.session_state.uploaded_file_path = str(dest)
                st.session_state.mode = "questionnaire"
                prompt = (
                    "I have uploaded an existing BUA or biosafety document at this path: "
                    f"{st.session_state.uploaded_file_path}. "
                    "Use the MCP tools to parse it, then continue the questionnaire to fill in any gaps."
                )
                asyncio.run(_send_and_render(prompt))
                _rerun()

        else:
            _render_chat_area()

    with col_right:
        st.subheader("Generated BUA document")
        doc_path = st.session_state.get("last_doc_path")
        if doc_path and Path(doc_path).exists():
            st.success("Latest BUA document generated.")
            with open(doc_path, "rb") as f:
                st.download_button(
                    label="Download BUA .docx",
                    data=f,
                    file_name=Path(doc_path).name,
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
        else:
            st.info("No BUA document has been generated yet.")

        feedback = st.text_area(
            "Feedback / critique (used to refine the BUA and possibly regenerate the document)",
            height=150,
        )
        if st.button("Submit feedback"):
            if feedback.strip():
                asyncio.run(
                    _send_and_render(
                        "Here is user feedback on the current BUA. "
                        "Use it, along with MCP tools, to update the BUA state and regenerate the document if helpful:\n\n"
                        + feedback.strip()
                    )
                )
                _rerun()

    _render_debug_panel(getattr(engine, "state", None))


if __name__ == "__main__":
    main()

